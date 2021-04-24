from typing import Dict, List

from nonebot import get_driver, logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import (GroupMessageEvent,
                                           PrivateMessageEvent)
from src.privilege import GROUP_ADMIN, PRIVATE, SUPERUSER, is_superuser
from src.Service import Service

global_config = get_driver().config


sv = Service('sv_manager',
             visible=False,
             use_priv=GROUP_ADMIN | PRIVATE,
             manage_priv=SUPERUSER)

_GROUP_USAGE = '用法：「启用 sv1 sv2 sv3...」'
_PRIVATE_USAGE = '用法：「启用 sv1 -123123123 -456456456 sv2 -234234234 sv3...」'


async def set_sv(sv: Service, group: int, enable: bool):
    """
    在一个群内，启用或关闭服务

    :参数:
      - `group: int`: 群号
      - `enable: bool`: 是否启用
    """
    if enable:
        await sv.set_enable_in_group(group)
    else:
        await sv.set_disable_in_group(group)


class ArgParserPrivate:
    NOTHING = 0
    SV_GOT = 1
    SV_GROUP_GOT = 2
    ERR_SV_NOT_FOUND = -1
    ERR_GROUP_NOT_FOUND = -2

    def __init__(self, enable: bool, args: List[str]) -> None:
        self.enable: bool = enable
        self.args: List[str] = args
        self.parse_result: Dict[str, List[int]] = {}
        self.status: int = self.NOTHING
        self.current_sv: str = ''
        self.succeed: List[tuple] = []
        self.failed: List[tuple] = []

        self._parse(args)

    def _parse(self, args: List[str]):
        if not args:
            raise ValueError('参数为空。')
        for arg in args:
            self._update_status(arg)
            self._process_arg(arg)

    async def run(self):
        for name, groups in self.parse_result.items():
            sv = Service.get_loaded_services().get(name)
            if not sv:
                self.failed.append((name, '不存在该服务'))
                continue
            if not groups:
                self.failed.append((name, '缺少待操作的群组'))
                continue
            for group in groups:
                try:
                    await set_sv(sv, group, self.enable)
                    self.succeed.append((name, ''))
                except Exception as e:
                    self.failed.append((name, f'发送错误：{str(e)}'))

    def _update_status(self, arg: str):
        status = self.status
        if status == self.NOTHING:
            if arg.startswith('-'):
                status = self.ERR_SV_NOT_FOUND
            else:
                status = self.SV_GOT
        elif status == self.SV_GOT:
            if arg.startswith('-'):
                status = self.SV_GROUP_GOT
            else:
                status = self.ERR_GROUP_NOT_FOUND
        elif status == self.SV_GROUP_GOT:
            if arg.startswith('-'):
                pass
            else:
                status = self.SV_GOT
        elif status == self.ERR_SV_NOT_FOUND:
            if arg.startswith('-'):
                pass
            else:
                status = self.SV_GOT
        elif status == self.ERR_GROUP_NOT_FOUND:
            pass

        self.status = status

    def _process_arg(self, arg: str):
        status = self.status
        if status == self.NOTHING:
            pass
        elif status == self.SV_GOT:
            self.current_sv = arg
            self.parse_result[arg] = []
        elif status == self.SV_GROUP_GOT:
            self.parse_result[self.current_sv].append(int(arg))
        elif status == self.ERR_SV_NOT_FOUND:
            pass
        elif status == self.ERR_GROUP_NOT_FOUND:
            self.status = self.SV_GOT
            self.current_sv = arg
            self.parse_result[arg] = []


async def process_msg(bot: Bot, event: Event, enable: bool):
    try:
        args = event.get_plaintext().strip()
        if not args:
            msg = _GROUP_USAGE if isinstance(
                event, GroupMessageEvent) else _PRIVATE_USAGE
            raise ValueError('未找到参数。' + msg)
        args = args.split(' ')

        # 从群组内调用
        if isinstance(event, GroupMessageEvent):
            succeed = set()
            failed = set()
            group_id = event.group_id
            services = args
            for sv_name in services:
                sv = Service.get_loaded_services().get(sv_name)
                if sv:
                    await set_sv(sv, group_id, enable)
                    succeed.add(sv_name)
                else:
                    failed.add(sv_name)
            msg = ''
            if succeed:
                msg += '服务' + '、'.join([str(i) for i in succeed]) + \
                       '已启用' if enable else '已禁用' + '\n'
            if failed:
                msg += '不存在这些服务：' + '、'.join([str(i) for i in failed])
            await bot.send(event, msg)

        # 私聊调用，需要superuser权限
        elif isinstance(event, PrivateMessageEvent):
            if not is_superuser(event.get_user_id()):
                return
            parser = ArgParserPrivate(enable, args)
            await parser.run()
            msg = ''
            if parser.succeed:
                msg += '执行完毕。\n'
            if parser.failed:
                msg += '以下群组发生错误：\n'
                msg += '\n'.join(
                    [f'  {name}: {msg}\n' for name, msg in parser.failed]) + '\n'
                msg += _PRIVATE_USAGE
            await bot.send(event, msg)

    except ValueError as e:
        await bot.send(event, str(e))


@sv.on_command('启用', aliases={'开启', '打开'})
async def enable_sv(bot: Bot, event: Event):
    await process_msg(bot, event, True)


@sv.on_command('禁用', aliases={'关闭'})
async def disable_sv(bot: Bot, event: Event):
    await process_msg(bot, event, False)


@sv.on_command('查看服务', aliases={'查看所有服务', '显示服务', '列出服务', '显示所有服务'})
async def ls_sv(bot: Bot, event: Event):
    if isinstance(event, GroupMessageEvent):
        all_sv = Service.get_loaded_services()
        enabled_sv = [sv_name
                      for sv_name, sv in all_sv.items()
                      if sv.visible and sv.check_enabled_in_group(event.group_id)]
        disabled_sv = [sv_name
                       for sv_name, sv in all_sv.items()
                       if sv.visible and not sv.check_enabled_in_group(event.group_id)]
        msg = ''
        if enabled_sv:
            msg += '已启用服务：\n    · ' + '\n    · '.join(enabled_sv) + '\n'
        if disabled_sv:
            msg += '已禁用服务：\n    · ' + '\n    · '.join(disabled_sv)
        await bot.send(event, msg)
    else:
        return
