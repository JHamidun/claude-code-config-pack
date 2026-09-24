"""Bounded, resumable lesson graphics build. No render without --start."""
import argparse
import hashlib
import time
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from common import SKILL, digest, read_json, write_json, run, stop_check, video_stream
from contract import load
from prepare import prepare
from compose import compose, export_sidecars
from qa import check_clip, verify


def cache_valid(path, stamp, key, s, fps):
    try:
        data = read_json(stamp)
        if data['input_hash'] != key or data['output_hash'] != digest(path):
            return False
        check_clip(path, s['width'], s['height'], fps, s['end'] - s['start'])
        return True
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError):
        return False


def execute(config, start=False, proof=False, only=None):
    c = load(config)
    if only and not set(only).issubset({s['id'] for s in c['scenes']}):
        raise ValueError('Unknown scene requested by --only')
    print(json.dumps({'id': c['id'], 'scenes': len(c['scenes']), 'seconds': c['video']['frames']/c['video']['fps'],
                      'output': str(c['_output']), 'mode': 'proof' if proof else 'full', 'start': start}, ensure_ascii=False), flush=True)
    if not start:
        return
    stop_check(c['_root'])
    c['_work'].mkdir(parents=True, exist_ok=True); c['_output'].mkdir(parents=True, exist_ok=True)
    (c['_work'] / 'clips').mkdir(exist_ok=True)
    check_clip(c['_base'], c['video']['width'], c['video']['height'], c['video']['fps'], c['video']['frames'])
    meta = video_stream(c['_base'])
    if meta.get('color_range') != 'tv' or meta.get('color_space') != 'bt709':
        raise ValueError('Approved base must already be BT709 limited; normalize exactly once before this stage')
    entry = prepare(c)
    node = shutil.which('node')
    cli = c['_runtime'] / 'node_modules/@remotion/cli/remotion-cli.js'
    tsc = c['_runtime'] / 'node_modules/typescript/bin/tsc'
    if not node or not cli.is_file() or not tsc.is_file():
        raise RuntimeError('Missing Node/Remotion/TypeScript runtime; use project.py install-runtime on the explicit runtime')
    run([node, tsc, '--project', entry.parent / 'tsconfig.json'], c['_work'] / 'typecheck.log', c['_root'], cwd=c['_runtime'], timeout=120)
    run([node, cli, 'bundle', entry, f'--out-dir={c["_work"] / "bundle"}'], c['_work'] / 'build.log', c['_root'], cwd=c['_runtime'],
        timeout=c.get('bundle_timeout_seconds', 600))   # 180 s proved too short on a loaded machine
    run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', SKILL / 'scripts/tests', '-v'],
        c['_work'] / 'tests.log', c['_root'], cwd=SKILL / 'scripts', timeout=120)
    prepared = read_json(c['_work'] / 'prepared.json')
    for s in c['scenes']:
        if only and s['id'] not in only:
            continue
        stop_check(c['_root'])
        path = c['_work'] / 'clips' / f'{s["id"]}.mp4'
        stamp = path.with_suffix('.stamp.json')
        h = prepared['hashes']
        keys = ['SketchPanel.tsx', f'{s["id"]}.json', 'public/heading.ttf', 'public/hand.ttf']
        keys += [f'public/{a["source"]}.png' for a in s['arts']]
        payload = {k: h[k] for k in keys}
        payload['fps'] = c['video']['fps']
        payload['dependencies'] = digest(c['_runtime'] / 'package.json')
        lock = c['_runtime'] / 'package-lock.json'
        if lock.is_file():
            payload['lock'] = digest(lock)
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if not proof and cache_valid(path, stamp, key, s, c['video']['fps']):
            print(s['id'], 'cached', flush=True)
            continue
        if proof:
            command = [node, cli, 'still', entry, s['id'], c['_output'] / f'{s["id"]}-proof.jpg',
                       f'--frame={s["end"]-s["start"]-1}', '--image-format=jpeg', '--log=error']
        else:
            command = [node, cli, 'render', entry, s['id'], path, '--codec=h264', '--crf=17', '--concurrency=2', '--timeout=120000']
        attempts = c.get('render_attempts', 3)
        for attempt in range(attempts):
            try:
                run(command, c['_work'] / f'{s["id"]}-{attempt}.log', c['_root'], cwd=c['_runtime'], timeout=c.get('timeout_seconds', 1800))
                if not proof:
                    check_clip(path, s['width'], s['height'], c['video']['fps'], s['end']-s['start'])
                break
            except (RuntimeError, TimeoutError):
                if attempt == attempts - 1:
                    raise
                # Remotion gives headless Chrome a fixed 25 s to come up; on a loaded machine it
                # misses that window now and then (observed in 3 of 4 runs once), so back off and retry.
                time.sleep(20 * (attempt + 1))
        if not proof:
            write_json(stamp, {'input_hash': key, 'output_hash': digest(path)})
        write_json(c['_work'] / 'checkpoint.json', {'last_scene': s['id'], 'proof': proof})
        print(s['id'], 'ready', flush=True)
    if proof or only:
        return
    candidate = c['_output'] / f'{c["id"]}.partial.mp4'
    compose(c, candidate)
    verify(c, candidate)
    final = c['_output'] / f'{c["id"]}.mp4'
    os.replace(candidate, final)
    export_sidecars(c, final)
    write_json(c['_work'] / 'checkpoint.json', {'status': 'technical_pass', 'final': str(final), 'editorial_review': 'pending'})
    print(final, flush=True)


def main():
    p = argparse.ArgumentParser(); p.add_argument('config'); p.add_argument('--start', action='store_true')
    p.add_argument('--proof', action='store_true'); p.add_argument('--only', nargs='+')
    a = p.parse_args()
    execute(a.config, a.start, a.proof, a.only)


if __name__ == '__main__':
    main()
