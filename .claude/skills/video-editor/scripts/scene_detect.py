#!/usr/bin/env python3
"""Shot/scene detection + optional split (PySceneDetect).

Usage:
  python scene_detect.py in.mp4                       # print scene cut timecodes
  python scene_detect.py in.mp4 --split --out-dir scenes/   # split into per-scene mp4s
  python scene_detect.py in.mp4 --threshold 3.0       # adaptive sensitivity (1.5 talk, 6 action)
  python scene_detect.py in.mp4 --json cuts.json      # dump cut times (sec) as JSON

Deps: pip install scenedetect opencv-python
Use for: auto b-roll segmentation, finding cut points in source footage, QC of own edits.
"""
import argparse
import json
import sys


def detect(video, threshold):
    from scenedetect import detect as sd_detect, AdaptiveDetector
    scenes = sd_detect(video, AdaptiveDetector(adaptive_threshold=threshold))
    return [(s.get_seconds(), e.get_seconds()) for s, e in scenes]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--threshold", type=float, default=3.0)
    ap.add_argument("--split", action="store_true")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    scenes = detect(a.video, a.threshold)
    print("found %d scenes:" % len(scenes))
    for i, (s, e) in enumerate(scenes):
        print("  %2d  %.2f -> %.2f  (%.2fs)" % (i + 1, s, e, e - s))
    if a.json:
        json.dump([{"start": s, "end": e} for s, e in scenes], open(a.json, "w"), indent=2)
        print("wrote", a.json)
    if a.split:
        from scenedetect import detect as sd_detect, AdaptiveDetector, split_video_ffmpeg
        sl = sd_detect(a.video, AdaptiveDetector(adaptive_threshold=a.threshold))
        split_video_ffmpeg(a.video, sl, output_dir=a.out_dir)
        print("split ->", a.out_dir)


if __name__ == "__main__":
    main()
