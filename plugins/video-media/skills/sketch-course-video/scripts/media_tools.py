"""Read-only inventory, explicit audio match candidates, unwrapped note copies."""
import argparse
import re
import subprocess
from pathlib import Path
from common import probe, digest, write_json, writable


def unwrap(text):
    paragraphs, lines = [], []
    def flush():
        if lines:
            paragraphs.append(' '.join(lines)); lines.clear()
    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif re.match(r'^\[(?:SCREEN|PAUSE|EDIT|ЭКРАН|ПАУЗА|МОНТАЖ)\]', s, re.I) or re.match(r'^(?:[-*•]|\d+[.)])\s', s):
            flush(); paragraphs.append(s)
        elif re.fullmatch(r'[=\-_]{5,}', s):
            flush()
        else:
            lines.append(s)
    flush()
    return '\n\n'.join(paragraphs) + '\n'


def sync_candidate(reference, target, reference_start, target_start, search_seconds, sample_seconds):
    import numpy as np
    from scipy.signal import correlate
    require = lambda test, msg: None if test else (_ for _ in ()).throw(ValueError(msg))
    require(0 < sample_seconds <= search_seconds <= 120, 'Use 0 < sample <= search <= 120 seconds')
    def samples(path, start, duration):
        return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(start), '-i', str(path),
            '-t', str(duration), '-vn', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], timeout=180), dtype=np.float32).astype(float)
    a, b = samples(reference, reference_start, search_seconds), samples(target, target_start, sample_seconds)
    require(len(a) >= len(b) and len(b) > 100, 'Insufficient audio')
    b -= b.mean(); a -= a.mean()
    require(np.std(b) > 1e-5, 'Target is silent; no reliable sync candidate')
    corr = correlate(a, b, mode='valid', method='fft')
    # Sliding energy without the quadratic cost of a long convolution kernel.
    cs = np.concatenate(([0.], np.cumsum(a*a)))
    denom = np.sqrt(np.maximum(1e-20, (cs[len(b):]-cs[:-len(b)]) * np.sum(b*b)))
    score = corr / denom
    n = int(np.argmax(score)); reference_in = reference_start + n / 8000
    return {'reference_in_for_target_start': reference_in, 'target_start': target_start,
            'reference_minus_target_seconds': reference_in-target_start, 'correlation': float(score[n]),
            'status': 'candidate_only', 'warning': 'Validate claps and lip consonants at start/middle/end. Not a video-sync measurement.'}


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('inventory'); s.add_argument('files', nargs='+'); s.add_argument('--output', required=True)
    s = sub.add_parser('unwrap-notes'); s.add_argument('source'); s.add_argument('output')
    s = sub.add_parser('sync-candidate'); s.add_argument('reference'); s.add_argument('target'); s.add_argument('--reference-start', type=float, default=0)
    s.add_argument('--target-start', type=float, default=0); s.add_argument('--search-seconds', type=float, default=20)
    s.add_argument('--sample-seconds', type=float, default=5); s.add_argument('--output', required=True)
    a = p.parse_args(); out = writable(a.output)
    if a.cmd == 'unwrap-notes':
        if out == Path(a.source).resolve():
            raise ValueError('Write notes to a separate file')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(unwrap(Path(a.source).read_text(encoding='utf-8-sig')), encoding='utf-8-sig')
    elif a.cmd == 'inventory':
        if out in [Path(x).resolve() for x in a.files]:
            raise ValueError('Cannot overwrite input with inventory')
        rows = []
        for value in a.files:
            path = Path(value).resolve(); before = path.stat()
            row = {'path': str(path), 'size': before.st_size, 'mtime_ns': before.st_mtime_ns,
                   'sha256': digest(path), 'media': probe(path)}
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError(f'Source is still being written: {path}')
            rows.append(row)
        write_json(out, rows)
    else:
        if out in [Path(a.reference).resolve(), Path(a.target).resolve()]:
            raise ValueError('Cannot overwrite source with sync report')
        write_json(out, sync_candidate(a.reference, a.target, a.reference_start, a.target_start, a.search_seconds, a.sample_seconds))
    print(out)


if __name__ == '__main__':
    main()
