import os
import unittest

from reiduploader import worker, helper

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class TestWorker(unittest.TestCase):

	def setUp(self):
		self.bucket = helper.get_bucket()
		self.orig_key = 'test-h264-10s.mp4'
		self.iphone_key = 'test-h264-10s-iphone.mp4'

	# this is a "roundtrip" test. should probably have finer-grained tests as well
	def test_process_s3_key(self):
		
		# Make sure keys don't already exist
		self.bucket.delete_keys([self.orig_key, self.iphone_key])
		
		# Upload test file
		path = os.path.join(DATA_DIR, self.orig_key)
		worker.upload_to_s3(path)
		worker.process_s3_key(os.path.basename(path))
		
		# Check files exist
		self.assertIsNotNone(self.bucket.get_key(self.orig_key))
		self.assertIsNotNone(self.bucket.get_key(self.iphone_key))

		# Cleanup
		self.bucket.delete_keys([self.orig_key, self.iphone_key])

if __name__ == '__main__':
	unittest.main()
