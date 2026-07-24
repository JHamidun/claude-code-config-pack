#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Full verbatim audit: split base audio into short chunks, Gemini-transcribe each
VERBATIM (captures repeats WhisperX collapses), print with running timecodes.

Usage: python verbatim_audit.py build/base_r1_clean2.mp4 r1
"""
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.pop("GEMINI_API_KEY", None)
from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
CHUNK = 14.0
OVER = 0.0
PROMPT = ("Расшифруй ДОСЛОВНО, слово в слово, ВСЁ что слышишь в этом аудио. "
          "Повторяющиеся подряд слова пиши столько раз, сколько слышишь. "
          "Запинки, оборванные слова, дубли — сохраняй. Ничего не схлопывай и не исправляй. "
          "Только текст.")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def main():
    src = BASE / sys.argv[1]
    tag = sys.argv[2]
    c = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    D = dur(src)
    tmp = BASE / "build" / "vb"
    tmp.mkdir(parents=True, exist_ok=True)
    t = 0.0
    out = []
    while t < D:
        e = min(t + CHUNK, D)
        clip = tmp / f"{tag}_{int(t):03d}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-to", f"{e:.2f}",
                        "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(clip)],
                       capture_output=True)
        f = c.files.upload(file=str(clip))
        while f.state.name == "PROCESSING":
            time.sleep(2)
            f = c.files.get(name=f.name)
        r = c.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=[types.Content(role="user", parts=[
                types.Part(file_data=types.FileData(file_uri=f.uri, mime_type=f.mime_type)),
                types.Part(text=PROMPT)])],
            config=types.GenerateContentConfig(temperature=0.0))
        txt = (r.text or "").strip().replace("\n", " ")
        print(f"[{t:5.1f}-{e:5.1f}] {txt}", flush=True)
        out.append(f"[{t:.1f}-{e:.1f}] {txt}")
        try:
            c.files.delete(name=f.name)
        except Exception:
            pass
        t = e
    (BASE / f"verbatim_{tag}.txt").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
