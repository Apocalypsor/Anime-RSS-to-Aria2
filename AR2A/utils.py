import os

import requests
import yaml

default_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"


def getConfigFile(config_path, rss_path):
    with open(config_path, "r", encoding="UTF-8") as c:
        config = yaml.safe_load(c)

    if rss_path.startswith("http"):
        print("使用RSS配置：{}".format(rss_path.split("/")[-1]))
        headers = {"User-Agent": default_user_agent}
        if os.getenv("AUTHORIZATION_TOKEN"):
            headers["Authorization"] = "token {}".format(
                os.getenv("AUTHORIZATION_TOKEN")
            )

        res = requests.get(rss_path, headers=headers).text
        rss = yaml.safe_load(res)
    else:
        print("使用RSS配置：{}".format(rss_path))
        with open(rss_path, "r", encoding="UTF-8") as c:
            rss = yaml.safe_load(c)

    return config, rss


def escapeText(text):
    escaped_chara = (
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    )

    for e in escaped_chara:
        text = text.replace(e, "\\" + e)

    return text
