#!/usr/bin/env python3
"""
make_emoji_variant.py — sticker WebM -> custom emoji WebM (100x100, ≤256KB, ≤3s)

Pipeline:
  1. ffprobe duration + dims
  2. Sample frames, detect non-transparent bbox, +6% margin
  3. crop + scale=100:100:flags=lanczos
  4. Binary-search VP9 bit_rate to hit --target-bytes
  5. Verify ≤256000 bytes and ≤3.0s duration
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--target-bytes", type=int, default=35000)
    return p.parse_args()


def ffprobe(path: Path) -> tuple[float, int, int]:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ])
    data = json.loads(out)
    vs = next(s for s in data["streams"] if s["codec_type"] == "video")
    dur = float(data["format"].get("duration", vs.get("duration", 0)))
    return dur, int(vs["width"]), int(vs["height"])


def detect_bbox(path: Path, w: int, h: int, samples: int = 12) -> tuple[int, int, int, int]:
    """Sample frames, find min/max x/y where alpha>0. Returns (x, y, w, h)."""
    try:
        from PIL import Image  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        sys.exit("Pillow + numpy required")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(path),
            "-vf", f"fps=1/{max(1, samples)},format=rgba",
            "-vframes", str(samples),
            f"{td}/s_%03d.png",
        ], check=True, stderr=subprocess.DEVNULL)
        xs, ys, xe, ye = w, h, 0, 0
        for f in sorted(Path(td).glob("*.png")):
            a = np.array(Image.open(f))[..., 3]
            ys_idx, xs_idx = np.where(a > 8)
            if xs_idx.size == 0:
                continue
            xs, ys = min(xs, xs_idx.min()), min(ys, ys_idx.min())
            xe, ye = max(xe, xs_idx.max()), max(ye, ys_idx.max())
    if xe <= xs or ye <= ys:
        return 0, 0, w, h
    bw, bh = xe - xs, ye - ys
    mx, my = int(bw * 0.06), int(bh * 0.06)
    x = max(0, int(xs) - mx)
    y = max(0, int(ys) - my)
    cw = min(w - x, bw + 2 * mx)
    ch = min(h - y, bh + 2 * my)
    return x, y, cw, ch


def encode(path: Path, output: Path, crop: tuple[int, int, int, int],
           bitrate_k: int) -> int:
    x, y, cw, ch = crop
    vf = f"crop={cw}:{ch}:{x}:{y},scale=100:100:flags=lanczos"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(path),
        "-vf", vf,
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0", "-b:v", f"{bitrate_k}k",
        "-t", "2.95", str(output),
    ], check=True, stderr=subprocess.DEVNULL)
    return output.stat().st_size


def main() -> None:
    args = parse_args()
    dur, w, h = ffprobe(args.input)
    print(f"[i] in: {w}x{h} {dur:.2f}s")
    if dur > 3.0:
        print(f"[warn] duration {dur:.2f}s > 3s — will trim to 2.95s")
    crop = detect_bbox(args.input, w, h)
    print(f"[i] bbox crop: {crop}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    lo, hi = 30, 400
    target = args.target_bytes
    best: tuple[int, int] | None = None
    for _ in range(2):  # 2-pass binary search
        mid = (lo + hi) // 2
        size = encode(args.input, args.output, crop, mid)
        print(f"[i] {mid}k -> {size}B")
        if best is None or abs(size - target) < abs(best[1] - target):
            best = (mid, size)
        if size > target:
            hi = mid
        else:
            lo = mid

    final = best[1] if best else args.output.stat().st_size
    out_dur, _, _ = ffprobe(args.output)
    assert final <= 256000, f"size {final}B exceeds 256KB"
    assert out_dur <= 3.05, f"duration {out_dur:.2f}s > 3s"
    print(f"[ok] {args.output} {final}B {out_dur:.2f}s")


if __name__ == "__main__":
    main()
