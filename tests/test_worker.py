import os
import subprocess
import unittest
import shutil

from reiduploader import worker, helper
from reiduploader.models import db, Video
from reiduploader.settings import TMPDIR

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

## Assert Reference
# assertEqual(a, b)           a == b
# assertNotEqual(a, b)        a != b
# assertTrue(x)               bool(x) is True
# assertFalse(x)              bool(x) is False
# assertIs(a, b)              a is b
# assertIsNot(a, b)           a is not b
# assertIsNone(x)             x is None
# assertIsNotNone(x)          x is not None
# assertIn(a, b)              a in b
# assertNotIn(a, b)           a not in b
# assertIsInstance(a, b)      isinstance(a, b)
# assertNotIsInstance(a, b)   not isinstance(a, b)

class TestWorker(unittest.TestCase):

    def setUp(self):
        self.bucket = helper.get_bucket()
        subprocess.call('rm %s/* 2> /dev/null' % TMPDIR, shell=True)
        self.test_video = os.path.join(DATA_DIR, 'test-h264-24fps-5s.mov')

    def test_process_s3_key(self):
        # Setup
        key = 'test-process-s3-key.mov'
        iphone_key = 'test-process-s3-key-iphone.mp4'
        if not self.bucket.get_key(key):
            worker.upload_to_s3(self.test_video, key)
        self.bucket.delete_key(iphone_key)

        # Test
        self.assertIsNone(self.bucket.get_key(iphone_key))
        worker.process_s3_key(key)
        self.assertIsNotNone(self.bucket.get_key(iphone_key))
        # todo: test that iphone video made it to the db

    def test_process_fullcopy(self, key='test-process-fullcopy.mov'):
        iphone_key = os.path.splitext(key)[0] + '-iphone.mp4'
        if not self.bucket.get_key(key):
            worker.upload_to_s3(self.test_video, key)
        self.bucket.delete_key(iphone_key)
        for video in db.query(Video).filter(Video.key.in_([key, iphone_key])):
            db.delete(video)

        self.assertEqual(0, db.query(Video).filter(Video.key.in_([key, iphone_key])).count())
        self.assertIsNone(self.bucket.get_key(iphone_key))
        worker._process_fullcopy(key)
        self.assertEqual(2, db.query(Video).filter(Video.key.in_([key, iphone_key])).count())
        self.assertIsNotNone(self.bucket.get_key(iphone_key))
        for k in [key, iphone_key]:
            self.assertFalse(os.path.isfile(os.path.join(TMPDIR, k)))

    def test_urls(self):
        pass
        # Include additional test URLs here
        # self.test_process_fullcopy('test-stormy.mov')
        # self.test_process_fullcopy('test-elegy.mov')
        # self.test_process_fullcopy('test-bite.mov')

    # def test_url_to_iphone_video(self):
    #     # Setup
    #     key = 'test-url-to-iphone-video.mov'
    #     iphone_path = os.path.join(TMPDIR, 'test-url-to-iphone-video-iphone.mp4')
    #     url = helper.get_s3url(key)
    #     if not self.bucket.get_key(key):
    #         worker.upload_to_s3(self.test_video, key)

    #     # Test
    #     worker.url_to_iphone_video(url)
    #     self.assertTrue(os.path.isfile(iphone_path))

    def test_upload_to_s3(self):
        key = 'test-upload-to-s3.mov'
        self.bucket.delete_key(key)
        self.assertIsNone(self.bucket.get_key(key))
        worker.upload_to_s3(self.test_video, key)
        self.assertIsNotNone(self.bucket.get_key(key))

    def test_get_ffmpeg_input_data(self):
        path = os.path.join(DATA_DIR, 'ffmpeg-output.txt')
        with open(path, 'r') as fp:
            data = fp.read()
            fp.close()
        data = worker.get_ffmpeg_input_data(data)
        lines = data.split('\n')
        self.assertEqual('  Metadata:', lines[1])

    def test_download_url(self):
        # Setup
        key = 'test-download-url.mov'
        url = helper.get_s3url(key)
        path = os.path.join(TMPDIR, key)
        if not self.bucket.get_key(key):
            worker.upload_to_s3(self.test_video, key)

        if os.path.isfile(path):
            os.remove(path)
        self.assertFalse(os.path.isfile(path))
        worker.download_url(url)
        self.assertTrue(os.path.isfile(path))

    def test_make_iphone(self):
        input_path = os.path.join(TMPDIR, 'test-make-iphone.mov')
        output_path = os.path.join(TMPDIR, 'test-make-iphone-iphone.mp4')
        shutil.copy(self.test_video, input_path)
        if os.path.isfile(output_path):
            os.remove(output_path)
        self.assertFalse(os.path.isfile(output_path))
        path, data = worker.make_iphone(input_path)
        self.assertTrue(os.path.isfile(output_path))
        self.assertEqual(path, output_path)
        self.assertIsInstance(data, str)
        # subprocess.call(['open', path]) # osx only

    def test_get_video_attrs(self):
        expected_attrs = {
            'num_audio_channels': 2,
            'video_bitrate': 1055,
            'framerate': 24000,
            'height': 540,
            'width': 960,
            'audio_bitrate': 125,
            'key': 'test-h264-24fps-5s.mov',
            'duration': 500,
            'filesize': 747349
        }
        actual_attrs = worker.get_video_attrs(self.test_video)
        for key, val in expected_attrs.items():
            self.assertEqual(val, actual_attrs[key])

    def test_parse_ffmpeg_data(self):
        path = os.path.join(DATA_DIR, 'ffmpeg-output.txt')
        with open(path, 'r') as fp:
            data = fp.read()
            fp.close()
        data = worker.get_ffmpeg_input_data(data)
        data = worker.parse_ffmpeg_data(data)
        self.assertEqual(1095,   data['video_bitrate'])
        self.assertEqual(126,    data['audio_bitrate'])
        self.assertEqual(29970,  data['framerate'])
        self.assertEqual(640,    data['width'])
        self.assertEqual(360,    data['height'])
        self.assertEqual(2,      data['num_audio_channels'])
        self.assertEqual(3180,   data['duration']) # 31.8 * framerate

if __name__ == '__main__':
    unittest.main()
