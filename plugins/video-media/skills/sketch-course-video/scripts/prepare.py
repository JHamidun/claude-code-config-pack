"""Build original-pixel reveal masks and isolated Remotion entrypoint."""
import copy
import hashlib
import json
import shutil
from pathlib import Path
import cv2
import numpy as np
from common import SKILL, digest, resolve, write_json, stop_check
from trace import trace_paths, order_strokes, color_paths


def finish_paths(mask, x, y):
    grown = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(grown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result = []
    for c in contours:
        if cv2.contourArea(c) < 3:
            continue
        points = cv2.approxPolyDP(c, .5, True).reshape(-1, 2)
        result.append('M' + ' L'.join(f'{a+x},{b+y}' for a, b in points) + ' Z')
    return ' '.join(result)


ACCENT_RULES = ('yellow', 'coral')


def clean(mask, minimum=6):
    """Drop specks smaller than `minimum` pixels (compression noise around coral edges)."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    keep = np.zeros(count, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= minimum
    return keep[labels]


def split_colors(crop, dark, rule='yellow'):
    """Separate contour ink from accent fill.

    'yellow' is the lesson rule, unchanged. 'coral' is for red or dark-orange accents
    (e.g. #E8643C): they never pass the yellow test (G>110), so with the yellow rule they
    would not be drawn at all — on a paper panel they even fall into the ink and get traced
    as contour without hatching.
    """
    r, g, b = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
    chroma = crop.max(axis=2) - crop.min(axis=2)
    if rule == 'coral':
        accent = (r > 155) & ((r - g) > 28) & ((r - b) > 48)
        ink = ((crop.min(axis=2) > 142) & (chroma < 65)) if dark else ((crop.mean(axis=2) < 145) & (chroma < 70))
        return clean(ink & ~accent), clean(accent)
    accent = (r > 155) & (g > 110) & ((r - b) > 55)
    ink = ((crop.min(axis=2) > 82) & (chroma < 85)) if dark else (crop.mean(axis=2) < 180) & ~accent
    return ink, accent


def shade_mask(crop, dark, rule, ink, accent):
    """Mid-grey fills revealed by the final fade, not traced as strokes.

    The coral dark rule keeps only bright contour ink (min>142), so a grey-filled shape (an
    arm, a header bar) fell outside the finish silhouette and was cut out with a ragged edge
    while it held on screen. Drop shadows composited over black stay near-black and are not
    picked up. The yellow rule is untouched.
    """
    if rule != 'coral' or not dark:
        return np.zeros(ink.shape, dtype=bool)
    chroma = crop.max(axis=2) - crop.min(axis=2)
    return clean((crop.min(axis=2) > 45) & (chroma < 60) & ~ink & ~accent)


BACKDROP = {'paper': (248, 243, 236), 'dark': (0, 0, 0)}


def load_source(path, theme):
    """RGB pixels for mask computation; the PNG itself is shipped untouched.

    A generated asset sheet may be RGBA with most of the page transparent and dark RGB left
    underneath (seen in practice: 64% of pixels alpha<90, RGB ~ (94,86,80)). Read
    without alpha, that hidden colour counts as ink on a paper panel and the whole empty page
    gets traced. Composite over the panel colour first, exactly what the viewer will see.
    """
    raw = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise ValueError(f'Unreadable image: {path}')
    if raw.ndim == 2:
        return cv2.cvtColor(raw, cv2.COLOR_GRAY2RGB)
    if raw.shape[2] == 4:
        rgba = cv2.cvtColor(raw, cv2.COLOR_BGRA2RGBA).astype(float)
        alpha = rgba[:, :, 3:4] / 255.0
        back = np.array(BACKDROP[theme], dtype=float)
        return (rgba[:, :, :3] * alpha + back * (1 - alpha)).round().astype(np.uint8)
    return cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)


def mask_data(img, item, dark, rule='yellow'):
    x, y, w, h = item['crop']
    crop = img[y:y+h, x:x+w].astype(float)
    ink, accent = split_colors(crop, dark, rule)
    shade = shade_mask(crop, dark, rule, ink, accent)
    for ex, ey, ew, eh in item.get('exclude', []):
        xa, xb, ya, yb = max(0, ex-x), min(w, ex+ew-x), max(0, ey-y), min(h, ey+eh-y)
        if xa < xb and ya < yb:
            ink[ya:yb, xa:xb] = False; accent[ya:yb, xa:xb] = False; shade[ya:yb, xa:xb] = False
    outlines = order_strokes(trace_paths(ink, x, y))
    fill = color_paths(accent, x, y)
    if not outlines and not fill:
        raise ValueError(f'No ink found in {item["name"]}; check crop/theme/palette')
    paths = []
    for group, portion, offset, color in [(outlines, .74, 0, False), (fill, .24, .76, True)]:
        total = sum(max(p['length'], 12) for p in group)
        cursor = offset
        for p in group:
            duration = portion * max(p['length'], 12) / total
            paths.append(dict(points=p['points'], width=p['width'], start=cursor, duration=duration, color=color))
            cursor += duration
    return dict(paths=paths, finish=finish_paths(ink | accent | shade, x, y), sourceWidth=img.shape[1], sourceHeight=img.shape[0])


def prepare(c):
    name = 'sketch-' + hashlib.sha256(str(c['_config']).encode()).hexdigest()[:12]
    runtime = c['_runtime']
    source, public = runtime / name, runtime / 'public' / name
    source.mkdir(parents=True, exist_ok=True); public.mkdir(parents=True, exist_ok=True)
    engine = source / 'SketchPanel.tsx'
    shutil.copy2(SKILL / 'assets/remotion/SketchPanel.tsx', engine)
    for role in ['heading', 'hand']:
        shutil.copy2(resolve(c['_root'], c['fonts'][role]), public / f'{role}.ttf')
    images, hashes = {}, {}
    for key, art in c['sources'].items():
        stop_check(c['_root'])
        path = resolve(c['_root'], art['path'])
        shutil.copy2(path, public / f'{key}.png')
        # imdecode handles Unicode paths on Windows reliably.
        images[key] = load_source(path, art['theme'])
        hashes[key] = digest(path)
    cache = {}
    for spec in c['scenes']:
        stop_check(c['_root'])
        s = copy.deepcopy(spec)
        s['assetRoot'] = name
        for a in s['arts']:
            a.setdefault('until', None); a.setdefault('pen', False)
            src = c['sources'][a['source']]
            key = (a['source'], tuple(a['crop']), str(a.get('exclude', [])))
            if key not in cache:
                cache[key] = mask_data(images[a['source']], a, src['theme'] == 'dark', src.get('accent', 'yellow'))
            a.update(cache[key]); a['sourceHash'] = hashes[a['source']]
        for label in s.get('labels', []):
            for k, default in [('until', None), ('heading', False), ('accent', False), ('size', 30)]:
                label.setdefault(k, default)
        write_json(source / f'{s["id"]}.json', s)
    entry = "import React from 'react';\nimport {Composition,registerRoot} from 'remotion';\nimport {SketchPanel,Scene} from './SketchPanel';\n"
    for i, s in enumerate(c['scenes']):
        entry += f"import scene{i} from './{s['id']}.json';\n"
    entry += 'registerRoot(()=> <>\n'
    for i, s in enumerate(c['scenes']):
        entry += f'<Composition id="{s["id"]}" component={{()=> <SketchPanel data={{scene{i} as unknown as Scene}}/>}} width={{{s["width"]}}} height={{{s["height"]}}} fps={{{c["video"]["fps"]}}} durationInFrames={{{s["end"]-s["start"]}}}/>\n'
    entry += '</>);\n'
    (source / 'index.tsx').write_text(entry, encoding='utf-8')
    write_json(source / 'tsconfig.json', {'compilerOptions': {'target': 'ES2020', 'module': 'commonjs', 'jsx': 'react-jsx',
        'lib': ['ES2020', 'DOM', 'DOM.Iterable'], 'moduleResolution': 'node', 'resolveJsonModule': True, 'esModuleInterop': True,
        'strict': True, 'skipLibCheck': True, 'noEmit': True}, 'include': ['*.tsx', '*.json']})
    dependencies = {str(p.relative_to(source)): digest(p) for p in source.glob('*') if p.is_file()}
    dependencies.update({f'public/{p.name}': digest(p) for p in public.iterdir() if p.is_file()})
    write_json(c['_work'] / 'prepared.json', {'entry': str(source / 'index.tsx'), 'asset_root': str(public),
        'hashes': dependencies, 'original_hashes': hashes})
    return source / 'index.tsx'
