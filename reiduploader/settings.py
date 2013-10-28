import os
import sys

def get_aws(path):
	with open(path, 'r') as fp:
		data = fp.read()
		fp.close()
	return data.strip().split(' ')

# this should be outside your web root
CONFIG_ROOT = '/home/reidransom/.reiduploader'

# if config_root doesn't exist look for ~/.reiduploader (for dev)
for path in [CONFIG_ROOT, os.path.join(os.path.expanduser('~'), '.reiduploader')]:
	if os.path.isdir(path):

		# get aws config from aws.txt (format should be `aws_access_key aws_secret`)
		# should be readable by apache
		_aws = get_aws(os.path.join(path, 'aws.txt'))

		# should be executable by apache
		_ffmpeg = os.path.join(path, 'ffmpeg')

		# should be read/writeable by apache
		_tmpdir = os.path.join(path, 'tmp')
		_engine = 'sqlite:///' + os.path.join(path, 'database.db')

		break

AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', _aws[0])
AWS_SECRET = os.environ.get('AWS_SECRET', _aws[1])
FFMPEG = os.environ.get('FFMPEG', _ffmpeg)
TMPDIR = os.environ.get('RU_TMPDIR', _tmpdir)
ENGINE = os.environ.get('DATABASE_URL', _engine)
BUCKET = os.environ.get('BUCKET', "reid-uploader")
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
PORT = int(os.environ.get('PORT', 5000))

# CAREFUL! If you modify this, you have to clear the chunk database;
# I recommend setting it before having any real upload data
CHUNK_SIZE = 6 * 1024 * 1024

MIME_TYPES = {
	'mp4': 'video/mp4',
	'mov': 'video/quicktime',
} # MIME_TYPES.keys() is the list of allowed file extensions.

FFMPEG_PRESETS = {
	'main': '-vcodec libx264 -acodec libfaac -ab 128k -ar 48k -aspect 16:9 -vf yadif,scale=960x540 -x264opts cabac=1:ref=3:deblock=1,0,0:analyse=0x3,0x113:me=hex:subme=7:psy=1:psy_rd=1.00,0.00:me_range=16:chroma_me=1:trellis=1:8x8dct=1:fast_pskip=1:chroma_qp_offset=-2:threads=36:sliced_threads=0:nr=0:interlaced=0:bluray_compat=0:constrained_intra=0:bframes=3:b_pyramid=2:b_adapt=1:b_bias=0:weightb=1:open_gop=0:weightp=2:keyint=240:keyint_min=24:scenecut=40:intra_refresh=0:rc_lookahead=40:mbtree=1:crf=22:qcomp=0.60:qpmin=0:qpmax=69:qpstep=4:vbv_maxrate=17500:vbv_bufsize=17500:crf_max=0.0:nal_hrd=none -movflags faststart',
	'baseline': '-vcodec libx264 -b 1.5M -bf 0 -refs 1 -weightb 0 -8x8dct 0 -level 30 -acodec libfaac -ab 128k -ac 2 -ar 48k -aspect 16:9 -vf yadif,scale=640:360 -movflags faststart'
}

# `main` is supported in iPhone 4 and later only.  If you need to support iPhone 3GS or earlier,
# you should use `baseline`.
FFMPEG_PRESET = FFMPEG_PRESETS['main']

# Fail on config errors
def config_fail(str):
	sys.stderr.write(str + '\n')
	sys.exit(1)
if not AWS_SECRET or not AWS_ACCESS_KEY:
	config_fail('settings.AWS_* undefined.')
if not os.path.isfile(FFMPEG):
	config_fail('settings.FFMPEG error. (%s is not a file)' % FFMPEG)
if not os.path.isdir(TMPDIR):
	config_fail('settings.TMPDIR error. (%s is not a directory)' % TMPDIR)
