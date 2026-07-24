#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Cut clean VO from raw takes per EDL.

edl.json: [{"file": "audio/raw_5785.wav", "start": 12.34, "end": 18.9}, ...]
Renders segments with 8ms edge fades, concatenated, into one WAV.

Usage: python cut_audio.py edl_r1.json audio/vo_r1.wav [--gap 0.12]
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())


def main():
    edl_path, out_path = sys.argv[1], sys.argv[2]
    gap = 0.12
    if "--gap" in sys.argv:
        gap = float(sys.argv[sys.argv.index("--gap") + 1])
    edl = json.loads(Path(edl_path).read_text(encoding="utf-8"))

    files = []
    for seg in edl:
        f = str((BASE / seg["file"]).resolve())
        if f not in files:
            files.append(f)
    fidx = {f: i for i, f in enumerate(files)}

    parts = []
    fc = []
    n = 0
    for seg in edl:
        f = str((BASE / seg["file"]).resolve())
        s, e = seg["start"], seg["end"]
        dur = e - s
        fade = min(0.008, dur / 4)
        fc.append(
            f"[{fidx[f]}:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={dur - fade:.3f}:d={fade:.3f}[s{n}]"
        )
        parts.append(f"[s{n}]")
        n += 1
        if gap > 0 and seg is not edl[-1] and not seg.get("nogap"):
            fc.append(f"anullsrc=channel_layout=stereo:sample_rate=48000,atrim=duration={gap}[g{n}]")
            parts.append(f"[g{n}]")
            n += 1

    fc.append("".join(parts) + f"concat=n={len(parts)}:v=0:a=1[out]")

    cmd = ["ffmpeg", "-y", "-v", "error"]
    for f in files:
        cmd += ["-i", f]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", "-ar", "48000", str(out_path)]
    subprocess.run(cmd, check=True)

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True,
    )
    print(f"OK {out_path}: {float(r.stdout.strip()):.2f}s from {len(edl)} segments")


if __name__ == "__main__":
    main()
