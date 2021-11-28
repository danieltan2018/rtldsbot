from __future__ import print_function
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from secret import gsheet, lotydb, lifedb

Base = declarative_base()


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    details = Column(String, nullable=True)

    def __init__(self, id, name, details):
        self.id = id
        self.name = name
        self.details = details


class Bucket(Base):
    __tablename__ = 'buckets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)

    def __init__(self, id, url):
        self.id = id
        self.url = url


class MediaType(Base):
    __tablename__ = 'media_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    def __init__(self, id, name):
        self.id = id
        self.name = name


class EventType(Base):
    __tablename__ = 'event_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    def __init__(self, id, name):
        self.id = id
        self.name = name


class EventGroup(Base):
    __tablename__ = 'event_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    location = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    thumbnail_url = Column(String, default=None)
    event_type_id = Column(Integer, nullable=False)
    details = Column(String, default=None)

    def __init__(self, id, name, location, start_date, end_date, thumbnail_url, event_type_id, details):
        self.id = id
        self.name = name
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.thumbnail_url = thumbnail_url
        self.event_type_id = event_type_id
        self.details = details


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(String)
    event_group_id = Column(Integer, nullable=False)
    thumbnail_url = Column(String, default=None)

    def __init__(self, id, name, date, event_group_id, thumbnail_url):
        self.id = id
        self.name = name
        self.date = date
        self.event_group_id = event_group_id
        self.thumbnail_url = thumbnail_url


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(String)
    category_id = Column(Integer, nullable=False)
    author_id = Column(Integer)
    scripture_reference = Column(String, default=None)
    details = Column(String, default=None)

    def __init__(self, id, name, date, category_id, author_id, scripture_reference, details):
        self.id = id
        self.name = name
        self.date = date
        self.category_id = category_id
        self.author_id = author_id
        self.scripture_reference = scripture_reference
        self.details = details


class MediaEntry(Base):
    __tablename__ = 'media_entries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, default=None)
    thumbnail_url = Column(String, default=None)
    original_filename = Column(String, nullable=False)
    encrypted_filename = Column(String, nullable=False)
    date = Column(String)
    event_id = Column(Integer, nullable=False)
    bucket_id = Column(Integer, nullable=False)
    details = Column(String, default=None)
    media_type_id = Column(Integer, nullable=False)
    author_id = Column(Integer)
    index = Column(Integer)
    downloadable = Column(Boolean, nullable=False)

    def __init__(self, id, title, thumbnail_url, original_filename, encrypted_filename, date, event_id, bucket_id, details, media_type_id, author_id, index, downloadable):
        self.id = id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.original_filename = original_filename
        self.encrypted_filename = encrypted_filename
        self.date = date
        self.event_id = event_id
        self.bucket_id = bucket_id
        self.details = details
        self.media_type_id = media_type_id
        self.author_id = author_id
        self.index = index
        self.downloadable = downloadable


def sync(server):
    if server == 'lotydb':
        dbauth = lotydb
    elif server == 'lifedb':
        dbauth = lifedb
    else:
        raise ValueError
    engine = create_engine(dbauth)
    Session = sessionmaker(bind=engine)
    session = Session()
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SPREADSHEET_ID = gsheet

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='authors!A2:F').execute()
    values = result.get('values', [])
    for row in values:
        data = {"id": row[0], "name": row[4], "details": None}
        session.merge(Author(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='buckets!A2:E').execute()
    values = result.get('values', [])
    for row in values:
        data = {"id": row[0], "url": row[4]}
        session.merge(Bucket(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='media_types!A2:E').execute()
    values = result.get('values', [])
    for row in values:
        data = {"id": row[0], "name": row[4]}
        session.merge(MediaType(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='event_types!A2:E').execute()
    values = result.get('values', [])
    for row in values:
        data = {"id": row[0], "name": row[4]}
        session.merge(EventType(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='event_groups!A2:K').execute()
    values = result.get('values', [])
    for row in values:
        data = {"id": row[0], "name": row[4], "location": row[5], "start_date": row[6],
                "end_date": row[7], "thumbnail_url": row[8], "event_type_id": row[9], "details": None}
        session.merge(EventGroup(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='categories!A2:H').execute()
    values = result.get('values', [])
    for row in values:
        thumbnail_url = None
        if len(row) > 7:
            thumbnail_url = row[7]
        data = {"id": row[0], "name": row[4], "date": row[5] or None,
                "event_group_id": row[6], "thumbnail_url": thumbnail_url}
        session.merge(Category(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='events!A2:J').execute()
    values = result.get('values', [])
    for row in values:
        details = None
        scripture_reference = None
        author_id = None
        if len(row) > 9:
            details = row[9] or None
        if len(row) > 8:
            scripture_reference = row[8] or None
        if len(row) > 7:
            author_id = row[7] or None
        data = {"id": row[0], "name": row[4], "date": row[5] or None, "category_id": row[6],
                "author_id": author_id, "scripture_reference": scripture_reference, "details": details}
        session.merge(Event(**data))
    session.commit()

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range='media_entries!A2:P').execute()
    values = result.get('values', [])
    for row in values:
        if row[15] == 't':
            download = True
        else:
            download = False
        data = {"id": row[0], "title": row[4], "thumbnail_url": row[5], "original_filename": row[6], "encrypted_filename": row[7], "date": row[8] or None, "event_id": row[9],
                "bucket_id": row[10], "details": row[11], "media_type_id": row[12], "author_id": row[13] or None, "index": row[14] or None, "downloadable": download}
        session.merge(MediaEntry(**data))
    session.commit()
