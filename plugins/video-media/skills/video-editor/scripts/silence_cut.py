#!/usr/bin/env python3
"""Silence / jump-cut auto-removal.

Two engines:
  --engine auto-editor  (default) : wraps `auto-editor` (best, NLE export). pip install auto-editor
  --engine ffmpeg                 : pure ffmpeg silencedetect + concat (no extra dep)

Usage:
  python silence_cut.py in.mp4 out.mp4
  python silence_cut.py in.mp4 out.mp4 --threshold-db -35 --min-silence 0.4 --margin 0.1
  python silence_cut.py in.mp4 out.xml --engine auto-editor --export resolve   # NLE roundtrip
"""
import argparse
import re
import subprocess
import sys


def auto_editor(inp, out, margin, threshold_pct, export):
    cmd = ["auto-editor", inp, "--margin", "%gsec" % margin,
           "--edit", "audio:threshold=%g%%" % threshold_pct, "-o", out]
    if export:
        cmd += ["--export", export]
    subprocess.run(cmd, check=True)


def detect_silence(inp, thresh_db, min_dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-vn", "-i", inp,
                        "-af", "silencedetect=n=%ddB:d=%g" % (thresh_db, min_dur), "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (\S+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (\S+)", r.stderr)]
    return list(zip(starts, ends))


def total_dur(inp):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", inp], capture_output=True, text=True)
    return float(r.stdout.strip())


def keep_segments(silences, total, pad):
    keep, prev = [], 0.0
    for s, e in silences:
        seg_end = s + pad
        if seg_end - prev > 0.1:
            keep.append((max(0, prev - pad), seg_end))
        prev = e
    if total - prev > 0.1:
        keep.append((max(0, prev - pad), total))
    return keep


def ffmpeg_cut(inp, out, segs):
    fp = []
    for i, (s, e) in enumerate(segs):
        fp.append("[0:v]trim=%.3f:%.3f,setpts=PTS-STARTPTS[v%d];" % (s, e, i))
        fp.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS[a%d];" % (s, e, i))
    n = len(segs)
    fp.append("".join("[v%d][a%d]" % (i, i) for i in range(n)) + "concat=n=%d:v=1:a=1[outv][outa]" % n)
    subprocess.run(["ffmpeg", "-y", "-i", inp, "-filter_complex", "".join(fp),
                    "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "fast",
                    "-crf", "20", "-c:a", "aac", out], check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--engine", default="auto-editor", choices=["auto-editor", "ffmpeg"])
    ap.add_argument("--threshold-db", type=int, default=-35)
    ap.add_argument("--threshold-pct", type=float, default=4.0)
    ap.add_argument("--min-silence", type=float, default=0.4)
    ap.add_argument("--margin", type=float, default=0.1)
    ap.add_argument("--export", default=None, help="auto-editor: davinci-resolve|premiere|final-cut-pro")
    a = ap.parse_args()
    if a.engine == "auto-editor":
        auto_editor(a.input, a.output, a.margin, a.threshold_pct, a.export)
    else:
        sil = detect_silence(a.input, a.threshold_db, a.min_silence)
        segs = keep_segments(sil, total_dur(a.input), a.margin)
        print("silences: %d -> keep %d segments" % (len(sil), len(segs)))
        ffmpeg_cut(a.input, a.output, segs)
    print("saved", a.output)


if __name__ == "__main__":
    main()
