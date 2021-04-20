# -*- coding: UTF-8 -*-

import os
import re
import time

import feedparser
import requests
import yaml
import aria2p
from pymongo import MongoClient


class Anime:
    def __init__(self, rss_file, config_file):
        self.rss_file = rss_file
        self.config_file = config_file
        self.loadConf()

    def loadConf(self):
        env = os.environ

        with open(self.config_file, "r", encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
            if env.get("ARIA2_HOST"):
                a_host = env["ARIA2_HOST"]
                if not a_host.startswith("http") or not a_host.startswith("HTTP"):
                    a_host = "http://" + a_host

                self.aria2 = aria2p.API(
                    aria2p.Client(
                        host=a_host,
                        port=env["ARIA2_PORT"],
                        secret=env["ARIA2_SECRET"],
                    )
                )

            elif config["aria2"]["host"]:
                a_host = config["aria2"]["host"]
                if not a_host.startswith("http") or not a_host.startswith("HTTP"):
                    a_host = "http://" + a_host

                self.aria2 = aria2p.API(
                    aria2p.Client(
                        host=a_host,
                        port=config["aria2"]["port"],
                        secret=config["aria2"]["secret"],
                    )
                )

            else:
                self.aria2 = None

            self.telegram = {}
            if env.get("TELEGRAM_ENABLE"):
                self.telegram["token"] = env["TELEGRAM_TOKEN"]
                self.telegram["chat_id"] = env["TELEGRAM_CHAT_ID"]
            elif config["telegrambot"]["enable"]:
                self.telegram = config["telegrambot"]

            if env.get("BASE_URL"):
                self.url = env["BASE_URL"]
            elif config["base_url"]:
                self.url = config["base_url"]
            else:
                self.url = None

            if env.get("DATABASE"):
                mongo_url = env["DATABASE"]
            else:
                mongo_url = config["mongo_url"]

        with open(self.rss_file, "r", encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
            self.rss = config["Anime"]

        client = MongoClient(mongo_url)
        self.db = client["Anime"]

    def readRSS(self, send=None):
        if send != None:
            self.send = send

        for s in self.rss:
            if s["source"].lower() == "mikan":
                self._readMikan(s)
            elif s["source"].lower() == "rarbg":
                self._readRarbg(s)

    # RSS source: https://mikanani.me/
    def _readMikan(self, a):
        entries = feedparser.parse(a["url"])["entries"]
        regex = re.compile(a["regex"])

        for r in entries:
            if regex.match(r["title"]) and not self.db["Download"].find_one(
                {"title": r["title"]}
            ):
                for l in r["links"]:
                    if l["type"] == "application/x-bittorrent":
                        if self._sendToAria2(a["path"], l["href"]):
                            down = {
                                "series": a["series"],
                                "title": r["title"],
                                "link": l["href"],
                                "create_time": time.time(),
                            }

                            self.db["Download"].insert_one(down)
                            if self.telegram:
                                self._sendToTelegram(
                                    r["title"], a["type"], a["series"], a["path"]
                                )

    # RSS source: https://rssbg.now.sh
    def _readRarbg(self, a):
        entries = feedparser.parse(
            a["url"],
            request_headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
            },
        )["entries"]
        regex = re.compile(a["regex"])

        for r in entries:
            try:
                r["title"] = regex.match(r["title"]).group(1)
                if not self.db["Download"].find_one({"title": r["title"]}):
                    if self._sendToAria2(a["path"], r["link"]):
                        down = {
                            "series": a["series"],
                            "title": r["title"],
                            "link": r["link"],
                            "create_time": time.time(),
                        }

                        self.db["Download"].insert_one(down)
                        if self.telegram:
                            self._sendToTelegram(
                                r["title"], a["type"], a["series"], a["path"]
                            )
            except Exception:
                pass

    def _sendToAria2(self, path, url):
        if not self.send:
            print("未添加Aria2客户端或仅作为测试！链接为: ", url)
            return False

        else:
            if url.startswith("magnet:?xt="):
                try:
                    self.aria2.add_magnet(url, options={"dir": path})
                except Exception:
                    print("添加失败 Magnet: ", url, "\n", e)
                    return False
                else:
                    print("添加成功 Magnet: ", url)
                    return True

            else:
                r = requests.get(url)
                with open("tmp.torrent", "wb") as f:
                    f.write(r.content)

                try:
                    self.aria2.add_torrent("tmp.torrent", options={"dir": path})
                except Exception as e:
                    print("添加失败 Torrent: ", url, "\n", e)
                    return False
                else:
                    print("添加成功 Torrent: ", url)
                    return True
                finally:
                    os.remove("tmp.torrent")

    def _sendToTelegram(self, title, type, series, path):
        if self.url:
            msg = (
                "🌟 更新剧集：*"
                + title
                + "*\n\n💡 直达链接："
                + self.url
                + path.strip("/").split("/")[-1]
                + "/\n\n#"
                + type
                + " #"
                + series.split(" ")[0]
            )
        else:
            msg = "🌟 更新剧集：*" + title + "*\n#" + type + " #" + series.split(" ")[0]

        url = "https://api.telegram.org/bot" + self.telegram["token"] + "/sendMessage"
        payload = {
            "chat_id": self.telegram["chat_id"],
            "text": msg,
            "parse_mode": "markdown",
            "disable_web_page_preview": "true",
        }

        r = requests.post(url, data=payload)

        if r.json()["ok"]:
            print(title + " 已成功发送到Telegram!")
