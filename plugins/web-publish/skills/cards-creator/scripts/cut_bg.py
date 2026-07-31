#!/usr/bin/env python3
"""
Cut background off card illustrations -> transparent PNG cutouts for integrated/bleed placement.

WHY: gpt-image-2 does NOT support `background:transparent` (returns 400). So generate the
illustration normally (gen_card_images.py), then remove the background here with rembg.
On flat vector art the `isnet-general-use` model + alpha matting gives clean edges; we then
tight-crop to the alpha bbox so the cutout can bleed to a card edge without a box.

Place the result with NO border / NO box (object-fit: contain) on the cream card, or on a
navy band, or bleeding off an edge — that's the reference-channel "integrated cutout" look.

Usage:
    pip install rembg onnxruntime    # once (downloads model on first run, CPU is fine)
    python cut_bg.py img1.png img2.png ...      # writes <name>_t.png next to each input
"""
import sys
from rembg import remove, new_session
from PIL import Image

session = new_session("isnet-general-use")  # better than u2net on graphics/illustration


def cut(path):
    im = Image.open(path).convert("RGBA")
    out = remove(im, session=session, alpha_matting=True,
                 alpha_matting_foreground_threshold=240,
                 alpha_matting_background_threshold=20)
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)          # tight crop so it can bleed to an edge
    dst = path.rsplit(".", 1)[0] + "_t.png"
    out.save(dst)
    print(f"cut {path} -> {dst} {out.size}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        cut(p)
