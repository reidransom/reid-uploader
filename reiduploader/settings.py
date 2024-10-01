import os
import sys

def get_aws(path):
    with open(path, 'r') as fp:
        data = fp.read()
        fp.close()
    return data.strip().split(' ')

# this should be outside your web root
CONFIG_ROOT = '/scratch'

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
    'm4v': 'video/m4v',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'webm': 'video/webm',
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'svg': 'image/svg+xml',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',
    'webp': 'image/webp',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
} # MIME_TYPES.keys() is the list of allowed file extensions.

FFMPEG_PRESETS = {

        # from <https://trac.ffmpeg.org/wiki/Encode/H.264>
        '-edx.mp4': '-c:v libx264 -preset slow -crf 22 -vf scale=960:540 -c:a aac -b:a 128k -strict -2',

        # from <https://trac.ffmpeg.org/wiki/Encode/VP8>
        '-edx.webm': '-c:v libvpx -crf 12 -b:v 1M -vf scale=720:404 -c:a libvorbis -b:a 128k',

}

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
