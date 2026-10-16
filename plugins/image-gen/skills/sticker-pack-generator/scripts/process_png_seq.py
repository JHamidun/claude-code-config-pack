#!/usr/bin/env python3
"""
process_png_seq.py — PNG sequence -> alpha WebM (VP9 yuva420p)

Pipeline:
  1. rembg isnet-general-use (alpha matting) on first frame -> seed mask
  2. SAM2 propagate seed mask across all frames (CUDA if available)
  3. UNION(SAM2, rembg-per-frame, chromakey>235 invert) per frame
  4. Apply mask -> RGBA PNG temp sequence
  5. ffmpeg encode VP9 yuva420p (or $STICKER_ALPHA_ENCODER if set)

Env:
  STICKER_ALPHA_ENCODER  optional path to alternative encoder binary
  SAM2_CHECKPOINT        path to SAM2 .pt checkpoint (required for SAM2 stage)
  REMBG_MODEL            override rembg model (default: isnet-general-use)
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
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PNG sequence -> alpha WebM")
    p.add_argument("--input-dir", required=True, type=Path,
                   help="dir with frame PNGs (sorted lexicographically)")
    p.add_argument("--output", required=True, type=Path,
                   help="output webm path")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--size", type=int, default=512,
                   help="square output size (px)")
    p.add_argument("--chromakey-thr", type=int, default=235,
                   help="luminance threshold for chromakey union (0..255)")
    return p.parse_args()


def collect_frames(input_dir: Path) -> list[Path]:
    frames = sorted(p for p in input_dir.iterdir()
                    if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not frames:
        sys.exit(f"no frames in {input_dir}")
    return frames


def rembg_first_frame_mask(frame_path: Path):
    """Run rembg isnet-general-use with alpha matting -> binary mask (np.uint8)."""
    model = os.environ.get("REMBG_MODEL", "isnet-general-use")
    try:
        from rembg import new_session, remove  # type: ignore
        from PIL import Image  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        sys.exit("rembg + Pillow + numpy required: pip install rembg pillow numpy")
    session = new_session(model)
    img = Image.open(frame_path).convert("RGBA")
    out = remove(
        img, session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=2,
    )
    return np.array(out.split()[-1])  # alpha channel


def sam2_propagate(frames: list[Path], seed_mask):
    """Propagate seed_mask across `frames` using SAM2 video predictor.

    Returns list[np.uint8] masks, one per frame (same dims as frames).
    Stubbed: requires SAM2 checkpoint via $SAM2_CHECKPOINT.
    """
    ckpt = os.environ.get("SAM2_CHECKPOINT")
    if not ckpt or not Path(ckpt).exists():
        print("[warn] SAM2_CHECKPOINT not set or missing — SAM2 stage skipped, "
              "falling back to rembg-per-frame + chromakey only.",
              file=sys.stderr)
        return None
    # TODO: import sam2.build_sam, init_video_predictor, add_new_mask(seed_mask),
    # propagate_in_video — yield per-frame mask. CUDA if torch.cuda.is_available().
    raise NotImplementedError(
        "SAM2 propagate not wired — plug your sam2 install here. "
        "Use sam2.build_sam.build_sam2_video_predictor(ckpt) and "
        "predictor.propagate_in_video over frames.")


def rembg_per_frame_mask(frame_path: Path):
    try:
        from rembg import new_session, remove  # type: ignore
        from PIL import Image  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return None
    model = os.environ.get("REMBG_MODEL", "isnet-general-use")
    session = new_session(model)
    img = Image.open(frame_path).convert("RGBA")
    out = remove(img, session=session)
    return np.array(out.split()[-1])


def chromakey_mask(frame_path: Path, threshold: int):
    """Return mask where pixels brighter than `threshold` are background (0)."""
    try:
        from PIL import Image  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return None
    img = np.array(Image.open(frame_path).convert("RGB"))
    luma = (0.299 * img[..., 0] + 0.587 * img[..., 1]
            + 0.114 * img[..., 2]).astype("uint8")
    mask = (luma <= threshold).astype("uint8") * 255
    return mask


def union_masks(*masks):
    import numpy as np  # type: ignore
    valid = [m for m in masks if m is not None]
    if not valid:
        return None
    base = valid[0].astype("uint16")
    for m in valid[1:]:
        if m.shape != base.shape:
            continue
        base = np.maximum(base, m.astype("uint16"))
    return base.clip(0, 255).astype("uint8")


def apply_mask_save(frame_path: Path, mask, out_path: Path, size: int):
    from PIL import Image  # type: ignore
    import numpy as np  # type: ignore
    img = Image.open(frame_path).convert("RGBA")
    if mask is not None:
        arr = np.array(img)
        arr[..., 3] = mask
        img = Image.fromarray(arr, "RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    img.save(out_path, "PNG")


def encode_webm(temp_dir: Path, output: Path, fps: int) -> None:
    encoder = os.environ.get("STICKER_ALPHA_ENCODER")
    if encoder and Path(encoder).exists():
        cmd = [encoder, "--input", str(temp_dir), "--fps", str(fps),
               "--output", str(output)]
    else:
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(temp_dir / "%04d.png"),
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0", "-b:v", "250k",
            str(output),
        ]
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()
    frames = collect_frames(args.input_dir)
    print(f"[i] {len(frames)} frames")

    seed = rembg_first_frame_mask(frames[0])
    print("[i] seed mask via rembg ok")

    sam_masks = sam2_propagate(frames, seed)

    with tempfile.TemporaryDirectory(prefix="stickerpack_") as td:
        td_path = Path(td)
        for i, frame in enumerate(frames):
            sam = sam_masks[i] if sam_masks is not None else None
            rmb = rembg_per_frame_mask(frame)
            chr_ = chromakey_mask(frame, args.chromakey_thr)
            mask = union_masks(sam, rmb, chr_)
            apply_mask_save(frame, mask, td_path / f"{i:04d}.png", args.size)
            if i % 10 == 0:
                print(f"[i] masked {i+1}/{len(frames)}")
        encode_webm(td_path, args.output, args.fps)
    print(f"[ok] wrote {args.output}")


if __name__ == "__main__":
    main()
