# -*- coding: utf-8 -*-
"""Match an input list against a Bitrix24 export by INN (exact) + name (fuzzy).

Usage:  python bitrix_match.py list.json bitrix_data.json [--out matches_by_inn.json]

list.json rows: [{name, inn?, ul?, ...}, ...]
bitrix_data.json: produced per references/bitrix-export.md (must include company_ids_to_inn + companies).

Output matches_by_inn.json: {inn: {bitrix_company_ids:[...], match: "inn"|"fuzzy", list_name, bitrix_name, score}}
Rows without INN are fuzzy-matched on company TITLE (rapidfuzz, threshold 88).
"""
import sys, io, json, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def norm(s):
    if not s:
        return ''
    s = str(s).lower()
    for junk in ['ооо', 'оао', 'зао', 'пао', 'ао', 'ип', 'нао', '«', '»', '"', "'", '(', ')', ',', '.', '-']:
        s = s.replace(junk, ' ')
    return ' '.join(s.split())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('list_json'); ap.add_argument('bitrix_json')
    ap.add_argument('--out', default='matches_by_inn.json')
    ap.add_argument('--threshold', type=int, default=88)
    a = ap.parse_args()

    rows = json.load(open(a.list_json, encoding='utf-8'))
    bd = json.load(open(a.bitrix_json, encoding='utf-8'))
    companies = bd.get('companies', {})
    ids_to_inn = bd.get('company_ids_to_inn', {})

    inn_to_ids = {}
    for cid, inn in ids_to_inn.items():
        if inn:
            inn_to_ids.setdefault(str(inn), []).append(cid)

    # name index for fuzzy
    name_idx = [(cid, norm(c.get('TITLE', ''))) for cid, c in companies.items() if c.get('TITLE')]
    fuzz = process = None
    try:
        from rapidfuzz import fuzz, process
        have_fuzz = True
    except Exception:
        have_fuzz = False

    matches = {}
    fuzzy_used = 0
    for r in rows:
        inn = str(r.get('inn') or '').strip()
        if inn and inn in inn_to_ids:
            ids = inn_to_ids[inn]
            matches[inn] = {'bitrix_company_ids': ids, 'match': 'inn',
                            'list_name': r.get('name'), 'bitrix_name': companies.get(ids[0], {}).get('TITLE'),
                            'score': 100}
            continue
        # fuzzy by name when no INN match
        if process is not None and fuzz is not None and r.get('name'):
            target = norm(r['name'])
            best = process.extractOne(target, [n for _, n in name_idx], scorer=fuzz.token_sort_ratio)
            if best and best[1] >= a.threshold:
                cid = name_idx[best[2]][0]
                key = inn or ('fuzzy:' + (companies.get(cid, {}).get('TITLE') or cid))
                matches[key] = {'bitrix_company_ids': [cid], 'match': 'fuzzy',
                                'list_name': r.get('name'), 'bitrix_name': companies.get(cid, {}).get('TITLE'),
                                'score': int(best[1])}
                fuzzy_used += 1

    json.dump(matches, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'Matched: {len(matches)} ({sum(1 for m in matches.values() if m["match"]=="inn")} by INN, {fuzzy_used} fuzzy)')
    if not have_fuzz:
        print('NOTE: rapidfuzz not installed — only exact INN matching. pip install rapidfuzz for name matching.')
    print(f'Saved -> {a.out}')

if __name__ == '__main__':
    main()
