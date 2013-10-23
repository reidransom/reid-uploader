# models.py

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

class Transcode(Base):
	__tablename__ = 'transcode'
	id
	filename # s3 key
	last_modified
	state = pending|transcode|upload|done
	percent

