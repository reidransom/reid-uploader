from settings import BUCKET, AWS_ACCESS_KEY, AWS_SECRET

def get_bucket():
	from boto.s3.connection import S3Connection
	conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET)
	return conn.create_bucket(BUCKET)
	