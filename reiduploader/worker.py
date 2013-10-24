#!/usr/bin/env python

import os
import subprocess
from urlparse import urlparse
	
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import helper
from settings import DEBUG, BUCKET, FFMPEG, TMPDIR, AWS_ACCESS_KEY, AWS_SECRET

def usage():
	return 'transcode.py <s3_key>'

def url_to_iphone_video(url, output_dir=TMPDIR):
	basename = os.path.basename(urlparse(url).path)
	output_path = os.path.join(output_dir, os.path.splitext(basename)[0] + '-iphone.mp4')
	cmd = 'curl %s | %s -f mov -i - -vcodec libx264 -acodec libfaac -ab 128k -ac 2 -ar 48k -aspect 16:9 -vf yadif,scale=960x540 -x264opts cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced_threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b_bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_lookahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500:crf_max=0.0:nal_hrd=none -movflags faststart -y %s' % (url, FFMPEG, output_path)
	if DEBUG:
		print cmd
	subprocess.call(cmd, shell=True)
	return output_path

def upload_to_s3(local_path):
	bucket = helper.get_bucket()
	k = Key(bucket)
	k.key = os.path.basename(local_path)
	k.set_contents_from_filename(local_path)
	k.set_canned_acl('public-read')

def process_s3_key(key):
	url = 'http://%s.s3.amazonaws.com/%s' % (BUCKET, key)
	local_path = url_to_iphone_video(url)
	upload_to_s3(local_path)
	os.remove(local_path)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.stderr.write(usage())
		sys.exit(1)
	process_s3_key(sys.argv[1])
