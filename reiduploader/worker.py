#!/usr/bin/env python2.7

import sys
import os
import subprocess
import re
from urlparse import urlparse
import shlex

from boto.s3.key import Key

import helper
from models import db, Video
from settings import FFMPEG, TMPDIR, FFMPEG_PRESETS

import logging
from logging.handlers import RotatingFileHandler
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(RotatingFileHandler(os.path.join(TMPDIR, 'reiduploader.worker.log'), maxBytes=30*1024, backupCount=10))

def usage():
    return 'transcode.py <s3_key>'

def get_ffmpeg_input_data(data):
    return re.search(
        'Input #0(.+)Output #0',
        data,
        re.MULTILINE|re.DOTALL).group(1)

def parse_ffmpeg_data(data):
    video = {}
    try:
        video_data = re.search('Video:.*', data, re.MULTILINE).group(0)
    except AttributeError:
        video_data = ''
    try:
        audio_data = re.search('Audio:.*', data, re.MULTILINE).group(0)
    except AttributeError:
        audio_data = ''
    try:
        video['audio_bitrate'] = int(re.search(' (\d+) kb/s', audio_data).group(1))
    except AttributeError:
        video['audio_bitrate'] = 0
    try:
        video['video_bitrate'] = int(re.search(' (\d+) kb/s', video_data).group(1))
    except AttributeError:
        video['video_bitrate'] = 0
    try:
        video['framerate'] = int(float(re.search(' ([\d\.]+) fps', video_data).group(1))*1000)
    except AttributeError:
        video['framerate'] = 0
    try:
        video['width'], video['height'] = map(int, re.search(', (\d+)x(\d+)', video_data).groups())
    except AttributeError:
        video['width'] = 0
        video['height'] = 0

    # taken from ffmpeg/libavutil/channel_layout.c
    channel_layout_map = {
        "mono":        1,
        "stereo":      2,
        "2.1":         3,
        "3.0":         3,
        "3.0(back)":   3,
        "4.0":         4,
        "quad":        4,
        "quad(side)":  4,
        "3.1":         4,
        "5.0":         5,
        "5.0(side)":   5,
        "4.1":         5,
        "5.1":         6,
        "5.1(side)":   6,
        "6.0":         6,
        "6.0(front)":  6,
        "hexagonal":   6,
        "6.1":         7,
        "6.1(front)":  7,
        "7.0":         7,
        "7.0(front)":  7,
        "7.1":         8,
        "7.1(wide)":   8,
        "7.1(wide-side)": 8,
        "octagonal":   8,
        "downmix":     2,
    }
    try:
        video['num_audio_channels'] = channel_layout_map[
            re.search(', (%s),' % '|'.join(channel_layout_map.keys()), audio_data).group(1)
        ]
    except AttributeError:
        video['num_audio_channels'] = 0

    try:
        hours, minutes, seconds, decimal = map(int, re.search(
            'Duration: (\d\d)\:(\d\d)\:(\d\d)\.(\d\d)',
            data,
            re.MULTILINE).groups())
        video['duration'] = (hours*3600 + minutes*60 + seconds)*100 + decimal
    except AttributeError:
        video['duration'] = 0
    return video

def get_video_attrs(path, ffmpeg_data=None):
    if not ffmpeg_data:
        cmd = [FFMPEG, '-i', path]
        try:
            ffmpeg_data = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            ffmpeg_data = e.output
    attrs = parse_ffmpeg_data(ffmpeg_data)
    attrs['key'] = os.path.basename(path)
    attrs['filesize'] = os.stat(path).st_size
    return attrs

def download_url(url):
    output_path = os.path.join(TMPDIR, os.path.basename(urlparse(url).path))
    cmd = ['curl', '-s', '-o', output_path, url]
    subprocess.call(cmd)
    return output_path

def make_iphone(input_path, output_path=None, preset=None):
    if not preset:
        preset = FFMPEG_PRESETS.keys()[0]
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + preset
    cmd = [FFMPEG, '-i', input_path] + shlex.split(FFMPEG_PRESETS[preset]) + ['-y', output_path]
    data = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return output_path, data

# def url_to_iphone_video(url, output_dir=TMPDIR):
#     log.debug('url_to_iphone_video')
#     basename = os.path.basename(urlparse(url).path)
#     output_path = os.path.join(output_dir, os.path.splitext(basename)[0] + '-iphone.mp4')
#     cmd = 'curl %s | %s -f mov -i - -vcodec libx264 -acodec libfaac -ab 128k -ar 48k -aspect 16:9 -vf yadif,scale=960x540 -x264opts cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced_threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b_bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_lookahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500:crf_max=0.0:nal_hrd=none -movflags faststart -y %s' % (url, FFMPEG, output_path)
#     data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

#     # Create a db entry for the original video
#     data = parse_ffmpeg_data(get_ffmpeg_input_data(data))
#     data['key'] = basename
#     data['filesize'] = helper.get_bucket().get_key(basename).size
#     video = Video(**data)
#     db.add(video)
#     db.commit()

#     return output_path

def upload_to_s3(local_path, key=None):
    if key is None:
        key = os.path.basename(local_path)
    bucket = helper.get_bucket()
    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(local_path)
    k.set_canned_acl('public-read')
    k.set_metadata('Content-Type', helper.get_mimetype(k.key))
    return k

def _process_fullcopy(key):

    # Set the content-type correctly
    bucket = helper.get_bucket()
    k = bucket.lookup(key)
    k.copy(k.bucket, k.name, preserve_acl=True, metadata={'Content-Type': helper.get_mimetype(k.name)})

    orig_video = Video(key=key, status='downloading')
    db.add(orig_video)
    db.commit()
    url = helper.get_s3url(key)
    orig_path = download_url(url)

    orig_video.update(get_video_attrs(orig_path))
    orig_video.status = 'done'

    for preset in FFMPEG_PRESETS.iterkeys():

        # Transcode/Upload based on ffmpeg preset
        iphone_path = os.path.splitext(orig_path)[0] + preset
        iphone_video = Video(key=os.path.basename(iphone_path), status='transcoding')
        db.add(iphone_video)
        db.commit()

        try:
            make_iphone(orig_path, iphone_path, preset)
            iphone_video.update(get_video_attrs(iphone_path))
        except:
            iphone_video.status = 'transcoding error'
        else:
            iphone_video.status = 'uploading'

        db.commit()

        if iphone_video.status = 'uploading':
            upload_to_s3(iphone_path)
            iphone_video.status = 'done'
            db.commit()
            os.remove(iphone_path)

    os.remove(orig_path)

def process_s3_key(key):

    _process_fullcopy(key)

    # This is a more streamlined workflow which involved piping curl output to ffmpeg.
    # It's a little more complex and doesn't work at all for prores codec.
    #
    # log.debug('process_s3_key')
    # url = helper.get_s3url(key)
    # iphone_path = url_to_iphone_video(url)
    # upload_to_s3(iphone_path)
    # # Create a db entry for the iphone video
    # cmd = '%s -i %s' % (FFMPEG, iphone_path)
    # try:
    #     data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    # except subprocess.CalledProcessError, e:
    #     data = e.output
    # data = parse_ffmpeg_data(data)
    # data['key'] = os.path.basename(iphone_path)
    # data['filesize'] = helper.get_bucket().get_key(data['key']).size
    # video = Video(**data)
    # db.add(video)
    # db.commit()
    # os.remove(iphone_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(usage())
        sys.exit(1)
    process_s3_key(sys.argv[1])
