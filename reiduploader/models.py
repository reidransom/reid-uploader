# models.py

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy import String, DateTime, Text, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import ENGINE

## The Upload DB Model
engine = create_engine(ENGINE, convert_unicode=True)
db = scoped_session(sessionmaker(
    autocommit=False, autoflush=True, bind=engine))

Base = declarative_base()
Base.query = db.query_property()
metadata = MetaData()

class Upload(Base):
    __tablename__ = 'upload'
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    filesize = Column(String)
    last_modified = Column(String)
    upload_start = Column(DateTime)
    last_information = Column(DateTime)
    key = Column(String)
    upload_id = Column(String)
    chunks_uploaded = Column(Text)

Upload.metadata.create_all(bind=engine)

class Video(Base):
    __tablename__ = 'video'
    id = Column(Integer, primary_key=True)
    key = Column(String)
    framerate = Column(Integer)            # framerate = fps * 1000
    width = Column(Integer)
    height = Column(Integer)
    num_audio_channels = Column(Integer)   # ex: 2 for stereo, 6 for 5.1 surround
    duration = Column(Integer)             # duration = total_seconds * 100
    video_bitrate = Column(Integer)        # kilobits per second
    audio_bitrate = Column(Integer)        # kilobits per second
    filesize = Column(Integer)             # bytes
    added = Column(DateTime)

    status = Column(String)

    def total_seconds(self):
        if not self.duration is None:
            return float(self.duration) / 100
        return None

    def total_bitrate(self):
        total_seconds = self.total_seconds()
        try:
            if not self.filesize is None and not total_seconds is None:
                return int((float(self.filesize)*8/1024)/total_seconds)  # kilobits per second
        except:
            return None
        return None

    def fps(self):
        if not self.framerate is None:
            return float(self.framerate) / 1000
        return None

    def update(self, attrs):
        # update attributes from dict
        for key, value in attrs.items():
            setattr(self, key, value)

Video.metadata.create_all(bind=engine)

metadata.create_all(bind=engine)

# class Transcode(Base):
# 	__tablename__ = 'transcode'
# 	id
# 	filename # s3 key
# 	last_modified
# 	state = pending|transcode|upload|done
# 	percent

