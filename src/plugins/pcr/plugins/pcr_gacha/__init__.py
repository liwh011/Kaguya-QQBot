# import nonebot
from .gacha import Gacha
from src.plugins.pcr import chara
from src.util import DailyNumberLimiter, concat_pic, pic2b64
from src.Service import Service
from src import util
from nonebot.adapters.cqhttp.message import Message, MessageSegment
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from nonebot.adapters.cqhttp import Bot
from nonebot import logger
from collections import defaultdict
import random
import os
from nonebot import get_driver

# from .config import Config

global_config = get_driver().config
# config = Config(**global_config.dict())


try:
    import ujson as json
except:
    import json


sv_help = '''
[星乃来发十连] 转蛋模拟
[星乃来发单抽] 转蛋模拟
[星乃来一井] 4w5钻！
[查看卡池] 模拟卡池&出率
[切换卡池] 更换模拟卡池
'''.strip()
sv = Service('pcr_gacha')
jewel_limit = DailyNumberLimiter(6000)
tenjo_limit = DailyNumberLimiter(10)

JEWEL_EXCEED_NOTICE = f'您今天已经抽过{jewel_limit.max}钻了，欢迎明早5点后再来！'
TENJO_EXCEED_NOTICE = f'您今天已经抽过{tenjo_limit.max}张天井券了，欢迎明早5点后再来！'
POOL = ('MIX', 'JP', 'TW', 'BL')
DEFAULT_POOL = POOL[0]

_pool_config_file = os.path.expanduser('~/.hoshino/group_pool_config.json')
_group_pool = {}
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    logger.warning(
        'group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)


def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)


gacha_10_aliases = ('抽十连', '十连', '十连！', '十连抽', '来个十连', '来发十连', '来次十连', '抽个十连', '抽发十连', '抽次十连', '十连扭蛋', '扭蛋十连',
                    '10连', '10连！', '10连抽', '来个10连', '来发10连', '来次10连', '抽个10连', '抽发10连', '抽次10连', '10连扭蛋', '扭蛋10连',
                    '十連', '十連！', '十連抽', '來個十連', '來發十連', '來次十連', '抽個十連', '抽發十連', '抽次十連', '十連轉蛋', '轉蛋十連',
                    '10連', '10連！', '10連抽', '來個10連', '來發10連', '來次10連', '抽個10連', '抽發10連', '抽次10連', '10連轉蛋', '轉蛋10連')
gacha_1_aliases = ('单抽', '单抽！', '来发单抽', '来个单抽', '来次单抽', '扭蛋单抽', '单抽扭蛋',
                   '單抽', '單抽！', '來發單抽', '來個單抽', '來次單抽', '轉蛋單抽', '單抽轉蛋')
gacha_300_aliases = ('抽一井', '来一井', '来发井', '抽发井',
                     '天井扭蛋', '扭蛋天井', '天井轉蛋', '轉蛋天井')


@sv.on_fullmatch(('卡池资讯', '查看卡池', '看看卡池', '康康卡池', '卡池資訊', '看看up', '看看UP'))
async def gacha_info(bot, event: GroupMessageEvent):
    gid = str(event.group_id)
    gacha = Gacha(_group_pool[gid])
    up_chara = gacha.up
    up_chara = map(lambda x: str(
        chara.fromname(x, star=3).icon.cqcode) + x, up_chara)
    up_chara = '\n'.join(up_chara)
    await bot.send(event, f"本期卡池主打的角色：\n{up_chara}\nUP角色合计={(gacha.up_prob/10):.1f}% 3★出率={(gacha.s3_prob)/10:.1f}%")


POOL_NAME_TIP = '请选择以下卡池\n> 切换卡池jp\n> 切换卡池tw\n> 切换卡池b\n> 切换卡池mix'


@sv.on_command(('切换卡池', '选择卡池', '切換卡池', '選擇卡池'), is_manage_func=True)
async def set_pool(bot, event: GroupMessageEvent):
    name = util.normalize_str(event.message.extract_plain_text())
    if not name:
        await bot.finish(event, POOL_NAME_TIP, at_sender=True)
    elif name in ('国', '国服', 'cn'):
        await bot.finish(event, '请选择以下卡池\n> 选择卡池 b服\n> 选择卡池 台服')
    elif name in ('b', 'b服', 'bl', 'bilibili'):
        name = 'BL'
    elif name in ('台', '台服', 'tw', 'sonet'):
        name = 'TW'
    elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
        name = 'JP'
    elif name in ('混', '混合', 'mix'):
        name = 'MIX'
    else:
        await bot.finish(event, f'未知服务器地区 {POOL_NAME_TIP}', at_sender=True)
    gid = str(event.group_id)
    _group_pool[gid] = name
    dump_pool_config()
    await bot.send(event, f'卡池已切换为{name}池', at_sender=True)
    await gacha_info(bot, event)


async def check_jewel_num(bot: Bot, event: GroupMessageEvent):
    if not jewel_limit.check(event.user_id):
        await bot.finish(event, JEWEL_EXCEED_NOTICE, at_sender=True)


