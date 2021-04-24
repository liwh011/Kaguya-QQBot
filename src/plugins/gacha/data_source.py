import base64
import os
import random
from io import BytesIO
from typing import Any, Dict, List

import requests
import ujson as json
from nonebot import Driver, get_driver, logger
from nonebot.adapters.cqhttp import MessageSegment
from PIL import Image
from src.util import pic2b64
from src import R

driver: Driver = get_driver()
global_config = driver.config
RES_DIR = os.path.join(global_config.res_dir, 'img', 'gacha')
CONFIG_PATH: str
CONFIG: dict

current_game: str = ''


def draw(times: int, game_name: str) -> Dict[str, List[str]]:
    """抽卡"""
    game: Dict[str, Any] = CONFIG[game_name]
    cards: List[dict] = game['cards']
    current_pool: str = game['current_pool']
    pool: Dict[str, dict] = game['pools'][current_pool]

    result = {k: [] for k in pool}
    for _ in range(times):
        rand = random.random()
        for type_name, item_type in pool.items():
            rate = item_type['rate']
            up_rate = item_type['up_rate']
            if rand > rate:
                rand -= rate  # 减去，相当于每个概率叠加的范围
                continue
            # 随机数落在范围里面
            # 再摇一个随机数，用于抽up角色
            if random.random() <= up_rate:
                item = random.choice(item_type['up'])
                result[type_name].append(item)
            else:
                item = random.choice(item_type['items'])
                result[type_name].append(item)
            break
    return result


def build_msg(draw_result: Dict[str, List[str]]) -> str:
    """生成纯文字回复信息"""
    msg = '\n'.join([f'{k}：{"、".join(v)}'
                     if len(v) != 0
                     else f'{k}：没抽到'
                     for k, v in draw_result.items()])
    return msg


def download_icon(url: str, target: str):
    """从url中下载图标"""
    save_path = target
    logger.info(f'正在从{url}下载图标...')
    try:
        rsp = requests.get(url, stream=True, timeout=5)
        if 200 == rsp.status_code:
            img = Image.open(BytesIO(rsp.content))
            img.save(save_path)
            logger.info(f'图标已保存到{save_path}')
        else:
            logger.error(f'从{url}下载失败。HTTP {rsp.status_code}')
    except Exception as e:
        logger.error(f'从{url}下载失败。{type(e)}')
        logger.exception(e)


def get_image(game_name: str, item_name: str) -> Image.Image:
    """获取图像，从本地或网络"""
    # 本地是否存在资源
    try:
        return R.img(f'gacha/{game_name}/{item_name}.png').open().convert("RGBA")
    except FileNotFoundError:
        logger.warning(f'没有在本地找到"{item_name}"，将试图从网络获取。')

    # 检查本地是否存在对应文件夹
    game_dir = os.path.join(RES_DIR, game_name)
    if not os.path.exists(game_dir):
        os.makedirs(game_dir)

    # 从卡片信息找到图像url
    url = [i for i in CONFIG['game_name']['cards'] if i.name == item_name]
    if not url:
        raise ValueError(f'找不到{item_name}')
    url = url[0]

    # 保存到本地
    save_path = os.path.join(game_dir, f'{item_name}.png')
    download_icon(url, save_path)
    return Image.open(save_path).convert("RGBA")


def concat_pic(imgs: List[Image.Image], border: int = 5) -> Image.Image:
    """多个图像拼接"""
    num = len(imgs)
    w, h = imgs[0].size
    # 计算合成的图中有多少行图标
    col = 5
    row = int(num/5 + 0.5)
    # 计算图的长宽
    des_w = col * w + (col-1) * border
    des_h = row * h + (row-1) * border
    des = Image.new('RGBA', (des_w, des_h), (255, 255, 255, 255))
    for i, img in enumerate(imgs):
        des.paste(img, ((i % col) * (w + border),
                        (i // col) * (h + border)), img)
    return des


def build_imgmsg(draw_result: Dict[str, List[str]]):
    """生成图像消息"""
    # 将每个类别的抽卡结果汇聚到一个列表
    items = []
    for _, l in draw_result.items():
        items.extend(l)
    # 对每个item获取图像
    imgs = [get_image(current_game, item) for item in items]
    res_img = concat_pic(imgs)
    res_b64 = pic2b64(res_img)

    msg = MessageSegment.image(file=res_b64)
    return msg


def sim_draw(times: int, game: str, noimg: bool = False):
    """模拟抽卡"""
    global current_game
    current_game = game
    if noimg:
        return build_msg(draw(times, game))
    else:
        return build_imgmsg(draw(times, game))


async def load_json_file(filename: str) -> Dict[str, Any]:
    """读取json文件"""
    global CONFIG_PATH
    try:
        with open(os.path.join(CONFIG_PATH, filename), "r", encoding="utf-8") as f:
            res = json.load(f)
        return res
    except FileNotFoundError:
        logger.info(f"找不到文件{filename}")
    except Exception as e:
        logger.exception(e)
    return {}


@driver.on_startup
async def check_data():
    """启动加载数据"""
    global CONFIG, CONFIG_PATH
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config')
    CONFIG = await load_json_file('config.json')
    if not CONFIG:
        logger.info("找不到config.json")
        return
    # 读取卡的数据
    for _, game in CONFIG.items():
        game['cards'] = await load_json_file(game['cards'])
    logger.info("gacha初始化成功")
