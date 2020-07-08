# -*- coding: utf-8 -*-
from peewee import *

db = SqliteDatabase("data.db")


class BaseModel(Model):
    class Meta:
        database = db


class Article(BaseModel):
    id = PrimaryKeyField()
    title = TextField()
    ex_link = TextField()
    url = TextField()
    chat_id = IntegerField()
    message_id = IntegerField()
    desc = TextField(default="")
    published = BooleanField(default=False)
    published_id = IntegerField(null=True)


class Admin(BaseModel):
    id = PrimaryKeyField()
    chat_id = IntegerField()
    