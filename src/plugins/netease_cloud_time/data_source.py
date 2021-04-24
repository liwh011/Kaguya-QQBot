import json
import random
import re
import urllib
import urllib.parse
import urllib.request

ban_words = ['网易云', '销量', '播放量', '评论', '更新',
             '哈哈', '中国', '党', '政治', '膜', '蛤', '暴力', '共', '国', '腰带']
min_length = 70
hotcomment_pick_range = 99


async def pick_comment():
    list_id = await get_all_search_list()
    pick_index = random.randint(0, len(list_id) - 1)

    # 获取热歌榜所有歌曲名称和id
    hot_song_name, hot_song_id = await get_all_hotSong(list_id[pick_index])
    # 在热榜随机选一首歌
    pick_index = random.randint(0, len(hot_song_id) - 1)
    comment = await get_hotComments(hot_song_name[pick_index], hot_song_id[pick_index])

    pick_index = random.randint(0, len(comment) - 1)
    return comment[pick_index]


async def get_all_list():  # 获取所有歌单
    url = 'https://music.163.com/discover/playlist/?cat=%E4%BC%A4%E6%84%9F'  # 伤感歌单
    header = {  # 请求头部
        'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    request = urllib.request.Request(url=url, headers=header)
    html = urllib.request.urlopen(request).read().decode('utf8')  # 打开url
    html = str(html)  # 转换成str
    pat1 = r'<a title=".*" href=".*" class="msk"></a>'  # 进行第一次筛选的正则表达式
    result = re.compile(pat1).findall(html)  # 用正则表达式进行筛选
    result = result[0]  # 获取tuple的第一个元素

    pat2 = r'<a title="(.*)" href=".*" class="msk"></a>'  # 进行歌名筛选的正则表达式
    # 进行歌ID筛选的正则表达式
    pat3 = r'<a title=".*" href="/playlist\?id=(.*)" class="msk"></a>'
    list_name = re.compile(pat2).findall(result)  # 获取所有热门歌曲名称
    list_id = re.compile(pat3).findall(result)  # 获取所有热门歌曲对应的Id

    return list_name, list_id


async def get_all_hotSong(list_id):  # 获取热歌榜所有歌曲名称和id
    # url = 'http://music.163.com/discover/toplist?id=71385702'  # 网易云云音乐热歌榜url
    url = 'http://music.163.com/playlist?id='+str(list_id)  # 网易云云音乐歌单url
    header = {  # 请求头部
        'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    request = urllib.request.Request(url=url, headers=header)
    html = urllib.request.urlopen(request).read().decode('utf8')  # 打开url
    html = str(html)  # 转换成str
    pat1 = r'<ul class="f-hide"><li><a href="/song\?id=\d*?">.*</a></li></ul>'  # 进行第一次筛选的正则表达式
    result = re.compile(pat1).findall(html)  # 用正则表达式进行筛选
    result = result[0]  # 获取tuple的第一个元素

    pat2 = r'<li><a href="/song\?id=\d*?">(.*?)</a></li>'  # 进行歌名筛选的正则表达式
    pat3 = r'<li><a href="/song\?id=(\d*?)">.*?</a></li>'  # 进行歌ID筛选的正则表达式
    hot_song_name = re.compile(pat2).findall(result)  # 获取所有热门歌曲名称
    hot_song_id = re.compile(pat3).findall(result)  # 获取所有热门歌曲对应的Id

    return hot_song_name, hot_song_id


async def get_hotComments(hot_song_name, hot_song_id):
    url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + \
        hot_song_id + '?csrf_token='  # 歌评url
    header = {  # 请求头部
        'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    # post请求表单数据
    data = {'params': 'zC7fzWBKxxsm6TZ3PiRjd056g9iGHtbtc8vjTpBXshKIboaPnUyAXKze+KNi9QiEz/IieyRnZfNztp7yvTFyBXOlVQP/JdYNZw2+GRQDg7grOR2ZjroqoOU2z0TNhy+qDHKSV8ZXOnxUF93w3DA51ADDQHB0IngL+v6N8KthdVZeZBe0d3EsUFS8ZJltNRUJ',
            'encSecKey': '4801507e42c326dfc6b50539395a4fe417594f7cf122cf3d061d1447372ba3aa804541a8ae3b3811c081eb0f2b71827850af59af411a10a1795f7a16a5189d163bc9f67b3d1907f5e6fac652f7ef66e5a1f12d6949be851fcf4f39a0c2379580a040dc53b306d5c807bf313cc0e8f39bf7d35de691c497cda1d436b808549acc'}
    postdata = urllib.parse.urlencode(data).encode('utf8')  # 进行编码
    request = urllib.request.Request(url, headers=header, data=postdata)
    reponse = urllib.request.urlopen(request).read().decode('utf8')
    json_dict = json.loads(reponse)  # 获取json
    hot_commit = json_dict['hotComments']  # 获取json中的热门评论
    
    good_comments = [comment['content'] for comment in hot_commit
                     if (len(comment['content']) > min_length and not any(comment['content'].find(word) != -1 for word in ban_words))]

    return good_comments
    # # 随机选一个热评
    # pick_index = random.randint(0, len(hot_commit) - 1)
    # if pick_index > hotcomment_pick_range:
    #     pick_index = random.randint(0, hotcomment_pick_range)
    # return hot_commit[pick_index]['content']


async def get_all_search_list():
    url = 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token=1dd86fe06dc4196cce4ad1899bc6e59f'
    header = {  # 请求头部
        'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    # post请求表单数据
    data = {'params': 'p6/GVIMO3Ej0C7BneM8oRoKZKgtCTp8MMm/K0rbCVeJgjMfrQ5+w9A3vUJgXeRp68Qbcs4rVsPEhnDtuO1Fgsd2ZEeSXIYn9t5tDJfwmA2HYU6SdRBjHdXCDIvZbTZcLKJy3OtgoBexG719aVmeirp+Q8UiYH8BMHq1l/r7efZF1ubc7cCnbdAaEzp6+cQZ56lnYgKTJYCjLZuoaek2jDEieLOPtJR7tzI4bydkzuF8nRB3xIlotlCfTCRDAEKcTB4gHqbogTREkTgGeawbmtDCT97Ku7vgoCnshRcbYkJINTsQ7IQ2APxgmtXfJae9uqNlrZ2IbRp0R+UN6D/uFkJHN14qqjQ/K4pdqGbwvYms=',
            'encSecKey': '791e60bca6fef3085bf080c09902e17122a80ca728e5257914cf5c9633cd245bbf44e966a1cbbd29ded2868454d97fb43c5048c93d4428e168f8f85c7b4f4f7d30f61509ae2d7a3f2c8dc2ca870ad353ee10e8a8a295b5ac05ad02deb457cdbceda0af04c15b3bce97f7d0b710ea8968b7df0b065c862d7c80bb478c6ef7b783'}
    postdata = urllib.parse.urlencode(data).encode('utf8')  # 进行编码
    request = urllib.request.Request(url, headers=header, data=postdata)
    reponse = urllib.request.urlopen(request).read().decode('utf8')
    json_dict = json.loads(reponse)  # 获取json
    hot_commit = json_dict['result']['playlists']  # 获取json中的热门评论
    return [playlist['id'] for playlist in hot_commit]
