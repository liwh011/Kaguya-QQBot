
from nonebot.adapters import Event
from nonebot.adapters.cqhttp.event import MessageEvent
from src.util import FreqLimiter

from src.plugins.pcr import chara
from . import sv

lmt = FreqLimiter(5)

@sv.on_endswith(('是谁', '是誰'))
@sv.on_startswith(('谁是', '誰是'))
async def whois(bot, event: MessageEvent):
    uid = event.user_id
    if not lmt.check(uid):
        await bot.send(event, f'兰德索尔花名册冷却中(剩余 {int(lmt.left_time(uid)) + 1}秒)', at_sender=True)
        return
    lmt.start_cd(uid)

    name = event.message.extract_plain_text().strip()
    if not name:
        await bot.send(event, '请发送"谁是"+别称，如"谁是霸瞳"')
        return
    id_ = chara.name2id(name)
    confi = 100
    if id_ == chara.UNKNOWN:
        id_, guess_name, confi = chara.guess_id(name)
    c = chara.fromid(id_)
    
    msg = ''
    if confi < 100:
        lmt.start_cd(uid, 120)
        msg = f'兰德索尔似乎没有叫"{name}"的人...\n角色别称补全计划: github.com/Ice-Cirno/HoshinoBot/issues/5'
        await bot.send(event, msg)
        msg = f'\n您有{confi}%的可能在找{guess_name} '

    if confi > 60:
        msg += f'{c.icon.cqcode} {c.name}'
        await bot.send(event, msg, at_sender=True)