async def check_tenjo_num(bot, event: GroupMessageEvent):
    if not tenjo_limit.check(event.user_id):
        await bot.finish(event, TENJO_EXCEED_NOTICE, at_sender=True)


@sv.on_startswith(gacha_1_aliases, only_to_me=False)
async def gacha_1(bot, event: GroupMessageEvent):

    await check_jewel_num(bot, event)
    jewel_limit.increase(event.user_id, 150)

    gid = str(event.group_id)
    gacha = Gacha(_group_pool[gid])
    chara, hiishi = gacha.gacha_one(
        gacha.up_prob, gacha.s3_prob, gacha.s2_prob)
    silence_time = hiishi * 60

    res = chara.icon.cqcode + f'{chara.name} {"★"*chara.star}'
    # await silence(ev, silence_time)
    await bot.send(event, '素敵な仲間が増えますよ！\n'+res, at_sender=True)


@sv.on_startswith(gacha_10_aliases, only_to_me=False)
async def gacha_10(bot, event: GroupMessageEvent):
    SUPER_LUCKY_LINE = 170

    await check_jewel_num(bot, event)
    jewel_limit.increase(event.user_id, 1500)

    gid = str(event.group_id)
    gacha = Gacha(_group_pool[gid])
    result, hiishi = gacha.gacha_ten()
    silence_time = hiishi * 6 if hiishi < SUPER_LUCKY_LINE else hiishi * 60

    res1 = chara.gen_team_pic(result[:5], star_slot_verbose=False)
    res2 = chara.gen_team_pic(result[5:], star_slot_verbose=False)
    res = concat_pic([res1, res2])
    res = pic2b64(res)
    res = MessageSegment.image(res)
    result = [f'{c.name}{"★"*c.star}' for c in result]
    res1 = ' '.join(result[0:5])
    res2 = ' '.join(result[5:])
    res = res + f'\n{res1}\n{res2}'
    msg = f'素敵な仲間が増えますよ！\n' + res
    if hiishi >= SUPER_LUCKY_LINE:
        await bot.send(event, '恭喜海豹！おめでとうございます！')
    await bot.send(event, msg, at_sender=True)
    # await silence(event, silence_time)


@sv.on_startswith(gacha_300_aliases, only_to_me=False)
async def gacha_300(bot, event: GroupMessageEvent):

    await check_tenjo_num(bot, event)
    tenjo_limit.increase(event.user_id)

    gid = str(event.group_id)
    gacha = Gacha(_group_pool[gid])
    result = gacha.gacha_tenjou()
    up = len(result['up'])
    s3 = len(result['s3'])
    s2 = len(result['s2'])
    s1 = len(result['s1'])

    res = [*(result['up']), *(result['s3'])]
    random.shuffle(res)
    lenth = len(res)
    if lenth <= 0:
        res = "竟...竟然没有3★？！"
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(
                res[i:j], star_slot_verbose=False))
        res = concat_pic(pics)
        res = pic2b64(res)
        res = MessageSegment.image(file=res)

    msg = f"\n素敵な仲間が増えますよ！\n" + \
          res + "\n" + \
          f"★★★×{up+s3} ★★×{s2} ★×{s1}\n" + \
          f"获得记忆碎片×{100*up}与女神秘石×{50*(up+s3) + 10*s2 + s1}！\n第{result['first_up_pos']}抽首次获得up角色" if up else f"获得女神秘石{50*(up+s3) + 10*s2 + s1}个！\n"

    if up == 0 and s3 == 0:
        msg += "太惨了，咱们还是退款删游吧...\n"
    elif up == 0 and s3 > 7:
        msg += "up呢？我的up呢？\n"
    elif up == 0 and s3 <= 3:
        msg += "这位酋长，梦幻包考虑一下？\n"
    elif up == 0:
        msg += "据说天井的概率只有12.16%\n"
    elif up <= 2:
        if result['first_up_pos'] < 50:
            msg += "你的喜悦我收到了，滚去喂鲨鱼吧！\n"
        elif result['first_up_pos'] < 100:
            msg += "已经可以了，您已经很欧了\n"
        elif result['first_up_pos'] > 290:
            msg += "标 准 结 局\n"
        elif result['first_up_pos'] > 250:
            msg += "补井还是不补井，这是一个问题...\n"
        else:
            msg += "期望之内，亚洲水平\n"
    elif up == 3:
        msg += "抽井母五一气呵成！多出30等专武～\n"
    elif up >= 4:
        msg += "记忆碎片一大堆！您是托吧？\n"

    await bot.send(event, msg, at_sender=True)
    silence_time = (100*up + 50*(up+s3) + 10*s2 + s1) * 1
    # await silence(event, silence_time)


@sv.on_startswith('氪金')
async def kakin(bot, event: GroupMessageEvent):
    if event.user_id not in bot.config.SUPERUSERS:
        return
    count = 0
    for m in event.get_message():
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            jewel_limit.reset(uid)
            tenjo_limit.reset(uid)
            count += 1
    if count:
        await bot.send(event, f"已为{count}位用户充值完毕！谢谢惠顾～")
