# -*- coding: UTF-8 -*-

import os
import re
import time
from urllib.parse import quote

import feedparser
import requests
from jinja2 import Template
from pymongo import MongoClient

from .downloader.aria2 import Aria2
from .downloader.pikpak import PikPak
from .utils import default_user_agent, escapeText


class Anime:
    def __init__(self, config, rss):
        env = os.environ

        enabled = (env["ENABLED"] or config.get("enabled") or "aria2").split(",")
        self.enable_aria2 = "aria2" in enabled
        self.enable_pikpak = "pikpak" in enabled

        if self.enable_aria2:
            print("启用Aria2下载器")
            self.aria2 = Aria2(config["aria2"])
        if self.enable_pikpak:
            print("启用PikPak下载器")
            self.pikpak = PikPak(config["pikpak"])

        self.telegram = {}
        if env.get("TELEGRAM_ENABLE"):
            self.telegram["token"] = env["TELEGRAM_TOKEN"]
            self.telegram["chat_id"] = env["TELEGRAM_CHAT_ID"]
        elif config["telegram"]["enable"]:
            self.telegram = config["telegram"]

        self.url = env.get("BASE_URL") or config.get("base_url") or None
        mongo_url = env.get("DATABASE") or config["mongo_url"]

        self.rss = rss["Anime"]
        self.template = Template(rss["Template"])

        client = MongoClient(mongo_url)
        self.db = client["Anime"]

    def readRSS(self, send=None):
        if send != None:
            self.send = send

        for item in self.rss:
            self.handleRSS(item)

    # RSS source:
    #   1. https://mikanani.me/
    #   2. https://rssbg.now.sh
    def handleRSS(self, item):
        entries = feedparser.parse(
            item["url"],
            request_headers={"user-agent": default_user_agent},
        )["entries"]
        regex = re.compile(item["regex"])

        for r in entries:
            if regex.match(r["title"]) and not self.db["Download"].find_one(
                    {"title": r["title"]}
            ):
                download_link = None
                for l in r["links"]:
                    if l["type"] == "application/x-bittorrent":
                        download_link = l["href"]

                download_link = download_link or r["link"]

                if self.sendToDownloader(download_link, item["path"]):
                    down = {
                        "series": item["series"],
                        "title": r["title"],
                        "link": download_link,
                        "create_time": time.time(),
                    }

                    self.db["Download"].insert_one(down)
                    if self.telegram:
                        self.sendToTelegram(
                            r["title"], item["type"], item["series"], item["path"]
                        )

    def sendToDownloader(self, url, path):
        if not self.send:
            print("未添加下载客户端或仅作为测试！链接为: ", url)
            return False

        else:
            added = False
            if self.enable_aria2 and self.aria2.download(url, path):
                added = True
            if self.enable_pikpak and self.pikpak.download(url, path):
                added = True

            return added

    def sendToTelegram(self, title, type, series, path):
        args = {
            "title": escapeText(title),
            "type": escapeText(type),
            "series": escapeText(series),
            "link": self.url.rstrip("/")
                    + "/"
                    + quote(path.strip("/").split("/")[-1])
                    + "/"
            if self.url
            else "",
        }

        msg = self.template.render(args)

        url = "https://api.telegram.org/bot" + self.telegram["token"] + "/sendMessage"
        payload = {
            "chat_id": self.telegram["chat_id"],
            "text": msg,
            "parse_mode": "MarkdownV2",
        }

        r = requests.post(url, data=payload)

        if r.json().get("ok"):
            print(title + " 已成功发送到Telegram!")
