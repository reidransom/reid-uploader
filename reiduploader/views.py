import os
import hmac
import base64
import time
import json
from hashlib import sha1

from flask import Flask, request, render_template

import helper
from models import db, Upload, Video
from settings import DEBUG, AWS_ACCESS_KEY, AWS_SECRET, BUCKET
from settings import PORT, CHUNK_SIZE, MIME_TYPES

## Boilerplate

app = Flask(__name__)
app.debug = DEBUG

@app.teardown_request
def teardown_db(exception=None):
    db.remove()

## Helper Functions

def _process_string(string):
    ret = base64.b64encode(
        hmac.new(AWS_SECRET.encode('UTF-8'), string.encode(), sha1).digest()
    ).decode()
    try:
        return ret.decode()
    except AttributeError:
        return ret

def _http_date():
    return time.strftime("%a, %d %b %Y %X %Z", time.localtime())

def _action_init(key, date=None):
    date = date or _http_date()
    return _process_string(
        "POST\n\n\n\nx-amz-acl:public-read\nx-amz-date:{}\n/{}/{}?uploads".format(
            date, BUCKET, key)), date

def _action_chunk(key, upload_id, chunk, mime_type, date=None):
    date = date or _http_date()
    return _process_string(
        "PUT\n\n{}\n\nx-amz-date:{}\n/{}/{}?partNumber={}&uploadId={}".format(
            mime_type, date, BUCKET, key, chunk, upload_id)), date

def _action_list(key, upload_id, date=None):
    date = date or _http_date()
    return _process_string(
        "GET\n\n\n\nx-amz-date:{}\n/{}/{}?uploadId={}".format(
            date, BUCKET, key, upload_id)), date

def _action_end(key, upload_id, mime_type, date=None):
    date = date or _http_date()
    return _process_string(
        "POST\n\n{}\n\nx-amz-date:{}\n/{}/{}?uploadId={}".format(
        mime_type, date, BUCKET, key, upload_id)), date


def _action_delete(key, upload_id, date=None):
    date = date or _http_date()
    return _process_string("DELETE\n\n\n\nx-amz-date:{}\n/{}/{}?uploadId={}".format(
                           date, BUCKET, key, upload_id)), date

def start_worker(key):
    # start up the worker process
    import subprocess
    worker = os.path.join(os.path.dirname(__file__), 'worker.py')
    subprocess.Popen([worker, key]).pid

## URLs

@app.route("/upload-backend/<action>/")
def upload_action(action):
    key = request.args.get('key')
    upload_id = request.args.get('upload_id')
    chunk = request.args.get('chunk')
    string = date = None
    mime_type = helper.get_mimetype(key)

    if action == 'chunk_loaded':
        filename = request.args['filename']
        filesize = request.args['filesize']
        last_modified = request.args['last_modified']
        chunk = int(request.args['chunk'])

        if int(filesize) > CHUNK_SIZE:
            try:
                u = db.query(Upload).filter(
                    Upload.filename == filename,
                    Upload.filesize == filesize,
                    Upload.last_modified == last_modified
                ).first()
                assert u

                chunks = set(map(int, u.chunks_uploaded.split(',')))
                chunks.add(chunk)
                u.chunks_uploaded = ','.join(map(str, chunks))
                db.commit()

            except AssertionError:
                u = Upload(
                    filename=filename,
                    filesize=filesize,
                    last_modified=last_modified,
                    chunks_uploaded=str(chunk),
                    key=key,
                    upload_id=upload_id,
                )
                db.add(u)
                db.commit()

        return ''

    if action == 'get_all_signatures':
        date = _http_date()
        list_signature, _ = _action_list(key, upload_id, date)
        end_signature, _ = _action_end(key, upload_id, mime_type, date)
        delete_signature, _ = _action_delete(key, upload_id, date)
        num_chunks = int(request.args['num_chunks'])
        chunk_signatures = dict([(chunk, (_action_chunk(key, upload_id, chunk, mime_type, date)))
                                for chunk in range(1, num_chunks + 1)])

        return json.dumps({
            'list_signature': [list_signature, date],
            'end_signature': [end_signature, date],
            'chunk_signatures': chunk_signatures,
        })

    if action == 'get_init_signature':
        filename = request.args['filename']
        filesize = request.args['filesize']
        last_modified = request.args['last_modified']

        try:
            assert 'force' not in request.args
            u = db.query(Upload).filter(
                Upload.filename == filename,
                Upload.filesize == filesize,
                Upload.last_modified == last_modified
            ).first()
            assert u

            string, date = _action_init(u.key)
            return json.dumps({
                "signature": string,
                "date": date,
                "key": u.key,
                "upload_id": u.upload_id,
                "chunks": map(int, u.chunks_uploaded.split(','))
            })
        except AssertionError:
            db.query(Upload).filter(
                Upload.filename == filename,
                Upload.filesize == filesize,
                Upload.last_modified == last_modified
            ).delete()
            db.commit()

        string, date = _action_init(key)

    elif action == 'get_chunk_signature':
        string, date = _action_chunk(key, upload_id, chunk, mime_type)

    elif action == 'get_list_signature':
        string, date = _action_list(key, upload_id)

    elif action == 'get_end_signature':
        string, date = _action_end(key, upload_id, mime_type)

    elif action == 'get_delete_signature':
        string, date = _action_delete(key, upload_id)

    elif action == 'upload_finished':
        start_worker(key)

    return json.dumps({
        'signature': string,
        'date': date,
    })

## Static files (debugging only)

from sqlalchemy import desc

PER_PAGE = 100

@app.route("/", defaults={'page': 1})
@app.route("/page/<int:page>")
def index(page):
    count = db.query(Video).count()
    start = (page-1) * PER_PAGE
    num_pages = int(((count-1) / PER_PAGE) + 1)

    prev_url = None
    if page > 1:
        prev_url = '/page/{}'.format(page-1)
    next_url = None
    if count > start + PER_PAGE:
        next_url = '/page/{}'.format(page+1)

    videos = db.query(Video).order_by(desc(Video.id))
    if page > 1:
        videos = videos.offset(start)
    videos = videos.limit(PER_PAGE)
    vid_urls = []
    for vid in videos:
        vid_urls.append(helper.get_s3url(vid.key))
    return render_template(
        'index.html',
        aws_access_key=AWS_ACCESS_KEY,
        bucket=BUCKET,
        accepted_extensions=','.join(MIME_TYPES.keys()),
        mime_types=json.dumps(MIME_TYPES),
        videos=videos,
        vid_urls=vid_urls,
        prev_url=prev_url,
        next_url=next_url,
        page=page,
        num_pages=num_pages,
        page_list=range(1, num_pages+1),
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
