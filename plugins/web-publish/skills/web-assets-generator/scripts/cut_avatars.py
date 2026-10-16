# -*- coding: utf-8 -*-
"""Cut backgrounds from portraits → transparent PNG for banner avatar circles.

Recipe: birefnet-portrait + alpha_matting + largest-connected-component (drops stray
objects/second person) + gaussian feather (smooth edges). Falls back to u2net_human_seg
if the birefnet model can't load. Output PNGs drop straight into banner-template.html
.host-pic circles. deps: rembg, pillow, numpy, scipy (scipy optional — LCC skipped without).

EDIT the SRC list: (input_photo, output_png) pairs. Then: python cut_avatars.py
"""
import sys

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Работа — в main(), под `if __name__ == "__main__"`. На верхнем уровне модуля
# только определения: импорт этого файла (линтер с исполнением, автодополнение
# в редакторе, `python -c "import ..."`) не должен ничего запускать и писать.
def main():
    SRC = [
        (r"path/to/portrait_1.jpg", r"path/to/avatar_1.png"),
        (r"path/to/portrait_2.jpg", r"path/to/avatar_2.png"),
    ]

    try:
        session = new_session("birefnet-portrait")
        print("model: birefnet-portrait")
    except Exception as e:
        print("birefnet failed (%s), falling back to u2net_human_seg" % e)
        session = new_session("u2net_human_seg")

    for src, dst in SRC:
        img = Image.open(src).convert("RGB")
        out = remove(img, session=session, alpha_matting=True,
                     alpha_matting_foreground_threshold=240,
                     alpha_matting_background_threshold=15,
                     alpha_matting_erode_size=8)
        # largest connected component on alpha + gaussian feather
        a = np.array(out.getchannel("A"))
        try:
            from scipy import ndimage
            lab, n = ndimage.label(a > 60)
            if n > 1:
                sizes = ndimage.sum(a > 60, lab, range(1, n + 1))
                keep = (np.argmax(sizes) + 1)
                a = np.where(lab == keep, a, 0).astype("uint8")
        except ImportError:
            pass
        am = Image.fromarray(a).filter(ImageFilter.GaussianBlur(1.2))
        out.putalpha(am)
        out.save(dst)
        print("saved", dst, out.size)


if __name__ == "__main__":
    main()
