from typing import Union
from .filter import DFAFilter
import os
from nonebot.adapters.cqhttp import Message

gfw = DFAFilter()
gfw.parse(os.path.join(os.path.dirname(__file__),
                       'sensitive_words.txt'))


def filt_message(message: Union[Message, str]):
    if isinstance(message, str):
        return gfw.filter(message)
    elif isinstance(message, Message):
        for seg in message:
            if seg.type == 'text':
                seg.data['text'] = gfw.filter(seg.data.get('text', ''))
        return message
    else:
        raise TypeError
