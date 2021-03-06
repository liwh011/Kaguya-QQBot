from typing import Type
from src.Service import Service
from .spider import *
from nonebot import logger

svtw = Service('pcr-news-tw')
svbl = Service('pcr-news-bili')


async def news_poller(spider: Type[BaseSpider], sv: Service, TAG):
    if not spider.item_cache:
        await spider.get_update()
        logger.info(f'{TAG}新闻缓存为空，已加载至最新')
        return
    news = await spider.get_update()
    if not news:
        logger.info(f'未检索到{TAG}新闻更新')
        return
    logger.info(f'检索到{len(news)}条{TAG}新闻更新！')
    await sv.broadcast(spider.format_items(news), TAG, interval_time=0.5)


@svtw.scheduled_job('cron', minute='*/5', jitter=20)
async def sonet_news_poller():
    await news_poller(SonetSpider, svtw, '台服官网')


@svbl.scheduled_job('cron', minute='*/5', jitter=20)
async def bili_news_poller():
    await news_poller(BiliSpider, svbl, 'B服官网')


async def send_news(bot, ev, spider: Type[BaseSpider], max_num=5):
    if not spider.item_cache:
        await spider.get_update()
    news = spider.item_cache
    news = news[:min(max_num, len(news))]
    await bot.send(ev, spider.format_items(news), at_sender=True)


@svtw.on_fullmatch(('台服新闻', '台服日程'))
async def send_sonet_news(bot, event):
    await send_news(bot, event, SonetSpider)


@svbl.on_fullmatch(('B服新闻', 'b服新闻', 'B服日程', 'b服日程'))
async def send_bili_news(bot, event):
    await send_news(bot, event, BiliSpider)
