import asyncio

from nonebot import logger
from nonebot.adapters import Event, Bot
from src.Service import Service
from src.util import split_list

from .data_source import get_today_shadiao_pic, get_single_shadiao_pic

sv = Service('shadiaotu', visible=True, enable_on_default=False)


@sv.scheduled_job('cron', hour=22, minute=30)
async def check():
    msgs = get_today_shadiao_pic()
    if not msgs:
        logger.info('未检测到今日沙雕图更新。')
        return
    msgs = split_list(msgs, 3)

    msg = '今日份沙雕图'
    await sv.broadcast(msg, 'shadiao_check', 0.2)
    for msg in msgs:
        msg = sum(msg)
        await sv.broadcast(msg, 'shadiao_check', 0.2)
        await asyncio.sleep(1)

@sv.on_keyword('沙雕图')
async def sdt(bot: Bot, event: Event):
    await bot.send(event, get_single_shadiao_pic())
    
