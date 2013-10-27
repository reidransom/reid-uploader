#!/usr/bin/env python2.7

import sys
import os
import subprocess
import re
from urlparse import urlparse

from boto.s3.key import Key

import helper
from models import db, Video
from settings import FFMPEG, TMPDIR

# todo: this file should define a Video child class VideoWorker or something

import logging
from logging.handlers import RotatingFileHandler
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(RotatingFileHandler(os.path.join(TMPDIR, 'reiduploader.worker.log'), maxBytes=30*1024, backupCount=10))

_ffmpeg_iphone_preset = '-vcodec libx264 -acodec libfaac -ab 128k -ar 48k -aspect 16:9 -vf yadif,scale=960x540 -x264opts cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced_threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b_bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_lookahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500:crf_max=0.0:nal_hrd=none -movflags faststart'

def usage():
    return 'transcode.py <s3_key>'

def get_ffmpeg_input_data(data):
    return re.search(
        'Input #0(.+)Output #0',
        data,
        re.MULTILINE|re.DOTALL).group(1)

def parse_ffmpeg_data(data):
    log.debug('parse_ffmpeg_data')
    video = {}
    video_data = re.search('Video:.*', data, re.MULTILINE).group(0)
    audio_data = re.search('Audio:.*', data, re.MULTILINE).group(0)
    video['audio_bitrate'] = int(re.search(' (\d+) kb/s', audio_data).group(1))
    video['video_bitrate'] = int(re.search(' (\d+) kb/s', video_data).group(1))
    video['framerate'] = int(float(re.search(' ([\d\.]+) fps', video_data).group(1))*1000)
    video['width'], video['height'] = map(int, re.search(', (\d+)x(\d+)', video_data).groups())

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
    video['num_audio_channels'] = channel_layout_map[
        re.search(', (%s),' % '|'.join(channel_layout_map.keys()), audio_data).group(1)
    ]

    hours, minutes, seconds, decimal = map(int, re.search(
        'Duration: (\d\d)\:(\d\d)\:(\d\d)\.(\d\d)',
        data,
        re.MULTILINE).groups())
    # video['duration'] = ((hours*3600 + minutes*60 + seconds)*video['framerate']) + \
    #                     ((decimal*video['framerate'])/100)
    video['duration'] = (hours*3600 + minutes*60 + seconds)*100 + decimal
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

def download_url(url, output_dir=TMPDIR, output_basename=None):
    if not output_basename:
        output_basename = os.path.basename(urlparse(url).path)
    output_path = os.path.join(output_dir, output_basename)
    cmd = ['curl', '-s', '-o', output_path, url]
    subprocess.call(cmd)
    return output_path

def make_iphone(input_path, output_dir=None, output_basename=None):
    if not output_basename:
        output_basename = os.path.splitext(os.path.basename(input_path))[0] + '-iphone.mp4'
    if not output_dir:
        output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, output_basename)
    cmd = '%s -i %s %s -y %s' % \
        (FFMPEG, input_path, _ffmpeg_iphone_preset, output_path)
    # todo: call this w/o shell=True
    data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    return output_path, data

def url_to_iphone_video(url, output_dir=TMPDIR):
    log.debug('url_to_iphone_video')
    basename = os.path.basename(urlparse(url).path)
    output_path = os.path.join(output_dir, os.path.splitext(basename)[0] + '-iphone.mp4')
    cmd = 'curl %s | %s -f mov -i - -vcodec libx264 -acodec libfaac -ab 128k -ar 48k -aspect 16:9 -vf yadif,scale=960x540 -x264opts cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced_threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b_bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_lookahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500:crf_max=0.0:nal_hrd=none -movflags faststart -y %s' % (url, FFMPEG, output_path)
    data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

    # Create a db entry for the original video
    data = parse_ffmpeg_data(get_ffmpeg_input_data(data))
    data['key'] = basename
    data['filesize'] = helper.get_bucket().get_key(basename).size
    video = Video(**data)
    db.add(video)
    db.commit()

    return output_path

def upload_to_s3(local_path, key=None):
    if key is None:
        key = os.path.basename(local_path)
    bucket = helper.get_bucket()
    k = Key(bucket)
    k.key = key
    k.set_contents_from_filename(local_path)
    k.set_canned_acl('public-read')
    return k

def _process_fullcopy(key):
    url = helper.get_s3url(key)
    orig_path = download_url(url)
    iphone_path, ffmpeg_data = make_iphone(orig_path)
    orig_attrs = get_video_attrs(orig_path, get_ffmpeg_input_data(ffmpeg_data))
    db.add(Video(**orig_attrs))
    upload_to_s3(iphone_path)
    iphone_attrs = get_video_attrs(iphone_path)
    db.add(Video(**iphone_attrs))
    db.commit()
    os.remove(orig_path)
    os.remove(iphone_path)

def process_s3_key(key):
    _process_fullcopy(key)
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
