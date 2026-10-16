#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Analyze a talking-head video via Gemini — find AUDIO glitches with timestamps.

Detects: duplicated phrases, cut-off/clipped words, false starts, stumbles,
off-script chatter, long dead air. Returns second-precise JSON to drive re-cuts.

Usage: python gemini_analyze.py build/base_r1.mp4 analysis_r1.json
"""
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402


# Ключ — по требованию, а не при импорте. Раньше на верхнем уровне модуля стояли
# os.environ.pop("GEMINI_API_KEY") (мутация окружения ЛЮБОГО импортёра) и
# load_dotenv(...) (чтение файла с ключами), а клиент строился как
# os.environ["GOOGLE_API_KEY"] — без ключа это KeyError, по которому причину не понять.
def _google_api_key():
    """GOOGLE_API_KEY: окружение → ~/.claude/.credentials.master.env → внятный отказ."""
    if not os.environ.get("GOOGLE_API_KEY"):
        load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
    os.environ.pop("GEMINI_API_KEY", None)  # конфликт SDK: приоритет у GOOGLE_API_KEY
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise SystemExit(
            "ОТКАЗ: не задан GOOGLE_API_KEY.\n"
            "  Где взять: aistudio.google.com/apikey\n"
            "  Как задать: export GOOGLE_API_KEY=... (или строка GOOGLE_API_KEY=... "
            "в ~/.claude/.credentials.master.env)"
        )
    return key

MODEL = "gemini-3.1-pro-preview"

PROMPT = """Ты — придирчивый видеомонтажёр. Это черновая склейка вертикального рилса:
говорящий парень (русская речь) снят на улице, склеен из нескольких дублей.

Твоя задача — ВНИМАТЕЛЬНО ПРОСЛУШАТЬ АУДИО и найти ВСЕ дефекты речи, которые портят ролик:
1. ДУБЛИ — одна и та же фраза/слово повторяется подряд (он переснимал и склейка оставила оба).
2. ОБРЫВЫ — слово/фраза обрезано на полуслове, резкий скачок звука.
3. ФАЛЬСТАРТЫ — начал фразу, запнулся, начал заново ("и далее я бы... и далее я бы резко").
4. ЗАПИНКИ / слова-паразиты / оговорки.
5. ОФФ-СКРИПТ — обращение не к зрителю ("так, призыв на ЛМ", "я не помню", разговор с кем-то за кадром).
6. ДЛИННЫЕ ПАУЗЫ / мёртвый звук > 0.6 сек.

Для КАЖДОГО дефекта верни точные тайм-коды в СЕКУНДАХ от начала видео (с десятыми, напр. 12.4).

Также предложи, на каких отрезках стоит ПОКАЗАТЬ Б-РОЛЛ (иллюстрацию поверх), а где — оставить лицо говорящего (на хуке и в эмоциональных акцентах лицо сильнее).

Верни СТРОГО JSON без markdown:
{
 "glitches": [
   {"start": 12.4, "end": 14.1, "type": "duplicate|cutoff|falsestart|stumble|offscript|deadair",
    "heard": "что слышно дословно", "action": "cut", "note": "почему"}
 ],
 "broll_windows": [
   {"start": 5.0, "end": 9.0, "topic": "о чём говорит — какой b-roll подойдёт"}
 ],
 "keep_face_windows": [
   {"start": 0.0, "end": 4.0, "reason": "хук — лицо сильнее"}
 ],
 "overall_notes": "общие замечания по ритму/звуку"
}"""


def main():
    video = sys.argv[1]
    out = sys.argv[2]
    c = genai.Client(api_key=_google_api_key())

    print(f"uploading {video}...", flush=True)
    f = c.files.upload(file=video)
    while f.state.name == "PROCESSING":
        time.sleep(3)
        f = c.files.get(name=f.name)
    if f.state.name != "ACTIVE":
        print(f"upload failed: {f.state.name}")
        sys.exit(1)
    print("analyzing...", flush=True)

    resp = c.models.generate_content(
        model=MODEL,
        contents=[
            types.Content(role="user", parts=[
                types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type)),
                types.Part(text=PROMPT),
            ])
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            media_resolution="MEDIA_RESOLUTION_LOW",
        ),
    )
    txt = resp.text
    try:
        data = json.loads(txt)
    except Exception:
        t = txt.strip().strip("`")
        if t.startswith("json"):
            t = t[4:]
        data = json.loads(t)
    if isinstance(data, list):  # model sometimes wraps in a list
        data = data[0] if data and isinstance(data[0], dict) else {"glitches": data}
    Path(out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== {out} ===")
    print(f"glitches: {len(data.get('glitches', []))}")
    for g in data.get("glitches", []):
        print(f"  {g['start']:6.1f}-{g['end']:6.1f} [{g['type']}] {g.get('heard','')[:50]} -> {g.get('action')}")
    print(f"broll_windows: {len(data.get('broll_windows', []))}")
    print("notes:", data.get("overall_notes", "")[:300])
    try:
        c.files.delete(name=f.name)
    except Exception:
        pass


if __name__ == "__main__":
    main()
