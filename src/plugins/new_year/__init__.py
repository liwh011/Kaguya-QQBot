from nonebot.adapters import Bot, Event
from src.Service import Service
import random
from .blessing import get_blessing_sentence, get_blessing_voice
from .song import get_song

sv = Service('new_year_blessing',
             enable_on_default=True,
             visible=True)


@sv.on_keyword('春节 过年 新年 除夕 牛年 新春 拜年 红包 过节 恭喜 祝福 发财'.split(' '))
async def func(bot: Bot, event: Event):
    if random.random() > 0.8:
        return
    funcs = [get_song, get_blessing_sentence, get_blessing_voice]
    await bot.send(event, random.choice(funcs)())


