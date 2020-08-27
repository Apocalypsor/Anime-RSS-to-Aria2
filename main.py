# -*- coding: UTF-8 -*-

import os

import aria2p
import yaml

from AR2A.anime import Anime


def createAria2(configFile):
    if os.path.exists(configFile):
        with open(configFile, 'r', encoding='UTF-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            conf = config['aria2']

    else:
        sys.exit('No configuration!')

    if conf['host'] and conf['port'] and conf['secret']:
        a_host = conf['host']
        a_port = conf['port']
        a_secret = conf['secret']

    elif os.getenv('ARIA2_HOST') and os.getenv('ARIA2_PORT') and os.getenv('ARIA2_SECRET'):
        a_host = os.getenv('ARIA2_HOST')
        a_port = os.getenv('ARIA2_PORT')
        a_secret = os.getenv('ARIA2_SECRET')

    else:
        print('Error Aria2 configuration! Use local Aria2 client.')
        a_host = '127.0.0.1'
        a_port = 6800
        a_secret = ''

    aria2 = aria2p.API(
        aria2p.Client(
            host=a_host,
            port=a_port,
            secret=a_secret
        )
    )

    return aria2


def main():
    rssFile = 'rss.yaml'
    dataFile = 'data.sqlite'

    aria2 = createAria2(rssFile)

    ani = Anime(rssFile, dataFile, aria2)

    ani.readRSS(send=True)


if __name__ == "__main__":
    main()
