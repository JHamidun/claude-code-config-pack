#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Second Gemini pass on the CLEAN base -> shot-by-shot montage plan.

Returns an ordered segment list covering the whole base: each segment is either
'face' (show creator) or 'broll' (overlay AI clip) with a topic + suggested energy.
Drives a dynamic, intentional edit (dense b-roll bursts around strong face beats).

Usage: python gemini_plan.py build/base_r1_clean.mp4 plan_r1.json
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

PROMPT = """Это ЧИСТАЯ склейка вертикального рилса: парень (русская речь) на улице говорит на камеру.
Звук уже почищен. Сделай ДИНАМИЧНЫЙ монтажный план в стиле виральных Instagram Reels
(быстрый темп, новый визуал каждые 2-3 сек, b-roll иллюстрирует слова).

Принципы:
- ЛИЦО говорящего показываем на ХУКЕ (первые секунды), на эмоциональных акцентах и на ФИНАЛЬНОЙ фразе/шутке — лицо вовлекает.
- B-ROLL (иллюстрация поверх) — когда он описывает конкретные вещи (типажи людей, приложение, звёзды, еда, эмоции). В b-roll-зонах режь ЧАСТО: каждые 2-2.5 сек новый клип.
- Покрытие: примерно 55-65% b-roll, 35-45% лицо. Лицо — это база, b-roll врывается бёрстами.

Прослушай речь и разбей ВСЮ длину видео на сегменты встык (без дыр и нахлёстов), от 0 до конца.
Для каждого сегмента укажи режим и (для b-roll) что показать.

Верни СТРОГО JSON без markdown:
{
 "segments": [
   {"start": 0.0, "end": 3.5, "mode": "face", "reason": "хук, лицо"},
   {"start": 3.5, "end": 6.0, "mode": "broll", "topic": "парень снимает рилс на телефон", "energy": "high"},
   {"start": 6.0, "end": 8.0, "mode": "broll", "topic": "звезда выходит из машины", "energy": "high"}
 ],
 "notes": "общий комментарий по ритму"
}
Сегменты b-roll делай КОРОТКИМИ (2-2.5с). Покрой всю длину до конца видео."""


def main():
    video, out = sys.argv[1], sys.argv[2]
    c = genai.Client(api_key=_google_api_key())
    print(f"uploading {video}...", flush=True)
    f = c.files.upload(file=video)
    while f.state.name == "PROCESSING":
        time.sleep(3)
        f = c.files.get(name=f.name)
    print("planning...", flush=True)
    resp = c.models.generate_content(
        model=MODEL,
        contents=[types.Content(role="user", parts=[
            types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type)),
            types.Part(text=PROMPT)])],
        config=types.GenerateContentConfig(temperature=0.4, response_mime_type="application/json",
                                           media_resolution="MEDIA_RESOLUTION_LOW"),
    )
    t = resp.text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:]
    data = json.loads(t)
    Path(out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    segs = data.get("segments", [])
    nb = sum(1 for s in segs if s["mode"] == "broll")
    cov = sum(s["end"] - s["start"] for s in segs if s["mode"] == "broll")
    tot = segs[-1]["end"] if segs else 0
    print(f"{out}: {len(segs)} segs, {nb} broll ({cov:.0f}/{tot:.0f}s = {100*cov/max(tot,1):.0f}%)")
    try:
        c.files.delete(name=f.name)
    except Exception:
        pass


if __name__ == "__main__":
    main()
