#!/usr/bin/env python3
"""Где на рисунке персонажа находится рот.

Персонаж в ролике — набор нарисованных поз. Пока рот на них неподвижен, персонаж
читается как картинка, а не как говорящий: зритель слышит голос, но видит статичное
лицо, и это первое, за что цепляется глаз при сравнении с чужим роликом.

Чтобы рот открывался под голос, нужно знать, где он на каждой позе. Рисунки не
одинаковые: персонаж стоит по-разному, голова смещена, масштаб гуляет. Поэтому
координаты не задаются вручную и не угадываются по центру головы, а спрашиваются у
модели, которая видит изображение, — по одному кадру за раз, в долях от размера
картинки, чтобы разметка пережила любое последующее масштабирование.

    python mouth_map.py ./poses -o mouth.json
    python mouth_map.py ./poses -o mouth.json --draw check/   # проверить глазами
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
import base64
import json
import mimetypes
import os
import pathlib
import sys
import urllib.error
import urllib.request

ENV = pathlib.Path.home() / ".claude" / ".credentials.master.env"
API = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-3.7-flash"   # 3.1-flash под этим именем не существует, только -lite

PROMPT = """На картинке нарисованный персонаж. Найди его РОТ.

Верни ТОЛЬКО JSON, без пояснений и без разметки кода:
{"cx": 0.0, "cy": 0.0, "w": 0.0, "h": 0.0, "found": true}

cx, cy — центр рта в долях ширины и высоты картинки (0 — левый/верхний край, 1 —
правый/нижний). w, h — ширина и высота рта в тех же долях.

