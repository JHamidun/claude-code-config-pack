"""Process single MP4 → 512x512 VP9-alpha WebM sticker (≤256KB).

Pipeline: rembg+chromakey seed (frame 0) → SAM2 propagate → per-frame chromakey UNION
        → RGBA PNG → yuva420p → WSL alpha_encoder → WebM.

Usage:
    python process_one.py --mp4 input.mp4 --out output.webm
    python process_one.py --mp4 input.mp4 --out output.webm --no-chromakey  # disable per-frame ck
    python process_one.py --mp4 input.mp4 --out output.webm --ck-threshold 200
"""
import sys, io, os, subprocess, tempfile, shutil, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import cuda_init  # noqa: F401  ← MUST be first
import numpy as np
from PIL import Image
import cv2
import torch
from sam2.build_sam import build_sam2_video_predictor
from rembg import remove, new_session

from _config import (sam2_checkpoint as _sam2_ckpt, sam2_config as _sam2_cfg,
                     wsl_distro, alpha_encoder_path, to_wsl_path)

DEFAULT_CHECKPOINT = _sam2_ckpt()
DEFAULT_CONFIG = _sam2_cfg()


def to_wsl(p):
    p = p.replace('\\', '/')
    if len(p) > 1 and p[1] == ':':
        return f'/mnt/{p[0].lower()}{p[2:]}'
    return p


def chromakey_inv_white(rgb, t=215):
    """Returns uint8 0/255 mask. 255 = non-white (foreground)."""
    return ((rgb.min(axis=-1) < t).astype(np.uint8) * 255)


def process(mp4, out, ck_threshold=215, per_frame_chromakey=True,
            duration=3, fps=30, size=512,
            rembg_model='isnet-general-use',
            sam2_config=DEFAULT_CONFIG, sam2_checkpoint=DEFAULT_CHECKPOINT,
            work_parent=None):
    work = tempfile.mkdtemp(prefix='spg_', dir=work_parent or os.path.dirname(out))
    print(f'work: {work}')
    try:
        raw_dir = f'{work}/raw'; os.makedirs(raw_dir)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4,
                        '-t', str(duration),
                        '-vf', f"crop='min(iw,ih)':'min(iw,ih)',scale={size}:{size},fps={fps}",
                        '-qmin', '1', '-q:v', '1',
                        f'{raw_dir}/%05d.jpg'], check=True)
        files = sorted(os.listdir(raw_dir))
        print(f'frames: {len(files)}')

        # Seed: rembg ∪ chromakey on frame 0
        rgb0 = np.array(Image.open(f'{raw_dir}/{files[0]}').convert('RGB'))
        sess = new_session(rembg_model,
                           providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        with open(f'{raw_dir}/{files[0]}', 'rb') as f:
            rem0 = np.array(Image.open(io.BytesIO(remove(f.read(), session=sess))).convert('RGBA'))
        rembg_mask = (rem0[..., 3] > 128).astype(np.uint8) * 255
        ck0 = chromakey_inv_white(rgb0, t=ck_threshold)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        seed = cv2.morphologyEx(np.maximum(rembg_mask, ck0), cv2.MORPH_CLOSE, kernel)
        seed_bool = (seed > 0).astype(np.uint8)
        print(f'seed coverage: {seed_bool.sum()} px')

        # SAM2 propagate
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        predictor = build_sam2_video_predictor(sam2_config, sam2_checkpoint, device=device)
        with torch.inference_mode(), torch.autocast(device.type, dtype=torch.bfloat16):
            state = predictor.init_state(video_path=raw_dir)
            predictor.add_new_mask(inference_state=state, frame_idx=0, obj_id=1,
                                   mask=torch.from_numpy(seed_bool).to(device))
            sam2_masks = {}
            for fi, _, ml in predictor.propagate_in_video(state):
                sam2_masks[fi] = (ml[0] > 0.0).cpu().numpy().squeeze(0)

        # Compose RGBA frames
        smooth = f'{work}/smooth'; os.makedirs(smooth)
        for i, fn in enumerate(files):
            rgb = np.array(Image.open(f'{raw_dir}/{fn}').convert('RGB'))
            sam_m = sam2_masks.get(i, np.zeros((size, size), dtype=bool)).astype(np.uint8) * 255
            if per_frame_chromakey:
                ck_m = chromakey_inv_white(rgb, t=ck_threshold)
                union = np.maximum(sam_m, ck_m)
            else:
                union = sam_m
            closed = cv2.morphologyEx(union, cv2.MORPH_CLOSE, kernel)
            a = closed.astype(np.int16)
            a = np.where(a < 60, 0, a)
            a = np.where(a > 180, 255, a).astype(np.uint8)
            Image.fromarray(np.dstack([rgb, a]), 'RGBA').save(f'{smooth}/{i+1:05d}.png')

        # Raw yuva420p
        yuva = f'{work}/raw.yuva'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps),
                        '-i', f'{smooth}/%05d.png', '-pix_fmt', 'yuva420p',
                        '-f', 'rawvideo', yuva], check=True)

        # WSL alpha_encoder
        subprocess.run(['wsl', '-d', wsl_distro(), '-u', 'root', 'bash', '-c',
                        f'cd /tmp && wd=$(mktemp -d) && cd $wd && '
                        f'{alpha_encoder_path()} '
                        f'-w {size} -h {size} -i {to_wsl(yuva)} -o {to_wsl(out)} '
                        f'-c vp9 > /dev/null 2>&1'], check=True)
        sz = os.path.getsize(out)
        print(f'OUT: {out} ({sz}b)')
        if sz > 256_000:
            print(f'WARNING: file >{256_000}b, Telegram may reject')
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mp4', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--ck-threshold', type=int, default=215)
    ap.add_argument('--no-chromakey', action='store_true',
                    help='disable per-frame chromakey UNION (SAM2 alone)')
    ap.add_argument('--rembg-model', default='isnet-general-use')
    ap.add_argument('--checkpoint', default=DEFAULT_CHECKPOINT)
    ap.add_argument('--config', default=DEFAULT_CONFIG)
    args = ap.parse_args()
    process(args.mp4, args.out,
            ck_threshold=args.ck_threshold,
            per_frame_chromakey=not args.no_chromakey,
            rembg_model=args.rembg_model,
            sam2_config=args.config, sam2_checkpoint=args.checkpoint)


if __name__ == '__main__':
    main()
