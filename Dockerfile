FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app
ADD . /app
RUN ls

RUN pip install requests lxml peewee pyTelegramBotAPI

ENTRYPOINT python main.py
