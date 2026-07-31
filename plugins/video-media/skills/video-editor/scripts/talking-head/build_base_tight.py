#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Build a TIGHT, content-complete talking-head base from take spans.

Per take: cut video+audio together, remove only LONG internal pauses (jump-cut,
A/V synced), 18ms edge afades to kill click joins. Keeps every spoken word.
This fixes "речь прерывается" (long pauses) WITHOUT losing content or dups.

Usage: python build_base_tight.py takes_r1.json IMG_5785 build/base_r1_tight.mp4 segmap_t_r1.json
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
SRC_DIR = Path(os.environ.get("REEL_SRC") or Path.cwd())
W, H, FPS = 1080, 1920, 30
MIN_SIL = 0.50      # collapse internal pauses longer than this
KEEP = 0.16         # keep this much silence at each speech edge (natural breath)
NOISE = "-30dB"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1500:])
        raise SystemExit(1)
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def silences(src, s, e):
    r = subprocess.run(
        ["ffmpeg", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(src),
         "-af", f"silencedetect=noise={NOISE}:d={MIN_SIL}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    sil = []
    st = None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            st = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and st is not None:
            sil.append((st, float(m.group(1))))
            st = None
    return sil  # times relative to the trimmed clip (0-based)


def main():
    takes = json.loads((BASE / sys.argv[1]).read_text(encoding="utf-8"))
    src = SRC_DIR / f"{sys.argv[2]}.MOV"
    out = BASE / sys.argv[3]
    segmap_out = BASE / sys.argv[4]
    tmp = BASE / "build" / "tight"
    tmp.mkdir(parents=True, exist_ok=True)

    parts = []
    segmap = []
    newt = 0.0
    pidx = 0
    for ti, t in enumerate(takes):
        s, e = t["start"], t["end"]
        L = e - s
        sil = silences(src, s, e)
        # keep-segments = complement of internal silences (with KEEP padding)
        keep = []
        cur = 0.0
        for a, b in sil:
            seg_end = min(a + KEEP, L)
            if seg_end - cur > 0.12:
                keep.append((cur, seg_end))
            cur = max(cur, b - KEEP)
        if L - cur > 0.12:
            keep.append((cur, L))
        if not keep:
            keep = [(0.0, L)]
        take_t0 = newt
        for (ks, ke) in keep:
            p = tmp / f"p_{pidx:03d}.mp4"
            seglen = ke - ks
            af = f"aresample=48000,afade=t=in:st=0:d=0.018,afade=t=out:st={max(0,seglen-0.018):.3f}:d=0.018"
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s+ks:.3f}", "-to", f"{s+ke:.3f}", "-i", str(src),
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}",
                 "-af", af, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(p)])
            d = dur(p)
            parts.append(p)
            newt += d
            pidx += 1
        segmap.append({"i": ti, "t0": round(take_t0, 3), "t1": round(newt, 3), "note": t.get("note", "")})

    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])
    segmap_out.write_text(json.dumps(segmap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: {dur(out):.1f}s, {len(takes)} takes -> {len(parts)} segs (pauses removed, joins smoothed)")


if __name__ == "__main__":
    main()
