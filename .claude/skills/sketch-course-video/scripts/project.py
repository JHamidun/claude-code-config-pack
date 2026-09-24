"""Create a portable lesson directory without copying private media."""
import argparse
import shutil
from pathlib import Path
from common import SKILL, write_json, writable, run


def initialize(directory):
    root = writable(directory)
    if root.exists() and any(root.iterdir()):
        raise ValueError('Initialize only an empty directory')
    for name in ['input', 'fonts', 'work', 'output', 'runtime']:
        (root / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL / 'assets/remotion/package.json', root / 'runtime/package.json')
    lock = SKILL / 'assets/remotion/package-lock.json'
    if lock.is_file():
        shutil.copy2(lock, root / 'runtime/package-lock.json')
    config = {
        'schema_version': 1, 'id': 'Lesson01',
        'video': {'width': 1920, 'height': 1080, 'fps': 30, 'frames': 360},
        'base_video': 'input/master.mp4',
        'paths': {'work': 'work', 'output': 'output', 'runtime': 'runtime'},
        'fonts': {'heading': 'fonts/heading.ttf', 'hand': 'fonts/hand.ttf'},
        'encoder': 'libx264', 'branding': {'logos': []},
        'protected_intervals': [[0, 30]], 'caption_band': [0, 900, 1920, 180],
        'sources': {}, 'scenes': [], 'subtitle_file': None,
    }
    write_json(root / 'project.json', config)
    example = {
        'id': 'Concept01', 'start': 30, 'end': 360, 'width': 1280, 'height': 720,
        'theme': 'paper', 'title': 'Заголовок сцены', 'subtitle': 'Шаг 1. Шаг 2. Шаг 3.',
        'arts': [{'source': 'paper', 'name': 'first-object', 'crop': [0, 0, 400, 300],
                  'dest': [100, 240, 400, 300], 'start': .2, 'duration': 3,
                  'pen': True, 'until': None, 'exclude': []}],
        'labels': [{'value': 'Подпись', 'x': 300, 'y': 600, 'start': 3.3,
                    'size': 30, 'accent': False, 'until': None, 'heading': False}],
        'placements': [{'start': 30, 'end': 360, 'rect': [32, 80, 1280, 720], 'radius': 22}],
    }
    write_json(root / 'scene-example.json', example)
    write_json(root / 'edit-example.json', {
        'schema_version': 1, 'id': 'Lesson01', 'video': config['video'],
        'output': 'input/master.mp4', 'work': 'raw-work', 'encoder': 'libx264',
        'segments': [{'id': 'Take01', 'frames': 360, 'background': '#E9E5DE',
            'audio': {'path': 'input/mic.wav', 'in': 0, 'track': 0},
            'layers': [{'path': 'input/screen.mp4', 'kind': 'video', 'in': 0,
                'rect': [32, 80, 1280, 720], 'fit': 'contain', 'radius': 22},
                {'path': 'input/camera.mp4', 'kind': 'video', 'in': 0,
                 'rect': [1340, 80, 548, 720], 'fit': 'cover', 'radius': 22,
                 'panel': {'center': '#F8F5EF', 'edge': '#D9D4C9'},
                 'key': {'color': '0x00ff00', 'similarity': .3, 'blend': .12}}]}]})
    print(root / 'project.json')


def main():
    p = argparse.ArgumentParser(description='Create a job directory or install its Remotion runtime.')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('init', help='create a new job in an empty directory')
    s.add_argument('directory', help='new empty job directory, e.g. ~/VideoJobs/2026-01-15-lesson-01')
    s = sub.add_parser('install-runtime', help='npm ci the pinned Remotion runtime (plan only without --start)')
    s.add_argument('directory'); s.add_argument('--start', action='store_true')
    a = p.parse_args()
    if a.cmd == 'init':
        initialize(a.directory)
    elif not a.start:
        print('Plan: install pinned npm dependencies into the explicit runtime. Use --start.')
    else:
        root = writable(a.directory)
        npm = shutil.which('npm.cmd') or shutil.which('npm')
        if not npm:
            raise RuntimeError('npm is missing')
        command = 'ci' if (root / 'package-lock.json').is_file() else 'install'
        run([npm, command, '--no-audit', '--no-fund'], root / 'install.log', root,
            cwd=root, timeout=600)


if __name__ == '__main__':
    main()
