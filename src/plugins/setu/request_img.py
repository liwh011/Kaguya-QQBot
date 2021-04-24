import os
import requests
import time

from src import R, aiorequests

setu_folder = R.img('setu/').path

header = {
    "Host": "i.xinger.ink:4443",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

url = 'https://i.xinger.ink:4443/images.php'


async def get_web_img() -> R.ResImg:
    filename = str(time.time())+'.jpg'
    full_path = os.path.join(setu_folder, filename)

    response = await aiorequests.get(url=url, headers=header, timeout=5)
    img = await response.content

    if not img:
        return None
        
    with open(full_path, 'wb') as img_file:
        img_file.write(img)
    
    # return filename
    return R.img('setu/', filename)
