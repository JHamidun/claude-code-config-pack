#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Word-level transcription via Deepgram Nova-3 (cleaner than WhisperX for RU,
does not collapse repeats). Outputs [{w,s,e}] for captions.

Usage: python deepgram_transcribe.py build/base_r1_final2.mp4 words_dg_r1.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
import requests  # noqa: E402

KEY = os.environ["DEEPGRAM_API_KEY"]


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def transcribe_chunk(src, a, b):
    wav = Path(src).with_suffix(f".dg_{int(a)}.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", src,
                    "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    body = wav.read_bytes()
    last = None
    for _ in range(4):
        try:
            r = requests.post(
                "https://api.deepgram.com/v1/listen?model=nova-3&language=ru&smart_format=true&punctuate=true",
                headers={"Authorization": f"Token {KEY}", "Content-Type": "audio/wav"},
                data=body, timeout=180)
            r.raise_for_status()
            break
        except Exception as ex:
            last = ex
            import time as _t
            _t.sleep(5)
    else:
        raise last
    alt = r.json()["results"]["channels"][0]["alternatives"][0]
    wav.unlink(missing_ok=True)
    return [{"w": w.get("punctuated_word", w["word"]), "s": round(w["start"] + a, 3), "e": round(w["end"] + a, 3)}
            for w in alt.get("words", [])]


def main():
    src, out = sys.argv[1], sys.argv[2]
    D = dur(src)
    CH = 30.0
    words = []
    t = 0.0
    while t < D:
        e = min(t + CH, D)
        ws = transcribe_chunk(src, t, e)
        # drop words overlapping the previous chunk tail to avoid dups at seams
        words += [w for w in ws if not words or w["s"] >= words[-1]["e"] - 0.05]
        t = e
    Path(out).write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    print(f"{out}: {len(words)} words (deepgram nova-3, chunked)")


if __name__ == "__main__":
    main()
