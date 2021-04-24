
import random
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from nonebot.adapters.cqhttp import MessageSegment

PLAYLISTS: List[str] = []
LIST_TO_SONGS: Dict[str, List[str]] = {}


def get_all_playlists() -> List[str]:
    data = {
        'params': 'skJw+zPqAso0TPRBXHr88c3LkiXJ2iBkSSAOOys2pNHKLmUbbsvzI8x6ZsuVHNGSM6b+amQcp1nvJA8SjnVtMaMiD8iXfu+L4bGlnsARof8migSRT2c81XOIPOwx6DxmxAxzhFTe60owNPkhOhq0D0N5d9KA/cgm4twJ15aTve7uCgVxn/66R734bbN2Y+EfrzRDQ4KN9X9609PQmnjdVwt41z6ykOYrISyYspBVADdvd6F7flBwF6077TOsmxZVZpdetnbr+jDAS96UmRO/RQ==',
        'encSecKey': '927db81ecb43f7c971f4bec3369c124618d777ec83e1ffd94d3932a569dc618f6380434c6b18ad8bf92a0cf1bde094913d050f87b1b1381c6a8316c16afb34cb66dd8faf04d4a168bb229e283879365e2af5933e078d9b6d53617165259161d784349c91736654c7c2ba837feda69e4330e76fec654a5735f3b58443994eb31c',
    }
    r = requests.post(
        'https://music.163.com/weapi/cloudsearch/get/web?csrf_token=', data=data)
    ids = [i['id'] for i in r.json()['result']['playlists']]
    return ids


def get_all_song(list_id: str) -> List[str]:
    url = f'https://music.163.com/playlist?id={list_id}'
    r = requests.get(url)
    html = r.content.decode(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    nodes = soup.select('#song-list-pre-cache .f-hide li a')
    songs = [n['href'] for n in nodes]
    ids = [s[len('/song?id='):] for s in songs]
    return ids


def get_song() -> MessageSegment:
    global PLAYLISTS, LIST_TO_SONGS
    if not PLAYLISTS:
        PLAYLISTS = get_all_playlists()
    list_id = random.choice(PLAYLISTS)
    if list_id not in LIST_TO_SONGS:
        songs = get_all_song(list_id)
        LIST_TO_SONGS[list_id] = songs
    else:
        songs = LIST_TO_SONGS[list_id]
    return MessageSegment.music('163', int(random.choice(songs)))
