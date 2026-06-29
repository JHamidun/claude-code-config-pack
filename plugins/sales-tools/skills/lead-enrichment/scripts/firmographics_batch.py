# -*- coding: utf-8 -*-
"""Batch firmographic enrichment for a list of companies. Mode B step 5.

Usage:  python firmographics_batch.py list.json [--out firmographics.json]
                                       [--cache-dir firmographics_cache] [--workers 3]

list.json rows: [{name?, inn, ...}, ...]  — only rows with an INN are enriched.
For each unique INN: try dadata_lookup.py (if DADATA_API_KEY set) → fallback egrul_lookup.py
(key-free). Results cached per-INN on disk, so re-runs are cheap. Output firmographics.json:
{inn: {name, name_full, director, income, address, okved, status, source, ...}}.

Calls the sibling scripts via subprocess — no credentials are read here directly.
"""
import sys, io, os, json, subprocess, time, argparse, concurrent.futures
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SK = os.path.dirname(os.path.abspath(__file__))

def resolve(inn, cache_dir):
    cache = os.path.join(cache_dir, f'{inn}.json')
    if os.path.exists(cache) and os.path.getsize(cache) > 2:
        try:
            return inn, json.load(open(cache, encoding='utf-8')), 'cached'
        except Exception:
            pass
    for script in ('dadata_lookup.py', 'egrul_lookup.py'):
        try:
            r = subprocess.run(['python', os.path.join(SK, script), inn],
                               capture_output=True, text=True, timeout=45, encoding='utf-8')
            data = json.loads(r.stdout or '[]')
            if isinstance(data, list) and data:
                card = data[0]
                json.dump(card, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
                return inn, card, ('dadata' if script.startswith('dadata') else 'egrul')
        except Exception:
            continue
    return inn, None, 'not_found'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('list_json')
    ap.add_argument('--out', default='firmographics.json')
    ap.add_argument('--cache-dir', default='firmographics_cache')
    ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()

    rows = json.load(open(a.list_json, encoding='utf-8'))
    inns = []
    seen = set()
    for r in rows:
        inn = str(r.get('inn') or '').strip()
        if inn.isdigit() and len(inn) in (10, 12) and inn not in seen:
            seen.add(inn); inns.append(inn)
    os.makedirs(a.cache_dir, exist_ok=True)
    print(f'Enriching {len(inns)} unique INNs ({a.workers} workers)...')

    out, t0 = {}, time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(resolve, inn, a.cache_dir): inn for inn in inns}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            inn, card, status = fut.result()
            if card:
                out[inn] = card
            print(f'[{i}/{len(inns)}] {status:9s} {inn} {(card or {}).get("name","") if card else "—"}')

    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\nDone in {time.time()-t0:.0f}s. Resolved {len(out)}/{len(inns)} → {a.out}')

if __name__ == '__main__':
    main()
