import os

import aria2p
import requests


class Aria2:
    def __init__(self, config):
        env = os.environ

        a_host = env["ARIA2_HOST"] or config["aria2"]["host"]
        if a_host and not a_host.startswith("http"):
            a_host = "http://" + a_host

        a_port = int(env.get("ARIA2_PORT") or config["aria2"]["port"] or 6800)
        a_secret = env.get("ARIA2_SECRET") or config["aria2"]["secret"]

        self.aria2 = None
        if a_host and a_port:
            self.aria2 = aria2p.API(aria2p.Client(host=a_host, port=a_port, secret=a_secret))
        else:
            exit("Aria2 未配置")

    def download(self, url, path):
        if url.startswith("magnet:?xt="):
            try:
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
                self.aria2.add_torrent("tmp.torrent", options={"dir": path})
                print("Aria2 添加成功 Torrent: ", url)
                return True
            except Exception as e:
                print("Aria2 添加失败 Torrent: ", url, e)
                return False
            finally:
                os.remove("tmp.torrent")
