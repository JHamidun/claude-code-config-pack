#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Cut creator's source VIDEO+AUDIO together at take spans -> synced talking-head base.

Audio stays married to video (no separate re-cut). Each take = continuous good
delivery; jump-cuts between takes get hidden by b-roll overlay later.
Normalizes to 1080x1920, 30fps, 48k stereo. Emits base + segmap (take offsets).

Usage: python cut_video.py takes_r1.json IMG_5785 build/base_r1.mp4 segmap_v_r1.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
SRC_DIR = Path(os.environ.get("REEL_SRC") or Path.cwd())
W, H, FPS = 1080, 1920, 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1500:])
        raise SystemExit(1)
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def main():
    takes = json.loads((BASE / sys.argv[1]).read_text(encoding="utf-8"))
    src = SRC_DIR / f"{sys.argv[2]}.MOV"
    out = BASE / sys.argv[3]
    segmap_out = BASE / sys.argv[4]
    tmp = BASE / "build" / "vparts"
    tmp.mkdir(parents=True, exist_ok=True)

    parts = []
    for i, t in enumerate(takes):
        p = tmp / f"{sys.argv[2]}_{i:02d}.mp4"
        s, e = t["start"], t["end"]
        # cut video+audio together, normalize, light edge fades to avoid clicks
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(src),
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}",
             "-af", "aresample=48000,afade=t=in:st=0:d=0.02",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(p)])
        parts.append(p)

    # concat (re-encode for clean joins)
    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", str(out)])

    # segmap: where each take lands on the base timeline
    seg = []
    t = 0.0
    for i, tk in enumerate(takes):
        d = dur(parts[i])
        seg.append({"i": i, "t0": round(t, 3), "t1": round(t + d, 3), "note": tk.get("note", "")})
        t += d
    segmap_out.write_text(json.dumps(seg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"base {out.name}: {dur(out):.2f}s, {len(parts)} takes")


if __name__ == "__main__":
    main()
