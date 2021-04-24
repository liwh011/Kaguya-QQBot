import json
import os
import re
import time
import random
from typing import List

import requests
from src import R

tmp_dir = './res/img/tmp/'
if not os.path.exists(tmp_dir):
    os.mkdir(tmp_dir)

def is_today(timestamp: int) -> bool:
    t1 = time.time()
    t1_str = time.strftime("%Y-%m-%d", time.localtime(t1))
    t2_str = time.strftime("%Y-%m-%d", time.localtime(timestamp))
    return t1_str == t2_str

def get_today_img_urls() -> List[str]:
    url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?visitor_uid=1679362&host_uid=149592&offset_dynamic_id=0&need_top=1'

    header = {
        'Host': 'api.vc.bilibili.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://space.bilibili.com',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': 'https://space.bilibili.com/149592/dynamic',
        'Cache-Control': 'max-age=0',
    }

    response = requests.get(url=url, headers=header)
    raw = response.content.decode('utf-8')
    data = json.loads(raw)

    card_list = data['data']['cards']
    today_card = [card for card in card_list if is_today(
        card['desc']['timestamp'])]

    for card in today_card:
        content_raw = card['card']
        content_json = json.loads(content_raw)
        if 'pictures' in content_json['item']:
            pics = content_json['item']['pictures']
            pics = [i['img_src'] for i in pics]
            if len(pics) == 9:
                return pics

    return []


def download_img(img_url: str):
    """下载图片到本地，返回CQ码"""

    header = {
        'Host': 'i0.hdslb.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    r = requests.get(img_url, headers=header, stream=True)
    img_name = re.match(r'.*/(.*)', img_url).group(1)
    if r.status_code == 200:
        local_img_path = os.path.join(tmp_dir, img_name)
        open(local_img_path,
             'wb').write(r.content)  # 将内容写入图片
        return R.img('tmp/', img_name).cqcode
    return ''


def get_today_shadiao_pic():
    """获得今日的9张图"""
    # 清除昨日缓存
    exist_files = os.listdir(tmp_dir)
    for i in exist_files:
        os.remove(os.path.join(tmp_dir, i))

    # 获取图片链接
    pic_urls = get_today_img_urls()

    # 下载
    msgs = [download_img(pic) for pic in pic_urls]
    return msgs

def get_single_shadiao_pic():
    """获得单张图"""
    exist_files = os.listdir(tmp_dir)
    if exist_files:
        return R.img('tmp/', random.choice(exist_files)).cqcode
    else:
        return '没有存货'


if __name__ == "__main__":
    get_today_shadiao_pic()
