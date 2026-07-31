#!/usr/bin/env python3
"""Color grading — apply LUT or built-in film looks via ffmpeg.

Usage:
  python color_grade.py in.mp4 out.mp4 --lut kodak2383          # bundled LUT name or .cube path
  python color_grade.py in.mp4 out.mp4 --lut path/to/look.cube --strength 0.7
  python color_grade.py in.mp4 out.mp4 --look teal-orange       # no LUT file needed
  python color_grade.py in.mp4 out.mp4 --look film              # LUT + lifted blacks + vignette + grain
  python color_grade.py in.mp4 out.mp4 --look grain             # grain only

Bundled LUTs live in skills/video-generation/luts/. Apply color as the FINAL video
filter step (after edits, before loudnorm pass).
"""
import argparse
import os
import re
import subprocess
import sys

LUT_DIR = os.path.expanduser("~/.claude/skills/video-generation/luts")
BUNDLED = {"kodak2383": "Kodak2383_D55.cube"}


def _sanitize_cube(path):
    """ffmpeg lut3d rejects the `LUT_3D_INPUT_RANGE` keyword (wants DOMAIN_MIN/MAX).
    If present, write a cleaned temp copy and return its path; else return original."""
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return path
    if "LUT_3D_INPUT_RANGE" not in txt:
        return path
    out = re.sub(r"(?im)^\s*LUT_3D_INPUT_RANGE.*$", "", txt)
    tmp = os.path.join(LUT_DIR, "_sanitized_" + os.path.basename(path))
    open(tmp, "w", encoding="utf-8").write(out)
    return tmp


def fesc(p):
    """forward slashes + ESCAPE drive colon for ffmpeg filter args (Windows gotcha:
    ffmpeg treats ':' as option separator even inside quotes)."""
    return p.replace("\\", "/").replace(":", "\\:")


def resolve_lut(name):
    p = os.path.join(LUT_DIR, BUNDLED[name]) if name in BUNDLED else name
    return fesc(_sanitize_cube(p))


def run(inp, out, vf, crf=18, tune=None):
    cmd = ["ffmpeg", "-y", "-i", inp, "-vf", vf, "-c:v", "libx264", "-crf", str(crf),
           "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy"]
    if tune:
        cmd += ["-tune", tune]
    cmd += [out]
    subprocess.run(cmd, check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--lut", help="bundled name (kodak2383) or .cube path")
    ap.add_argument("--strength", type=float, default=1.0, help="LUT blend 0-1")
    ap.add_argument("--look", choices=["teal-orange", "film", "grain"], help="built-in look")
    a = ap.parse_args()

    TEAL = ("colorbalance=rs=0.05:gs=-0.05:bs=-0.15:rm=0.03:gm=-0.03:bm=-0.08:"
            "rh=0.12:gh=-0.05:bh=-0.18,curves=all='0/0 0.25/0.20 0.5/0.50 0.75/0.82 1/1'")
    if a.look == "teal-orange":
        run(a.input, a.output, TEAL)
    elif a.look == "grain":
        run(a.input, a.output, "noise=c0s=25:c0f=t+u", tune="grain")
    elif a.look == "film":
        lut = resolve_lut(a.lut or "kodak2383")
        run(a.input, a.output,
            "lut3d=file='%s':interp=tetrahedral,"
            "curves=all='0/0.10 0.5/0.52 1/0.97',"
            "colorbalance=rs=0.05:bs=-0.10:rh=0.08:bh=-0.12,"
            "vignette=angle=PI/5,noise=c0s=20:c0f=t+u" % lut, crf=16, tune="grain")
    elif a.lut:
        lut = resolve_lut(a.lut)
        if a.strength < 1.0:
            k = a.strength
            vf = ("[0:v]split[a][b];[a]lut3d=file='%s':interp=tetrahedral[l];"
                  "[b][l]blend=all_expr='A*%.2f+B*%.2f'" % (lut, 1 - k, k))
            subprocess.run(["ffmpeg", "-y", "-i", a.input, "-filter_complex", vf,
                            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", a.output], check=True)
        else:
            run(a.input, a.output, "lut3d=file='%s':interp=tetrahedral" % lut)
    else:
        ap.error("specify --lut or --look")
    print("graded:", a.output)


if __name__ == "__main__":
    main()
