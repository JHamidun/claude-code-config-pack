#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Build tight EDL: chosen take spans minus internal silences.

takes json: [{"file": "audio/raw_5785.wav", "start": s, "end": e}]
Runs ffmpeg silencedetect per file (cached), subtracts silences >MIN_SIL from spans,
keeps PAD seconds around speech edges.

Usage: python build_edl.py takes_r1.json edl_r1.json
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
MIN_SIL = 0.40   # collapse silences longer than this
PAD = 0.10       # keep this much silence at each speech edge
NOISE = "-32dB"

_cache = {}


def silences(path):
    if path in _cache:
        return _cache[path]
    r = subprocess.run(
        ["ffmpeg", "-i", path, "-af", f"silencedetect=noise={NOISE}:d={MIN_SIL}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    sil = []
    start = None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            sil.append((start, float(m.group(1))))
            start = None
    _cache[path] = sil
    return sil


def main():
    takes = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    edl = []
    for t in takes:
        f = str((BASE / t["file"]).resolve())
        s, e = t["start"], t["end"]
        sil = [(a, b) for a, b in silences(f) if a < e and b > s]
        cur = s
        for a, b in sil:
            a, b = max(a, s), min(b, e)
            if a - cur > 0.05:
                seg_end = min(a + PAD, e)
                edl.append({"file": t["file"], "start": round(cur, 3), "end": round(seg_end, 3)})
            cur = max(cur, b - PAD)
        if e - cur > 0.05:
            edl.append({"file": t["file"], "start": round(cur, 3), "end": round(e, 3)})
    Path(sys.argv[2]).write_text(json.dumps(edl, indent=1), encoding="utf-8")
    total = sum(x["end"] - x["start"] for x in edl)
    print(f"EDL: {len(edl)} segments, {total:.1f}s speech (from {len(takes)} takes)")


if __name__ == "__main__":
    main()
