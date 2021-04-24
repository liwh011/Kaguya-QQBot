import os
import random

from src import R

setu_folder = R.img('setu/').path

def setu_gener():
    while True:
        filelist = os.listdir(setu_folder)
        random.shuffle(filelist)
        for filename in filelist:
            if os.path.isfile(os.path.join(setu_folder, filename)):
                yield R.img('setu/', filename)

setu_gener = setu_gener()

def get_local_setu() -> R.ResImg:
    try:
        return setu_gener.__next__()
    except StopIteration:
        return None
