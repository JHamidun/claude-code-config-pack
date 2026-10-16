"""Cut character from white background + tight crop bounding box.

Telegram static stickers accept rectangular PNG ≤512px on either side, but
gpt-image-2 outputs come with white background and lots of padding. This
script: rembg (background removal) → getbbox tight crop → resize so longest
side = 512px.

Usage:
    python tight_crop_alpha.py --in ./emotions/01-fire.png --out ./final/01-fire.webp
    python tight_crop_alpha.py --in-dir ./emotions/ --out-dir ./final/
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import sys, io, os, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from PIL import Image
from rembg import remove, new_session


def process(in_path: str, out_path: str, session, target_side: int = 512,
            fmt: str = 'webp'):
    """rembg → tight crop → resize → save."""
    with open(in_path, 'rb') as f:
        data = f.read()
    cut = remove(data, session=session)
    img = Image.open(io.BytesIO(cut)).convert('RGBA')
    # Tight crop based on alpha bbox
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    # Resize so longest side = target_side, keep aspect ratio
    w, h = img.size
    if max(w, h) > target_side:
        scale = target_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    if fmt == 'webp':
        img.save(out_path, format='WEBP', quality=95, method=6)
    else:
        img.save(out_path, format='PNG', optimize=True)
    return img.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', help='Single input PNG')
    ap.add_argument('--in-dir', help='Batch: input directory of PNGs')
    ap.add_argument('--out', help='Single output')
    ap.add_argument('--out-dir', help='Batch: output directory')
    ap.add_argument('--target', type=int, default=512)
    ap.add_argument('--format', choices=['webp', 'png'], default='webp')
    ap.add_argument('--model', default='isnet-general-use')
    args = ap.parse_args()
    sess = new_session(args.model,
                       providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    if args.inp and args.out:
        sz = process(args.inp, args.out, sess, args.target, args.format)
        print(f'OK {args.out} {sz}')
        return
    if not (args.in_dir and args.out_dir):
        raise SystemExit('Need --in/--out OR --in-dir/--out-dir')
    os.makedirs(args.out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(args.in_dir)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')))
    print(f'Batch: {len(files)} files')
    for i, fn in enumerate(files):
        out = os.path.join(args.out_dir, os.path.splitext(fn)[0] + f'.{args.format}')
        if os.path.exists(out):
            print(f'[{i+1}/{len(files)}] {fn} SKIP'); continue
        try:
            sz = process(os.path.join(args.in_dir, fn), out, sess, args.target, args.format)
            print(f'[{i+1}/{len(files)}] {fn} → {os.path.basename(out)} {sz}')
        except Exception as e:
            print(f'[{i+1}/{len(files)}] {fn} FAIL {e}')


if __name__ == '__main__':
    main()
