# -*- coding: utf-8 -*-
import requests
from . import config


def get_galley_info(url):
    """
    Params:
    url:
        https://exhentai.org/g/1678954/ddcbc51afc/

    Return:
    Tuple
        [0]: 标题
        [1]: List，每一页的url
    """
    return "[Yukiusagi.] Tonari no Sakyubasu Oneesan | 邻家的魅魔大姐姐 (COMIC Unreal 2019-10 Vol. 81) [Chinese] [暴碧汉化组] [Digital]", ["https://exhentai.org/s/3169d62d59/1678954-1"]


def download_image(url):
    """
    Params:
    url:
        https://exhentai.org/s/3169d62d59/1678954-1

    Return:
    Bytes
        图片的二进制数据
    """
    with open("001.jpg", "rb") as file:
        return file.read()