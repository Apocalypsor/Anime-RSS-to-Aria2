# -*- coding: UTF-8 -*-

import os

from AR2A.anime import Anime


def main():
    if env["RSS_FILE"]:
        rss_file = "data/" + env["RSS_FILE"]
    else:
        rss_file = "data/rss.yaml"
    
    if env["CONF_FILE"]:
        config_file = "data/" + env["CONF_FILE"]
    else:
        config_file = "data/config.yaml"

    ani = Anime(rss_file, config_file)

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
