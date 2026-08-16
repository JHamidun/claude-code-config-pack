#!/usr/bin/env python3
"""Каталог шрифтов для монтажа: что есть на машине и что чем является.

Зачем. Монтажу нужен не список названий, а ответ на вопрос «каким шрифтом набрать
крупный заголовок на кириллице, чтобы он влез в вертикаль». Название этого не говорит:
половина модных гротесков кириллицы не содержит и при выводе даёт пустые квадраты, а
имя файла об этом молчит.

Поэтому каждый файл открывается и проверяется по фактам:
    покрытие алфавитов   — по таблице символов, а не по имени и не по заявленным subset
    вес и ширина         — из метрик OS/2, а не из слова Bold в названии
    засечки              — из PANOSE, если производитель её заполнил
    моноширинность       — сравнением ширин глифов

На выходе JSON-каталог и подбор по роли: заголовок, субтитры, цифры, подпись.

    python font_catalog.py scan                     # пересобрать каталог
    python font_catalog.py list --cyrillic --role display
    python font_catalog.py pick display             # один лучший под роль
    python font_catalog.py pick caption --cyrillic  # путь к файлу, годный для ffmpeg

Каталог кладётся рядом со скриптом (fonts_catalog.json) и переиспользуется.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
CATALOG = HERE / "fonts_catalog.json"

SEARCH_DIRS = [
    pathlib.Path(r"C:\Windows\Fonts"),
    pathlib.Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    HERE.parent / "assets" / "fonts",                       # свои, докачанные
    pathlib.Path.home() / ".claude/skills/video-shotcraft/assets/fonts",
]

# Пробы покрытия: если нет хотя бы одного символа из набора — алфавит считается непокрытым.
PROBES = {
    "latin": "AZaz09",
    "cyrillic": "АЯаяЁёЙй",
    "cyrillic_ext": "ҐЄІЇґєії",       # украинский/белорусский набор
}

# Роли в кадре и требования к ним. Пороги — не вкусовые: тонкий шрифт на видео
# рассыпается при сжатии, поэтому у заголовка нижняя граница веса высокая.
ROLES = {
    "display":  {"min_weight": 700, "serif": None,  "mono": False,
                 "note": "крупный заголовок, слово-удар на весь экран"},
    "caption":  {"min_weight": 600, "serif": False, "mono": False,
                 "note": "субтитры: жирный гротеск, читается на любом фоне"},
    "body":     {"min_weight": 400, "serif": None,  "mono": False,
                 "note": "поясняющий текст, подписи в кадре"},
    "numeric":  {"min_weight": 600, "serif": None,  "mono": True,
                 "note": "счётчики и цифры: моноширинный, чтобы не дёргалось"},
    "accent":   {"min_weight": 400, "serif": True,  "mono": False,
                 "note": "цитата, засечки — контраст к гротеску"},
}


def probe(font, chars: str) -> bool:
    """Есть ли ВСЕ символы пробы в таблице соответствия."""
    try:
        cmap = font.getBestCmap()
    except Exception:
        return False
    return all(ord(c) in cmap for c in chars)


def is_mono(font) -> bool:
    """Моноширинность — по факту равенства ширин, а не по флагу.

    Флаг isFixedPitch в post-таблице производители заполняют небрежно; ширины врать
    не умеют. Берём выборку цифр и букв: если разброс нулевой — шрифт моноширинный.
    """
    try:
        hmtx = font["hmtx"]
        cmap = font.getBestCmap()
        widths = set()
        for ch in "0123456789ilmW":
            gid = cmap.get(ord(ch))
            if gid and gid in hmtx.metrics:
                widths.add(hmtx.metrics[gid][0])
        return len(widths) == 1 and bool(widths)
    except Exception:
        return False


def describe(path: pathlib.Path, font) -> dict | None:
    try:
        os2 = font["OS/2"]
        name_tbl = font["name"]
        family = name_tbl.getDebugName(1) or path.stem
        style = name_tbl.getDebugName(2) or ""
        full = name_tbl.getDebugName(4) or f"{family} {style}"
    except Exception:
        return None

    weight = int(getattr(os2, "usWeightClass", 400) or 400)
    width = int(getattr(os2, "usWidthClass", 5) or 5)
    panose = getattr(os2, "panose", None)
    fam_type = int(getattr(panose, "bFamilyType", 0) or 0)
    serif_style = int(getattr(panose, "bSerifStyle", 0) or 0)
    # PANOSE: тип 2 — латинский текстовый; засечки 11..13 — без засечек.
    serif = None
    if fam_type == 2:
        serif = not (11 <= serif_style <= 13)

    # Вариативный шрифт: диапазон весов важнее одного значения
    variable = "fvar" in font
    wght_range = None
    if variable:
        for ax in font["fvar"].axes:
            if ax.axisTag == "wght":
                wght_range = [int(ax.minValue), int(ax.maxValue)]

    return {
        "file": str(path),
        "family": family,
        "style": style,
        "full": full,
        "weight": weight,
        "weight_range": wght_range,
        "width_class": width,
        "condensed": width <= 4,
        "serif": serif,
        "mono": is_mono(font),
        "variable": variable,
        "latin": probe(font, PROBES["latin"]),
        "cyrillic": probe(font, PROBES["cyrillic"]),
        "cyrillic_ext": probe(font, PROBES["cyrillic_ext"]),
        "size_kb": round(path.stat().st_size / 1024),
    }


def scan() -> list[dict]:
    from fontTools.ttLib import TTFont, TTCollection

    out, seen = [], set()
    for d in SEARCH_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in (".ttf", ".otf", ".ttc"):
                continue
            key = f.name.lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                if f.suffix.lower() == ".ttc":
                    # Коллекция: внутри несколько начертаний, разбираем каждое
                    coll = TTCollection(str(f), lazy=True)
                    fonts = list(coll.fonts)
                else:
                    fonts = [TTFont(str(f), lazy=True, fontNumber=0)]
            except Exception:
                continue
            for fo in fonts:
                try:
                    rec = describe(f, fo)
                except Exception:
                    rec = None
                if rec:
                    out.append(rec)
                try:
                    fo.close()
                except Exception:
                    pass
    return out


def load() -> list[dict]:
    if not CATALOG.exists():
        raise SystemExit(f"каталога нет — сначала: python {pathlib.Path(__file__).name} scan")
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def matches(rec: dict, role: str, cyrillic: bool) -> bool:
    r = ROLES[role]
    if cyrillic and not rec["cyrillic"]:
        return False
    w = rec["weight_range"][1] if rec["weight_range"] else rec["weight"]
    if w < r["min_weight"]:
        return False
    if r["mono"] is not None and rec["mono"] != r["mono"]:
        return False
    if r["serif"] is not None and rec["serif"] is not None and rec["serif"] != r["serif"]:
        return False
    return True


def score(rec: dict, role: str) -> float:
    """Чем выше, тем лучше под роль. Вариативные и широкие семейства — в приоритете."""
    s = 0.0
    w = rec["weight_range"][1] if rec["weight_range"] else rec["weight"]
    if role in ("display", "caption"):
        s += min(w, 900) / 100.0                 # чем жирнее, тем лучше читается
        if rec["condensed"]:
            s += 1.5                             # в вертикаль влезает больше букв
    if role == "numeric" and rec["mono"]:
        s += 3
    if role == "accent" and rec["serif"]:
        s += 2
    if rec["variable"]:
        s += 1.2
    if rec["cyrillic_ext"]:
        s += 0.4
    # Системные служебные гарнитуры не годятся как акцент
    if any(k in rec["family"].lower() for k in ("wingding", "webding", "symbol", "mt extra")):
        s -= 10
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="пересобрать каталог")

    p = sub.add_parser("list", help="показать подходящие")
    p.add_argument("--role", choices=sorted(ROLES))
    p.add_argument("--cyrillic", action="store_true")
    p.add_argument("--limit", type=int, default=25)

    p = sub.add_parser("pick", help="один лучший файл под роль (для ffmpeg)")
    p.add_argument("role", choices=sorted(ROLES))
    p.add_argument("--cyrillic", action="store_true")

    sub.add_parser("stats", help="сводка по каталогу")
    a = ap.parse_args()

    if a.cmd == "scan":
        recs = scan()
        CATALOG.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
        cyr = sum(r["cyrillic"] for r in recs)
        print(f"  разобрано начертаний: {len(recs)}   с кириллицей: {cyr}   "
              f"вариативных: {sum(r['variable'] for r in recs)}")
        print(f"  каталог: {CATALOG}")
        return 0

    recs = load()

    if a.cmd == "stats":
        fams = {r["family"] for r in recs}
        print(f"  начертаний {len(recs)}, семейств {len(fams)}")
        print(f"  кириллица {sum(r['cyrillic'] for r in recs)}, "
              f"расширенная {sum(r['cyrillic_ext'] for r in recs)}, "
              f"моно {sum(r['mono'] for r in recs)}, "
              f"узких {sum(r['condensed'] for r in recs)}, "
              f"вариативных {sum(r['variable'] for r in recs)}")
        for role in ROLES:
            n = sum(matches(r, role, True) for r in recs)
            print(f"    {role:8s} с кириллицей подходит: {n:4d}   — {ROLES[role]['note']}")
        return 0

    if a.cmd == "list":
        pool = [r for r in recs if not a.role or matches(r, a.role, a.cyrillic)]
        if a.cyrillic and not a.role:
            pool = [r for r in pool if r["cyrillic"]]
        pool.sort(key=lambda r: score(r, a.role or "display"), reverse=True)
        for r in pool[:a.limit]:
            flags = "".join(("К" if r["cyrillic"] else "·", "М" if r["mono"] else "·",
                             "У" if r["condensed"] else "·", "В" if r["variable"] else "·"))
            w = f"{r['weight_range'][0]}–{r['weight_range'][1]}" if r["weight_range"] else str(r["weight"])
            print(f"  {flags}  {w:>9}  {r['full'][:46]:46s}  {pathlib.Path(r['file']).name}")
        print(f"\n  показано {min(len(pool), a.limit)} из {len(pool)}   (К кириллица, М моно, У узкий, В вариативный)")
        return 0

    if a.cmd == "pick":
        pool = [r for r in recs if matches(r, a.role, a.cyrillic)]
        if not pool:
            raise SystemExit(f"под роль {a.role} ничего не нашлось — ослабь условия или докачай шрифты")
        best = max(pool, key=lambda r: score(r, a.role))
        print(best["file"])
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
