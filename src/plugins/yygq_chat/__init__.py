# import nonebot
import random
from typing import List
from loguru import logger

from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import GroupMessageEvent
from src.Service import Service

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

sv = Service('yygq_chat', variables={'YYGQ_RATE': 0.01, })

# YYGQ_RATE: float = sv.get_config('YYGQ_RATE') or 0.2  # 回复概率
FORCE_UNIVERSAL_ANSWER_RATE: float = 0.13

UNIVERSAL_ANSWERS = [
    "你说你🐎呢？",
    "那没事了。",
    "真别逗我笑啊。",
    "那可真是有趣呢。",
    "就这？就这？",
    "你品，你细品。",
    "不会真有人觉得是这样的吧，不会吧不会吧？",
    "你在教我做事？",
    "给👴整笑了"
    # "お前の🐎さんのことですか？",
    # "お邪魔します。",
    # "笑わせないでください。",
    # "それは面白いですね。",
    # "これだけですか？これだけですか？",
    # "あなたの細品。",
    # "本当にそうだと思う人はいないでしょう。ね？ね？",
    # "あなたは私に仕事を教えていますか？",
    # "👴を笑わせました。",
]

STRONG_EMOTION_ANSWERS = [
    "你急了急了急了？",
    "他急了，他急了！"
]

QUESTION_ANSWERS = [
    "まさか本当に知らない人がいるでしょう？",
    "あなたも分かりません、どうしてお前の🐎のことを言っていますか",
]

STRONG_EMOTION_PATTERNS = [
    "！",
    "？？？",
    "???",
    "气抖冷",
    "nm",
    "傻逼",
    "sb",
    "尼玛",
    "你妈",
    "操",
]

QUESTION_PATTERNS = [
    "？",
    "怎么",
    "什么",
    "咋",
    "?"
]


def check_patterns(str_in: str, patterns: List[str]) -> bool:
    for p in patterns:
        if p in str_in:
            return True
    return False


def pick_answer(question: str) -> str:
    if random.random() < FORCE_UNIVERSAL_ANSWER_RATE:
        return random.choice(UNIVERSAL_ANSWERS)

    if check_patterns(question, STRONG_EMOTION_PATTERNS):
        return random.choice(STRONG_EMOTION_ANSWERS)
    elif check_patterns(question, QUESTION_PATTERNS):
        return random.choice(QUESTION_ANSWERS)
    else:
        return random.choice(UNIVERSAL_ANSWERS)


@sv.on_keyword(QUESTION_PATTERNS, only_to_me=False)
async def deal_question(bot: Bot, event: Event):
    if random.random() > sv.get_config('YYGQ_RATE', event):
        return
    if random.random() < 0.5:
        await bot.send(event, random.choice(QUESTION_ANSWERS), at_sender=event.is_tome())
    else:
        await bot.send(event, random.choice(UNIVERSAL_ANSWERS), at_sender=event.is_tome())


@sv.on_keyword(STRONG_EMOTION_PATTERNS, only_to_me=False)
async def deal_strong_emotion(bot: Bot, event: Event):
    if random.random() > sv.get_config('YYGQ_RATE', event):
        return
    if random.random() < 0.7:
        await bot.send(event, random.choice(STRONG_EMOTION_ANSWERS), at_sender=event.is_tome())
    else:
        await bot.send(event, random.choice(UNIVERSAL_ANSWERS), at_sender=event.is_tome())


@sv.on_message()
async def deal_normal(bot: Bot, event: Event):
    if random.random() > sv.get_config('YYGQ_RATE', event):
        return
    await bot.send(event, random.choice(UNIVERSAL_ANSWERS), at_sender=event.is_tome())


@sv.on_command('设置yygq概率', only_to_me=True, is_manage_func=True)
async def set_rate(bot: Bot, event: GroupMessageEvent):
    try:
        rate = float(event.get_plaintext().strip())
        if rate > 1 or rate < 0:
            await bot.send(event, '概率要在0~1之间', at_sender=event.is_tome())
            return
        YYGQ_RATE = rate
        await sv.set_config('YYGQ_RATE', YYGQ_RATE, target=event.group_id)
        await bot.send(event, f'当前回复概率为{YYGQ_RATE}')
    except Exception as e:
        await bot.send(event, str(e))
