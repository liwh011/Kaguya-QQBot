from nonebot import logger
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp.event import Event
from src.Service import Service
from src.util import DailyNumberLimiter, FreqLimiter
from .local_img import get_local_setu
from .request_img import get_web_img

_max = 5
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)

sv = Service('setu', enable_on_default=False, visible=False)


@sv.on_regex(r'不够[涩瑟色]|[涩瑟色]图|来一?[点份张].*[涩瑟色]|再来[点份张]|看过了|铜')
async def setu(bot: Bot, event: Event):
    """随机叫一份涩图，对每个用户有冷却时间"""
    uid = event.get_user_id()
    if not _nlmt.check(uid):
        await bot.send(event, EXCEED_NOTICE, at_sender=True)
        return
    if not _flmt.check(uid):
        await bot.send(event, '您冲得太快了，请稍候再冲', at_sender=True)
        return
    _flmt.start_cd(uid)
    _nlmt.increase(uid)

    # conditions all ok, send a setu.
    try:
        logger.debug('开始从网络爬取图片。')
        pic = await get_web_img()
    except Exception as e:
        logger.error(f"爬取网络图片失败，将从本地选择。({e})")
        pic = get_local_setu()
    
    try:
        if pic:
            await bot.send(event, pic.cqcode)
    except Exception as e:
        logger.error(f"发送图片{pic.path}失败")
        logger.exception(e)
        try:
            await bot.send(event, '涩图太涩，发不出去勒...')
        except:
            pass
