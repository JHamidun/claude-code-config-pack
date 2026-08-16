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

import argparse
import base64
import json
import mimetypes
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
        result[p.stem] = {k: round(float(box[k]), 4) for k in ("cx", "cy", "w", "h")}
        print(f"  {p.stem:12} рот на {box['cx']:.2f} × {box['cy']:.2f}, "
              f"размер {box['w']:.3f} × {box['h']:.3f}")
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
