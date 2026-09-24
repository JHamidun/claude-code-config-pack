"""Project validation before any heavy work."""
import math
import re
from pathlib import Path
from common import read_json, resolve, writable


def require(test, message):
    if not test:
        raise ValueError(message)


def interval(a, b, total):
    return type(a) is int and type(b) is int and 0 <= a < b <= total


def overlap(a, b):
    return max(a[0], b[0]) < min(a[1], b[1])


def box(rect, width, height):
    return len(rect) == 4 and all(isinstance(n, (int, float)) and math.isfinite(n) for n in rect) and \
        rect[0] >= 0 and rect[1] >= 0 and rect[2] > 0 and rect[3] > 0 and \
        rect[0] + rect[2] <= width + .01 and rect[1] + rect[3] <= height + .01


def load(path, files=True):
    path = Path(path).resolve()
    c = read_json(path)
    require(c.get('schema_version') == 1, 'Unsupported schema_version')
    require(re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', c.get('id', '')), 'Unsafe project id')
    v = c['video']
    for k in ['width', 'height', 'fps', 'frames']:
        require(type(v[k]) is int and v[k] > 0, f'video.{k} must be a positive integer')
    require(v['width'] % 2 == 0 and v['height'] % 2 == 0, 'H264 dimensions must be even')
    root = path.parent
    c['_root'], c['_config'] = root, path
    for key, default in [('work', 'work'), ('output', 'output'), ('runtime', 'runtime')]:
        c['_' + key] = writable(resolve(root, c.get('paths', {}).get(key, default)))
    require(c['_work'] != c['_output'], 'work and output must differ')
    require(c['_runtime'] not in [c['_work'], c['_output']], 'runtime needs its own directory')
    dirs = [c['_work'], c['_output'], c['_runtime']]
    for i, a in enumerate(dirs):
        require(all(a not in b.parents and b not in a.parents for b in dirs[i+1:]), 'State directories must not nest')
    c['_base'] = resolve(root, c['base_video'])
    if files:
        require(c['_base'].is_file(), f'Missing base: {c["_base"]}')
        if c.get('subtitle_file'):
            require(resolve(root, c['subtitle_file']).is_file(), 'Missing subtitle sidecar')
        from PIL import Image
        for role in ['heading', 'hand']:
            require(resolve(root, c['fonts'][role]).is_file(), f'Missing {role} font')
        for sid, source in c['sources'].items():
            require(re.fullmatch(r'[A-Za-z0-9_-]+', sid), 'Unsafe source ID')
            p = resolve(root, source['path'])
            with Image.open(p) as im:
                require(im.format == 'PNG', f'Source {sid} must be actual PNG, not renamed JPEG')
                source['_size'] = im.size
            require(source['theme'] in ['paper', 'dark'], 'Source theme must be paper/dark')
    for sid, source in c['sources'].items():
        require(source.get('accent', 'yellow') in ['yellow', 'coral'], f'Source {sid}: accent must be yellow/coral')
    protected = c.get('protected_intervals', [])
    for p in protected:
        require(interval(*p, v['frames']), 'Invalid protected interval')
    ids, occupied = set(), []
    for s in c['scenes']:
        require(re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', s['id']), 'Unsafe scene ID')
        require(s['id'] not in ids, f'Duplicate scene: {s["id"]}')
        ids.add(s['id'])
        require(interval(s['start'], s['end'], v['frames']), f'Bad interval: {s["id"]}')
        require(s['width'] > 0 and s['height'] > 0 and s['width'] % 2 == 0 and s['height'] % 2 == 0, 'Bad panel dimensions')
        require(s['theme'] in ['paper', 'dark'], 'Bad scene theme')
        # SketchPanel reads data.title.length; a missing title only fails inside the browser render.
        require(isinstance(s.get('title'), str) and isinstance(s.get('subtitle'), str),
                f'Scene {s["id"]}: title and subtitle must be strings (use "" to leave empty)')
        layout = s.get('titleLayout')
        if layout is not None:
            require(isinstance(layout.get('size'), (int, float)) and layout['size'] > 0 and
                    isinstance(layout.get('y'), (int, float)) and 0 < layout['y'] < s['height'] and
                    layout.get('align', 'center') in ['center', 'left'], f'Scene {s["id"]}: bad titleLayout')
        require(bool(s['placements']), 'Scene needs at least one placement')
        s.setdefault('labels', [])
        duration = (s['end'] - s['start']) / v['fps']
        names = set()
        for a in s['arts']:
            require(a['name'] not in names, 'Duplicate art name')
            names.add(a['name'])
            require(a['source'] in c['sources'], 'Unknown source')
            require(0 <= a['start'] and a['duration'] > 0 and a['start'] + a['duration'] <= duration + 1e-6,
                    f'Incomplete drawing at scene end: {s["id"]}/{a["name"]}')
            if a.get('until') is not None:
                require(a['start'] + a['duration'] <= a['until'] <= duration, 'Art disappears before drawing completes')
            require(box(a['dest'], s['width'], s['height']), 'Art destination outside panel')
            require(a['crop'][2] > 0 and a['crop'][3] > 0, 'Empty crop')
            require(abs((a['dest'][2] / a['dest'][3]) / (a['crop'][2] / a['crop'][3]) - 1) < .005,
                    'Art destination stretches original illustration')
            if files:
                require(box(a['crop'], *c['sources'][a['source']]['_size']), 'Crop outside source')
            require(all(type(x) is int for x in a['crop']), 'Crop pixels must be integers')
        for label in s.get('labels', []):
            require(0 <= label['start'] < duration, 'Label starts after scene')
            require(0 <= label['x'] <= s['width'] and 0 <= label['y'] <= s['height'], 'Label anchor outside panel')
            require(label.get('align', 'center') in ['center', 'left'], 'Label align must be center/left')
        for p in s['placements']:
            require(interval(p['start'], p['end'], v['frames']), 'Invalid placement')
            require(s['start'] <= p['start'] < p['end'] <= s['end'], 'Placement outside scene')
            require(box(p['rect'], v['width'], v['height']), 'Placement outside frame')
            require(all(type(n) is int for n in p['rect']), 'Placement pixels must be integers')
            require(type(p.get('shadow', False)) is bool, 'Placement shadow must be true or false')
            w, h = p['rect'][2:]
            require(abs((w / h) / (s['width'] / s['height']) - 1) < .005, 'Placement stretches source panel')
            require(all(not overlap([p['start'], p['end']], q) for q in protected), 'Placement overlaps protected footage')
            require(all(not overlap([p['start'], p['end']], q) for q in occupied), 'Overlapping panel placements')
            occupied.append([p['start'], p['end']])
            band = c.get('caption_band')
            if band:
                x, y, w, h = p['rect']; bx, by, bw, bh = band
                require(not (x < bx + bw and bx < x + w and y < by + bh and by < y + h), 'Panel covers caption band')
    for logo in c.get('branding', {}).get('logos', []):
        require(box(logo['rect'], v['width'], v['height']), 'Logo outside frame')
        if files:
            require(resolve(root, logo['path']).is_file(), 'Missing logo')
        for a, b in logo.get('intervals', [[0, v['frames']]]):
            require(interval(a, b, v['frames']), 'Invalid logo interval')
    inputs = [c['_base']] + [resolve(root, x['path']) for x in c['sources'].values()]
    for p in inputs:
        require(p != c['_output'] and c['_output'] not in p.parents, 'Inputs must not be in output')
    return c
