# -*- coding: utf-8 -*-
from telebot import apihelper
import telebot
import config

apihelper.proxy = {"https": "socks5://127.0.0.1:10808"}
bot = telebot.TeleBot(config.TG_BOT_TOKEN)

from . import command