# -*- coding: utf-8 -*-
import re
from . import bot, config
from .exhentai import session


@bot.message_handler(commands=["start"])
def bot_start(message):
    bot.reply_to(message, "奇怪的XP增加了！输入/help以查看帮助")


@bot.message_handler(commands=["help"])
def bot_help(message):
    bot.reply_to(message, "向Bot发送exhentai链接并遵循指引以发布本子")


@bot.message_handler(regexp="https:\/\/exhentai\.org\/g\/\d+\/[a-z0-9]+\/")
def handle_url(message):
    m = bot.reply_to(message, "正在处理Ex链接……")
    
