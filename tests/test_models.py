import os
import unittest

from reiduploader import helper, worker
from reiduploader.models import *

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TEST_VIDEO = os.path.join(DATA_DIR, 'test-h264-24fps-5s.mov')

class TestModels(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_video(self):
        bucket = helper.get_bucket()
        keyname = 'test-create-video.mov'
        key = bucket.get_key(keyname)
        if not key:
            key = worker.upload_to_s3(TEST_VIDEO, keyname)
        attrs = {
            'key': keyname,
            'video_bitrate': 1095,
            'audio_bitrate': 126,
            'framerate': 29970,
            'width': 640,
            'height': 360,
            'num_audio_channels': 2,
            'duration': 3180,
            # 'filesize':
        }
        video = Video(**attrs)
        db.add(video)
        db.commit()
        self.assertIsInstance(video.id, int)
        self.assertEqual(attrs['key'],                video.key)
        self.assertEqual(attrs['video_bitrate'],      video.video_bitrate)
        self.assertEqual(attrs['audio_bitrate'],      video.audio_bitrate)
        self.assertEqual(attrs['framerate'],          video.framerate)
        self.assertEqual(attrs['width'],              video.width)
        self.assertEqual(attrs['height'],             video.height)
        self.assertEqual(attrs['num_audio_channels'], video.num_audio_channels)
        self.assertEqual(attrs['duration'],           video.duration)
        self.assertEqual(31.8,                        video.total_seconds())
        # self.assertEqual(747349,                      video.filesize())





