#!/usr/bin/env python3
"""Grade calibration helper — side-by-side variants of an exposure/LUT grade on ONE
bright frame, so you pick the right strength in a single look (instead of 5 renders).

Why: client kept saying "картинка супер светлая" — soft grade wasn't enough. Compare
0.86 / 0.78 / 0.72 highlight-rolloff variants on the brightest frame, read with eyes.

Usage:
  python grade_preview.py VIDEO --t 2.0 [--lut /path/Kodak2383.cube] [--out preview.jpg]

Outputs a horizontal strip: RAW | soft(0.86) | medium(0.78) | strong(0.72).
Pick a level, then put its curve into assemble_overlay.py grade.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# (label, curves highlight point, brightness, gamma, saturation)
VARIANTS = [
    ("soft_0.86", "0/0 0.5/0.45 1/0.86", -0.04, 1.00, 1.02),
    ("med_0.78", "0/0 0.5/0.42 1/0.78", -0.07, 1.00, 1.03),
    ("strong_0.72", "0/0 0.5/0.40 1/0.72", -0.09, 0.95, 1.04),
]
DEFAULT_LUT = Path.home() / ".claude/skills/video-generation/luts/_sanitized_Kodak2383_D55.cube"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-1200:] + "\n")
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--t", type=float, default=2.0, help="timestamp of a BRIGHT frame (sec)")
    ap.add_argument("--lut", default=str(DEFAULT_LUT))
    ap.add_argument("--out", default="grade_preview.jpg")
    a = ap.parse_args()

    tmp = Path("_grade_tmp")
    tmp.mkdir(exist_ok=True)
    # LUT colon-escape on Windows is unreliable in filter args → copy to a relative path.
    lut_local = tmp / "lut.cube"
    if Path(a.lut).exists():
        shutil.copy(a.lut, lut_local)
    raw = tmp / "raw.png"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a.t}", "-i", a.video, "-frames:v", "1", str(raw)])

    frames = [raw]
    for label, hi, br, gm, sat in VARIANTS:
        out = tmp / f"{label}.png"
        lut3d = f"lut3d={lut_local.as_posix()}:interp=tetrahedral," if lut_local.exists() else ""
        vf = f"curves=all='{hi}',eq=brightness={br}:gamma={gm},{lut3d}eq=saturation={sat}"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-vf", vf, str(out)])
        frames.append(out)

    inputs = []
    for f in frames:
        inputs += ["-i", str(f)]
    n = len(frames)
    fc = ("".join(f"[{i}]scale=240:-2[s{i}];" for i in range(n))
          + "".join(f"[s{i}]" for i in range(n)) + f"hstack={n},format=yuvj420p")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-frames:v", "1", a.out])
    print(f"{a.out}: RAW | {' | '.join(v[0] for v in VARIANTS)}  (read it, pick a level)")


if __name__ == "__main__":
    main()
