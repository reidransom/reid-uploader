import os
import sys

def get_aws(path):
	with open(path, 'r') as fp:
		data = fp.read()
		fp.close()
	return data.strip().split('\n')

# this should be outside your web root
CONFIG_ROOT = '/home/reidransom/.reiduploader'

aws_access_key = aws_secret = ffmpeg = tmpdir = None

# if config_root doesn't exist look for ~/.reiduploader (for dev)
for path in [CONFIG_ROOT, os.path.join(os.path.expanduser('~'), '.reiduploader')]:
	if os.path.isdir(path):
		# get aws config from ~/.aws - format should be `aws_access_key\naws_secret`
		# should be readable by apache
		aws_access_key, aws_secret = get_aws(os.path.join(path, 'aws.txt'))
		# should be executable by apache
		ffmpeg = os.path.join(path, 'ffmpeg')
		# should be read/writeable by apache
		tmpdir = os.path.join(path, 'tmp')
		break

MIME_TYPE = os.environ.get('MIME_TYPE', "application/octet-stream")
BUCKET = os.environ.get('BUCKET', "reid-uploader")
AWS_SECRET = os.environ.get('AWS_SECRET', aws_secret)
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', aws_access_key)
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
ENGINE = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
PORT = int(os.environ.get('PORT', 5000))
CHUNK_SIZE = 6 * 1024 * 1024  # CAREFUL! If you modify this, you have to
                              # clear the chunk database; I recommend
                              # setting it before having any real upload data
FFMPEG = os.environ.get('FFMPEG', ffmpeg)
TMPDIR = tmpdir

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
