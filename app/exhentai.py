# -*- coding: utf-8 -*-
import logging
from lxml import etree
import requests, threading, re, queue


from . import config

class Exhentai(object):
    def __init__(self, url):
        self.url = url
        self.cache = {}
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like "
                          "Gecko) Chrome/43.0.2357.132 Safari/537.36",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "cookie": config.EX_COOKIES,
            "hosts": "exhentai.org"
        }
        self.client = requests.session()
        self.list = []
        self.result = []
        self.queue = queue.Queue()
        self.thread = int(config.DOWNLOAD_THREAD_NUMBER)

    def get_result(self):
        return self.result

    def __thread_download(self):
        while not self.queue.empty():
            target = self.queue.get()
            web_source = self.client.get(target[1], headers=self.headers)
            html = etree.HTML(web_source.content)
            image = html.xpath("//img[@id='img']")[0].attrib["src"]
            if image:
                img_raw = self.client.get(image, headers=self.headers)
                self.result[target[0]] = img_raw.content
            else:
                self.result[target[0]] = False
                return 

    def info(self):
        web_source = self.client.get(self.url, headers=self.headers)
        html = etree.HTML(web_source.content)
        title = html.xpath("//h1[@id='gn']")[0].text
        self.list = [a.attrib["href"] for a in html.xpath("//div[@class='gdtm']/div/a")]
        page_node = html.xpath("//table[@class='ptb']/tr/td")
        if len(page_node) > 3:
            for p in range(1, int(page_node[-2][0].text)):
                web_source = self.client.get(self.url + f"?p={p}", headers=self.headers)
                html = etree.HTML(web_source.content)
                self.list += [a.attrib["href"] for a in html.xpath("//div[@class='gdtm']/div/a")]
        return title, len(self.list)
    
    def start_download(self):
        self.result = [None for i in range(len(self.list))]
        for i, j in enumerate(self.list):
            self.queue.put((i, j))
        threads = []
        for i in range(self.thread):
            t = threading.Thread(target=self.__thread_download)
            threads.append(t)
        for start in threads:
            start.start()
        for join in threads:
            join.join()
        for r in self.result:
            if not r:
                return []
        return self.result
