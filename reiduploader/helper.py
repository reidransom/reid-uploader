import os

from settings import BUCKET, AWS_ACCESS_KEY, AWS_SECRET, MIME_TYPES

def get_bucket():
    from boto.s3.connection import S3Connection
    conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET)
    return conn.create_bucket(BUCKET)

def get_s3url(key):
    return 'https://%s.s3.amazonaws.com/%s' % (BUCKET, key)

def get_mimetype(filename):
    try:
        return MIME_TYPES[os.path.splitext(filename)[1][1:]]
    except KeyError:
        return 'application/octet-stream'
