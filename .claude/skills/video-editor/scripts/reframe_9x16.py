#!/usr/bin/env python3
"""Auto-reframe 16:9 → 9:16 (Shorts/Reels). Three methods, fast→smart.

Usage:
  python reframe_9x16.py in.mp4 out.mp4 --method center      # static center crop (instant)
  python reframe_9x16.py in.mp4 out.mp4 --method yolo        # subject-tracked (needs ultralytics)
  python reframe_9x16.py in.mp4 out.mp4 --method saliency    # saliency (needs pyautoflip)
  python reframe_9x16.py in.mp4 out.mp4 --ratio 9:16

center  = zero deps, good for centered subjects.
yolo    = person-tracking crop with smoothed motion (talking heads, people).
saliency= attention-based crop (products, scenery).
"""
import argparse
import subprocess
import sys


def center_crop(inp, out, rw, rh):
    subprocess.run(["ffmpeg", "-y", "-i", inp,
                    "-vf", "crop=ih*%d/%d:ih:(iw-ih*%d/%d)/2:0,scale=1080:1920" % (rw, rh, rw, rh),
                    "-c:v", "libx264", "-crf", "18", "-c:a", "copy", out], check=True)


def yolo_crop(inp, out, rw, rh):
    """Person-tracked crop, smoothed, via YOLOv8 + ffmpeg sendcmd."""
    from ultralytics import YOLO
    import cv2, numpy as np
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(inp)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cw = int(H * rw / rh)
    centers = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        res = model(fr, classes=[0], verbose=False)
        if res[0].boxes:
            b = res[0].boxes[0].xyxy[0].cpu().numpy()
            centers.append(int((b[0] + b[2]) / 2))
        else:
            centers.append(centers[-1] if centers else W // 2)
    cap.release()
    sm = np.convolve(centers, np.ones(30) / 30, mode="same")
    sm = np.clip(sm, cw // 2, W - cw // 2).astype(int)
    with open("_crop_cmd.txt", "w") as f:
        prev = -1
        for i, cx in enumerate(sm):
            x = int(cx - cw // 2)
            if x != prev:
                f.write("%.4f crop x %d;\n" % (i / fps, x)); prev = x
    subprocess.run(["ffmpeg", "-y", "-i", inp,
                    "-vf", "sendcmd=f=_crop_cmd.txt,crop=%d:%d,scale=1080:1920" % (cw, H),
                    "-c:v", "libx264", "-crf", "18", "-c:a", "copy", out], check=True)


def saliency_crop(inp, out, rw, rh):
    import subprocess as sp
    sp.run(["pyautoflip", "reframe", "-i", inp, "-o", out,
            "--method", "saliency", "--aspect-ratio", "%d:%d" % (rw, rh)], check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--method", default="center", choices=["center", "yolo", "saliency"])
    ap.add_argument("--ratio", default="9:16")
    a = ap.parse_args()
    rw, rh = (int(x) for x in a.ratio.split(":"))
    {"center": center_crop, "yolo": yolo_crop, "saliency": saliency_crop}[a.method](a.input, a.output, rw, rh)
    print("reframed (%s):" % a.method, a.output)


if __name__ == "__main__":
    main()
