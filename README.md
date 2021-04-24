# Kaguya
本机器人的名字取自「辉夜大小姐」，实际上与辉夜并没有什么关系，请勿将bot与人物联系起来~           

最初将Bot用于PCR公会群的管理，使用的是HoshinoBot。后来本人开始魔改Bot，但苦于HoshinoBot没有全面的API文档，举步维艰，将其搁置了很长一段时间。偶然间发现Nonebot框架推出了v2版本，便打算基于Nonebot2来实现自己的bot，并将HoshinoBot的部分功能移植到其中。      

HoshinoBot将Nonebot的API封装为Service的思路令人印象深刻，因此，这个项目也采取了类似的封装方法。    



# 部署指南
## 环境配置
本项目使用poetry来管理虚拟环境。    
1. cd到项目根目录
2. 使用`poetry install`来为虚拟环境安装依赖包。
3. 使用`poetry shell`进入虚拟环境
4. 使用`nb run`运行bot。

如果没啥问题的话就能在终端看到启动全过程了。

## 服务器部署
请参阅NoneBot2文档中的[CQHTTP 协议使用指南](https://v2.nonebot.dev/guide/cqhttp-guide.html)    
注：文中提到的【nonebot配置】默认为`.env.dev`

如使用Docker部署，请自行修改docker配置。



# 快速上手
## 配置机器人参数
在根目录下有`.env`开头的几个文件，查阅[NoneBot2基本配置](https://v2.nonebot.dev/guide/basic-configuration.html)     
### 配置项
这里仅介绍几个额外添加的配置项：
- `RES_DIR`：图片资源目录。R模块中提供了方法来访问的该目录。
- `CACHE_DIR`：缓存目录。某些功能可能需要建立一个数据库，或者缓存一些东西在其中。
- `INCREASE_WELCOMES`：入群欢迎词

### 在程序中使用全局配置
可通过
```py
from nonebot import get_driver
global_config = get_driver().config

var = global_config.somekey
```
来获取配置。



## 添加新功能
### 自行编写新功能
1. 使用`nb plugin new`创建新插件
2. 在插件的`__init__.py`内敲入`sv = Service('svname')`来创建服务
3. 按照你的需要使用Service下的各种修饰器来修饰你的函数。

下面是一个Example
```python
from nonebot.adapters.cqhttp import Bot, Event

sv = Service('Test')

# 响应指令“你好”
@sv.on_command('你好')
async def on_greet(bot: Bot, event: Event):
    await bot.send(event, '好个锤子')

# 响应关键词“草”等
@sv.on_keyword(['草', 'ww', '艹'])
async def on_grass(bot: Bot, event: Event):
    await bot.send(event, '草草草')
```
### 安装Nonebot插件
兼容Nonebot2的插件。    
请前往[NoneBot商店](https://v2.nonebot.dev/store.html)获取，安装方法查阅NoneBot2文档


## Bot使用说明
[Bot功能使用说明](./docs/usage.md)

## API说明
[API文档](./docs/api.md)    
文档在慢慢完善。。。   



# 使用过的开源代码
- Pcr模块、dice模块、util模块、R、aiorequests移植自 @Ice-Cirno [HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot/)
- PcrDuel模块来着 @Rs794613 [PcrDuel](https://github.com/Rs794613/PcrDuel)
- gacha模块魔改自 @abrahum [nonebot_plugin_simdraw](https://github.com/abrahum/nonebot_plugin_simdraw)
- genshin模块移植自 @H-K-Y [Genshin_Impact_bot](https://github.com/H-K-Y/Genshin_Impact_bot)