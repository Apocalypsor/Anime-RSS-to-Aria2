import os

import aria2p
import requests


class Aria2:
    def __init__(self, config):
        env = os.environ

        if env.get("ARIA2_HOST"):
            self.a_host = env["ARIA2_HOST"]
            if not self.a_host.startswith("http"):
                self.a_host = "http://" + self.a_host
        else:
            self.a_host = config["aria2"]["host"]
            if not self.a_host.startswith("http"):
                self.a_host = "http://" + self.a_host

        self.a_port = int(env.get("ARIA2_PORT") or config["aria2"]["port"] or 6800)

        self.a_secret = env.get("ARIA2_SECRET") or config["aria2"]["secret"]

        self.aria2 = None
        if self.valid():
            self.aria2 = aria2p.API(
                aria2p.Client(
                    host=self.a_host,
                    port=self.a_port,
                    secret=self.a_secret,
                )
            )
        else:
            exit("Aria2 配置错误")

    def valid(self):
        if self.a_host and self.a_port:
            return True

        return False

    def download(self, url, path, file_name):
        if url.startswith("magnet:?xt="):
            try:
                if file_name is not None:
                    self.aria2.add_magnet(url, options={"dir": path, "index-out": '1=' + file_name})
                else:
                    self.aria2.add_magnet(url, options={"dir": path})
                print("Aria2 添加成功 Magnet: ", url)
                return True
            except Exception as e:
                print("Aria2 添加失败 Magnet: ", url, e)
                return False

        else:
            r = requests.get(url)
            with open("tmp.torrent", "wb") as f:
                f.write(r.content)

            try:
                if file_name is not None:
                    self.aria2.add_torrent("tmp.torrent", options={"dir": path, "index-out": '1=' + file_name})
                else:
                    self.aria2.add_torrent("tmp.torrent", options={"dir": path})
                print("Aria2 添加成功 Torrent: ", url)
                return True
            except Exception as e:
                print("Aria2 添加失败 Torrent: ", url, e)
                return False
            finally:
                os.remove("tmp.torrent")
