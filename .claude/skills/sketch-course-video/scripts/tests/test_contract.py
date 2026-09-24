"""Contract tests use disposable fixtures, not recordings from any real lesson."""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def system_font():
    """A TrueType font file for caption measurement: SKETCH_TEST_FONT, else a common system font."""
    candidates = [os.environ.get('SKETCH_TEST_FONT', ''),
                  'C:/Windows/Fonts/arial.ttf',
                  '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf',
                  '/usr/share/fonts/TTF/DejaVuSans.ttf']
    try:
        import matplotlib
        candidates.append(str(Path(matplotlib.__file__).parent / 'mpl-data/fonts/ttf/DejaVuSans.ttf'))
    except ImportError:
        pass
    return next((c for c in candidates if c and Path(c).is_file()), None)
import numpy as np
from PIL import ImageFont
from contract import load, interval, overlap
from common import writable, SKILL, stop_check
from captions import cues, wrap, color, stamp, caption_parts, generate, term_pattern
from media_tools import unwrap
from prepare import mask_data, load_source


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = {
            'schema_version': 1, 'id': 'Test01',
            'video': {'width': 1920, 'height': 1080, 'fps': 30, 'frames': 180},
            'base_video': 'base.mp4', 'sources': {'paper': {'path': 'art.png', 'theme': 'paper'}},
            'protected_intervals': [[0, 30]], 'caption_band': [0, 900, 1920, 180],
            'scenes': [{'id': 'Draw01', 'start': 30, 'end': 180, 'width': 1280, 'height': 720,
                'theme': 'paper', 'title': 'Заголовок', 'subtitle': '', 'arts': [{'name': 'box', 'source': 'paper', 'crop': [0, 0, 200, 200],
                    'dest': [200, 200, 200, 200], 'start': .2, 'duration': 2}],
                'placements': [{'start': 30, 'end': 180, 'rect': [32, 80, 1280, 720]}]}]}

    def tearDown(self):
        self.temp.cleanup()

    def check_config(self, c=None):
        path = self.root / 'project.json'
        path.write_text(json.dumps(c or self.config), encoding='utf-8')
        return load(path, files=False)

    def test_valid_and_default_labels(self):
        self.assertEqual(self.check_config()['scenes'][0]['labels'], [])

    def test_half_open_boundaries(self):
        self.assertTrue(interval(0, 30, 30))
        self.assertFalse(interval(1.0, 30, 30))
        self.assertFalse(overlap([0, 30], [30, 60]))

    def test_incomplete_draw_rejected(self):
        self.config['scenes'][0]['arts'][0]['duration'] = 7
        with self.assertRaisesRegex(ValueError, 'Incomplete drawing'):
            self.check_config()

    def test_duplicate_scene_rejected(self):
        self.config['scenes'].append(copy.deepcopy(self.config['scenes'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate scene'):
            self.check_config()

    def test_overlapping_placements_rejected(self):
        self.config['scenes'][0]['placements'].append({'start': 170, 'end': 180, 'rect': [32, 80, 1280, 720]})
        with self.assertRaisesRegex(ValueError, 'Overlapping panel'):
            self.check_config()

    def test_protected_footage_rejected(self):
        self.config['protected_intervals'].append([90, 100])
        with self.assertRaisesRegex(ValueError, 'protected footage'):
            self.check_config()

    def test_caption_collision_rejected(self):
        self.config['caption_band'] = [0, 600, 1920, 200]
        with self.assertRaisesRegex(ValueError, 'caption band'):
            self.check_config()

    def test_stretching_rejected(self):
        self.config['scenes'][0]['arts'][0]['dest'][2] = 400
        with self.assertRaisesRegex(ValueError, 'stretches original'):
            self.check_config()

    def test_empty_placements_rejected(self):
        self.config['scenes'][0]['placements'] = []
        with self.assertRaisesRegex(ValueError, 'at least one'):
            self.check_config()

    def test_inputs_in_output_rejected(self):
        self.config['base_video'] = 'output/base.mp4'
        with self.assertRaisesRegex(ValueError, 'Inputs must not'):
            self.check_config()

    def test_nested_state_directories_rejected(self):
        self.config['paths'] = {'work': 'state', 'output': 'state/export', 'runtime': 'runtime'}
        with self.assertRaisesRegex(ValueError, 'must not nest'):
            self.check_config()

    def test_skill_not_used_for_job_state(self):
        with self.assertRaises(ValueError):
            writable(SKILL / 'cache')

    def test_stop_marker(self):
        (self.root / 'STOP').touch()
        with self.assertRaises(InterruptedError):
            stop_check(self.root)

    def test_unwrap_preserves_paragraphs_and_cues(self):
        self.assertEqual(unwrap('=====\nHello\nworld\n\n[SCREEN] demo\n\nNext line'),
                         'Hello world\n\n[SCREEN] demo\n\nNext line\n')

    def test_caption_overlap_rejected(self):
        path = self.root / 'test.srt'
        path.write_text('1\n00:00:00,000 --> 00:00:02,000\nFirst\n\n2\n00:00:01,000 --> 00:00:03,000\nSecond')
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            cues(path)

    def test_caption_measurement(self):
        font = ImageFont.load_default(size=20)
        self.assertLessEqual(len(wrap('Hello test', font, 130)), 2)
        with self.assertRaises(ValueError):
            wrap('One two three four five six seven eight nine ten eleven twelve', font, 50)
        self.assertEqual(color('#FFD014'), '14D0FF')
        self.assertEqual(stamp(61.25), '0:01:01.25')

    def test_pill_marks_first_term_once_per_cue(self):
        font = system_font()
        if not font:
            self.skipTest('No TrueType font found; set SKETCH_TEST_FONT')
        srt = self.root / 'pill.srt'
        srt.write_text('1\n00:00:00,500 --> 00:00:03,000\nСегодня опишем задачу и проверим задачу\n', encoding='utf-8')
        out = self.root / 'pill.ass'
        generate(srt, font, out, 1920, 1080, 40, 1400, 960, 914, '#272C33', '#B38A00',
                 ['задач*', 'провер*'], highlight='pill')
        events = [l for l in out.read_text(encoding='utf-8-sig').splitlines() if l.startswith('Dialogue:')]
        plates = [e for e in events if '\\p1' in e]
        self.assertEqual(len(plates), 1)                      # first term only, not every match
        self.assertIn('&H3BD4FF&', plates[0])                 # #FFD43B in ASS BGR order
        self.assertTrue(all('Dialogue: 1,' in e for e in events if '\\p1' not in e))

    def test_keep_breaks_uses_reviewed_rows(self):
        font = system_font()
        if not font:
            self.skipTest('No TrueType font found; set SKETCH_TEST_FONT')
        srt = self.root / 'rows.srt'
        srt.write_text('1\n00:00:00,500 --> 00:00:03,000\nСначала опишите задачу,\nпотом соберите черновик\n',
                       encoding='utf-8')
        for keep, expected in [(True, 2), (False, 1)]:
            out = self.root / f'rows-{keep}.ass'
            generate(srt, font, out, 1920, 1080, 40, 1400, 960, 914, '#272C33', '#B38A00', [], keep_breaks=keep)
            layout = json.loads(out.with_suffix('.layout.json').read_text(encoding='utf-8'))
            self.assertEqual(layout[0]['lines'], expected)

    def test_term_wildcard_matches_word_forms(self):
        self.assertTrue(term_pattern(['задач*']).search('Задачей'))
        self.assertIsNone(term_pattern(['кот']).search('котлета'))

    def test_caption_position_changes_do_not_shift_speech(self):
        region = {'start': 2, 'end': 4, 'x': 900, 'y': 150}
        self.assertEqual(list(caption_parts(1, 5, [region])), [(1, 2, {}), (2, 4, region), (4, 5, {})])

    def test_trace_original_pixels_and_blank_failure(self):
        image = np.full((100, 100, 3), 250, dtype=np.uint8)
        image[20:24, 20:80] = 20
        image[20:80, 20:24] = 20
        image[55:65, 30:70] = [255, 208, 20]
        original = image.copy()
        item = {'name': 'test', 'crop': [0, 0, 100, 100]}
        data = mask_data(image, item, False)
        self.assertTrue(data['paths'])
        self.assertTrue(any(p['color'] for p in data['paths']))
        self.assertTrue(data['finish'])
        self.assertTrue(np.array_equal(image, original))
        with self.assertRaisesRegex(ValueError, 'No ink'):
            mask_data(np.full_like(image, 250), item, False)

    def test_transparent_page_is_not_traced_as_ink(self):
        rgba = np.zeros((100, 100, 4), dtype=np.uint8)
        rgba[..., :3] = [94, 86, 80]                 # dark RGB under a transparent page
        rgba[20:24, 20:80] = [20, 20, 20, 255]       # the one real contour
        path = self.root / 'sheet.png'
        from PIL import Image
        Image.fromarray(rgba, 'RGBA').save(path)
        flat = load_source(str(path), 'paper')
        self.assertEqual(flat.shape, (100, 100, 3))
        self.assertEqual(flat[60, 60].tolist(), [248, 243, 236])  # transparent area reads as paper, not ink
        data = mask_data(flat, {'name': 't', 'crop': [0, 0, 100, 100]}, False)
        ys = [p[1] for path_ in data['paths'] for p in path_['points']]
        self.assertTrue(ys and max(ys) < 30)        # only the drawn line was traced

    def test_missing_title_rejected(self):
        del self.config['scenes'][0]['title']
        with self.assertRaisesRegex(ValueError, 'title and subtitle'):
            self.check_config()

    def test_unknown_accent_rule_rejected(self):
        self.config['sources']['paper']['accent'] = 'blue'
        with self.assertRaisesRegex(ValueError, 'accent must be'):
            self.check_config()

    def test_coral_accent_is_hatched_not_traced_as_ink(self):
        # A coral accent (#E8643C) fails the yellow test (G>110) and, being darker than
        # mean 180, the yellow rule on paper even swallows it into the ink contours.
        image = np.full((100, 100, 3), 248, dtype=np.uint8)
        image[20:24, 20:80] = 20
        image[20:80, 20:24] = 20
        image[40:70, 40:75] = [232, 100, 60]
        item = {'name': 'coral', 'crop': [0, 0, 100, 100]}
        yellow = mask_data(image, item, False, 'yellow')
        coral = mask_data(image, item, False, 'coral')
        self.assertFalse(any(p['color'] for p in yellow['paths']))
        self.assertTrue(any(p['color'] for p in coral['paths']))
        self.assertTrue(any(not p['color'] for p in coral['paths']))


    def test_shadow_flag_must_be_bool(self):
        self.config['scenes'][0]['placements'][0]['shadow'] = 'yes'
        with self.assertRaisesRegex(ValueError, 'shadow'):
            self.check_config()

    def test_shadow_png_is_soft_and_below(self):
        from compose import shadow, wants_shadow
        path = self.root / 'sh.png'
        m = shadow(path, 200, 100, 22)
        from PIL import Image
        a = np.asarray(Image.open(path))[..., 3].astype(int)
        self.assertEqual(a.shape, (100 + 2 * m, 200 + 2 * m))
        self.assertGreater(a[m + 100 + 4, m + 100], a[m - 4, m + 100])   # heavier below than above
        self.assertLess(a.max(), 70)                                     # modest, never a hard border
        self.assertTrue(wants_shadow({'radius': 22}))
        self.assertFalse(wants_shadow({'radius': 0}))
        self.assertFalse(wants_shadow({'radius': 22, 'shadow': False}))

    def test_dark_coral_grey_fill_is_in_finish(self):
        # A grey-filled arm next to a bright outline on black: traced ink stays the outline only,
        # but the final reveal must cover the fill, or it is cut out while the frame holds.
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[20:24, 10:90] = 230                     # bright contour
        image[40:70, 60:95] = 90                      # mid-grey fill, not touching the contour
        item = {'name': 'arm', 'crop': [0, 0, 100, 100]}
        data = mask_data(image, item, True, 'coral')
        paths = [p for p in data['finish'].split('Z') if p.strip()]
        self.assertEqual(len(paths), 2)                # contour + fill (was contour only)
        self.assertFalse(any(p['color'] for p in data['paths']))
        self.assertTrue(all(max(pt[1] for pt in p['points']) < 30 for p in data['paths']))  # fill is not traced
        yellow = mask_data(image, item, True, 'yellow')
        self.assertEqual(len([p for p in yellow['finish'].split('Z') if p.strip()]), 2)   # yellow rule unchanged: fill >82 is ink


if __name__ == '__main__':
    unittest.main()
