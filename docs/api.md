# `Service`
以下全是class Service的成员函数。

### `__init__(...)`
- 参数
    * `name: str`: 服务名字
    * `use_priv: Privilege`: 使用权限。默认为所有人
    * `manage_priv: Privilege`: 管理权限。默认为群管理
    * `enable_on_default: bool`: 是否默认在所有群开启
    * `visible: bool`: 是否在服务管理列表可见
    * `variables: Dict[str, Any]`: 需要保存在配置文件中的变量

## 配置
当你需要依照不同群组来具体配置功能（如本群的抽卡概率调得很高，隔壁群概率调为0），下面的函数为你提供了配置统一管理。

前提是，你需要在创建Service时，将需要保存的变量通过`variables`参数传入，如：
```py
sv = Service('sv_using_config', variables={'num': 0.01, })
```

### `set_config(self, var_name, val, target)`
- 说明  
    设置配置变量的值，并保存配置（每个群组都拥有一份独有配置）

- 参数
    * `var_name: str` 配置变量名
    * `val: Any` 变量值，仅支持基础类型，不支持自定义对象等
    * `target: Union[str, int, Event]`: 对哪个群组应用该配置。一般传入`event`对象，或者手动传入qq群号。**缺省时或不存在时，将设置为全局配置（覆盖所有群组的配置）**。


### `get_config(self, name, source)`
- 说明  
    获取配置中的变量值（每个群组都拥有一份独有配置）。若不存在则返回None。

- 参数
    * `name: str` 配置变量名
    * `source: Union[str, int, Event]`: 获取来源。一般传入`event`对象，或者手动传入qq群号。缺省时或不存在时，返回全局配置。


## 工具
### async `broadcast()`
- 说明  
    向所有开启了本服务的群发送一条消息

- 参数
    * `msgs: Union[str, MessageSegment, Message, Iterable[Any]]` 消息。传入一个列表时，函数将会以一定时间间隔来发送每一条消息
    * `TAG: str` 本次群发的标注
    * `interval_time: float` 与上次发送的间隔时间。仅当消息传入一个列表时才有用。
    * `randomiser` 不太清楚


## Service事件处理
用于跨服务通讯。比如：某群员在猜角色游戏中获胜了，另外一个模块将会给他发奖励。   
（这玩意其实应该叫做观察者模式？）
### 修饰器 `on_service_event(self, event_name)`
- 说明  
    订阅事件，当事件发生时调用被装饰的函数。注意，这个事件与Nonebot的事件不同。Service中的事件用于跨服务通信。     
    被修饰的函数需要为**异步函数 (`async`)**。另外，如要接受传参，请在写入对应名称的参数，或者使用`**kwargs`接受。

- 参数
    * `event_name: str` 事件名称

- 示例
    ```py
    # 方法1
    @sv.on_service_event('xxxevent')
    async def handler1(foo: str, bar: int):
        ...

    # 方法二
    @sv.on_service_event('xxxevent')
    async def handler2(**kwargs):
        foo = kwargs.get('foo')
        bar = kwargs.get('bar')
        ...
    ```


### async `notify_others(self, event_name, **kwargs)`
- 说明  
    主动发起一个事件

- 参数
    * `event_name: str` 事件名称
    * `**kwargs` 其他参数，将会传递给订阅了该事件的处理函数。





## 消息响应器
### 修饰器 `on_message()`
- 说明  
    收到类型为`msg_type`的消息时，调用被修饰的函数。

- 参数
    * `msg_type: Permission` 消息类型，可取值`GROUP, GROUP_ADMIN, GROUP_MEMBER, GROUP_OWNER, PRIVATE, PRIVATE_FRIEND, PRIVATE_GROUP`
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_message`的可选参数


### 修饰器 `on_command()`
- 说明  
    收到以cmd开头的命令时，调用被修饰的函数。

- 参数
    * `cmd: Union[str, Tuple[str, ...]]` 命令，可为单个字符串，或者一个元组
    * `aliases: Optional[Set[Union[str, Tuple[str, ...]]]]` 命令别称，可为单个字符串，或者一个元组
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_command`的可选参数



### 修饰器 `on_keyword()`
- 说明  
    消息中含有特定关键词时触发被修饰的函数。    

- 参数
    * `keyword: Set[str]` 关键词集合
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_keyword`的可选参数


### 修饰器 `on_startswith()`
- 说明  
    消息以指定内容开头时触发被修饰的函数。   

- 参数
    * `prefix: str` 开头内容
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_startswith`的可选参数



### 修饰器 `on_endswith()`
- 说明  
    消息以指定内容结尾时触发被修饰的函数。   

- 参数
    * `suffix: str` 结尾内容
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_endswith`的可选参数


### 修饰器 `on_regex()`
- 说明  
    消息被正则匹配时触发被修饰的函数。   

- 参数
    * `pattern: str` 正则表达式
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_regex`的可选参数


### 修饰器 `on_fullmatch()`
- 说明  
    消息完全匹配对应内容时触发被修饰的函数。

- 参数
    * `words: Union[str, Set[str]]` 匹配内容
    * `only_to_me: bool` 是否限定为@bot才会触发
    * `**kwargs` 其他传给原`nonebot.on_startswith`的可选参数


### 修饰器 `on_notice()`
- 说明  
    收到对应通知时触发被修饰的函数

- 参数
    * `notice_type: str` 通知类型，使用`notice_type.sub_type`的格式，可省略sub_type。具体类型请查看[OneBot通知事件](https://github.com/howmanybots/onebot/blob/master/v11/specs/event/notice.md)
    * `**kwargs` 其他传给原`nonebot.on_notice`的可选参数


### 修饰器 `scheduled_job()`
- 说明  
    设置一个定时任务为被修饰的函数

- 参数
    * `trigger: str` 定时器类型。详细请参阅APScheduler的文档
    * `name: Optional[str]` 定时器名字，可用于管理定时器
    * `**kwargs` 其他传给原`scheduler.add_job`的可选参数


# `R`
### `img(path, *paths)`
- 说明  
    将path和paths与`./res/img/`拼接，从得到的图片路径加载图片，返回`ResImg`

- 参数
    * `path: str` 路径名
    * `*paths` 多个路径名


# `privilege`
消息权限管理，可用于定义Service时限制使用权限；也可用于在定义消息响应器时单独设置权限，通过`permission`参数传入（见Nonebot文档）。
- `DEFAULT` 默认权限，群聊和私聊任何消息都被允许
- `PRIVATE` 仅限私聊
- `GROUP_ADMIN` 仅限群管理员及以上
- `GROUP_OWNER` 仅限群主及以上
- `WHITE` 仅限白名单和bot管理员
- `SUPERUSER` 仅限bot管理员

## 示例
```py
sv1 = Service('private_only',
             use_priv=PRIVATE)

sv2 = Service('admin_only',
             visible=False,
             use_priv=GROUP_ADMIN,
             manage_priv=SUPERUSER)
```