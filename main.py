# -*- coding: UTF-8 -*-

import os

from AR2A.anime import Anime


def main():
    if os.getenv("RSS_FILE"):
        rss_file = "data/" + os.getenv("RSS_FILE")
    else:
        rss_file = "data/rss.yaml"

    if os.getenv("CONF_FILE"):
        config_file = "data/" + os.getenv("CONF_FILE")
    else:
        config_file = "data/config.yaml"

    ani = Anime(rss_file, config_file)

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
