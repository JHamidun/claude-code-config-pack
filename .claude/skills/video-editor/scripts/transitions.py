#!/usr/bin/env python3
"""Transitions between clips — ffmpeg xfade chain + special effect cuts.

Pure ffmpeg (no node-gyp / GL build needed). Covers the 44 built-in xfade transitions
plus hand-built flash / glitch / whip-pan cuts.

Usage:
  python transitions.py a.mp4 b.mp4 c.mp4 -o out.mp4 --transition wipeleft --dur 0.2
  python transitions.py a.mp4 b.mp4 -o out.mp4 --effect flash     # white flash cut
  python transitions.py a.mp4 b.mp4 -o out.mp4 --effect glitch    # RGB-split + pixelize
  python transitions.py a.mp4 b.mp4 -o out.mp4 --effect whip      # motion-blur whip

xfade names: fade fadeblack fadewhite dissolve wipeleft/right/up/down
slideleft/right/up/down circleopen circleclose pixelize zoomin radial hblur
diagtl diagtr smoothleft ... (44 total — see references/xfade-transitions.md)

For GLSL-grade transitions without recompiling ffmpeg, use the `xfade-easing` project
(https://github.com/scriptituk/xfade-easing) expression mode — see the reference doc.
"""
import argparse
import subprocess
import sys


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", p], capture_output=True, text=True)
    return float(r.stdout.strip())


def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def xfade_chain(clips, out, transition, d, music=None):
    n = len(clips)
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    durs = [dur(c) for c in clips]
    audio = all(has_audio(c) for c in clips)
    norm = "".join("[%d:v]settb=AVTB,setsar=1,fps=30[%dv];" % (i, i) for i in range(n))
    fgv, fga, cum, lv, la = [], [], 0.0, "0v", "0:a"
    for i in range(1, n):
        cum += durs[i - 1] - d
        ov = "xv%d" % i if i < n - 1 else "outv"
        fgv.append("[%s][%dv]xfade=transition=%s:duration=%.3f:offset=%.4f[%s]" % (lv, i, transition, d, cum, ov))
        lv = ov
        if audio:
            oa = "xa%d" % i if i < n - 1 else "outa"
            fga.append("[%s][%d:a]acrossfade=d=%.3f[%s]" % (la, i, d, oa))
            la = oa
    fc = norm + ";".join(fgv) + ((";" + ";".join(fga)) if audio else "")
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", "[outv]"]
    if audio:
        cmd += ["-map", "[outa]"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", out]
    subprocess.run(cmd, check=True)


def flash(a, b, out, d=0.15):
    subprocess.run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex",
                    "[0:v][1:v]xfade=transition=fadewhite:duration=%g:offset=%.3f" % (d, dur(a) - d),
                    "-c:v", "libx264", "-crf", "18", out], check=True)


def glitch(a, b, out):
    off = dur(a) - 0.4
    fc = ("[0:v]rgbashift=rh=-8:gh=8:bv=-4[ag];"
          "[ag][1:v]xfade=transition=pixelize:duration=0.4:offset=%.3f[out]" % off)
    subprocess.run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex", fc,
                    "-map", "[out]", "-c:v", "libx264", "-crf", "18", out], check=True)


def whip(a, b, out):
    da = dur(a)
    fc = ("[0:v]boxblur=luma_radius='if(gte(t,%.3f),min((t-%.3f)*80,40),0)':luma_power=1[ab];"
          "[ab][1:v]xfade=transition=wipeleft:duration=0.2:offset=%.3f[out]" % (da - 0.5, da - 0.5, da - 0.2))
    subprocess.run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex", fc,
                    "-map", "[out]", "-c:v", "libx264", "-crf", "18", out], check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("-o", "--output", default="transition_out.mp4")
    ap.add_argument("--transition", default="fade")
    ap.add_argument("--dur", type=float, default=0.25)
    ap.add_argument("--effect", choices=["flash", "glitch", "whip"], help="2-clip special cut")
    a = ap.parse_args()
    if a.effect:
        if len(a.clips) != 2:
            ap.error("--effect needs exactly 2 clips")
        {"flash": flash, "glitch": glitch, "whip": whip}[a.effect](a.clips[0], a.clips[1], a.output)
    else:
        xfade_chain(a.clips, a.output, a.transition, a.dur)
    print("saved", a.output)


if __name__ == "__main__":
    main()
