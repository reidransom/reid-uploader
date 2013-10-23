import os

def get_aws(path):
	with open(path, 'r') as fp:
		data = fp.read()
		fp.close()
	return data.strip().split('\n')

# get aws config from ~/.aws - format should be `aws_access_key\naws_secret`
aws_access_key = aws_secret = ''
for path in ['/home/reidransom/.aws', '/Users/reid/.aws']:
	if os.path.isfile(path):
		aws_access_key, aws_secret = get_aws(path)
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

