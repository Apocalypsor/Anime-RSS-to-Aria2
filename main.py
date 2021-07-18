# -*- coding: UTF-8 -*-

import os

from AR2A.anime import Anime
from AR2A.utils import getConfigFile


def main():
    if os.getenv("RSS_CONFIG"):
        rss_path = os.getenv("RSS_CONFIG")
        if not rss_path.startswith("http"):
            rss_path = "data/" + rss_path
    else:
        rss_path = "data/rss.yaml"

    config_path = "data/config.yaml"

    ani = Anime(*getConfigFile(config_path, rss_path))

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
