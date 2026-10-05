"""Frame measurements for code-cartoon QA: stills from render/still.py or JPEG frames kept by render.py --keep.

    python qa_frames.py t 240,241,242,243                        exact times of video frames f/24 for still.py (10 decimals)
    python qa_frames.py cuts <timing.js|timing.json>              frame pairs around every scene cut: last before / first after
    python qa_frames.py mouth <timing.js|timing.json> [--n 4]     moments with the mouth wide open / shut while the voice runs
    python qa_frames.py diff A B [x0,y0,x1,y1] [--thr 30] [--png out.png]   changed pixels between two frames (box optional)
    python qa_frames.py ink A [--thr 40]                          share of «ink»: pixels far from the frame's median colour
    python qa_frames.py cap A x0,y0,x1,y1 [--thr 60]              height of the ink inside a box drawn around ONE capital letter
    python qa_frames.py fsheet out.jpg <cols> <tile_w> <dir.frames> f1,f2,...  contact sheet from kept frames, labels above tiles
    python qa_frames.py guides A out.png                           copy of a frame with the safe lines drawn on it:
                                                                  red = 85 % line (no text below), yellow = 5 % box, cyan = 10 % box
Boxes are output pixels of the frame: x0,y0 top-left, x1,y1 bottom-right.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

FPS = 24


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def gray(p, box=None):
    a = np.asarray(Image.open(p).convert('L'), dtype=np.int16)
    if box:
        x0, y0, x1, y1 = box
        a = a[y0:y1, x0:x1]
    return a


def parse_box(s):
    return [int(v) for v in s.split(',')] if s and ',' in s and not s.startswith('-') else None


def timing(path):
    src = Path(path).read_text(encoding='utf-8')
    return json.loads(src.split('=', 1)[1].rstrip().rstrip(';') if src.lstrip().startswith('window') else src)


cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 't':
    print(','.join(f'{int(f) / FPS:.10f}' for f in sys.argv[2].split(',')))
elif cmd == 'cuts':
    tm = timing(sys.argv[2])
    fps = tm.get('fps', FPS)
    for prev, sc in zip(tm['scenes'], tm['scenes'][1:]):
        f = math.ceil(sc['start'] * fps - 1e-9)              # first frame of the new scene
        print(f"{prev['name']} -> {sc['name']}: frames {f - 1}/{f}  t={(f - 1) / fps:.10f},{f / fps:.10f}")
elif cmd == 'mouth':
    tm = timing(sys.argv[2])
    m, fps, n = tm['mouth'], tm.get('fps', FPS), int(arg('--n', 4))
    speech = [(w['s'], w['e']) for w in tm['words']]
    inside = [f for f in range(len(m)) if any(s <= f / fps <= e for s, e in speech)]
    top = sorted(inside, key=lambda f: -m[f])
    picked = []
    for f in top:                                             # spread the picks at least 2 s apart
        if all(abs(f - g) > 2 * fps for g in picked):
            picked.append(f)
        if len(picked) == n:
            break
    shut = [f for f in inside if m[f] < 0.05][::max(1, len([f for f in inside if m[f] < 0.05]) // n)][:n]
    print('open :', ','.join(f'{f / fps:.10f}' for f in sorted(picked)), '| mouth', [round(m[f], 2) for f in sorted(picked)])
    print('shut :', ','.join(f'{f / fps:.10f}' for f in shut), '| mouth', [round(m[f], 2) for f in shut])
    print(f'mouth frames {len(m)}, expected ceil(duration*fps) = {math.ceil(tm["duration"] * fps)}')
elif cmd == 'diff':
    box = parse_box(sys.argv[4]) if len(sys.argv) > 4 else None
    a, b = gray(sys.argv[2], box), gray(sys.argv[3], box)
    d = np.abs(a - b) > arg('--thr', 30)
    ys, xs = np.nonzero(d)
    bb = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
    print(f'changed px {int(d.sum())} of {d.size} ({d.mean() * 100:.3f} %), bbox {bb}')
    if '--png' in sys.argv:                                   # what changed: frame B dimmed, changed pixels red
        vis = np.stack([b // 3] * 3, -1).astype(np.uint8)
        vis[d] = (255, 40, 40)
        Image.fromarray(vis).save(sys.argv[sys.argv.index('--png') + 1])
elif cmd == 'ink':
    a = gray(sys.argv[2])
    print(f'ink share {(np.abs(a - np.median(a)) > arg("--thr", 40)).mean() * 100:.2f} %')
elif cmd == 'cap':
    a = gray(sys.argv[2], parse_box(sys.argv[3]))
    ink = np.abs(a - np.median(a)) > arg('--thr', 60)
    rows = np.nonzero(ink.sum(1) >= 2)[0]                     # rows with 2+ ink pixels: single specks ignored
    print(f'ink height {int(rows.max() - rows.min() + 1) if len(rows) else 0} px')
elif cmd == 'fsheet':
    out, cols, tw, d = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), Path(sys.argv[5])
    fr = [int(f) for f in sys.argv[6].split(',')]
    ims = [Image.open(d / f'f{f:05d}.jpg').convert('RGB') for f in fr]
    th = round(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw + (cols + 1) * 8, rows * (th + 26) + 8), '#444')
    dr = ImageDraw.Draw(sh)
    for i, (f, im) in enumerate(zip(fr, ims)):
        x, y = 8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 26)
        sh.paste(im.resize((tw, th)), (x, y + 18))
        dr.text((x, y + 2), f'f{f}  {f / FPS:.3f} s', fill='#fff')   # label in the strip ABOVE the tile, never on the frame
    sh.save(out, quality=88)
    print(out, sh.size)
elif cmd == 'guides':
    im = Image.open(sys.argv[2]).convert('RGB')
    w, h = im.size
    dr = ImageDraw.Draw(im)
    for k, col in ((0.05, (255, 210, 0)), (0.10, (0, 200, 255))):
        dr.rectangle([int(w * k), int(h * k), int(w * (1 - k)), int(h * (1 - k))], outline=col, width=3)
    dr.line([(0, int(h * 0.85)), (w, int(h * 0.85))], fill=(255, 40, 40), width=4)
    im.save(sys.argv[3])
    print(sys.argv[3], f'85 % line at y = {int(h * 0.85)} px')
else:
    raise SystemExit(__doc__)
