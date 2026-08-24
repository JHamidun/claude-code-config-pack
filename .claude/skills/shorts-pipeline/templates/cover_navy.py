"""Generate vertical 1080x1920 shorts thumbnails via PIL.

Layout: navy gradient bg + matrix dots + avatar circle (small, необязателен) + headline + "AI NEWS" badge + подпись бренда ($SHORTS_BRAND).
No GPT cost — PIL renders text directly. ~50ms per cover.
"""
import os, sys, json, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')

W, H = 1080, 1920
NAVY_DARK = (1, 3, 52)       # #010334
NAVY_LIGHT = (4, 17, 105)    # gradient lighter
CYAN = (0, 220, 255)
YELLOW = (250, 206, 0)
WHITE = (255, 255, 255)
RED = (220, 33, 33)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import config

OUT_DIR = str(config.COVERS_DIR)   # каталог создаётся при запуске, не при импорте

def get_font(size, bold=True):
    """Try several font paths."""
    candidates = [
        r'C:\Windows\Fonts\arialbd.ttf' if bold else r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\segoeuib.ttf' if bold else r'C:\Windows\Fonts\segoeui.ttf',
    ]
    for p in candidates:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()


def gradient_bg():
    """Navy radial gradient."""
    img = Image.new('RGB', (W, H), NAVY_DARK)
    px = img.load()
    cx, cy = W // 2, H // 3
    max_d = math.hypot(cx, cy)
    for y in range(H):
        for x in range(0, W, 4):  # step 4 for speed
            d = math.hypot(x - cx, y - cy) / max_d
            t = max(0, 1 - d * 0.7)  # 0..1
            r = int(NAVY_DARK[0] + (NAVY_LIGHT[0] - NAVY_DARK[0]) * t)
            g = int(NAVY_DARK[1] + (NAVY_LIGHT[1] - NAVY_DARK[1]) * t)
            b = int(NAVY_DARK[2] + (NAVY_LIGHT[2] - NAVY_DARK[2]) * t)
            for dx in range(4):
                if x+dx < W: px[x+dx, y] = (r, g, b)
    return img


def matrix_dots(img):
    """Subtle digital dots."""
    draw = ImageDraw.Draw(img, 'RGBA')
    rng = random.Random(42)
    for _ in range(800):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        r = rng.randint(1, 3)
        alpha = rng.randint(20, 80)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*CYAN, alpha))
    return img


def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = ' '.join(cur + [w])
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur.append(w)
        else:
            if cur: lines.append(' '.join(cur))
            cur = [w]
    if cur: lines.append(' '.join(cur))
    return lines


def render_shorts_cover(title, out_path, hero_img=None):
    """Render one shorts cover."""
    img = Image.new('RGB', (W, H), NAVY_DARK)
    # Simpler bg: vertical gradient
    px = img.load()
    for y in range(H):
        t = (y / H) * 0.8
        r = int(NAVY_DARK[0] + (NAVY_LIGHT[0] - NAVY_DARK[0]) * t)
        g = int(NAVY_DARK[1] + (NAVY_LIGHT[1] - NAVY_DARK[1]) * t)
        b = int(NAVY_DARK[2] + (NAVY_LIGHT[2] - NAVY_DARK[2]) * t)
        for x in range(W): px[x, y] = (r, g, b)

    img = matrix_dots(img)
    draw = ImageDraw.Draw(img, 'RGBA')

    # Top badge "AI NEWS"
    badge_font = get_font(72)
    badge_text = 'AI NEWS'
    badge_bbox = draw.textbbox((0,0), badge_text, font=badge_font)
    bw = badge_bbox[2] - badge_bbox[0]
    bh = badge_bbox[3] - badge_bbox[1]
    bx = (W - bw) // 2
    by = 100
    draw.rectangle([bx-30, by-15, bx+bw+30, by+bh+15], fill=RED)
    draw.text((bx, by-10), badge_text, font=badge_font, fill=WHITE)

    # Headline
    title_font = get_font(80)
    pad = 80
    lines = wrap_text(title.upper(), title_font, W - 2*pad, draw)
    line_h = title_font.getbbox('A')[3] + 20

    # Center vertically
    title_block_h = line_h * len(lines)
    title_top = (H - title_block_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=title_font)
        lw = bbox[2] - bbox[0]
        lx = (W - lw) // 2
        ly = title_top + i * line_h
        # Black outline + white fill
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,3),(-3,3),(3,-3)]:
            draw.text((lx+dx, ly+dy), line, font=title_font, fill=(0,0,0))
        draw.text((lx, ly), line, font=title_font, fill=WHITE)

    # Подпись бренда внизу. Пусто ($SHORTS_BRAND не задан) — блока просто нет:
    # чужое имя на своей обложке хуже, чем отсутствие подписи.
    brand = config.BRAND
    if brand:
        brand_font = get_font(44)
        bbox = draw.textbbox((0,0), brand, font=brand_font)
        bw = bbox[2] - bbox[0]
        draw.text(((W-bw)//2, H-130), brand, font=brand_font, fill=CYAN)

    # Save
    img.save(out_path, 'PNG', optimize=True)
    return out_path


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    snapshot = config.CHANNEL_SNAPSHOT
    if not snapshot.exists():
        print(f'Нет снимка канала ({snapshot}) — сначала scripts/inventory.py')
        sys.exit(1)

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    with open(snapshot, encoding='utf-8') as f: vids = json.load(f)
    shorts = [v for v in vids if v.get('is_short')]
    top = sorted(shorts, key=lambda v: v.get('views', 0), reverse=True)[:n]

    print(f'Rendering top {len(top)} shorts covers...')
    for i, v in enumerate(top, 1):
        out = os.path.join(OUT_DIR, f'{v["id"]}.png')
        if os.path.exists(out): continue
        render_shorts_cover(v['title'], out)
        if i % 10 == 0:
            print(f'  {i}/{len(top)} done')
    print('Done.')
