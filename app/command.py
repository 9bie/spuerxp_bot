# -*- coding: utf-8 -*-
import os
import re
import json
import traceback
from queue import Queue
import requests
from telebot import types
from . import bot, config
from .exhentai import *
from .model import Article, Admin


@bot.message_handler(commands=["start"])
def bot_start(message):
    bot.reply_to(message, "奇怪的XP增加了！输入/help以查看帮助")


@bot.message_handler(commands=["help"])
def bot_help(message):
    bot.reply_to(message, "向Bot发送exhentai链接并遵循指引以发布本子")


@bot.message_handler(regexp="https:\/\/exhentai\.org\/g\/\d+\/[a-z0-9]+\/")
def handle_url(message):
    if not message.is_admin:
        bot.reply_to(message, f"您不是管理员[CHAT_ID: {message.from_user.id}]")
        return 
    
    m = bot.reply_to(message, "正在解析链接...")
    ex_link = re.search("https:\/\/exhentai\.org\/g\/\d+\/[a-z0-9]+\/", message.text).group(0)
    ex = Exhentai(ex_link)
    try:
        title, img_cnt = ex.info()
    except Exception as e:
        traceback.print_exc()
        bot.edit_message_text(f"解析链接失败!\n{e}", chat_id=m.chat.id, message_id=m.message_id)

    bot.edit_message_text(f"{title}\n共 {img_cnt} 张\n正在下载图片...", chat_id=m.chat.id, message_id=m.message_id)
    try:
        imgs = ex.start_download()
        assert imgs
    except Exception as e:
        traceback.print_exc()
        bot.edit_message_text(f"下载图片失败!\n{e}", chat_id=m.chat.id, message_id=m.message_id)
        return 
    
    bot.edit_message_text(f"图片下载成功，正在上传...", chat_id=m.chat.id, message_id=m.message_id)
    uploaded = []
    uploading = []
    images = Queue()
    size = 0
    for i in imgs:
        images.put(i)
    try:
        """
        for i in imgs:
            uploaded.append(requests.post("https://telegra.ph/upload/",
                                        files={"image": i}).json()[0]["src"])
        """
        while not images.empty():
            tmp = images.get()
            uploading.append(tmp)
            size += len(tmp)
            if size >= 5 * 1024 * 1024 or images.empty():
                uploaded += [i["src"] for i in requests.post("https://telegra.ph/upload/",
                                                             files={f"image-{i}": v for i, v in enumerate(uploading)}).json()]
                uploading = []
                size = 0
                
    except Exception as e:
        traceback.print_exc()
        bot.edit_message_text(f"图片上传失败!\n{e}", chat_id=m.chat.id, message_id=m.message_id)
        return 
    
    bot.edit_message_text(f"正在生成文章...", chat_id=m.chat.id, message_id=m.message_id)
    try:
        page = requests.post("https://api.telegra.ph/createPage",
                             data={"access_token": config.PH_TOKEN,
                                   "title": title,
                                   "author_name": config.AURHOR_NAME,
                                   "author_url ": config.AUTHOR_URL,
                                   "content": json.dumps([{"tag": "img",
                                                           "attrs": {"src": f"https://telegra.ph{i}"}} for i in uploaded])})
    except Exception as e:
        traceback.print_exc()
        bot.edit_message_text(f"生成文章失败!\n{e}", chat_id=m.chat.id, message_id=m.message_id)
        return 
    
    if page.json()["ok"]:
        url = page.json()['result']['url']
        article = Article(title=title,
                          ex_link=ex_link,
                          url=url,
                          message_id=m.message_id,
                          chat_id=m.chat.id,
                          desc="")
        article.save()
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("发布至频道",
                                              callback_data=json.dumps({"action": "publish_to_chanel", "article_id": article.id})),
                   types.InlineKeyboardButton("添加描述",
                                              callback_data=json.dumps({"action": "edit_desc", "article_id": article.id})))
        bot.edit_message_text(f"<a href=\"{url}\">{title}</a>\n<b>Source: </b><a href=\"{ex_link}\">ExHentai</a>",
                              chat_id=m.chat.id,
                              message_id=m.message_id,
                              parse_mode="html",
                              reply_markup=markup)
    else:
        bot.edit_message_text(f"文章生成失败!\n{page.text}", chat_id=m.chat.id, message_id=m.message_id)


@bot.callback_query_handler(func=lambda x: True)
def callback_button(call):
    if not call.is_admin:
        bot.answer_callback_query(call.id, text=f"您不是管理员[CHAT_ID: {call.from_user.id}]", show_alert=True)
        return 
    data = json.loads(call.data)
    article = Article.get_or_none(Article.id == data["article_id"])
    if not article:
        bot.answer_callback_query(call.id, text="文章不存在!", show_alert=True)
        return 
    if data["action"] == "publish_to_chanel":
        if article.published:
            bot.answer_callback_query(call.id, text="文章已发布!")
        else:
            pub_m = bot.send_message(config.TG_CHANNEL_ID,
                                     f"<a href=\"{article.url}\">{article.title}</a>\n<b>Source: </b><a href=\"{article.ex_link}\">ExHentai</a>\n{article.desc}",
                                     parse_mode="html")
            article.published = True
            article.published_id = pub_m.message_id
            article.save()
            bot.answer_callback_query(call.id, text="发布成功!")
    elif data["action"] == "edit_desc":
        markup = types.ForceReply(selective=True)
        m = bot.reply_to(call.message,
                         f"输入文章(ID: {article.id})的描述",
                         reply_markup=markup)


        def callback(message):
            bot.clear_reply_handlers(message.reply_to_message)
            article = Article.get_or_none(Article.id == data["article_id"])
            if not article:
                bot.answer_callback_query(call.id, text="文章不存在!", show_alert=True)
                return 
            article.desc = message.text
            
            if article.published:
                bot.edit_message_text(f"<a href=\"{article.url}\">{article.title}</a>\n<b>Source: </b><a href=\"{article.ex_link}\">ExHentai</a>\n{article.desc}",
                                      chat_id=config.TG_CHANNEL_ID,
                                      message_id=article.published_id,
                                      parse_mode="html")
            bot.delete_message(message.chat.id, article.message_id)
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("发布至频道",
                                                callback_data=json.dumps({"action": "publish_to_chanel", "article_id": article.id})),
                    types.InlineKeyboardButton("修改描述",
                                                callback_data=json.dumps({"action": "edit_desc", "article_id": article.id})))
            new_m = bot.reply_to(message,
                                 f"<a href=\"{article.url}\">{article.title}</a>\n<b>Source: </b><a href=\"{article.ex_link}\">ExHentai</a>\n{article.desc}",
                                 parse_mode="html",
                                 reply_markup=markup)
            article.message_id = new_m.message_id
            article.save()


        bot.register_for_reply(m, callback)


@bot.middleware_handler(update_types=["message", "callback_query"])
def check_admin(bot_instance, message):
    message.is_admin = not Admin.get_or_none(Admin.chat_id == message.from_user.id) is None
