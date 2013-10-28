import os
import sys

def get_aws(path):
	with open(path, 'r') as fp:
		data = fp.read()
		fp.close()
	return data.strip().split(' ')

# this should be outside your web root
CONFIG_ROOT = '/home/reidransom/.reiduploader'

aws_access_key = aws_secret = ffmpeg = tmpdir = None

# if config_root doesn't exist look for ~/.reiduploader (for dev)
for path in [CONFIG_ROOT, os.path.join(os.path.expanduser('~'), '.reiduploader')]:
	if os.path.isdir(path):

		# get aws config from aws.txt (format should be `aws_access_key aws_secret`)
		# should be readable by apache
		aws = get_aws(os.path.join(path, 'aws.txt'))
		AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY', aws[0])
		AWS_SECRET = os.environ.get('AWS_SECRET', aws[1])

		# should be executable by apache
		FFMPEG = os.environ.get('FFMPEG', os.path.join(path, 'ffmpeg'))

		# should be read/writeable by apache
		TMPDIR = os.path.join(path, 'tmp')
		ENGINE = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(path, 'database.db'))

		break

BUCKET = os.environ.get('BUCKET', "reid-uploader")
DEBUG = bool(int(os.environ.get('DEBUG', 1)))
PORT = int(os.environ.get('PORT', 5000))
CHUNK_SIZE = 6 * 1024 * 1024  # CAREFUL! If you modify this, you have to
                              # clear the chunk database; I recommend
                              # setting it before having any real upload data

MIME_TYPES = {
	'mp4': 'video/mp4',
	'mov': 'video/quicktime',
} # MIME_TYPES.keys() is the list of allowed file extensions.

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
