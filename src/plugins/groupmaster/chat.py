import json
import os
import random

from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import HonorNotifyEvent
from nonebot.adapters.cqhttp.message import MessageSegment
from src import R, util
from src.privilege import is_superuser
from src.Service import Service

sv = Service('chat', visible=False)


@sv.on_notice('notify.honor')
async def longwang(bot: Bot, event: HonorNotifyEvent):
    if event.honor_type == 'talkative':
        reply = ['龙王出来喷水','呼风唤雨']
        msg = MessageSegment.at(event.get_user_id())
        msg += random.choice(reply)
        await bot.send(event, msg)
    

@sv.on_fullmatch(('沙雕机器人', '沙雕機器人'))
async def say_sorry(bot: Bot, event: Event):
    await bot.send(event, 'ごめんなさい！嘤嘤嘤(〒︿〒)')


@sv.on_fullmatch(('老婆', 'waifu', 'laopo'), only_to_me=True)
async def chat_waifu(bot: Bot, event: Event):
    if not is_superuser(event.get_user_id()):
        await bot.send(event, R.img('laopo.jpg').cqcode)
    else:
        await bot.send(event, 'mua~')


@sv.on_fullmatch('老公', only_to_me=True)
async def chat_laogong(bot: Bot, event: Event):
    await bot.send(event, '你给我滚！', at_sender=True)


@sv.on_fullmatch('mua', only_to_me=True)
async def chat_mua(bot: Bot, event: Event):
    await bot.send(event, '笨蛋~', at_sender=True)


@sv.on_fullmatch(('我有个朋友说他好了', '我朋友说他好了', ))
async def ddhaole(bot: Bot, event: Event):
    await bot.send(event, '那个朋友是不是你弟弟？')
    await util.silence(event, 30)


@sv.on_fullmatch('我好了')
async def nihaole(bot: Bot, event: Event):
    await bot.send(event, '不许好，憋回去！')
    await util.silence(event, 30)



keywords = []
dirname = os.path.dirname(__file__)
keyword_json = os.path.join(dirname, 'chat_keyword.json')
with open(keyword_json, 'r', encoding='utf-8') as f:
    root = json.load(f)
    for key, value in root.items():
        rep = ''
        if value['text']:
            rep += value['text']
        if value['pic']:
            rep += R.img(value['pic']).cqcode
        keywords.append((tuple(key.split('，')), rep, value['probability']))
for kw in keywords:
    def func_creater():
        kw_list, reply, prob = kw
        async def func(bot: Bot, event: Event):
            if random.random()<prob:
                await bot.send(event, reply)
        func.__name__ = f'keyword_{kw_list[0]}'
        return func
    sv.on_keyword(kw[0])(func_creater())
