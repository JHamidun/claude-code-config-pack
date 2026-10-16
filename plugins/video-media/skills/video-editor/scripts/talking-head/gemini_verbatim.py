#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Verbatim transcription of a SHORT audio clip via Gemini — captures EVERY word
including repeats/stutters that WhisperX collapses. Use on short clips for accuracy.

Usage: python gemini_verbatim.py build/chk_r1_38.wav
"""
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

PROMPT = ("Расшифруй ДОСЛОВНО что слышно в этом аудио, СЛОВО В СЛОВО, включая ВСЕ повторы, "
          "запинки, оборванные и продублированные слова. Если слово повторяется подряд — "
          "напиши его столько раз, сколько слышишь. НИЧЕГО не исправляй и не схлопывай. "
          "Верни только текст расшифровки.")


def main():
    clip = sys.argv[1]
    c = genai.Client(api_key=_google_api_key())
    f = c.files.upload(file=clip)
    while f.state.name == "PROCESSING":
        time.sleep(2)
        f = c.files.get(name=f.name)
    resp = c.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=[types.Content(role="user", parts=[
            types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type)),
            types.Part(text=PROMPT)])],
        config=types.GenerateContentConfig(temperature=0.0),
    )
    print(f"{Path(clip).name}: {resp.text.strip()}")
    try:
        c.files.delete(name=f.name)
    except Exception:
        pass


if __name__ == "__main__":
    main()
