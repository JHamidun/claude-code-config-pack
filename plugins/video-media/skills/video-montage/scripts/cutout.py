#!/usr/bin/env python3
"""Убрать однотонный фон у рисунка персонажа.

Картинки поз приходят от генератора с белым фоном. Пока он есть, персонаж стоит на
экране в белом прямоугольнике: фон сцены серый в сетку, и граница картинки читается
как рамка вокруг героя. В ролике это заметнее липсинка — глаз сразу видит вклеенную
картинку.

Фон убирается заливкой от краёв, а не «удалить всё белое»: белое есть и внутри
рисунка — зубы, белки глаз, светлая одежда. Заливка идёт только по связной области,
дотягивающейся до края кадра, поэтому внутренние светлые пятна остаются.

    python cutout.py ./poses -o ./poses_cut
    python cutout.py ./poses -o ./poses_cut --tolerance 26
"""
from __future__ import annotations
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


import argparse
import pathlib
import sys
from collections import deque


def cut(src: pathlib.Path, dst: pathlib.Path, tol: int, feather: float,
        outline: int = 0) -> tuple[int, int]:
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    px = im.load()
    assert px is not None

    # Цвет фона берём с углов: он надёжнее «просто белого» — генератор часто отдаёт
    # чуть тёплый или чуть серый фон, и жёсткое сравнение с белым не сработает.
    corners = [px[0, 0], px[W - 1, 0], px[0, H - 1], px[W - 1, H - 1]]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))

    def near(c) -> bool:   # пиксель RGBA из im.load()
        return (abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2])) <= tol * 3

    # Заливка от всех краёв разом. Персонаж обычно упирается в нижний край, но это не
    # мешает: заливка обходит его по фону, а сквозь него не проходит.
    seen = bytearray(W * H)
    q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if near(px[x, y]):
                q.append((x, y)); seen[y * W + x] = 1
    for y in range(H):
        for x in (0, W - 1):
            if near(px[x, y]) and not seen[y * W + x]:
                q.append((x, y)); seen[y * W + x] = 1

    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx] and near(px[nx, ny]):
                seen[ny * W + nx] = 1
                q.append((nx, ny))

    mask = Image.new("L", (W, H), 255)
    mp = mask.load()
    assert mp is not None
    cleared = 0
    for y in range(H):
        row = y * W
        for x in range(W):
            if seen[row + x]:
                mp[x, y] = 0
                cleared += 1
    # Размыть край: резкая граница по пикселю даёт зубчатый контур на светлом фоне.
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    im.putalpha(mask)

    if outline:
        im = add_outline(im, mask, outline)
    im.save(dst)
    return cleared, W * H


def add_outline(im, mask, width: int):
    """Белая кайма по контуру — тот самый вид наклейки.

    Отличие наклейки от просто вырезанной картинки — именно кайма: она отделяет
    предмет от любого фона и держит его читаемым поверх пёстрого кадра. Без неё
    вырезанный объект сливается со сценой, и приходится подкладывать плашку — а
    плашка превращает наклейку в карточку.

    Контур получается расширением маски: маска размывается, всё сколько-нибудь
    заметное берётся за единицу — получается силуэт крупнее исходного.
    """
    from PIL import Image, ImageFilter
    W, H = im.size
    grown = mask.filter(ImageFilter.GaussianBlur(width)).point(
        lambda v: 255 if v > 28 else 0).filter(ImageFilter.GaussianBlur(0.8))
    # Слой каймы — сплошной белый, видимый только внутри расширенного силуэта.
    halo = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    halo.putalpha(grown)
    # Кайма под картинкой, картинка поверх: так контур виден только снаружи предмета.
    out = Image.alpha_composite(halo, im)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="папка с картинками")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--tolerance", type=int, default=22,
                    help="насколько цвет может отличаться от фона, 0…255")
    ap.add_argument("--feather", type=float, default=0.8, help="размытие края в пикселях")
    ap.add_argument("--outline", type=int, default=0,
                    help="ширина белой каймы вокруг предмета; 0 — без каймы")
    a = ap.parse_args()

    src, dst = pathlib.Path(a.src), pathlib.Path(a.out)
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.png"))
    if not files:
        raise SystemExit(f"нет картинок в {src}")

    for p in files:
        cleared, total = cut(p, dst / p.name, a.tolerance, a.feather, a.outline)
        share = cleared * 100 // total
        note = ""
        if share < 5:
            note = "  ← фон почти не нашёлся, проверь допуск"
        elif share > 85:
            note = "  ← срезало почти всё, допуск велик"
        print(f"  {p.stem:14} прозрачным стало {share}%{note}")

    print(f"\n  готово: {len(files)} шт. → {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
