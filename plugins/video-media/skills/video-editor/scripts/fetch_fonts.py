#!/usr/bin/env python3
"""Докачать свободные шрифты с кириллицей — те, что реально нужны видео.

Зачем. В системе стоят офисные гарнитуры: ими можно набрать документ, но не заголовок
на весь экран. Для видео нужен другой набор — тяжёлые гротески, узкие (в вертикаль
влезает вдвое больше букв), моноширинные для счётчиков, рукописные для подписей.

Все перечисленные ниже — под свободной лицензией шрифтов, кириллица проверяется не по
обещанию каталога, а по факту: после скачивания шрифт открывается и в нём ищутся
русские буквы. Не прошёл — файл удаляется, чтобы в кадре не появились пустые квадраты.

Качаем через сервис шрифтов в современном формате и переводим в обычный, потому что
ни наложение текста в ffmpeg, ни субтитры сжатый формат не открывают.

    python fetch_fonts.py            # докачать всё, чего нет
    python fetch_fonts.py --list     # что в подборке
    python fetch_fonts.py --only Oswald Unbounded
"""
from __future__ import annotations

import argparse
import hashlib
import io
import pathlib
import re
import sys
import urllib.request

DEST = pathlib.Path(__file__).parent.parent / "assets" / "fonts"
CSS = "https://fonts.googleapis.com/css2?family={q}&display=swap"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Подборка под задачи видео. Комментарий — за что взят, а не описание внешности.
FAMILIES = {
    # --- тяжёлые гротески: слово-удар на весь экран -------------------------------
    "Montserrat":          "wght@400;700;900",
    "Unbounded":           "wght@400;700;900",   # характерный, кириллица родная
    "Onest":               "wght@400;700;900",
    "Golos Text":          "wght@400;700;900",   # нейтральный, отлично на подложке
    "Geologica":           "wght@400;700;900",
    "Rubik":               "wght@400;700;900",
    "Manrope":             "wght@400;700;800",
    "Nunito":              "wght@400;700;900",
    "Exo 2":               "wght@400;700;900",
    "Raleway":             "wght@400;700;900",
    "Commissioner":        "wght@400;700;900",
    "Jost":                "wght@400;700;900",
    "Wix Madefor Display": "wght@400;700;800",
    "Tektur":              "wght@400;700;900",   # техно-дисплей
    "Inter":               "wght@400;700;900",
    "Open Sans":           "wght@400;700;800",
    "Noto Sans":           "wght@400;700;900",
    "Source Sans 3":       "wght@400;700;900",
    "IBM Plex Sans":       "wght@400;700",
    "Ubuntu":              "wght@400;700",
    "Comfortaa":           "wght@400;700",
    "Philosopher":         "wght@400;700",
    "Arsenal":             "wght@400;700",
    "Spline Sans":         "wght@400;700",
    # --- узкие: вертикаль 9:16, влезает вдвое больше букв --------------------------
    "Oswald":              "wght@400;600;700",
    "Roboto Condensed":    "wght@400;700",
    "PT Sans Narrow":      "wght@400;700",
    "Cuprum":              "wght@400;700",
    "Yanone Kaffeesatz":   "wght@400;700",
    "Alumni Sans":         "wght@400;700;900",
    "Fira Sans Condensed": "wght@400;700",
    "Ubuntu Condensed":    "",
    "Scada":               "wght@400;700",
    # --- моноширинные: счётчики, цифры, код в кадре --------------------------------
    "JetBrains Mono":      "wght@400;700",
    "Roboto Mono":         "wght@400;700",
    "IBM Plex Mono":       "wght@400;700",
    "Spline Sans Mono":    "wght@400;700",
    "Ubuntu Mono":         "wght@400;700",
    "Inconsolata":         "wght@400;700;900",
    "Anonymous Pro":       "wght@400;700",
    "PT Mono":             "",
    # --- засечки: цитата, контраст к гротеску --------------------------------------
    "PT Serif":            "wght@400;700",
    "Literata":            "wght@400;700;900",
    "Cormorant":           "wght@400;700",
    "Playfair Display":    "wght@400;700;900",
    "Merriweather":        "wght@400;700;900",
    "Alegreya":            "wght@400;700;900",
    "Vollkorn":            "wght@400;700;900",
    "Source Serif 4":      "wght@400;700;900",
    "IBM Plex Serif":      "wght@400;700",
    "Old Standard TT":     "wght@400;700",
    "Prata":               "",
    "Yeseva One":          "",
    "Podkova":             "wght@400;700",
    # --- рукописные: подпись, «человеческий» слой ---------------------------------
    "Caveat":              "wght@400;700",
    "Bad Script":          "",
    "Marck Script":        "",
    "Neucha":              "",
    "Pacifico":            "",
    "Lobster":             "",
    "Amatic SC":           "wght@400;700",
    # --- декоративные: одно слово, не абзац ---------------------------------------
    "Russo One":           "",
    "Stalinist One":       "",
    "Ruslan Display":      "",
    "Kelly Slab":          "",
    "Rubik Mono One":      "",
    "Rubik Glitch":        "",
    "Play":                "wght@400;700",
    "Ruda":                "wght@400;700;900",
    "Bebas Neue":          "",
}

