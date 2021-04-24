
from nonebot.adapters import Bot, Event
from src.privilege import SUPERUSER
from nonebot import get_driver
from src.Service import Service

from .data_source import pick_comment

global_config = get_driver().config


sv = Service('网易云热评')


@sv.on_keyword(('网易云', '网抑云', '到点网抑', 'wyy', '老网易云了'), only_to_me=False)
async def wyy(bot: Bot, event: Event):
    comment = await pick_comment()
    await bot.send(event, comment)