Важно: нужен именно рот, не нос и не подбородок. Если лицо не видно или рот закрыт
рукой — верни {"found": false}."""


def key() -> str:
    # Переменная окружения — первый источник: файла ключей может не быть вовсе,
    # и без этой проверки скрипт падал бы трейсбеком FileNotFoundError.
    env_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if env_key:
        return env_key
    if not ENV.exists():
        raise SystemExit(
            f"нет GOOGLE_API_KEY: ни в окружении, ни в {ENV}. "
            "Заведи файл из ~/.claude/templates/.credentials.master.env.example "
            "или экспортируй переменную."
        )
    for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("GOOGLE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет GOOGLE_API_KEY")


def ask(path: pathlib.Path, api_key: str) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    body = {
        "contents": [{"parts": [
            {"inlineData": {"mimeType": mime,
                            "data": base64.b64encode(path.read_bytes()).decode()}},
            {"text": PROMPT},
        ]}],
        # Схема ответа вместо просьбы «верни JSON»: без неё модель тратит лимит на
        # размышления и отдаёт оборванную строку. Размышление здесь и не нужно —
        # это разметка координат, а не рассуждение.
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 800,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "cx": {"type": "number"}, "cy": {"type": "number"},
                    "w": {"type": "number"}, "h": {"type": "number"},
                    "found": {"type": "boolean"},
                },
                "required": ["cx", "cy", "w", "h", "found"],
            },
        },
    }
    req = urllib.request.Request(
        f"{API}/models/{MODEL}:generateContent?key={api_key}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())

    text = "".join(p.get("text", "")
                   for c in d.get("candidates", [])
                   for p in c.get("content", {}).get("parts", []))
    # Модель иногда оборачивает ответ в ```json — берём то, что между фигурными скобками.
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < 0:
        raise ValueError(f"не разобрал ответ: {text[:120]}")
    return json.loads(text[s:e + 1])


def refine(src: pathlib.Path, box: dict, search: float = 0.045) -> dict:
    """Уточнить положение рта по самой картинке.

    Модель показывает рот примерно: на отдельных позах промах доходил до двадцати
    пяти пикселей, и рот открывался ниже губ — в бороде. На глаз разметка при этом
    выглядела верной: овал накрывал губы целиком, а смещение внутри него не читалось.

    Линия смыкания губ — самая тёмная горизонталь в окрестности: у рта всегда есть
    тёмный контур, а кожа и борода вокруг светлее. Ищем её и сдвигаем центр туда.
    """
    from PIL import Image
    import numpy as np

    im = Image.open(src).convert("L")
    a = np.asarray(im, dtype=float)
    H, W = a.shape
    cx, cy = box["cx"] * W, box["cy"] * H

    # Окно поиска — по высоте самого рта, а не по высоте картинки. С широким окном
    # находилась борода: она темнее губ, и на позах со светлым сомкнутым ртом центр
    # уезжал на два сантиметра вниз, под нижнюю губу.
    half = max(int(box["h"] * H * 1.1), 8)
    x0, x1 = int(cx - box["w"] * W * 0.35), int(cx + box["w"] * W * 0.35)
    y0, y1 = max(0, int(cy - half)), min(H, int(cy + half))
    if x1 <= x0 or y1 <= y0:
        return box

    rows = a[y0:y1, x0:x1].mean(axis=1)

    # Ищем не самую тёмную строку, а линию СМЫКАНИЯ губ. Разница принципиальная:
    # под нижней губой тень переходит в бороду, и там темнее, чем во рту, — прежний
    # способ уверенно ставил рот в бороду. Линия смыкания устроена иначе: узкая
    # тёмная полоса, а сверху и снизу от неё светлее. Такой перепад и ищем.
    k = max(int(box["h"] * H * 0.45), 3)
    contrast = np.full(len(rows), 1e9)
    for i in range(k, len(rows) - k):
        above, below = rows[i - k:i].mean(), rows[i + 1:i + 1 + k].mean()
        # Чем строка темнее ОБОИХ соседей, тем лучше. Если ниже так же темно —
        # это переход в бороду, и кандидат отбраковывается сам собой.
        contrast[i] = rows[i] - min(above, below)

    dist = np.abs(np.arange(y0, y1) - cy)
    score = contrast + dist * 1.2
    found = y0 + int(np.argmin(score))

    shift_px = found - cy
    # Последняя страховка: сдвиг больше высоты рта — не уточнение, а промах.
    if abs(shift_px) > box["h"] * H * 1.2:
        out = dict(box)
        out["shift_px"] = 0
        return out

    out = dict(box)
    out["cy"] = round(box["cy"] + shift_px / H, 4)
    out["shift_px"] = int(shift_px)
    return out


def skin_tone(src: pathlib.Path, box: dict) -> dict:
    """Цвет кожи вокруг рта — им закрывается нарисованный рот.

    Свой рот поверх нарисованного даёт кашу: губы персонажа остаются на месте, а
    новая полость появляется внутри них, и это читается как дыра. Поэтому под свой
    рот подкладывается заплатка цвета кожи. Цвет берётся не из палитры, а с самой
    картинки — прямо над ртом, где кожа чистая: у разных поз тон отличается
    освещением, и общий бежевый заметен заплаткой.
    """
    from PIL import Image
    import numpy as np

    im = Image.open(src).convert("RGB")
    a = np.asarray(im)
    H, W = a.shape[:2]
    cx, cy = box["cx"] * W, box["cy"] * H
    # Берём широкую область вокруг рта и отбираем из неё только кожу. Точка «над
    # ртом» не годится: у персонажа там усы, и заплатка выходила коричневой.
    dy = int(box["h"] * H * 3)
    dx = int(box["w"] * W * 1.2)
    y0, y1 = max(0, int(cy - dy)), min(H, int(cy + dy))
    x0, x1 = max(0, int(cx - dx)), min(W, int(cx + dx))
    patch = a[y0:y1, x0:x1].reshape(-1, 3).astype(int)
    if not len(patch):
        return {"skin": "#e8b795"}

    r, g, b = patch[:, 0], patch[:, 1], patch[:, 2]
    # Кожа на рисунке — светлая и тёплая: красного заметно больше синего. Усы,
    # борода и тень внутри рта этому не отвечают и отсеиваются.
    skin = patch[(r > 140) & (r > g) & (g > b) & (r - b > 25)]
    if len(skin) < 20:
        skin = patch[r > np.percentile(r, 75)]
    if not len(skin):
        return {"skin": "#e8b795"}
    rr, gg, bb = (int(np.median(skin[:, i])) for i in range(3))
    return {"skin": f"#{rr:02x}{gg:02x}{bb:02x}"}


def draw_check(src: pathlib.Path, box: dict, out: pathlib.Path) -> None:
    """Обвести найденный рот — чтобы разметку можно было проверить глазами, а не верой."""
    from PIL import Image, ImageDraw
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    d = ImageDraw.Draw(im)
    x, y = box["cx"] * W, box["cy"] * H
    w, h = box["w"] * W / 2, box["h"] * H / 2
    d.ellipse([x - w, y - h, x + w, y + h], outline=(255, 40, 90, 255), width=5)
    d.line([x - 30, y, x + 30, y], fill=(255, 40, 90, 255), width=3)
    im.save(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("poses", help="папка с картинками поз")
    ap.add_argument("-o", "--out", required=True, help="куда сложить разметку")
    ap.add_argument("--draw", help="папка для картинок с обведённым ртом")
    ap.add_argument("--skip", default="ref_,sheet_,_preview",
                    help="не размечать файлы с такими кусками в имени")
    a = ap.parse_args()

    api_key = key()
    src = pathlib.Path(a.poses)
    skip = [s for s in a.skip.split(",") if s]
    files = sorted(p for p in src.glob("*.png")
                   if not any(s in p.name for s in skip))
    if not files:
        raise SystemExit(f"нет картинок в {src}")

    out_dir = pathlib.Path(a.draw) if a.draw else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    result, missed = {}, []
    for p in files:
        try:
            box = ask(p, api_key)
        except (urllib.error.HTTPError, ValueError) as e:
            print(f"  {p.stem:12} — не вышло: {e}")
            missed.append(p.stem)
            continue
        if not box.get("found", True):
            print(f"  {p.stem:12} — рот не виден")
            missed.append(p.stem)
            continue
        box = refine(p, box)
        box.update(skin_tone(p, box))
        result[p.stem] = {k: round(float(box[k]), 4) for k in ("cx", "cy", "w", "h")}
        result[p.stem]["skin"] = box.get("skin", "#e8b795")
        note = ""
        if abs(box.get("shift_px", 0)) >= 6:
            note = f"  ← поправлено на {box['shift_px']:+d} px по линии губ"
        print(f"  {p.stem:12} рот на {box['cx']:.2f} × {box['cy']:.2f}, "
              f"размер {box['w']:.3f} × {box['h']:.3f}{note}")
        if out_dir:
            draw_check(p, result[p.stem], out_dir / p.name)

    pathlib.Path(a.out).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  размечено: {len(result)} из {len(files)} → {a.out}")
    if missed:
        print(f"  без разметки: {', '.join(missed)} — у них рот останется неподвижным")
    if out_dir:
        print(f"  проверить глазами: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
