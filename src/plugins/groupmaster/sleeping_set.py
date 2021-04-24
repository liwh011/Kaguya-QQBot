import math
import random
from datetime import timedelta
from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import GroupMessageEvent

from src import util, R
from src.Service import Service
from src.privilege import set_block_user


sv = Service('sleeping-set', visible=False)


@sv.on_fullmatch(('睡眠套餐', '休眠套餐', '精致睡眠', '来一份精致睡眠套餐', '精緻睡眠', '來一份精緻睡眠套餐'))
async def sleep_8h(bot: Bot, event: GroupMessageEvent):
    await util.silence(event, 8*60*60, skip_su=False)


@sv.on_regex(r'(来|來)(.*(份|个)(.*)(睡|茶)(.*))套餐')
async def sleep(bot: Bot, event: GroupMessageEvent):
    base = 0 if '午' in event.get_plaintext() else 5*60*60
    length = len(event.get_plaintext())
    sleep_time = base + round(math.sqrt(length) *
                              60 * 30 + 60 * random.randint(-15, 15))
    await util.silence(event, sleep_time, skip_su=False)


BANNED_WORD = (
    'rbq', 'RBQ', '憨批', '废物', '死妈', '崽种', '傻逼', '傻逼玩意',
    '没用东西', '傻B', '傻b', 'SB', 'sb', '煞笔', 'cnm', '爬', 'kkp',
    'nmsl', 'D区', '口区', '我是你爹', 'nmbiss', '弱智', '给爷爬', '杂种爬', '爪巴'
)


@sv.on_keyword(BANNED_WORD, only_to_me=True)
async def ban_word(bot: Bot, event: GroupMessageEvent):
    """ban掉骂bot的人"""
    user_id = event.get_user_id()
    msg_from = str(user_id)
    msg_from += f'@[群:{event.group_id}]'
    logger.critical(
        f'Self: {event.self_id}, Message {event.message_id} from {msg_from}: {event.message}')
    set_block_user(user_id, timedelta(hours=8))

    pic = R.img(f"chieri{random.randint(1, 4)}.jpg").cqcode
    await bot.send(event, "不理你啦！バーカー\n"+pic, at_sender=True)
    await util.silence(event, 8*60*60)
