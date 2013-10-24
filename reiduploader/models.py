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
    filename = Column(String(256))
    filesize = Column(String(64))
    last_modified = Column(String(64))

    upload_start = Column(DateTime)
    last_information = Column(DateTime)

    key = Column(String(256))
    upload_id = Column(String(128))
    chunks_uploaded = Column(Text)

Upload.metadata.create_all(bind=engine)

# class Transcode(Base):
# 	__tablename__ = 'transcode'
# 	id
# 	filename # s3 key
# 	last_modified
# 	state = pending|transcode|upload|done
# 	percent

