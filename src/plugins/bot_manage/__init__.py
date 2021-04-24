from src.privilege import SUPERUSER
from nonebot import on_notice, get_driver
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.adapters.cqhttp.event import GroupDecreaseNoticeEvent, NoticeEvent, PrivateMessageEvent
from src.Service import Service
from nonebot import logger

global_config = get_driver().config

sv = Service('bot_manage',
             visible=False)


@sv.on_notice('group_decrease.kick_me')
async def kick_me_alert(bot: Bot, event: GroupDecreaseNoticeEvent):
    group_id = event.group_id
    operator_id = event.operator_id
    coffee = list(global_config.superusers)[0]
    await bot.send_private_msg(self_id=event.self_id, user_id=coffee, message=f'被Q{operator_id}踢出群{group_id}')

# @sv.on_command('帮助')
# async def help(bot: Bot, event: Event):
#     await bot.send(event, '查看http://asdasdasda/help')

@sv.on_command('广播',aliases={'群发'}, permission=SUPERUSER.permission)
async def su_broadcast(bot: Bot, event: PrivateMessageEvent):
    await sv.broadcast(event.get_plaintext().strip())


@sv.on_command('解除禁言')
async def set_unban(bot: Bot, event: Event):
    try:
        args = event.get_plaintext().strip().split()
        group_id, user_id = args[:2]
        await bot.set_group_ban(group_id=int(group_id), user_id=int(user_id), duration=0, self_id=event.self_id)
        await bot.send(event, '解除成功')
    except Exception as e:
        logger.exception(e)
        await bot.send(event, f'发生错误{e}')
