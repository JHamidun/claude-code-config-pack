"""Contact sheet from stills: python render/sheet.py <out.png> <cols> <scale> <files...>
    e.g. python render/sheet.py st/sheet.png 4 0.25 st/p_*.png
Cell size = first image x scale; every frame keeps its aspect ratio (a 9:16 frame next to 16:9 ones is letterboxed,
not squashed). The label (file name part after the last '_', i.e. the time) sits in a strip ABOVE each frame, so it never
covers the frame corner (titles live there)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

if len(sys.argv) < 5:
    raise SystemExit(__doc__)
out, cols, s = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
fs = sys.argv[4:]
ims = [Image.open(f).convert('RGB') for f in fs]
w, h = ims[0].size
W, H = int(w * s), int(h * s)
rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (cols * W + (cols + 1) * 8, rows * (H + 26) + 8), '#444')
d = ImageDraw.Draw(sh)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = 8 + (i % cols) * (W + 8), 8 + (i // cols) * (H + 26)
    k = min(W / im.width, H / im.height)
    iw, ih = max(1, int(im.width * k)), max(1, int(im.height * k))
    sh.paste(im.resize((iw, ih)), (x + (W - iw) // 2, y + 18 + (H - ih) // 2))
    d.text((x, y + 2), Path(f).name.split('_')[-1].replace('.png', ' s'), fill='#fff')
Path(out).parent.mkdir(parents=True, exist_ok=True)
sh.save(out)
print('->', out)
