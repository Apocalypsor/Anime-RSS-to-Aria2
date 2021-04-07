# -*- coding: UTF-8 -*-

import os

from AR2A.anime import Anime


def main():
    rss_file = "data/rss.yaml"

    config_file = "data/config.yaml"

    ani = Anime(rss_file, config_file)

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
