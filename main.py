# -*- coding: UTF-8 -*-

import os

from AR2A.anime import Anime


def main():
    rssFile = "data/rss.yaml"

    ani = Anime(rssFile)

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
