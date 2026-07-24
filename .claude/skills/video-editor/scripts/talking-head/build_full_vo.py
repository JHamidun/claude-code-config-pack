#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Concat body VO + gap + ending CTA audio -> full VO track. Also emit ending words
remapped onto the full timeline so captions cover the outro.

Usage: python build_full_vo.py vo_r1.wav GAP > prints body_dur + total_dur
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
ENDING_AUDIO = BASE / "audio" / "ending_clean.wav"
ENDING_RAW = "audio/raw_5784.wav"
ENDING_SPAN = (6.10, 18.85)  # clean CTA span in raw_5784


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    vo = sys.argv[1]            # vo_r1.wav (body)
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    out = sys.argv[3] if len(sys.argv) > 3 else vo.replace(".wav", "_full.wav")
    words_out = sys.argv[4] if len(sys.argv) > 4 else None

    body = BASE / "audio" / vo
    body_dur = dur(body)
    # concat body + gap silence + ending
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(body),
        "-f", "lavfi", "-t", f"{gap}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-i", str(ENDING_AUDIO),
        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[o]",
        "-map", "[o]", "-ar", "48000", str(BASE / "audio" / out),
    ], check=True)
    total = dur(BASE / "audio" / out)
    end_t0 = body_dur + gap

    if words_out:
        segs = json.loads((BASE / "transcripts" / "raw_5784.json").read_text(encoding="utf-8"))
        ws = []
        for s in segs:
            for w in s["words"]:
                if w["s"] >= 0 and ENDING_SPAN[0] - 0.05 <= (w["s"] + w["e"]) / 2 <= ENDING_SPAN[1] + 0.05:
                    ws.append({
                        "w": w["w"],
                        "s": round(w["s"] - ENDING_SPAN[0] + end_t0, 3),
                        "e": round(w["e"] - ENDING_SPAN[0] + end_t0, 3),
                    })
        (BASE / words_out).write_text(json.dumps(ws, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({"body_dur": round(body_dur, 3), "end_t0": round(end_t0, 3), "total": round(total, 3)}))


if __name__ == "__main__":
    main()
