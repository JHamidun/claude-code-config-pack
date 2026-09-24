"""Opt-in FFmpeg integration tests: SKETCH_MEDIA_TESTS=1, no personal fixtures."""
import os
import sys
import json
import wave
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image, ImageDraw
from media_tools import sync_candidate
from raw_edit import execute
from common import video_stream


@unittest.skipUnless(os.environ.get('SKETCH_MEDIA_TESTS') == '1' and shutil.which('ffmpeg'), 'Opt-in media tests')
class MediaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def wav(self, name, data):
        path = self.root / name
        with wave.open(str(path), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(8000)
            f.writeframes(np.int16(data * 8000).tobytes())
        return path

    def test_known_audio_offset(self):
        audio = np.random.default_rng(72).uniform(-1, 1, 32000)
        ref = self.wav('reference.wav', audio)
        target = self.wav('target.wav', audio[6000:22000])
        match = sync_candidate(ref, target, 0, 0, 4, 1)
        self.assertAlmostEqual(match['reference_minus_target_seconds'], .75, places=3)
        self.assertGreater(match['correlation'], .99)

    def test_keying_and_base_contract(self):
        source = Image.new('RGB', (320, 180), '#00ff00')
        ImageDraw.Draw(source).rectangle((100, 30, 220, 179), fill='#101010')
        source.save(self.root / 'camera.png')
        self.wav('voice.wav', np.random.default_rng(9).uniform(-.2, .2, 8000))
        cfg = {'schema_version': 1, 'id': 'Test', 'video': {'width': 320, 'height': 180, 'fps': 30, 'frames': 30},
            'work': 'state', 'output': 'master.mp4', 'segments': [{'id': 'Take1', 'frames': 30,
            'background': '#eeeeee', 'audio': {'path': 'voice.wav', 'in': 0},
            'layers': [{'path': 'camera.png', 'kind': 'image', 'rect': [0, 0, 320, 180],
                'radius': 0, 'key': {'color': '0x00ff00', 'similarity': .3, 'blend': .12},
                'panel': {'center': '#eeeeee', 'edge': '#eeeeee'}}]}]}
        file = self.root / 'edit.json'; file.write_text(json.dumps(cfg), encoding='utf-8')
        execute(file, start=True)
        meta = video_stream(self.root / 'master.mp4')
        self.assertEqual(meta['nb_frames'], '30')
        self.assertEqual(meta['color_space'], 'bt709')
        self.assertEqual(meta['color_range'], 'tv')
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(self.root / 'master.mp4'),
            '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        image = np.frombuffer(pixels, dtype=np.uint8).reshape(180, 320, 3)
        self.assertLess(int(np.ptp(image[10, 10])), 8)
        self.assertGreater(float(image[10, 10].mean()), 225)
        self.assertLess(float(image[100, 150].mean()), 30)


if __name__ == '__main__':
    unittest.main()
