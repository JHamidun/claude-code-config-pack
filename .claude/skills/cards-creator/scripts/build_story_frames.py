"""Adapt 4:5 cards (1080x1350 @2x) -> 9:16 story frames (1080x1920 @2x) with NO horizontal crop.
Each card is centered; top/bottom bands are filled with the card's own edge color (seamless),
so Telegram shows the full card width with nothing cut off. Safe-zone aware (Telegram overlays
~top header + bottom reply area land on the empty bands, never on content)."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image, ImageFilter
import numpy as np
LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS

# CWD-relative by default (matches render_cards.py output ./png); override via argv.


# Работа — в main(), под `if __name__ == "__main__"`. На верхнем уровне модуля
# только определения: импорт этого файла (линтер с исполнением, автодополнение
# в редакторе, `python -c "import ..."`) не должен ничего запускать и писать.
def main():
    SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), 'png')
    OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.getcwd(), 'story_png')
    os.makedirs(OUT, exist_ok=True)

    TARGET_W = 2160          # 1080 @2x
    TARGET_H = 3840          # 1920 @2x (9:16)


    def edge_color(arr, top=True):
        """Median color of the outermost rows — the card's own background at that edge."""
        rows = arr[2:14, :, :3] if top else arr[-14:-2, :, :3]
        med = np.median(rows.reshape(-1, 3), axis=0)
        return tuple(int(x) for x in med)


    for i in range(1, 10):
        p = f'{SRC}/series-{i:02d}.png'
        im = Image.open(p).convert('RGB')
        w, h = im.size
        # normalize card width to TARGET_W (preserve aspect)
        if w != TARGET_W:
            nh = round(h * TARGET_W / w)
            im = im.resize((TARGET_W, nh), LANCZOS)
            w, h = TARGET_W, nh
        arr = np.asarray(im)
        top_c, bot_c = edge_color(arr, True), edge_color(arr, False)

        y = (TARGET_H - h) // 2
        if y < 0:  # card taller than frame -> scale down to fit height
            scale = TARGET_H / h
            im = im.resize((round(w * scale), TARGET_H), LANCZOS)
            w, h = im.size
            canvas = Image.new('RGB', (TARGET_W, TARGET_H), top_c)
            canvas.paste(im, ((TARGET_W - w) // 2, 0))
        else:
            canvas = Image.new('RGB', (TARGET_W, TARGET_H), top_c)
            # seamless bands: stretch the card's edge rows to fill, then soften streaks
            if y > 0:
                top_band = im.crop((0, 0, w, 8)).resize((w, y), LANCZOS).filter(ImageFilter.GaussianBlur(14))
                canvas.paste(top_band, (0, 0))
                bot_h = TARGET_H - (y + h)
                bot_band = im.crop((0, h - 8, w, h)).resize((w, bot_h), LANCZOS).filter(ImageFilter.GaussianBlur(14))
                canvas.paste(bot_band, (0, y + h))
            canvas.paste(im, (0, y))
        canvas.save(f'{OUT}/story-{i:02d}.png')
        print(f'story-{i:02d}: card {w}x{h} -> {TARGET_W}x{TARGET_H}  top{top_c} bot{bot_c}', flush=True)

    print('DONE -> story_png/')


if __name__ == "__main__":
    main()