PROBE = "АЯаяЁёЙй"


def fetch(url: str, *, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def to_ttf(woff2: bytes) -> bytes:
    """Перевести сжатый веб-формат в обычный: ffmpeg и субтитры читают только его."""
    from fontTools.ttLib.woff2 import decompress
    out = io.BytesIO()
    decompress(io.BytesIO(woff2), out)
    return out.getvalue()


def font_name(ttf: bytes, fallback: str) -> str:
    """Имя из метаданных шрифта: файл должен называться тем, что в нём лежит."""
    from fontTools.ttLib import TTFont
    try:
        f = TTFont(io.BytesIO(ttf), lazy=True)
        n = (f["name"].getDebugName(6) or f["name"].getDebugName(4) or fallback)
        f.close()
        return re.sub(r"[^A-Za-z0-9_\-]", "", n) or fallback
    except Exception:
        return fallback


def has_cyrillic(ttf: bytes) -> bool:
    from fontTools.ttLib import TTFont
    try:
        f = TTFont(io.BytesIO(ttf), lazy=True)
        cmap = f.getBestCmap()
        ok = all(ord(c) in cmap for c in PROBE)
        f.close()
        return ok
    except Exception:
        return False


def family_files(name: str, axis: str) -> list[tuple[str, str]]:
    """Ссылки на начертания семейства: (подпись, адрес). Берём только кириллический блок.

    В ответе сервиса начертания разложены по алфавитам: каждому блоку предшествует
    комментарий с названием набора символов. Берём адреса из блока кириллицы — так в
    файле не окажется лишних тысяч глифов, которых мы не используем.
    """
    q = name.replace(" ", "+") + (f":{axis}" if axis else "")
    css = fetch(CSS.format(q=q))
    out, current = [], ""
    for line in css.splitlines():
        m = re.match(r"\s*/\*\s*([\w\-\[\] ]+)\s*\*/", line)
        if m:
            current = m.group(1).strip()
            continue
        m = re.search(r"src:\s*url\((https://[^)]+\.woff2)\)", line)
        if m and current.startswith("cyrillic"):
            out.append((current, m.group(1)))
    if not out:                       # кириллического блока нет — семейство не подходит
        return []
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", nargs="*", help="только эти семейства")
    a = ap.parse_args()

    if a.list:
        for n, ax in FAMILIES.items():
            print(f"  {n:22s} {ax or '(одно начертание)'}")
        print(f"\n  всего семейств: {len(FAMILIES)}")
        return 0

    DEST.mkdir(parents=True, exist_ok=True)
    # То, что уже лежит, повторно не качаем и не плодим под другими именами
    have = {hashlib.md5(f.read_bytes()).hexdigest() for f in DEST.glob("*.ttf")}
    names = a.only or list(FAMILIES)
    added = skipped = failed = 0

    for name in names:
        axis = FAMILIES.get(name, "")
        try:
            links = family_files(name, axis)
        except Exception as e:
            print(f"  ✗ {name}: не получил список ({type(e).__name__})")
            failed += 1
            continue
        if not links:
            print(f"  – {name}: кириллицы в семействе нет, пропускаю")
            skipped += 1
            continue

        got = 0
        for block, url in links:
            try:
                ttf = to_ttf(fetch(url, binary=True))
            except Exception as e:
                print(f"  ✗ {name} [{block}]: {type(e).__name__}")
                continue
            if not has_cyrillic(ttf):
                continue          # обещали кириллицу, а её нет — такой файл нам вреден
            h = hashlib.md5(ttf).hexdigest()
            if h in have:         # вариативное семейство приезжает одним файлом на все веса
                continue
            have.add(h)
            dst = DEST / f"{font_name(ttf, name.replace(' ', ''))}.ttf"
            if dst.exists():
                dst = DEST / f"{dst.stem}-{h[:6]}.ttf"
            dst.write_bytes(ttf)
            got += 1
        if got:
            print(f"  ✓ {name}: начертаний {got}")
            added += got
        else:
            print(f"  – {name}: проверку кириллицы не прошло ни одно начертание")
            skipped += 1

    total = len(list(DEST.glob("*.ttf")))
    print(f"\n  добавлено {added}, пропущено семейств {skipped}, ошибок {failed}")
    print(f"  в {DEST}: {total} файлов")
    print("  дальше: python font_catalog.py scan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
