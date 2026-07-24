#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Build clean talking-head base from Gemini-selected take spans.

Snaps each span's start/end to nearest silence (clean cuts on pauses, no clipped
words), cuts video+audio together with edge afades, concatenates. Emits segmap.

Usage: python build_from_selection.py takes_sel_r1.json IMG_5785 build/base_r1_sel.mp4 segmap_s_r1.json
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
NOISE = "-30dB"
SILD = 0.18          # min silence to consider a boundary
SNAP_WIN = 0.9       # search window around the given boundary
EDGE = 0.10          # keep this much silence past the speech edge


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1200:])
        raise SystemExit(1)
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def detect_sil(src, a, b):
    """Return list of (silence_start, silence_end) absolute times within [a,b]."""
    a = max(0, a)
    r = subprocess.run(
        ["ffmpeg", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(src),
         "-af", f"silencedetect=noise={NOISE}:d={SILD}", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = []
    st = None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            st = float(m.group(1)) + a
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and st is not None:
            out.append((st, float(m.group(1)) + a))
            st = None
    return out


def snap_start(src, t):
    """Move start to the speech onset = end of the silence just before t."""
    sils = detect_sil(src, t - SNAP_WIN, t + SNAP_WIN)
    cands = [se for (ss, se) in sils if se <= t + 0.35]
    if cands:
        return max(0, max(cands) - EDGE)
    return t


def snap_end(src, t):
    """Move end to speech offset = start of the silence just after t."""
    sils = detect_sil(src, t - SNAP_WIN, t + SNAP_WIN)
    cands = [ss for (ss, se) in sils if ss >= t - 0.35]
    if cands:
        return min(cands) + EDGE
    return t


def main():
    takes = json.loads((BASE / sys.argv[1]).read_text(encoding="utf-8"))["takes"]
    src = SRC_DIR / f"{sys.argv[2]}.MOV"
    out = BASE / sys.argv[3]
    segmap_out = BASE / sys.argv[4]
    tmp = BASE / "build" / "sel"
    tmp.mkdir(parents=True, exist_ok=True)

    parts = []
    segmap = []
    newt = 0.0
    for tk in takes:
        s = snap_start(src, tk["start"])
        e = snap_end(src, tk["end"])
        if e - s < 0.4 or e - s > 22:
            # fallback to raw span if snap produced something silly
            s, e = tk["start"], tk["end"]
        p = tmp / f"s_{tk['line']:02d}.mp4"
        seglen = e - s
        af = f"aresample=48000,afade=t=in:st=0:d=0.02,afade=t=out:st={max(0,seglen-0.02):.3f}:d=0.02"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(src),
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}",
             "-af", af, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(p)])
        d = dur(p)
        segmap.append({"i": tk["line"] - 1, "t0": round(newt, 3), "t1": round(newt + d, 3),
                       "note": tk.get("verbatim", "")[:50], "src": [round(s, 2), round(e, 2)]})
        newt += d
        parts.append(p)

    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)])
    segmap_out.write_text(json.dumps(segmap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: {dur(out):.1f}s, {len(parts)} clean takes")
    for sg in segmap:
        print(f"  L{sg['i']+1:02d} {sg['t0']:5.1f}-{sg['t1']:5.1f} src{sg['src']} {sg['note'][:40]}")


if __name__ == "__main__":
    main()
