import base64
import hashlib
import os
import urllib.parse

import fastbencode as bencode
import requests

PIKPAK_API_URL = "https://api-drive.mypikpak.com"
PIKPAK_USER_URL = "https://user.mypikpak.com"


class PikPak:
    def __init__(self, config):
        env = os.environ
        self.username = env.get("PIKPAK_USERNAME") or config["pikpak"]["username"]
        self.password = env.get("PIKPAK_PASSWORD") or config["pikpak"]["password"]
        self.session = requests.Session()
        if self.valid():
            self.login()
        else:
            exit("PikPak 账号信息不完整")

    def valid(self):
        return self.username is not None and self.password is not None

    def login(self):
        # 登录所需所有信息
        login_url = f"{PIKPAK_USER_URL}/v1/auth/signin"
        login_data = {
            "captcha_token": "",
            "client_id": "YNxT9w7GMdWvEOKa",
            "client_secret": "dbw2OtmVEeuUvIptb1Coyg",
            "password": self.password,
            "username": self.username,
        }
        headers = {
            "User-Agent": "protocolversion/200 clientid/YNxT9w7GMdWvEOKa action_type/ networktype/WIFI sessionid/ "
                          "devicesign/div101.073163586e9858ede866bcc9171ae3dcd067a68cbbee55455ab0b6096ea846a0 sdkversion/1.0.1.101300 "
                          "datetime/1630669401815 appname/android-com.pikcloud.pikpak session_origin/ grant_type/ clientip/ devicemodel/LG "
                          "V30 accesstype/ clientversion/ deviceid/073163586e9858ede866bcc9171ae3dc providername/NONE refresh_token/ "
                          "usrno/null appid/ devicename/Lge_Lg V30 cmd/login osversion/9 platformversion/10 accessmode/",
            "Content-Type": "application/json; charset=utf-8",
            "Host": "user.mypikpak.com",
        }

        info = self.session.post(
            url=login_url, json=login_data, headers=headers, timeout=5
        ).json()

        if "error" in info:
            print(f"PikPak 账号登录失败，错误信息：{info['error_description']}")
            return False
        else:
            headers["Authorization"] = f"Bearer {info['access_token']}"
            self.session.headers = headers
            headers["Host"] = "api-drive.mypikpak.com"
            print("PikPak 账号登录成功")
            return True

    def download(self, url, path=None):
        magnet_url = url
        if not url.startswith("magnet:?xt="):
            r = requests.get(url)
            with open("tmp.torrent", "wb") as f:
                f.write(r.content)

            url = self.convert_to_magnet("tmp.torrent")
            os.remove("tmp.torrent")

        try:
            self.magnet_upload(url, path)
            print("PikPak 添加成功 Magnet: ", magnet_url)
            return True
        except Exception as e:
            print("PikPak 添加失败 Magnet: ", magnet_url, e)
            return False

    def magnet_upload(self, url, path):
        # 请求离线下载所需数据
        torrent_url = f"{PIKPAK_API_URL}/drive/v1/files"
        torrent_data = {
            "kind": "drive#file",
            "parent_id": path,
            "upload_type": "UPLOAD_TYPE_URL",
            "url": {
                "url": url,
            },
        }
        # 请求离线下载
        torrent_result = self.session.post(
            url=torrent_url, json=torrent_data, timeout=5
        ).json()

        # 处理请求异常
        if "error" in torrent_result:
            if torrent_result["error_code"] == 16:
                print(f"PikPak 账号登录过期，正在重新登录")
                self.login()  # 重新登录该账号
                self.download(url, path)  # 重新下载
                return True
            else:
                # 可以考虑加入删除离线失败任务的逻辑
                print(f"PikPak 账号提交离线下载任务失败，错误信息：{torrent_result['error_description']}")
                return False

        return True

    @staticmethod
    def convert_to_magnet(torrent_file):
        with open(torrent_file, "rb") as source_file:
            metadata = bencode.bdecode(source_file.read())

        hashcontents = bencode.bencode(metadata[b"info"])
        digest = hashlib.sha1(hashcontents).digest()
        b32hash = base64.b32encode(digest)
        params = {
            "dn": metadata[b"info"][b"name"].decode("utf-8"),
            "tr": metadata[b"announce"].decode("utf-8"),
            "xl": metadata[b"info"][b"length"],
        }

        magneturi = "magnet:?xt=urn:btih:{}&{}".format(
            b32hash.decode("utf-8"), urllib.parse.urlencode(params)
        )
        return magneturi
