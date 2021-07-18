# -*- coding: UTF-8 -*-

import os
import re
import time

import aria2p
import feedparser
import requests
from jinja2 import Template
from pymongo import MongoClient

from .utils import default_user_agent, escapeText, postData


class Anime:
    def __init__(self, config, rss):
        env = os.environ

        if env.get("ARIA2_HOST"):
            a_host = env["ARIA2_HOST"]
            if not a_host.startswith("http"):
                a_host = "http://" + a_host
        else:
            a_host = config["aria2"]["host"]
            if not a_host.startswith("http"):
                a_host = "http://" + a_host

        a_port = int(env.get("ARIA2_PORT") or config["aria2"]["port"] or 6800)

        a_secret = env.get("ARIA2_SECRET") or config["aria2"]["secret"]

        if a_host:
            self.aria2 = aria2p.API(
                aria2p.Client(
                    host=a_host,
                    port=a_port,
                    secret=a_secret,
                )
            )
        else:
            self.aria2 = None

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

        for s in self.rss:
            self.handleRSS(s)

    # RSS source:
    #   1. https://mikanani.me/
    #   2. https://rssbg.now.sh
    def handleRSS(self, a):
        entries = feedparser.parse(
            a["url"],
            request_headers={"user-agent": default_user_agent},
        )["entries"]
        regex = re.compile(a["regex"])

        for r in entries:
            if regex.match(r["title"]) and not self.db["Download"].find_one(
                    {"title": r["title"]}
            ):
                download_link = None
                for l in r["links"]:
                    if l["type"] == "application/x-bittorrent":
                        download_link = l["href"]

                download_link = download_link or r["link"]

                if self.sendToAria2(a["path"], download_link):
                    down = {
                        "series": a["series"],
                        "title": r["title"],
                        "link": download_link,
                        "create_time": time.time(),
                    }

                    self.db["Download"].insert_one(down)
                    if self.telegram:
                        self.sendToTelegram(
                            r["title"], a["type"], a["series"], a["path"]
                        )

    def sendToAria2(self, path, url):
        if not self.send:
            print("未添加Aria2客户端或仅作为测试！链接为: ", url)
            return False

        else:
            if url.startswith("magnet:?xt="):
                try:
                    self.aria2.add_magnet(url, options={"dir": path})
                    print("添加成功 Magnet: ", url)
                    return True
                except Exception as e:
                    print("添加失败 Magnet: ", url, e)
                    return False

            else:
                r = requests.get(url)
                with open("tmp.torrent", "wb") as f:
                    f.write(r.content)

                try:
                    self.aria2.add_torrent("tmp.torrent", options={"dir": path})
                    print("添加成功 Torrent: ", url)
                    return True
                except Exception as e:
                    print("添加失败 Torrent: ", url, e)
                    return False
                finally:
                    os.remove("tmp.torrent")

    def sendToTelegram(self, title, type, series, path):
        args = {
            "title": escapeText(title),
            "type": escapeText(type),
            "series": escapeText(series),
            "link": self.url.rstrip("/") + "/" + path.strip("/").split("/")[-1]
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

        r = postData(url, data=payload)

        if r.json().get("ok"):
            print(title + " 已成功发送到Telegram!")
