#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Remove Gemini-flagged glitch ranges from a base (video+audio together, sync kept).

Keeps the complement of glitch ranges, concatenates. Emits clean base + an
offset map so windows on the OLD timeline can be remapped to the NEW one.

Usage: python trim_glitches.py build/base_r1.mp4 analysis_r1.json build/base_r1_clean.mp4 offmap_r1.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
W, H, FPS = 1080, 1920, 30
PAD = 0.06  # keep a hair around speech so words aren't clipped


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1500:])
        raise SystemExit(1)
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def main():
    base = BASE / sys.argv[1]
    analysis = json.loads((BASE / sys.argv[2]).read_text(encoding="utf-8"))
    out = BASE / sys.argv[3]
    offmap_out = BASE / sys.argv[4]
    total = dur(base)

    # merge glitch ranges (only those with action cut / any glitch)
    ranges = []
    for g in analysis.get("glitches", []):
        s, e = max(0, g["start"] - PAD), min(total, g["end"] + PAD)
        if e > s:
            ranges.append((s, e))
    ranges.sort()
    merged = []
    for s, e in ranges:
        if merged and s <= merged[-1][1] + 0.05:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # complement = keep segments
    keep = []
    cur = 0.0
    for s, e in merged:
        if s - cur > 0.25:
            keep.append((cur, s))
        cur = e
    if total - cur > 0.25:
        keep.append((cur, total))

    tmp = BASE / "build" / "trim"
    tmp.mkdir(parents=True, exist_ok=True)
    parts = []
    offmap = []  # {old0, old1, new0, new1}
    newt = 0.0
    for i, (s, e) in enumerate(keep):
        p = tmp / f"k_{i:02d}.mp4"
        seglen = e - s
        # 18ms edge afades kill click artifacts at cut joins
        af = f"aresample=48000,afade=t=in:st=0:d=0.018,afade=t=out:st={max(0,seglen-0.018):.3f}:d=0.018"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(base),
             "-vf", f"scale={W}:{H},setsar=1,fps={FPS}", "-af", af,
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(p)])
        d = dur(p)
        offmap.append({"old0": round(s, 3), "old1": round(e, 3), "new0": round(newt, 3), "new1": round(newt + d, 3)})
        newt += d
        parts.append(p)

    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])
    offmap_out.write_text(json.dumps(offmap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: {dur(out):.1f}s (was {total:.1f}s, cut {total-dur(out):.1f}s, {len(merged)} glitches, {len(keep)} kept segs)")


if __name__ == "__main__":
    main()
