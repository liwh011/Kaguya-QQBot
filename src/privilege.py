from datetime import datetime, timedelta
from os import name
from typing import Callable, Coroutine, Dict, Optional, Union

from nonebot import get_driver
from nonebot.log import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import MessageEvent
from nonebot.adapters.cqhttp.permission import GROUP as _GROUP_
from nonebot.adapters.cqhttp.permission import GROUP_ADMIN as _GROUP_ADMIN_
from nonebot.adapters.cqhttp.permission import GROUP_OWNER as _GROUP_OWNER_
from nonebot.adapters.cqhttp.permission import PRIVATE as _PRIVATE_
from nonebot.permission import MESSAGE, SUPERUSER as _SUPERUSER_
from nonebot.permission import Permission

global_config = get_driver().config

def is_superuser(user_id: Union[str, int]):
    """判断是否是superuser"""
    if isinstance(user_id, int):
        user_id = str(user_id)
    return user_id in global_config.superusers


class Privilege:
    """等级特权"""
    _exist_priv: Dict[str, 'Privilege'] = {}

    def __init__(self, name: str, weight: int = 0,  permission: Permission = None) -> None:
        self.name: str = name
        self.weight: int = weight
        self.permission: Optional[Permission] = permission

        self._exist_priv[self.name] = self

    @classmethod
    def get(cls, name: str):
        """根据字符串获取实例"""
        if name not in cls._exist_priv:
            raise ValueError(f'不存在该Privilege：{name}')
        return cls._exist_priv[name]

    def __str__(self) -> str:
        return self.name

    def __or__(self, other: 'Privilege'):
        return Privilege(f'{self.name}_{other.name}', permission=self.permission | other.permission)


async def _whitelist(bot: "Bot", event: "Event") -> bool:
    """白名单判断函数"""
    return event.get_user_id() in bot.config.whitelist


async def _blacklist(bot: "Bot", event: "Event") -> bool:
    """判断在黑名单"""
    return check_block_user(event.get_user_id())


def _perm_checker_decorater(perm: Permission) -> Permission:
    """将原来的Permission常量，与黑名单前置判断一起包装"""
    async def _perm_checker_wrapper(bot: "Bot", event: "Event"):
        return isinstance(event, MessageEvent) \
            and not await _blacklist(bot, event) \
            and await list(perm.checkers)[0](bot, event)
    return Permission(_perm_checker_wrapper)


_WHITELIST_ = Permission(_whitelist)

"""包装之前的permission"""
_PRIVATE = _perm_checker_decorater(_PRIVATE_)
_WHITELIST = _perm_checker_decorater(_WHITELIST_)
_GROUP_ADMIN = _perm_checker_decorater(_GROUP_ADMIN_)
_GROUP_OWNER = _perm_checker_decorater(_GROUP_OWNER_)
_SUPERUSER = _perm_checker_decorater(_SUPERUSER_)
_GROUP = _perm_checker_decorater(_GROUP_)


"""一系列常量"""
BLACK = Privilege('BLACK', -999, Permission(_blacklist))
DEFAULT = Privilege('DEFAULT', 0, _GROUP | _PRIVATE)
PRIVATE = Privilege('PRIVATE', 10, _PRIVATE)
GROUP_ADMIN = Privilege('ADMIN', 21,
                        _GROUP_ADMIN | _GROUP_OWNER | _SUPERUSER | _WHITELIST)
GROUP_OWNER = Privilege('OWNER', 22, _GROUP_OWNER | _SUPERUSER | _WHITELIST)
WHITE = Privilege('WHITE', 51, _WHITELIST | _SUPERUSER)
SUPERUSER = Privilege('SUPERUSER', 999, _SUPERUSER)


__all__ = [
    "BLACK", "DEFAULT", "PRIVATE", "GROUP_ADMIN", "GROUP_OWNER",
    "WHITE", "SUPERUSER"
]


# ============================================
# ban掉某人某群
# ============================================

_black_group = {}  # Dict[group_id, expr_time]
_black_user = {}  # Dict[user_id, expr_time]


def set_block_group(group_id: str, time: timedelta):
    _black_group[group_id] = datetime.now() + time


def set_block_user(user_id: str, time: timedelta):
    if user_id not in global_config.superusers:
        _black_user[user_id] = datetime.now() + time


def check_block_group(group_id: str):
    if group_id in _black_group and datetime.now() > _black_group[group_id]:
        del _black_group[group_id]  # 拉黑时间过期
        return False
    return bool(group_id in _black_group)


def check_block_user(user_id: str):
    if user_id in _black_user and datetime.now() > _black_user[user_id]:
        del _black_user[user_id]  # 拉黑时间过期
        return False
    return bool(user_id in _black_user)
