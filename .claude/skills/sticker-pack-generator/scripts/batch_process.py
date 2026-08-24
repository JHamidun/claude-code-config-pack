"""Batch process: process every MP4 in mp4-dir → webm-dir.

Skips outputs that already exist (resumable).

Usage:
    python batch_process.py --mp4-dir ./mp4s --out-dir ./webms
"""
import sys, io, os, argparse, time, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# Тяжёлый стек (torch / rembg / sam2) здесь не импортируется: его подтягивает
# process_one._load_deps() в момент реальной работы и с внятным отказом вместо
# голого `ModuleNotFoundError: No module named 'sam2'` — sam2 на PyPI нет вовсе,
# и pip на такое отвечает «No matching distribution», уводя диагноз в сторону.
# Побочно: благодаря этому у скрипта работает `--help`.
from process_one import process, DEFAULT_CHECKPOINT, DEFAULT_CONFIG, check_alpha_encoder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mp4-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--ck-threshold', type=int, default=215)
    ap.add_argument('--no-chromakey', action='store_true')
    ap.add_argument('--rembg-model', default='isnet-general-use')
    ap.add_argument('--checkpoint', default=DEFAULT_CHECKPOINT)
    ap.add_argument('--config', default=DEFAULT_CONFIG)
    args = ap.parse_args()

    # Preflight до цикла: без кодировщика VP9-alpha провалится КАЖДЫЙ файл, причём
    # каждый — после полного прогона SAM2. Один внятный отказ здесь дешевле тридцати
    # одинаковых трейсбеков внизу.
    ok, info = check_alpha_encoder()
    if not ok:
        raise SystemExit(f'[sticker-pack-generator] {info}')
    print(f'alpha_encoder: {info}')

    os.makedirs(args.out_dir, exist_ok=True)
    mp4s = sorted(f for f in os.listdir(args.mp4_dir) if f.lower().endswith('.mp4'))
    print(f'found {len(mp4s)} mp4s')
    t0 = time.time()
    for i, fn in enumerate(mp4s):
        name = fn[:-4]
        out = os.path.join(args.out_dir, f'{name}.webm')
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f'[{i+1:>2}/{len(mp4s)}] {name} SKIP (exists)')
            continue
        t1 = time.time()
        try:
            process(os.path.join(args.mp4_dir, fn), out,
                    ck_threshold=args.ck_threshold,
                    per_frame_chromakey=not args.no_chromakey,
                    rembg_model=args.rembg_model,
                    sam2_config=args.config, sam2_checkpoint=args.checkpoint,
                    work_parent=args.out_dir)
        except Exception as e:
            traceback.print_exc()
            print(f'[{i+1:>2}/{len(mp4s)}] {name} FAIL {e}')
            continue
        dt = time.time() - t1; total = time.time() - t0
        print(f'[{i+1:>2}/{len(mp4s)}] {name} OK {dt:.1f}s total={total:.0f}s')


if __name__ == '__main__':
    main()
