"""Batch-generate emotion variations from a JSON list.

emotions.json format:
    [
      {"name": "01-fire", "emoji": "🔥", "change": "Mascot is fired up..."},
      {"name": "02-love", "emoji": "❤️", "change": "Eyes turn into hearts..."}
    ]

Skips existing outputs (resumable).

Usage:
    python batch_gen_emotions.py \
        --master ./mascot/master.png \
        --emotions ../references/sample-emotions.json \
        --constraints ../references/character-constraints.txt \
        --out-dir ./emotions/
"""
import sys, io, os, json, argparse, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from gen_emotion import gen_emotion


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', required=True)
    ap.add_argument('--emotions', required=True, help='Path to emotions JSON')
    ap.add_argument('--constraints', required=True, help='Path to constraints text')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--size', default='1024x1024')
    ap.add_argument('--quality', default='high')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=None)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    emotions = json.load(open(args.emotions, encoding='utf-8'))
    constraints = open(args.constraints, encoding='utf-8').read()

    subset = emotions[args.start:args.end] if args.end else emotions[args.start:]
    print(f'Processing {len(subset)} emotions')
    t0 = time.time()
    fails = []
    for i, item in enumerate(subset):
        name = item['name']
        out = os.path.join(args.out_dir, f'{name}.png')
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f'[{i+1}/{len(subset)}] {name} SKIP (exists)')
            continue
        t1 = time.time()
        ok = gen_emotion(args.master, name, item['change'], constraints, out,
                         args.size, args.quality)
        if not ok:
            fails.append(name)
        dt = time.time() - t1
        print(f'[{i+1}/{len(subset)}] {name} {"OK" if ok else "FAIL"} {dt:.1f}s  '
              f'total={time.time()-t0:.0f}s')
    print(f'\nDone. Generated {len(subset)-len(fails)}/{len(subset)}. Fails: {fails}')


if __name__ == '__main__':
    main()
