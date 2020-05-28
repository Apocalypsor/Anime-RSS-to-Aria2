# -*- coding: UTF-8 -*-

import os
import re
import time

import feedparser
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

    def __init__(self, rssFile, dataFile):
        self.rssFile = rssFile
        self.dataFile = dataFile

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

        self.urls = {}

    def readRSS(self):
        for s in self.rss:
            self.urls[s['path']] = []

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
                        self.urls[a['path']].append(l['href'])
                        self.addDownload(session, a['series'], r['title'], l['href'])
                        session.close()

    def readRarbg(self, a):
        entries = feedparser.parse(a['url'])['entries']
        regex = re.compile(a['regex'])
        session = self.DBSession()

        for r in entries:
            if regex.match(r['title']) and not session.query(exists().where(Downloaded.title == r['title'])).scalar():
                self.urls[a['path']].append(r['link'])
                self.addDownload(session, a['series'], r['title'], r['link'])
                session.close()

    def addDownload(self, session, anime, title, link):
        ticks = time.time()
        new_ep = Downloaded(anime=anime, title=title, link=link, create_time=str(ticks))
        session.add(new_ep)
        session.commit()
