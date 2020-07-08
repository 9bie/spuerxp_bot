FROM python:3.7-slim

RUN mkdir /app
ADD . /app
WORKDIR /app

RUN pip install requests lxml peewee pyTelegramBotAPI

ENTRYPOINT python main.py
