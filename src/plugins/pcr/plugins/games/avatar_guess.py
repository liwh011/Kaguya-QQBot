# ref: https://github.com/GWYOG/GWYOG-Hoshino-plugins/blob/master/pcravatarguess
# Originally written by @GWYOG
# Reflacted by @Ice-Cirno
# GPL-3.0 Licensed
# Thanks to @GWYOG for his great contribution!

import asyncio
from datetime import datetime
import os
import random

from nonebot import get_driver
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent
from nonebot.adapters.cqhttp.event import Event, GroupMessageEvent
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot.adapters.cqhttp.utils import escape
from src import util
from src.plugins.pcr import _pcr_data, chara
from src.Service import Service

from . import GameMaster

global_config = get_driver().config

PATCH_SIZE = 32
ONE_TURN_TIME = 20
DB_PATH = os.path.join(global_config.cache_dir, "pcr_avatar_guess.db")
# DB_PATH = os.path.expanduser("~/.hoshino/pcr_avatar_guess.db")
BLACKLIST_ID = [1072, 1908, 4031, 9000]

gm = GameMaster(DB_PATH)
sv = Service("pcr-avatar-guess",)


@sv.on_fullmatch(("猜头像排行", "猜头像排名", "猜头像排行榜", "猜头像群排行"))
async def description_guess_group_ranking(bot: Bot, event: GroupMessageEvent):
    ranking = gm.db.get_ranking(event.group_id)
    msg = ["【猜头像小游戏排行榜】"]
    for i, item in enumerate(ranking):
        uid, count = item
        m = await bot.get_group_member_info(
            self_id=event.self_id, group_id=event.group_id, user_id=uid
        )
        name = escape(m["card"]) or escape(m["nickname"]) or str(uid)
        msg.append(f"第{i + 1}名：{name} 猜对{count}次")
    await bot.send(event, "\n".join(msg))


@sv.on_fullmatch("猜头像")
async def avatar_guess(bot: Bot, event: GroupMessageEvent):
    if gm.is_playing(event.group_id):
        await bot.send(event, "游戏仍在进行中…")
        return
    with gm.start_game(event.group_id) as game:
        ids = list(_pcr_data.CHARA_NAME.keys())
        game.answer = random.choice(ids)
        while chara.is_npc(game.answer):
            game.answer = random.choice(ids)
        c = chara.fromid(game.answer)
        img = c.icon.open()
        w, h = img.size
        l = random.randint(0, w - PATCH_SIZE)
        u = random.randint(0, h - PATCH_SIZE)
        cropped = img.crop((l, u, l + PATCH_SIZE, u + PATCH_SIZE))
        cropped = MessageSegment.image(util.pic2b64(cropped))
        await bot.send(event, f"猜猜这个图片是哪位角色头像的一部分?({ONE_TURN_TIME}s后公布答案)" + cropped)
        await asyncio.sleep(ONE_TURN_TIME)
        if game.winner:
            return
    await bot.send(event, f"正确答案是：{c.name}" + c.icon.cqcode + "\n很遗憾，没有人答对~")


@sv.on_message()
async def on_input_chara_name(bot, event: GroupMessageEvent):
    game = gm.get_game(event.group_id)
    if not game or game.winner:
        return
    dtime = int((datetime.now()-game.start_time).total_seconds())

    c = chara.fromname(event.message.extract_plain_text())
    if c.id != chara.UNKNOWN and c.id == game.answer:
        game.winner = event.user_id
        n = game.record()
        msg = f"正确答案是：{c.name}"+c.icon.cqcode+"\n"
        msg += MessageSegment.at(event.user_id) + \
            f"花了{dtime}秒就猜到了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        await bot.send(event, msg)
        await sv.notify_others('pcr_guess_chara_avatar_win',
                               group_id=event.group_id, user_id=event.user_id, use_time=dtime, bot=bot, event=event)
