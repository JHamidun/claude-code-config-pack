# -*- coding: utf-8 -*-
"""Perplexity deep B2B dossier over a priority queue of companies. Port of the proven script.

Usage:  python research_companies.py aggregated.json list.json [--out-dir research] [--workers 3] [--top-cold 500]

Builds a priority queue (Tier S=active history, B=in base no touches, A=cold by revenue),
runs Perplexity pro per company (cached by INN), saves <inn>.md + results.json.
Customize the dossier prompt for the product set in PROMPT_TEMPLATE.
"""
import sys, io, json, os, subprocess, time, argparse, concurrent.futures
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PPLX = os.path.expanduser('~/.claude/skills/perplexity/pplx-max.py')

PROMPT_TEMPLATE = '''Подготовь сжатое досье для B2B-продаж по компании "{name}" {ul_hint} {industry_hint} в России на 2026 год.

Структурно:
1. **Ключевые лица для outreach** — CDTO/CIO/CTO, директор HR/L&D/обучения, директор по корп. развитию. Имя + должность + LinkedIn если есть.
2. **Свежие новости** (последние 6 месяцев): сделки, M&A, смена топ-менеджмента, цифровая трансформация.
3. **Сигналы под ваши категории продуктов**: инициативы по обучению, AI-внедрениям, HR-tech.
4. **Триггеры** (за 3-6 мес., дают повод написать): рост штата, новый CIO, IPO, новая стратегия.
5. **Пейн-поинты** под продукты: {product_hint}.

Кратко (300-400 слов), со ссылками. Если данных нет — "нет в открытых источниках".'''

def build_queue(agg, rows, top_cold):
    inn_rec = {}
    for r in rows:
        if r.get('inn'):
            inn_rec.setdefault(str(r['inn']), r)
    q = []
    for inn, info in agg.items():
        if not info:
            continue
        rec = inn_rec.get(inn, {})
        name = rec.get('name') or (info['titles'][0] if info.get('titles') else inn)
        if info['touch_count'] > 0:
            tier, reason = 'S', 'Активная история в Bitrix. Продукты: ' + (', '.join(info['products']) or 'нет')
        else:
            tier, reason = 'B', 'В Bitrix карточка, без касаний.'
        q.append({'tier': tier, 'inn': inn, 'name': name, 'ul': rec.get('ul', ''),
                  'industry': rec.get('industry') or rec.get('segment', ''), 'reason': reason})
    cold = []
    for r in rows:
        inn = str(r.get('inn') or '')
        if not inn or inn in agg:
            continue
        try:
            rev = float(r.get('rev2024') or 0)
        except Exception:
            rev = 0
        if rev > 0:
            cold.append((rev, r))
    cold.sort(key=lambda x: -x[0])
    for rev, r in cold[:top_cold]:
        q.append({'tier': 'A', 'inn': str(r['inn']), 'name': r['name'], 'ul': r.get('ul', ''),
                  'industry': r.get('industry') or r.get('segment', ''),
                  'reason': f'Холодняк, выручка 2024: {rev:,.0f} RUB. В Bitrix отсутствует.'.replace(',', ' ')})
    return q

def research(p, out_dir):
    out_path = os.path.join(out_dir, f"{p['inn']}.md")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 200:
        return p['inn'], open(out_path, encoding='utf-8').read(), 'cached'
    query = PROMPT_TEMPLATE.format(name=p['name'],
        ul_hint=f"(юр. лицо: {p['ul']})" if p.get('ul') and p['ul'] != p['name'] else '',
        industry_hint=f"(отрасль: {p['industry']})" if p.get('industry') else '')
    try:
        r = subprocess.run(['python', PPLX, '--mode', 'pro', query],
                           capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            return p['inn'], 'ERROR: ' + r.stderr[:300], 'error'
        text = r.stdout.strip()
        if len(text) < 100:
            return p['inn'], 'TOO_SHORT', 'error'
        open(out_path, 'w', encoding='utf-8').write(text)
        return p['inn'], text, 'ok'
    except subprocess.TimeoutExpired:
        return p['inn'], 'TIMEOUT', 'timeout'
    except Exception as e:
        return p['inn'], f'EXCEPTION: {e}', 'error'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('aggregated_json'); ap.add_argument('list_json')
    ap.add_argument('--out-dir', default='research'); ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--top-cold', type=int, default=500)
    a = ap.parse_args()
    agg = json.load(open(a.aggregated_json, encoding='utf-8'))
    rows = json.load(open(a.list_json, encoding='utf-8'))
    os.makedirs(a.out_dir, exist_ok=True)
    q = build_queue(agg, rows, a.top_cold)
    json.dump(q, open(os.path.join(a.out_dir, 'queue.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'Queue: {len(q)} (S={sum(1 for p in q if p["tier"]=="S")}, A={sum(1 for p in q if p["tier"]=="A")}, B={sum(1 for p in q if p["tier"]=="B")})')
    results, t0 = {}, time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(research, p, a.out_dir): p for p in q}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            p = futs[fut]
            inn, text, status = fut.result()
            results[inn] = {'text': text, 'status': status, 'name': p['name'], 'tier': p['tier']}
            print(f'[{i}/{len(q)}] {status:7s} {p["tier"]} {p["name"][:48]:48s} ({time.time()-t0:.0f}s)')
    json.dump(results, open(os.path.join(a.out_dir, 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('Done. OK:', sum(1 for v in results.values() if v['status'] in ('ok', 'cached')), '/', len(q))

if __name__ == '__main__':
    main()
