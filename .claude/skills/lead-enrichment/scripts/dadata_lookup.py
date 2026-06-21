# -*- coding: utf-8 -*-
"""DaData firmographics — primary company-leg source (clean, no captcha).

Usage:
  python dadata_lookup.py <INN | OGRN>            # findById/party  (exact card)
  python dadata_lookup.py --suggest "Название компании"     # suggest/party   (search by name)

Needs DADATA_API_KEY in ~/.claude/.credentials.master.env (free tier: 10k/day).
Output: JSON normalized card {name, name_full, inn, kpp, ogrn, type, status, director,
        okved, address, employee_count, income, expense, founded, branch_count, source}.

Docs: https://dadata.ru/api/find-party/  ·  https://dadata.ru/api/suggest/party/
"""
import sys, io, os, json, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CRED = os.path.expanduser('~/.claude/.credentials.master.env')

def _key():
    k = os.getenv('DADATA_API_KEY')
    if k:
        return k.strip().strip('"').strip("'")
    try:
        for line in open(CRED, encoding='utf-8'):
            if line.startswith('DADATA_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None

FIND = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party'
SUGG = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party'

def _call(url, payload, key):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
        'Content-Type': 'application/json', 'Accept': 'application/json',
        'Authorization': 'Token ' + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def _norm(s):
    d = s.get('data', {})
    fin = d.get('finance') or {}
    return {
        'name': (d.get('name') or {}).get('short_with_opf') or s.get('value'),
        'name_full': (d.get('name') or {}).get('full_with_opf'),
        'inn': d.get('inn'), 'kpp': d.get('kpp'), 'ogrn': d.get('ogrn'),
        'type': d.get('type'),                                  # LEGAL / INDIVIDUAL
        'status': (d.get('state') or {}).get('status'),         # ACTIVE / LIQUIDATING ...
        'director': (d.get('management') or {}).get('name'),
        'director_post': (d.get('management') or {}).get('post'),
        'okved': d.get('okved'), 'okved_type': d.get('okved_type'),
        'address': (d.get('address') or {}).get('value'),
        'employee_count': d.get('employee_count'),
        'income': fin.get('income'), 'expense': fin.get('expense'),
        'revenue_year': fin.get('year'),
        'founded': (d.get('state') or {}).get('registration_date'),
        'branch_count': d.get('branch_count'),
        'okpo': d.get('okpo'), 'okfs': d.get('okfs'),
        'source': 'dadata',
    }

def find_by_id(q, key):
    res = _call(FIND, {'query': q}, key)
    return [_norm(s) for s in res.get('suggestions', [])]

def suggest(q, key, count=10):
    res = _call(SUGG, {'query': q, 'count': count}, key)
    return [_norm(s) for s in res.get('suggestions', [])]

if __name__ == '__main__':
    key = _key()
    if not key:
        print(json.dumps({'error': 'DADATA_API_KEY not set',
                          'hint': 'register at dadata.ru, add key to .credentials.master.env, or use egrul_lookup.py'},
                         ensure_ascii=False))
        sys.exit(2)
    args = sys.argv[1:]
    try:
        if args and args[0] == '--suggest':
            print(json.dumps(suggest(' '.join(args[1:]), key), ensure_ascii=False, indent=2))
        elif args:
            print(json.dumps(find_by_id(args[0], key), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({'error': 'usage: dadata_lookup.py <INN|OGRN> | --suggest "name"'}, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print(json.dumps({'error': f'HTTP {e.code}', 'hint': '403=bad key, 429=rate limit; fallback egrul_lookup.py'}, ensure_ascii=False))
