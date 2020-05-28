# -*- coding: UTF-8 -*-

import os
import re
import time

import feedparser
import yaml
import requests
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

        if os.path.exists(self.rssFile):
            with open(self.rssFile, 'r', encoding='UTF-8') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                self.rss = config['Anime']
        else:
            print('No RSS file!')
            exit()

        if not os.path.exists(self.dataFile):
            open(self.dataFile, 'w').close()

        database = 'sqlite:///' + self.dataFile
        engine = create_engine(database)
        Base.metadata.create_all(engine)
        self.DBSession = sessionmaker(bind=engine)

    def readRSS(self, send = 'default'):
        if not send == 'default':
            self.send = send

        for s in self.rss:
            if s['source'].lower() == 'mikan':
                self.readMikan(s)
            elif s['source'].lower() == 'rarbg':
                self.readRarbg(s)

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

    def readRarbg(self, a):
        entries = feedparser.parse(a['url'])['entries']
        regex = re.compile(a['regex'])
        session = self.DBSession()

        for r in entries:
            if regex.match(r['title']) and not session.query(exists().where(Downloaded.title == r['title'])).scalar():
                if self.send2Aria2(a['path'], r['link']):
                    self.addDownload(session, a['series'], r['title'], r['link'])
                    session.close()

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
                    rs = self.aria2.add_magnet(url, options={'dir': path})
                except:
                    print('添加失败 Magnet: ', url)
                    print(rs)
                    return False
                else:
                    print('添加成功 Magnet: ', url)
                    return True

            else:
                r = requests.get(url)
                with open('tmp.torrent', 'wb') as f:
                    f.write(r.content)

                try:
                    rs = self.aria2.add_torrent('tmp.torrent', options={'dir': path})
                except:
                    print('添加失败 Torrent: ', url)
                    print(rs)
                    os.remove('tmp.torrent')
                    return False
                else:
                    print('添加成功 Torrent: ', url)
                    os.remove('tmp.torrent')
                    return True
