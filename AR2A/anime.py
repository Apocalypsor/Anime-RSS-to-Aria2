# -*- coding: UTF-8 -*-

import os
import re
import sys
import time

import feedparser
import requests
import yaml
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists

Base = declarative_base()


class Downloaded(Base):
    __tablename__ = 'download'

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime = Column(String(2048))
    title = Column(String(2048))
    link = Column(String(2048))
    create_time = Column(String(10))

    def __repr__(self):
        return '<Download %r>' % self.title


class Anime():

    def __init__(self, rssFile, dataFile, aria2 = None):
        self.rssFile = rssFile
        self.dataFile = dataFile
        self.aria2 = aria2

        if self.aria2 == None:
            self.send = False
        else:
            self.send = True

        with open(self.rssFile, 'r', encoding='UTF-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            if config['Anime']:
                self.rss = config['Anime']
            else:
                sys.exit('Nothing Subscribed!')
                
            if config['telegrambot']['enable']:
                self.telegram = config['telegrambot']

                if not self.telegram['token']:
                    sys.exit('No Telegram Bot Token!')
                elif not self.telegram['chat_id']:
                    sys.exit('No Telegram Chat ID!')

            elif os.getenv('TELEGRAM_ENABLE') == 'true':
                if not os.getenv('TELEGRAM_TOKEN'):
                    sys.exit('No Telegram Bot Token!')
                elif not os.getenv('TELEGRAM_CHAT_ID'):
                    sys.exit('No Telegram Chat ID!')
                else:
                    self.telegram['token'] = os.getenv('TELEGRAM_TOKEN')
                    self.telegram['chat_id'] = os.getenv('TELEGRAM_CHAT_ID')

            else:
                self.telegram = None

            if config['base_url']:
                self.url = config['base_url']
            else:
                self.url = None

        if not os.path.exists(self.dataFile):
            open(self.dataFile, 'w').close()

        database = 'sqlite:///' + self.dataFile
        engine = create_engine(database)
        Base.metadata.create_all(engine)
        self.DBSession = sessionmaker(bind=engine)

    def readRSS(self, send=None):
        if send != None:
            self.send = send

        for s in self.rss:
            if s['source'].lower() == 'mikan':
                self.readMikan(s)
            elif s['source'].lower() == 'rarbg':
                self.readRarbg(s)

    # RSS来源: https://mikanani.me/
    def readMikan(self, a):
        entries = feedparser.parse(a['url'])['entries']
        regex = re.compile(a['regex'])
        session = self.DBSession()

        for r in entries:
            if regex.match(r['title']) and not session.query(exists().where(Downloaded.title == r['title'])).scalar():
                for l in r['links']:
                    if l['type'] == 'application/x-bittorrent':
                        if self.send2Aria2(a['path'], l['href']):
                            self.addDownload(session, a['series'], r['title'], l['href'])
                            session.close()

                            self.send2Telegram(r['title'], a['type'], a['series'])

    # 需配合 https://rssbg.now.sh 食用
    def readRarbg(self, a):
        entries = feedparser.parse(a['url'], request_headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'})['entries']
        regex = re.compile(a['regex'])
        session = self.DBSession()

        for r in entries:
            try:
                r['title'] = regex.match(r['title']).group(1)
                if not session.query(exists().where(Downloaded.title == r['title'])).scalar():
                    if self.send2Aria2(a['path'], r['link']):
                        self.addDownload(session, a['series'], r['title'], r['link'])
                        session.close()

                        self.send2Telegram(r['title'], a['type'], a['series'])
            except:
                pass

    def addDownload(self, session, anime, title, link):
        ticks = time.time()
        new_ep = Downloaded(anime=anime, title=title, link=link, create_time=str(ticks))
        session.add(new_ep)
        session.commit()

    def send2Aria2(self, path, url):
        if not self.send:
            print('未添加Aria2客户端或仅作为测试！链接为: ', url)
            return False

        else:
            if 'magnet:?xt=' in url:
                try:
                    self.aria2.add_magnet(url, options={'dir': path})
                except Exception as e:
                    print('添加失败 Magnet: ', url, '\n', e)
                    return False
                else:
                    print('添加成功 Magnet: ', url)
                    return True

            else:
                r = requests.get(url)
                with open('tmp.torrent', 'wb') as f:
                    f.write(r.content)

                try:
                    self.aria2.add_torrent('tmp.torrent', options={'dir': path})
                except Exception as e:
                    print('添加失败 Torrent: ', url, '\n', e)
                    return False
                else:
                    print('添加成功 Torrent: ', url)
                    return True
                finally:
                    os.remove('tmp.torrent')

    def send2Telegram(self, title, type, series):
        if self.url:
            msg = '🌟 更新剧集：*' + title + '*\n\n' + '💡 直达链接：' + self.url + series + '/' + '\n\n#' + type + ' #' + series
        else:
            msg = '🌟 更新剧集：*' + title + '*\n#' + type + ' #' + series

        url = 'https://api.telegram.org/bot' + self.telegram['token'] + '/sendMessage'
        payload = {
            'chat_id': self.telegram['chat_id'],
            'text': msg,
            'parse_mode': 'markdown',
            'disable_web_page_preview': 'true'
        }

        r = requests.post(url, data=payload)

        if r.json()['ok']:
            print(title + ' 已成功发送到Telegram!')
