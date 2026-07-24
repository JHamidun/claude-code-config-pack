#!/usr/bin/env python3
"""Visual QA — contact sheet of the whole reel at a glance (one frame every N sec,
tiled). The fastest way to eyeball b-roll placement, captions, grade, jump-cuts
across the entire video without scrubbing. Used on every iteration of the reels.

Usage:
  python qa_contact_sheet.py VIDEO [--every 3.5] [--cols 6] [--out sheet.jpg]
"""
import argparse
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--every", type=float, default=3.5, help="seconds between sampled frames")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=4)
    ap.add_argument("--out", default="contact_sheet.jpg")
    a = ap.parse_args()
    vf = (f"fps=1/{a.every},scale=200:-2,tile={a.cols}x{a.rows},format=yuvj420p")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-vf", vf, "-frames:v", "1", a.out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1000:] + "\n")
        raise SystemExit(1)
    print(f"{a.out}: {a.cols}x{a.rows} grid, 1 frame / {a.every}s")


if __name__ == "__main__":
    main()
