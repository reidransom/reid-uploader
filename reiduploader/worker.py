#!/usr/bin/env python

import logging
import os
import re
import shlex
import subprocess
import sys
import urllib.parse
from logging.handlers import RotatingFileHandler

import helper
from models import db, Video
from settings import FFMPEG, TMPDIR, FFMPEG_PRESETS

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
        video['audio_bitrate'] = int(re.search(r' (\d+) kb/s', audio_data).group(1))
    except AttributeError:
        video['audio_bitrate'] = 0
    try:
        video['video_bitrate'] = int(re.search(r' (\d+) kb/s', video_data).group(1))
    except AttributeError:
        video['video_bitrate'] = 0
    try:
        video['framerate'] = int(float(re.search(r' ([\d\.]+) fps', video_data).group(1))*1000)
    except AttributeError:
        video['framerate'] = 0
    try:
        video['width'], video['height'] = map(int, re.search(r', (\d+)x(\d+)', video_data).groups())
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
            r'Duration: (\d\d)\:(\d\d)\:(\d\d)\.(\d\d)',
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
        except subprocess.CalledProcessError as e:
            ffmpeg_data = e.output
    attrs = parse_ffmpeg_data(ffmpeg_data)
    attrs['key'] = os.path.basename(path)
    attrs['filesize'] = os.stat(path).st_size
    return attrs


def download_url(url):
    output_path = os.path.join(TMPDIR, os.path.basename(urllib.parse(url).path))
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


def _process_fullcopy(key):
    # Set the content-type correctly
    bucket = helper.get_bucket()
    k = bucket.lookup(key)
    k.copy(k.bucket, k.name, preserve_acl=True, metadata={'Content-Type': helper.get_mimetype(k.name)})

    orig_video = Video(key=key, status='downloading')
    db.add(orig_video)
    db.commit()


def process_s3_key(key):
    # _process_fullcopy(key)
    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write(usage())
        sys.exit(1)
    process_s3_key(sys.argv[1])
