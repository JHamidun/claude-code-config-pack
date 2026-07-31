# -*- coding: utf-8 -*-
"""Stage 3 — Enrich: priority queue + batch research via perplexity skill.

Usage:
    python 03_research_perplexity.py --input extracted.json --bitrix bitrix_data.json \
        --workdir research/ --output research/results.json --limit 500

    # Gentle retry on failed:
    python 03_research_perplexity.py --workdir research/ --gentle

Idempotent: per-INN .md cache. Re-runs skip companies with substantive existing .md.
"""
import sys, io, os, json, time, subprocess, concurrent.futures, argparse, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PPLX_CLI = os.path.expanduser('~/.claude/skills/perplexity/pplx-max.py')


# ---------- Queue building ----------

def build_queue(extracted, bitrix_data, limit):
    inn_to_record = {}
    for r in extracted:
        if r.get('inn'):
            inn_to_record.setdefault(r['inn'], r)

    by_inn = bitrix_data.get('by_inn', {})
    priorities = []

    # Tier S (active touches) + Tier B (in CRM, no touches)
    for inn, info in by_inn.items():
        rec = inn_to_record.get(inn, {})
        name = rec.get('name') or (info['titles'][0] if info.get('titles') else inn)
        products = ', '.join(info.get('products', [])) or 'нет'
        last = info.get('last_touch', '')
        if info.get('touch_count', 0) > 0:
            tier = 'S'
            reason = f'Активная история в CRM. Продукты: {products}. Последнее касание: {last}.'
        else:
            tier = 'B'
            reason = 'В CRM как карточка, без активных касаний.'
        priorities.append({
            'tier': tier,
            'inn': inn,
            'name': name,
            'ul': rec.get('ul', ''),
            'industry': rec.get('industry', '') or rec.get('segment', ''),
            'reason': reason,
            'rev2024': rec.get('rev2024'),
        })

    # Tier A — cold, top by revenue
    cold = []
    for r in extracted:
        if not r.get('inn') or r['inn'] in by_inn:
            continue
        rev = r.get('rev2024') or 0
        try:
            rev_f = float(rev) if rev else 0
        except Exception:
            rev_f = 0
        if rev_f <= 0:
            continue
        cold.append((rev_f, r))
    cold.sort(key=lambda x: -x[0])

    cold_limit = limit if limit is not None and limit > 0 else len(cold)
    for rev_f, r in cold[:cold_limit]:
        rev_str = f'{rev_f:,.0f}'.replace(',', ' ')
        priorities.append({
            'tier': 'A',
            'inn': r['inn'],
            'name': r['name'],
            'ul': r.get('ul', ''),
            'industry': r.get('industry', '') or r.get('segment', ''),
            'reason': f'Холодняк, выручка 2024: {rev_str} RUB. В CRM отсутствует.',
            'rev2024': rev_f,
        })
    return priorities


# ---------- Research a batch ----------

def build_prompt(batch, product_hint):
    items = []
    for idx, p in enumerate(batch, start=1):
        line = f'{idx}. **{p["name"]}**'
        if p.get('ul') and p['ul'] != p['name']:
            line += f' (юр. лицо: {p["ul"]})'
        line += f' — ИНН {p["inn"]}'
        if p.get('industry'):
            line += f' — {p["industry"]}'
        items.append(line)
    items_str = '\n'.join(items)
    signals_hint = f'для {product_hint}' if product_hint else 'для B2B-продукта'

    return f'''Подготовь краткие досье (по 150-200 слов на каждую) для B2B-продаж по этим {len(batch)} российским компаниям на 2026 год:

{items_str}

Для **каждой** компании дай ровно такую структуру:

## Компания {{N}}: {{Название}} [{{ИНН}}]

**ЛПР:** имя + должность (CDTO/CIO/CTO, HR/L&D-директор, директор по корпоративному развитию). Если данных нет — пиши "нет в открытых источниках".

**Свежие новости (2025-2026):** ключевые события, сделки, реструктуризация, смена топов.

**Сигналы {signals_hint}:** обучение сотрудников, AI-инициативы, HR-tech, цифровая трансформация.

**Триггеры для outreach:** что произошло за 3-6 месяцев и даёт повод написать.

Со ссылками на источники [1][2]. Очень кратко по делу. Не пропускай ни одну компанию из списка.'''


