# -*- coding: utf-8 -*-
from app import bot, model


if __name__ == "__main__":
    model.db.create_tables([model.Article, model.Admin])
    bot.polling(none_stop=True)
