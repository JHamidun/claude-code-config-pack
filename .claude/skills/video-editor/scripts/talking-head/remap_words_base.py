#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Remap raw-take word timestamps onto the talking-head BASE timeline.

base = takes concatenated (no gaps). segmap_v gives each take's [t0,t1] on base.
For take i (source span from takes_rX.json) at base offset t0:
  base_time(word) = (word_time - take.start) + t0
Emits words on base timeline for captions.

Usage: python remap_words_base.py takes_r1.json segmap_v_r1.json raw_5785 words_base_r1.json
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())


def main():
    takes = json.loads((BASE / sys.argv[1]).read_text(encoding="utf-8"))
    segv = json.loads((BASE / sys.argv[2]).read_text(encoding="utf-8"))
    raw = sys.argv[3]
    out = sys.argv[4]
    segs = json.loads((BASE / "transcripts" / f"{raw}.json").read_text(encoding="utf-8"))

    allw = []
    for s in segs:
        for w in s["words"]:
            if w["s"] >= 0:
                allw.append(w)

    words = []
    for i, tk in enumerate(takes):
        t0 = segv[i]["t0"]
        s, e = tk["start"], tk["end"]
        for w in allw:
            mid = (w["s"] + w["e"]) / 2
            if s - 0.02 <= mid <= e + 0.02:
                ns = max(0.0, w["s"] - s) + t0
                ne = min(e - s, w["e"] - s) + t0
                if ne - ns > 0.03:
                    words.append({"w": w["w"], "s": round(ns, 3), "e": round(ne, 3)})
    words.sort(key=lambda x: x["s"])
    (BASE / out).write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    print(f"{out}: {len(words)} words on base timeline")


if __name__ == "__main__":
    main()