def parse_response(text, batch):
    chunks = re.split(r'\n(?=## ?(?:Компания|Company)\s*\d)', text)
    results = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r'## ?(?:Компания|Company)\s*(\d+)[:.\s\-]+(.+?)(?=\n)', chunk)
        if not m:
            continue
        n = int(m.group(1))
        if 1 <= n <= len(batch):
            results[batch[n - 1]['inn']] = chunk
    return results


def research_batch(batch, out_dir, mode, timeout, product_hint):
    prompt = build_prompt(batch, product_hint)
    try:
        result = subprocess.run(
            ['python', PPLX_CLI, '--mode', mode, prompt],
            capture_output=True, text=True, timeout=timeout,
            encoding='utf-8', errors='replace',
        )
        if result.returncode != 0:
            return batch, None, f'rc={result.returncode}: {result.stderr[:200]}'
        text = result.stdout.strip()
        if len(text) < 200:
            return batch, None, f'too_short: {text[:200]}'
        per_company = parse_response(text, batch)
        for inn, chunk in per_company.items():
            with open(os.path.join(out_dir, f'{inn}.md'), 'w', encoding='utf-8') as f:
                f.write(chunk)
        return batch, per_company, None
    except subprocess.TimeoutExpired:
        return batch, None, 'timeout'
    except Exception as e:
        return batch, None, f'{type(e).__name__}: {e}'


def filter_remaining(queue, out_dir):
    """Skip INNs that already have substantive .md."""
    remaining = []
    for p in queue:
        md = os.path.join(out_dir, f'{p["inn"]}.md')
        if os.path.exists(md):
            try:
                text = open(md, encoding='utf-8').read()
                if len(text) > 300 and 'ERROR' not in text[:50] and 'TIMEOUT' not in text[:50]:
                    continue
            except Exception:
                pass
        remaining.append(p)
    return remaining


