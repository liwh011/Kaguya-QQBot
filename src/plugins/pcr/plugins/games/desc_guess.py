# ref: https://github.com/GWYOG/GWYOG-Hoshino-plugins/blob/master/pcrdescguess
# Originally written by @GWYOG
# Reflacted by @Ice-Cirno
# GPL-3.0 Licensed
# Thanks to @GWYOG for his great contribution!

import asyncio
from datetime import datetime
import os
import random
from loguru import logger

from nonebot import get_driver

from nonebot.adapters.cqhttp.event import Event, GroupMessageEvent
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot.adapters.cqhttp.utils import escape
from src.plugins.pcr import _pcr_data, chara
from src.Service import Service

from . import GameMaster

global_config = get_driver().config

PREPARE_TIME = 5
ONE_TURN_TIME = 12
TURN_NUMBER = 5
# DB_PATH = os.path.expanduser("~/.hoshino/pcr_desc_guess.db")
DB_PATH = os.path.join(global_config.cache_dir, "pcr_desc_guess.db")

gm = GameMaster(DB_PATH)
sv = Service("pcr-desc-guess")


@sv.on_fullmatch(("猜角色排行", "猜角色排名", "猜角色排行榜", "猜角色群排行"))
async def description_guess_group_ranking(bot, event: GroupMessageEvent):
    ranking = gm.db.get_ranking(event.group_id)
    msg = ["【猜角色小游戏排行榜】"]
    for i, item in enumerate(ranking):
        uid, count = item
        m = await bot.get_group_member_info(self_id=event.self_id, group_id=event.group_id, user_id=uid)
        name = escape(m["card"]) or escape(m["nickname"]) or str(uid)
        msg.append(f"第{i + 1}名：{name} 猜对{count}次")
    await bot.send(event, "\n".join(msg))


@sv.on_fullmatch(("猜角色", "猜人物"))
async def description_guess(bot, event: GroupMessageEvent):
    if gm.is_playing(event.group_id):
        await bot.send(event, "游戏仍在进行中…")
        return
    with gm.start_game(event.group_id) as game:
        game.answer = random.choice(list(_pcr_data.CHARA_PROFILE.keys()))
        profile = _pcr_data.CHARA_PROFILE[game.answer]
        kws = list(profile.keys())
        kws.remove('名字')
        random.shuffle(kws)
        kws = kws[:TURN_NUMBER]
        await bot.send(event, f"{PREPARE_TIME}秒后每隔{ONE_TURN_TIME}秒我会给出某位角色的一个描述，根据这些描述猜猜她是谁~")
        await asyncio.sleep(PREPARE_TIME)
        for i, k in enumerate(kws):
            await bot.send(event, f"提示{i + 1}/{len(kws)}:\n她的{k}是 {profile[k]}")
            await asyncio.sleep(ONE_TURN_TIME)
            if game.winner:
                return
        c = chara.fromid(game.answer)
    await bot.send(event, f"正确答案是：{c.name} {c.icon.cqcode}\n很遗憾，没有人答对~")


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
        msg = f"正确答案是：{c.name}" + c.icon.cqcode+"\n"
        msg += MessageSegment.at(event.user_id) + \
            f"花了{dtime}秒就猜对了，真厉害！TA已经猜对{n}次了~\n(此轮游戏将在几秒后自动结束，请耐心等待)"
        await bot.send(event, msg)
        await sv.notify_others('pcr_guess_chara_name_win',
                               group_id=event.group_id, user_id=event.user_id, use_time=dtime, bot=bot, event=event)
