from loguru import logger
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.cqhttp import Bot, Event
from src.Service import Service
from .data_source import sim_draw

sv = Service('gacha')


@sv.on_command("Fgo_Draw",
               aliases={"FGO抽卡", "FGO来一单", "fgo抽卡", "fgo来一单", "Fgo抽卡", "Fgo来一单"})
async def fgo_draw_handler(bot: Bot, event: Event):
    args = str(event.get_message()).strip()
    msg = sim_draw(55, game="fgo")
    await bot.send(event, msg)

@sv.on_command("Prts_Draw",
               aliases={"明日方舟抽卡", "明日方舟来一单", "方舟抽卡", "方舟来一单"})
async def prts_draw_handler(bot: Bot, event: Event):
    args = str(event.get_message()).strip()
    msg = sim_draw(55, game="prts")
    await bot.send(event, msg)


@sv.on_command("Ys_Draw",
               aliases={"原神抽卡"})
async def ys_draw_handler(bot: Bot, event: Event):
    args = str(event.get_message()).strip()
    try:
        msg = sim_draw(10, game="yuanshen")
    except Exception as e:
        msg = f'发生错误：{repr(e)}'
        logger.exception(e)
    await bot.send(event, msg, at_sender=True)
