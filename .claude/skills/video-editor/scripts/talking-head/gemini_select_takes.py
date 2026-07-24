#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""For each SCRIPT line, ask Gemini to find the single cleanest complete delivery
in the RAW source (which has many stumbly retakes). Returns precise spans.

Usage: python gemini_select_takes.py script_r1.json takes_sel_r1.json
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.pop("GEMINI_API_KEY", None)
from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

SRC_DIR = Path(os.environ.get("REEL_SRC") or Path.cwd())
MODEL = "gemini-3.1-pro-preview"


def main():
    script = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = sys.argv[2]
    num = script["raw"].replace("IMG_", "")
    proxy = Path(__file__).parent / "build" / f"proxy_{num}.mp4"
    raw = proxy if proxy.exists() else (SRC_DIR / f"{script['raw']}.MOV")
    lines = script["lines"]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(lines))

    prompt = f"""Это СЫРОЙ исходник: блогер записывает рилс, делает МНОГО дублей одной фразы,
запинается, начинает заново, болтает не по делу, читает с телефона, делает паузы.

Ниже ЦЕЛЕВОЙ СКРИПТ — что должно остаться в финале (по строкам):
{numbered}

Твоя задача: для КАЖДОЙ строки скрипта найди в видео ЕДИНСТВЕННЫЙ САМЫЙ ЧИСТЫЙ полный дубль —
без запинок, без слов-паразитов, без оговорок, сказанный уверенно от начала до конца.
Если строку он говорил много раз — выбери лучший вариант.

Верни точные тайм-коды в СЕКУНДАХ (с десятыми). Диапазон должен охватывать ТОЛЬКО эту фразу,
начинаться ровно с первого слова и заканчиваться на последнем слове (без хвостовых пауз и лишних слов).

СТРОГО JSON без markdown:
{{"takes": [
  {{"line": 1, "start": 12.4, "end": 17.8, "verbatim": "что именно слышно дословно в этом дубле", "quality": "clean|ok"}},
  ...
]}}
По одному лучшему дублю на каждую из {len(lines)} строк, по порядку."""

    c = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    print(f"uploading {raw.name}...", flush=True)
    f = c.files.upload(file=str(raw))
    while f.state.name == "PROCESSING":
        time.sleep(4)
        f = c.files.get(name=f.name)
    print("selecting best takes...", flush=True)
    resp = c.models.generate_content(
        model=MODEL,
        contents=[types.Content(role="user", parts=[
            types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type)),
            types.Part(text=prompt)])],
        config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"),
    )
    t = resp.text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:]
    data = json.loads(t)
    if isinstance(data, list):
        data = {"takes": data}
    Path(out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== {out} ===")
    for tk in data["takes"]:
        print(f"  L{tk['line']:02d} {tk['start']:6.1f}-{tk['end']:6.1f} [{tk.get('quality','')}] {tk.get('verbatim','')[:55]}")
    try:
        c.files.delete(name=f.name)
    except Exception:
        pass


if __name__ == "__main__":
    main()
