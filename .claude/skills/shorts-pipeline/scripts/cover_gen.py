"""Generate vertical 1080x1920 cover images for YouTube Shorts.

Two backends:
  - navy   — PIL navy gradient + matrix dots + headline + подпись бренда ($SHORTS_BRAND)
             (no GPT cost, ~50ms per cover)
  - html   — cinematic HTML (templates/cover_ai_top100.html via Playwright; optional)

Usage:
    # Single cover
    python cover_gen.py --title "$4M за 10 дней" --out cover.png

    # Bulk from analysis JSON
    python cover_gen.py --bulk $SHORTS_HOME/analysis.json --out-dir covers/

    # From channel shorts list (covers missing)
    python cover_gen.py --from-channel $SHORTS_HOME/channel_shorts.json --out-dir covers/

The navy template lives in templates/cover_navy.py and exposes
`render_shorts_cover(title, out_path)`.
"""
import sys, os, json, argparse
from pathlib import Path
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

THIS = Path(__file__).parent
TEMPLATES = THIS.parent / 'templates'
sys.path.insert(0, str(TEMPLATES))

from cover_navy import render_shorts_cover  # type: ignore


def gen_one(title, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_shorts_cover(title, str(out_path))
    print(f'  ✓ {out_path}')


def gen_bulk_from_analysis(analysis_path, out_dir):
    """analysis.json (from analyze_srt.py) → covers for each `keep:true` short."""
    data = json.load(open(analysis_path, encoding='utf-8'))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    todo = [(k, v) for k, v in data.items() if v.get('keep')]
    print(f'Rendering {len(todo)} covers from analysis...')
    for i, (key, v) in enumerate(todo, 1):
        safe = key.replace('/', '__')
        op = out / f'{safe}.png'
        if op.exists(): continue
        try:
            render_shorts_cover(v.get('title') or v.get('on_screen_text') or 'AI NEWS', str(op))
        except Exception as e:
            print(f'  FAIL {key}: {e}')
            continue
        if i % 10 == 0: print(f'  {i}/{len(todo)}...', flush=True)
    print(f'Done. Out: {out}')


def gen_from_channel(shorts_path, out_dir, only_missing=True):
    """Channel inventory JSON (all_shorts.json) → covers for each video id."""
    data = json.load(open(shorts_path, encoding='utf-8'))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    print(f'Rendering covers for {len(data)} shorts...')
    for i, s in enumerate(data, 1):
        vid = s.get('id') or s.get('vid')
        if not vid: continue
        op = out / f'{vid}.png'
        if only_missing and op.exists(): continue
        try:
            render_shorts_cover(s.get('title') or 'AI NEWS', str(op))
        except Exception as e:
            print(f'  FAIL {vid}: {e}')
            continue
        if i % 10 == 0: print(f'  {i}/{len(data)}...', flush=True)
    print(f'Done. Out: {out}')


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--title', help='Single cover headline')
    g.add_argument('--bulk', help='Path to analysis JSON (from analyze_srt.py)')
    g.add_argument('--from-channel', help='Path to channel inventory JSON (all_shorts.json)')
    ap.add_argument('--out', help='Output path (single mode)')
    ap.add_argument('--out-dir', help='Output dir (bulk modes)')
    ap.add_argument('--regen', action='store_true', help='Re-render existing covers (bulk)')
    args = ap.parse_args()

    if args.title:
        if not args.out:
            ap.error('--out required for --title')
        gen_one(args.title, args.out)
    elif args.bulk:
        if not args.out_dir:
            ap.error('--out-dir required for --bulk')
        gen_bulk_from_analysis(args.bulk, args.out_dir)
    elif args.from_channel:
        if not args.out_dir:
            ap.error('--out-dir required for --from-channel')
        gen_from_channel(args.from_channel, args.out_dir, only_missing=not args.regen)


if __name__ == '__main__':
    main()