def sync_results(queue, out_dir):
    """Rebuild results.json from .md files."""
    results = {}
    for p in queue:
        md = os.path.join(out_dir, f'{p["inn"]}.md')
        if os.path.exists(md):
            try:
                text = open(md, encoding='utf-8').read()
                if len(text) > 300 and 'ERROR' not in text[:50] and 'TIMEOUT' not in text[:50]:
                    results[p['inn']] = {
                        'text': text, 'status': 'ok',
                        'name': p['name'], 'tier': p['tier'],
                    }
                    continue
            except Exception:
                pass
        results[p['inn']] = {
            'text': '', 'status': 'pending',
            'name': p['name'], 'tier': p['tier'],
        }
    return results


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', help='extracted.json (required unless --gentle)')
    ap.add_argument('--bitrix', help='bitrix_data.json (required unless --gentle)')
    ap.add_argument('--workdir', default='research', help='where to write per-INN .md files')
    ap.add_argument('--output', default='', help='results.json path (default: workdir/results.json)')
    ap.add_argument('--limit', type=int, default=500, help='cap on Tier A (cold) by rev2024')
    ap.add_argument('--batch', type=int, default=5, help='companies per Perplexity call')
    ap.add_argument('--workers', type=int, default=3, help='parallel workers')
    ap.add_argument('--mode', default='pro', choices=['pro', 'auto'], help='perplexity mode')
    ap.add_argument('--timeout', type=int, default=300, help='per-batch timeout, seconds')
    ap.add_argument('--product-hint', default='', help='hint for "сигналы" prompt section, e.g. "YourProduct, EdTech, HR-tech"')
    ap.add_argument('--gentle', action='store_true', help='retry-only mode: batch=3, workers=1, mode=auto')
    args = ap.parse_args()

    out_dir = os.path.abspath(args.workdir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(args.output) if args.output else os.path.join(out_dir, 'results.json')
    queue_path = os.path.join(out_dir, 'queue.json')

    if args.gentle and os.path.exists(queue_path):
        queue = json.load(open(queue_path, encoding='utf-8'))
    else:
        if not args.input or not args.bitrix:
            raise SystemExit('--input and --bitrix required (or use --gentle with existing queue.json)')
        with open(args.input, encoding='utf-8') as f:
            extracted = json.load(f)
        with open(args.bitrix, encoding='utf-8') as f:
            bitrix_data = json.load(f)
        queue = build_queue(extracted, bitrix_data, args.limit)
        with open(queue_path, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2, default=str)

    s_count = sum(1 for p in queue if p['tier'] == 'S')
    b_count = sum(1 for p in queue if p['tier'] == 'B')
    a_count = sum(1 for p in queue if p['tier'] == 'A')
    print(f'Queue: {len(queue)} (Tier S: {s_count}, Tier B: {b_count}, Tier A: {a_count})')

    remaining = filter_remaining(queue, out_dir)
    print(f'Already done: {len(queue) - len(remaining)}, remaining: {len(remaining)}')

    if not remaining:
        results = sync_results(queue, out_dir)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        ok = sum(1 for v in results.values() if v['status'] == 'ok')
        print(f'Nothing to do. Synced {ok}/{len(results)} OK to {out_path}')
        return

    batch_size = 3 if args.gentle else args.batch
    workers = 1 if args.gentle else args.workers
    mode = 'auto' if args.gentle else args.mode

    batches = [remaining[i:i + batch_size] for i in range(0, len(remaining), batch_size)]
    print(f'Batches of {batch_size}: {len(batches)}, workers: {workers}, mode: {mode}')

    t0 = time.time()
    saved = 0
    failed_batches = 0

    if workers == 1:
        for i, batch in enumerate(batches, start=1):
            _, per_company, err = research_batch(batch, out_dir, mode, args.timeout, args.product_hint)
            elapsed = time.time() - t0
            if per_company:
                saved += len(per_company)
                names = ', '.join(p['name'][:20] for p in batch)
                print(f'[{i}/{len(batches)}] OK {len(per_company)}/{len(batch)} (saved={saved}) ({elapsed:.0f}s) | {names[:90]}')
            else:
                failed_batches += 1
                names = ', '.join(p['name'][:20] for p in batch)
                print(f'[{i}/{len(batches)}] FAIL ({(err or "?")[:80]}) ({elapsed:.0f}s) | {names[:90]}')
            time.sleep(1 if args.gentle else 0)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(research_batch, b, out_dir, mode, args.timeout, args.product_hint): b for b in batches}
            for i, fut in enumerate(concurrent.futures.as_completed(futures), start=1):
                batch = futures[fut]
                try:
                    _, per_company, err = fut.result()
                except Exception as e:
                    err = str(e)
                    per_company = None
                elapsed = time.time() - t0
                if per_company:
                    saved += len(per_company)
                    names = ', '.join(p['name'][:25] for p in batch)
                    print(f'[{i}/{len(batches)}] OK {len(per_company)}/{len(batch)} ({elapsed:.0f}s) saved={saved} | {names[:90]}')
                else:
                    failed_batches += 1
                    names = ', '.join(p['name'][:20] for p in batch)
                    print(f'[{i}/{len(batches)}] FAIL ({(err or "?")[:80]}) ({elapsed:.0f}s) | {names[:90]}')

    # Final sync
    results = sync_results(queue, out_dir)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for v in results.values() if v['status'] == 'ok')
    elapsed = time.time() - t0
    print(f'\nDone in {elapsed:.0f}s. Companies saved: {saved}. OK total: {ok}/{len(queue)}. Failed batches: {failed_batches}')
    print(f'  → {out_path}')


if __name__ == '__main__':
    main()
