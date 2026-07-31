#!/usr/bin/env python3
"""Speed ramps — slow-mo / fast segments with audio-tempo correction + motion blur.

Usage:
  python speed_ramp.py in.mp4 out.mp4 --ramp "0:3:0.25, 3:12:1.0, 12:18:2.0"
    ramp = comma-separated  start:end:speed   (speed 0.25 = 4x slo-mo, 2.0 = 2x fast)
  python speed_ramp.py in.mp4 out.mp4 --ramp "..." --motion-blur   # tmix on fast parts
  python speed_ramp.py in.mp4 out_slow.mp4 --true-slowmo 4         # minterpolate 4x (no ramp)

Notes: ffmpeg atempo only accepts 0.5-2.0 → chained automatically for extreme speeds.
"""
import argparse
import subprocess
import sys


def atempo_chain(speed):
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0"); s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5"); s *= 2.0
    parts.append("atempo=%.4f" % s)
    return ",".join(parts)


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def build_ramp(inp, out, segs, motion_blur=False):
    audio = has_audio(inp)
    fc_v, fc_a, cv, ca = [], [], "", ""
    for i, (start, end, speed) in enumerate(segs):
        pts = 1.0 / speed
        vf = "[0:v]trim=%s:%s,setpts=%.4f*(PTS-STARTPTS)" % (start, end, pts)
        if motion_blur and speed > 1.0:
            vf += ",tmix=frames=8:weights='1 1 1 1 1 1 1 1'"
        fc_v.append(vf + "[v%d];" % i)
        cv += "[v%d]" % i
        if audio:
            fc_a.append("[0:a]atrim=%s:%s,asetpts=PTS-STARTPTS,%s[a%d];" % (start, end, atempo_chain(speed), i))
            ca += "[a%d]" % i
    n = len(segs)
    if audio:
        fc = "".join(fc_v) + "".join(fc_a) + "%s%sconcat=n=%d:v=1:a=1[outv][outa]" % (cv, ca, n)
        maps = ["-map", "[outv]", "-map", "[outa]", "-c:a", "aac", "-b:a", "192k"]
    else:
        fc = "".join(fc_v) + "%sconcat=n=%d:v=1:a=0[outv]" % (cv, n)
        maps = ["-map", "[outv]"]
    subprocess.run(["ffmpeg", "-y", "-i", inp, "-filter_complex", fc] + maps +
                   ["-c:v", "libx264", "-preset", "slow", "-crf", "18", out], check=True)


def true_slowmo(inp, out, factor):
    subprocess.run(["ffmpeg", "-y", "-i", inp, "-vf",
                    "minterpolate=fps=120:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=%.2f*PTS" % factor,
                    "-r", "30", "-an", out], check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--ramp", help="start:end:speed, comma-separated")
    ap.add_argument("--motion-blur", action="store_true")
    ap.add_argument("--true-slowmo", type=float, help="minterpolate factor (e.g. 4)")
    a = ap.parse_args()
    if a.true_slowmo:
        true_slowmo(a.input, a.output, a.true_slowmo)
    else:
        segs = []
        for part in a.ramp.split(","):
            s, e, sp = part.strip().split(":")
            segs.append((float(s), float(e), float(sp)))
        build_ramp(a.input, a.output, segs, a.motion_blur)
    print("saved", a.output)


if __name__ == "__main__":
    main()
