import asyncio
import inspect
import json
import os
from functools import wraps
from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Union)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import (get_bots, on_command, on_endswith, on_keyword, on_message,
                     on_regex, on_startswith, require)
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.event import (GroupMessageEvent,
                                           PrivateMessageEvent)
from nonebot.adapters.cqhttp.message import Message, MessageSegment
from nonebot.adapters.cqhttp.permission import (GROUP, GROUP_ADMIN,
                                                GROUP_MEMBER, GROUP_OWNER,
                                                PRIVATE, PRIVATE_FRIEND,
                                                PRIVATE_GROUP, Permission)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.plugin import on_notice
from nonebot.rule import Rule, to_me
from nonebot.typing import T_RuleChecker, T_State
from typing_extensions import Literal

import src.privilege as priv
from src.privilege import Privilege

scheduler: AsyncIOScheduler = require('nonebot_plugin_apscheduler').scheduler
_save_path: str = os.path.join(
    os.path.abspath('./'), 'services.json')  # 配置文件保存路径


def _load_config() -> Dict[str, Any]:
    """载入外部的配置文件"""
    try:
        with open(_save_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        logger.warning(f'未找到配置文件"{_save_path}"，将使用默认配置。')
        return {}
    except Exception as e:
        logger.exception(e)
        return {}


_config = _load_config()


class Service:
    _loaded_services: Dict[str, 'Service'] = {}  # 已加载的服务
    _event_handlers: Dict[str, List[Callable]] = {}  # 事件 - 对应的回调函数的列表

    def __init__(self,
                 name: str,
                 *,
                 use_priv: Privilege = None,
                 manage_priv: Privilege = None,
                 enable_on_default: bool = True,
                 visible: bool = True,
                 variables: Dict[str, Any] = None,
                 usage_file_dir: str = None) -> None:
        """
        定义一个服务
        配置的优先级别：配置文件 > 程序指定 > 缺省值

        :参数:
          * `name: str`: 服务名字
          * `use_priv: Privilege`: 使用权限。默认为所有人
          * `manage_priv: Privilege`: 管理权限。默认为群管理
          * `enable_on_default: bool`: 是否默认在所有群开启
          * `visible: bool`: 是否在服务管理列表可见
          * `variables: Dict[str, Any]`: 需要保存在配置文件中的变量
        """
        assert name not in self._loaded_services, f'服务"{name}"已经存在！'
        self._loaded_services[name] = self

        loaded_config = _config.get(name, {})

        self.name: str = name
        self.enabled: bool = loaded_config.get('enabled', True)
        self.enable_on_default: bool = enable_on_default
        self.enabled_group: Set[int] = set(
            loaded_config.get('enabled_group', set()))
        self.disabled_group: Set[int] = set(
            loaded_config.get('disabled_group', set()))
        self.use_priv: Privilege = use_priv or priv.DEFAULT
        self.manage_priv: Privilege = manage_priv or priv.GROUP_ADMIN
        self.visible: bool = visible
        self.config: Dict[str, Dict[str, Any]
                          ] = self._load_variables(variables or {})

    def _load_variables(self, vars_in_program: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """从外部配置中载入变量"""
        result = {}
        vars_in_config = _config.get(self.name, {}).get('other', {})
        # 对于程序指定的变量，如果配置中存在则采用配置
        # 否则才采用程序的值
        # 即优先级：配置文件 > 程序设定
        for var in vars_in_program:
            if var in vars_in_config:
                result[var] = vars_in_config[var]
            result[var] = {'default': vars_in_program[var]}
        return result

    def _to_dict(self) -> Dict:
        """将对象转化为dict，便于保存为配置文件"""
        d = {
            # "name": self.name,
            "enabled": self.enabled,
            # "enable_on_default": self.enable_on_default,
            "enabled_group": list(self.enabled_group),
            "disabled_group": list(self.disabled_group),
            # "use_priv": str(self.use_priv),
            # "manage_priv": str(self.manage_priv),
            # "visible": self.visible,
            "other": {**self.config},
        }
        return d

    @classmethod
    def get_loaded_services(cls) -> Dict[str, 'Service']:
        return cls._loaded_services

    @classmethod
    async def save_config(cls):
        with open(_save_path, 'w', encoding='utf-8') as f:
            sv = {name: sv._to_dict()
                  for name, sv in cls.get_loaded_services().items()}
            json.dump(sv, f, indent=4, ensure_ascii=False)
        logger.info('已成功保存服务配置文件。')

    def check_globally_enabled(self) -> bool:
        """
        :说明:

          检查是否全局启用了本服务。
        """
        return self.enabled

    def check_enabled_in_group(self, group_id: int) -> bool:
        """
        :说明:

          检查该群是否启用了本服务。

        :参数:

          * `group_id: int` 群号
        """
        return (group_id in self.enabled_group) or (self.enable_on_default and group_id not in self.disabled_group)

    async def set_enable_globally(self):
        """全局启用"""
        self.enabled = True
        logger.info(f'服务{self.name}已全局启用。')
        await self.save_config()

    async def set_disable_globally(self):
        """全局禁用"""
        self.enabled = False
        logger.info(f'服务{self.name}已全局启用。')
        await self.save_config()

    async def set_enable_in_group(self, group_id: int):
        """在群里启用"""
        self.enabled_group.add(group_id)
        self.disabled_group.discard(group_id)
        logger.info(f'服务{self.name}已在群{group_id}启用。')
        await self.save_config()

    async def set_disable_in_group(self, group_id: int):
        """在群里禁用"""
        self.disabled_group.add(group_id)
        self.enabled_group.discard(group_id)
        logger.info(f'服务{self.name}已在群{group_id}禁用。')
        await self.save_config()

    async def get_enabled_groups(self, bot: Bot) -> List[str]:
        all_groups = await bot.get_group_list(self_id=bot.self_id)
        res = [g['group_id']
               for g in all_groups if self.check_enabled_in_group(int(g['group_id']))]
        return res

    async def set_config(self, var_name: str, val: Any, target: Union[str, int, Event] = 'global') -> None:
        """
        设置配置变量的值，并保存配置

        :参数:
          - `var_name: str`: 变量名
          - `val: Any`: 变量值
          - `target: Union[str, int, Event]`: 配置的作用群组，缺省时为所有群组。
        """
        if isinstance(target, PrivateMessageEvent):
            target = 'global'
        elif isinstance(target, GroupMessageEvent):
            target = str(target.group_id)
        else:
            target = str(target)

        self.config[var_name][target] = val
        if target == 'global':
            # 对所有群组的配置都更新值
            for t in self.config[var_name]:
                self.config[var_name][t] = val
        logger.info(
            f'服务{self.name}：已在"{target}"内将变量"{var_name}"赋值"{str(val)}"。')
        await self.save_config()

    def get_config(self, name: str, source: Union[str, int, Event] = 'global') -> Any:
        """
        获取配置中的变量值。若不存在则返回None。

        :参数:
          - `source: Union[str, int, Event]`: 获取来源。缺省时或不存在时，返回全局配置。
        """
        if isinstance(source, PrivateMessageEvent):
            source = 'global'
        elif isinstance(source, GroupMessageEvent):
            source = str(source.group_id)
        else:
            source = str(source)

        # 不存在时返回全局配置
        default_val = self.config.get(name, {}).get('default')
        return self.config.get(name, {}).get(source, default_val)

    def on_service_event(self, event_name: str):
        """设置事件处理器"""
        def decorator(func: Callable):
            # 将处理程序加入列表
            if event_name not in self._event_handlers:
                self._event_handlers[event_name] = []
            self._event_handlers[event_name].append(func)
            logger.info(f'{self._event_handlers}')
            return func
        return decorator

    async def notify_others(self, event_name: str, **kwargs):
        """
        主动发出事件
        
        :参数:
            - `event_name: str`: 发出事件的名称
            - `kwargs`: 传递给事件处理器的参数
        """
        handlers = self._event_handlers.get(event_name, [])
        if not handlers:
            logger.info(f'服务事件{event_name}没有处理程序。')
            return
        for handler in handlers:
            try:
                await handler(**kwargs)
                logger.info(f'服务事件{event_name}被{handler.__name__}处理。')
            except Exception as e:
                logger.error(f'服务事件{event_name}被{handler.__name__}处理时发生错误：{e}')
                logger.exception(e)

    def _pre_check(self, **kwargs):
        """
        :说明:

          执行前通用检查，若检查不通过，被修饰的函数就不执行

        :参数:

          * `func: Callable` 异步函数，参数为`bot: Bot, event: Event, state: T_State`
        """
        only_to_me: bool = kwargs.get('only_to_me') or False

        def decorator(func: Callable[[Bot, Event, T_State], Any]):
            @wraps(func)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                # 检查是否全局开启
                if not self.check_globally_enabled():
                    return
                # 当来源是群消息时，检查在该群是否开启
                if isinstance(event, GroupMessageEvent) and not self.check_enabled_in_group(event.group_id):
                    return
                # 是否限制了仅当@bot触发
                if only_to_me and not event.is_tome():
                    return
                # 来源是私聊
                if isinstance(event, PrivateMessageEvent):
                    pass
                await func(bot, event, state)
            return wrapper
        return decorator

    def on_message(self,
                   msg_type: Permission = GROUP,
                   only_to_me: bool = False,
                   **kwargs) -> Callable:
        """
        :说明:

          收到类型为`msg_type`的消息时，调用被修饰的函数。

        :参数:

          * `Permission` 消息类型
          * `**kwargs` 其他传给原`nonebot.on_message`的可选参数
        """
        def decorator(func: Callable):
            matcher = on_message(permission=msg_type, priority=9, **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_message处理器{func.__name__}处理。')
                await matcher.finish()
            return matcher.handle()(wrapper)
        return decorator

    def on_command(self,
                   cmd: Union[str, Tuple[str, ...]],
                   aliases: Optional[Set[Union[str, Tuple[str, ...]]]] = None,
                   only_to_me: bool = False,
                   is_manage_func: bool = False,
                   **kwargs) -> Callable:
        """
        :说明:

          收到命令时，调用被修饰的函数。

        :参数:

          * `cmd: Union[str, Tuple[str, ...]]` 命令，可为单个字符串，或者一个元组
          * `aliases: Optional[Set[Union[str, Tuple[str, ...]]]]` 命令别称，可为单个字符串，或者一个元组
          * `**kwargs` 其他传给原`nonebot.on_command`的可选参数
        """
        kwargs['aliases'] = aliases
        kwargs.setdefault('permission', self.use_priv.permission)
        if is_manage_func:
            kwargs['permission'] = self.manage_priv.permission

        def decorator(func: Callable):
            matcher = on_command(cmd, **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_command处理器{func.__name__}处理。')
                await matcher.finish()
            return matcher.handle()(wrapper)
        return decorator

    def on_keyword(self,
                   keyword: Union[str, Iterable[str]],
                   only_to_me: bool = False,
                   **kwargs) -> Callable:
        """
        :说明:

          消息中含有特定关键词时触发。

        :参数:

          * `keyword: Set[str]` 关键词集合
          * `**kwargs` 其他传给原`nonebot.on_keyword`的可选参数
        """
        if isinstance(keyword, str):
            keyword = {keyword, }
        kwargs.setdefault('permission', self.use_priv.permission)

        def decorator(func: Callable):
            matcher = on_keyword(set(keyword), **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_keyword处理器{func.__name__}处理。')
                await matcher.finish()
            return matcher.handle()(wrapper)
        return decorator

    def on_startswith(self,
                      prefix: Union[str, Iterable[str]],
                      only_to_me: bool = False,
                      **kwargs) -> Callable:
        """
        :说明:

          消息以指定内容开头时触发。

        :参数:

          * `prefix: str` 开头内容
          * `**kwargs` 其他传给原`nonebot.on_startswith`的可选参数
        """
        if isinstance(prefix, str):
            prefix = {prefix, }
        else:
            prefix = set(prefix)
        kwargs.setdefault('permission', self.use_priv.permission)

        def decorator(func: Callable):
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                logger.debug(state)
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_startswith处理器{func.__name__}处理。')
                # await matcher.finish()
            for pfx in prefix:
                matcher = on_startswith(pfx, **kwargs)
                matcher.handle()(wrapper)
            return wrapper
        return decorator

    def on_endswith(self,
                    suffix: str,
                    only_to_me: bool = False,
                    **kwargs) -> Callable:
        """
        :说明:

          消息以指定内容结尾时触发。

        :参数:

          * `suffix: str` 结尾内容
          * `**kwargs` 其他传给原`nonebot.on_endswith`的可选参数
        """
        kwargs.setdefault('permission', self.use_priv.permission)

        def decorator(func: Callable):
            matcher = on_endswith(suffix, **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_endswith处理器{func.__name__}处理。')
                await matcher.finish()
            return matcher.handle()(wrapper)
        return decorator

    def on_regex(self,
                 pattern: str,
                 only_to_me: bool = False,
                 **kwargs) -> Callable:
        """
        :说明:

          消息被正则匹配时触发。

        :参数:

          * `pattern: str` 正则表达式
          * `**kwargs` 其他传给原`nonebot.on_regex`的可选参数
        """
        kwargs.setdefault('permission', self.use_priv.permission)

        def decorator(func: Callable):
            matcher = on_regex(pattern, **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                match_group = state['_matched_groups']
                setattr(event, 'match', match_group)
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_regex处理器{func.__name__}处理。')
                await matcher.finish()
            return matcher.handle()(wrapper)
        return decorator

    def on_fullmatch(self,
                     words: Union[str, Iterable[str]],
                     only_to_me: bool = False,
                     **kwargs) -> Callable:
        """
        :说明:

          消息完全匹配对应内容时触发。

        :参数:

          * `words: Union[str, Set[str]]` 匹配内容
          * `**kwargs` 其他传给原`nonebot.on_startswith`的可选参数
        """
        # 对单个字符串转化为集合
        if isinstance(words, str):
            words = {words, }
        elif isinstance(words, Iterable):
            words = set(words)
        else:
            raise TypeError('类型错误')
        kwargs.setdefault('permission', self.use_priv.permission)

        async def fullmatch_checker(bot: Bot, event: Event, state: T_State):
            return event.get_plaintext() in words

        def decorator(func: Callable):
            matcher = on_message(rule=Rule(fullmatch_checker), **kwargs)
            @wraps(func)
            @self._pre_check(only_to_me=only_to_me)
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'消息{event.get_session_id()}已被on_fullmatch处理器{func.__name__}处理。')
            matcher.handle()(wrapper)
        return decorator

    def on_notice(self,
                  notice_type: str,
                  **kwargs) -> Callable:
        """
        :说明:

          消息完全匹配对应内容时触发。

        :参数:

          * `words: Union[str, Set[str]]` 匹配内容
          * `**kwargs` 其他传给原`nonebot.on_startswith`的可选参数
        """

        def decorator(func: Callable):
            # notice类型检查函数
            async def checker(bot: Bot, event: Event, state: T_State):
                return event.get_event_name().find(notice_type) != -1
            matcher = on_notice(rule=Rule(checker), **kwargs)
            @wraps(func)
            @self._pre_check()
            async def wrapper(bot: Bot, event: Event, state: T_State):
                await func(bot, event)
                logger.info(
                    f'通知{event.get_event_name()}已被on_notice处理器{func.__name__}处理。')
            matcher.handle()(wrapper)
        return decorator

    def scheduled_job(self,
                      trigger: str,
                      name: Optional[str] = None,
                      **kwargs):
        """
        :说明:

          设置一个定时任务

        :参数:

          * `trigger: str` 定时器类型
          * `name: Optional[str]` 定时器名字，可用于管理定时器
          * `**kwargs` 其他传给原`scheduler.add_job`的可选参数
        """
        def decorator(func: Callable):
            job_name = name or func.__name__
            kwargs['id'] = job_name
            @wraps(func)
            async def wrapper():
                if not self.enabled:
                    return
                logger.info(f'定时任务{job_name}开始执行。')
                await func()
                logger.info(f'定时任务{job_name}执行完毕。')
            scheduler.add_job(wrapper, trigger, **kwargs)
            return wrapper
        return decorator

    async def broadcast(self,
                        msgs: Union[str, MessageSegment, Message, Iterable[Any]],
                        TAG: str = '',
                        interval_time: float = 0.5,
                        randomiser=None):
        bot = list(get_bots().values())[0]
        if isinstance(msgs, (str, MessageSegment, Message)):
            msgs = (msgs, )
        else:
            msgs = tuple(msgs)
        group_list = await self.get_enabled_groups(bot)
        for gid in group_list:
            try:
                for msg in msgs:
                    await asyncio.sleep(interval_time)
                    msg = randomiser(msg) if randomiser else msg
                    await bot.send_group_msg(self_id=bot.self_id, group_id=gid, message=msg)
                l = len(msgs)
                if l:
                    logger.info(f"群{gid} 投递{TAG}成功 共{l}条消息")
            except Exception as e:
                logger.error(f"群{gid} 投递{TAG}失败：{type(e)}")
                logger.exception(e)
