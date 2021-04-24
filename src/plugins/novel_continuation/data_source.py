import random
from nonebot import logger
from asyncio import sleep

from src import aiorequests

HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Content-Type": "application/json;charset=utf-8",
}


async def get_nid(text: str) -> str:
    """获得文章id"""
    url = 'http://if.caiyunai.com/v1/dream/602c8c0826a17bcd889faca7/novel_save'
    data = {"content": text, "title": "", "ostype": ""}
    response = await aiorequests.post(url, json=data, headers=HEADER)
    if response.status_code == 200:
        return (await response.json())['data']['nid']
    else:
        raise Exception(f'HTTP {response.status_code}')


async def submit_to_ai(text: str, novel_id: str, model_id: str = '601f92f60c9aaf5f28a6f908'):
    """将文本提交到指定模型的AI，得到xid"""
    url = 'http://if.caiyunai.com/v1/dream/602c8c0826a17bcd889faca7/novel_ai'
    data = {
        "nid": novel_id,
        "content": text,
        "uid": "602c8c0826a17bcd889faca7",
        "mid": model_id,
        "title": "",
        "ostype": ""
    }
    response = await aiorequests.post(url, json=data, headers=HEADER)
    rsp_json = await response.json()
    xid = rsp_json['data']['xid']
    return xid


async def poll_for_result(nid: str, xid: str):
    """不断查询，直到服务器返回生成结果"""
    url = 'http://if.caiyunai.com/v1/dream/602c8c0826a17bcd889faca7/novel_dream_loop'
    data = {
        "nid": nid,
        "xid": xid,
        "ostype": ""
    }
    max_retry_times = 10
    for _ in range(max_retry_times):
        response = await aiorequests.post(url, json=data, headers=HEADER)
        rsp_json = await response.json()
        if rsp_json['data']['count'] != 0:  # 说明还没有生成好，继续重试
            await sleep(1.5)
            continue
        results = rsp_json['data']['rows']
        results = [res['content'] for res in results]
        return results
    raise TimeoutError('服务器太久没响应')


async def get_single_continuation(text: str):
    try:
        result=''
        for i in range(3): # 连续续写三次
            nid = await get_nid(text)
            xid = await submit_to_ai(text, nid)
            logger.info(f'正在等待服务器返回第{i+1}段续写结果')
            continuation = await poll_for_result(nid, xid)
            result += text + random.choice(continuation)
        logger.info('续写完成')
        return result
    except Exception as e:
        logger.error(f'发生错误{e}')
        logger.exception(e)
        return f'发生错误{e}'
