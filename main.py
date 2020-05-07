import os

import aria2p
import requests
import yaml

from AR2A.anime import Anime


def createAria2(configFile):
    if os.path.exists(configFile):
        with open(configFile, 'r', encoding='UTF-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            conf = config['aria2']

    else:
        print('No configuration!')

    if conf['host'] and conf['port'] and conf['secret']:
        a_host = conf['host']
        a_port = conf['port']
        a_secret = conf['secret']

    elif os.getenv('ARIA2_HOST') and os.getenv('ARIA2_PORT') and os.getenv('ARIA2_SECRET'):
        a_host = os.getenv('ARIA2_HOST')
        a_port = os.getenv('ARIA2_PORT')
        a_secret = os.getenv('ARIA2_SECRET')

    else:
        print('Error Aria2 configuration!')
        exit()

    aria2 = aria2p.API(
        aria2p.Client(
            host=a_host,
            port=a_port,
            secret=a_secret
        )
    )

    return aria2


def send2Aria2(urls, aria2):
    for path in urls.keys():
        for url in urls[path]:
            r = requests.get(url)
            with open('tmp.torrent', 'wb') as f:
                f.write(r.content)
            try:
                aria2.add_torrent('tmp.torrent', options={'dir': path})
            except:
                print('添加失败 Torrent: ', url)
                os.remove('tmp.torrent')
            else:
                print('添加成功 Torrent: ', url)
                os.remove('tmp.torrent')


def main():
    rssFile = 'rss.yaml'
    dataFile = 'data.sqlite'

    aria2 = createAria2(rssFile)

    ani = Anime(rssFile, dataFile)

    ani.readRSS()

    send2Aria2(ani.urls, aria2)


if __name__ == "__main__":
    main()
