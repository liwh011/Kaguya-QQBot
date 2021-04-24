from nonebot.adapters import Bot, Event
from src.Service import Service

from nonebot import logger
from .data_source import get_single_continuation

sv = Service('novel_continuation',
             enable_on_default=True,
             visible=True)



@sv.on_command('续写')
async def novel_continue(bot: Bot, event: Event):
    await bot.send(event, '请耐心等候', at_sender=True)
    text = event.get_plaintext().strip()
    res = await get_single_continuation(text)
    if res:
        await bot.send(event, res, at_sender=True)
