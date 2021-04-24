from nonebot import logger, get_driver
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import GroupDecreaseNoticeEvent, GroupIncreaseNoticeEvent
from src.Service import Service

global_config = get_driver().config

sv1 = Service('group-leave-notice', visible=False)


@sv1.on_notice('group_decrease.leave')
async def leave_notice(bot: Bot, event: GroupDecreaseNoticeEvent):
    await bot.send(event, f"{event.get_user_id()}退群了。")


sv2 = Service('group-welcome', visible=False)


@sv2.on_notice('group_increase')
async def increace_welcome(bot: Bot, event: GroupIncreaseNoticeEvent):
    if event.get_user_id() == bot.self_id:
        return  # ignore myself

    welcomes = global_config.increase_welcomes
    gid = event.group_id
    if gid in welcomes:
        await bot.send(event, welcomes[gid], at_sender=True)
    elif 'default' in welcomes:
        await bot.send(event, welcomes['default'], at_sender=True)
