# -*- coding: utf-8 -*-
"""Query egrul.nalog.ru via its unofficial web API (key-free fallback for firmographics).

Usage:  python egrul_lookup.py <INN | OGRN | "Название компании">
Output: JSON list of matches {name, inn, ogrn, kpp, address, director, status, kind}

Flow (mirrors roma8ok/egrul):
  1. POST https://egrul.nalog.ru/        body: query=<q>            -> {"t": <token>}
  2. GET  https://egrul.nalog.ru/search-result/<token>             -> {"rows":[...]} (poll until rows present)

Official, free, no key. Rate-limit gently (built-in retry/poll). For volume use DaData.
"""
import sys, io, json, time
import urllib.request, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'https://egrul.nalog.ru'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def _post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        'User-Agent': UA, 'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def search(query):
    tok = _post(BASE + '/', {'query': query, 'vyp3CaptchaToken': '', 'page': '', 'region': '',
                             'PreventChromeAutocomplete': ''}).get('t')
    if not tok:
        return []
    rows = []
    for _ in range(12):  # poll up to ~6s
        res = _get(f'{BASE}/search-result/{tok}')
        rows = res.get('rows', [])
        if rows:
            break
        time.sleep(0.5)
    out = []
    for r in rows:
        out.append({
            'name': r.get('c') or r.get('n'),          # short name / full name
            'name_full': r.get('n'),
            'inn': r.get('i'),
            'ogrn': r.get('o'),
            'kpp': r.get('p'),
            'address': r.get('a'),
            'director': r.get('g'),                     # руководитель
            'status': r.get('e') or r.get('rmsp') or 'действующая',
            'reg_date': r.get('r'),
            'term_date': r.get('e'),
            'kind': r.get('k'),                         # ul / fl (ИП)
            'okved': r.get('ok'),
            'source': 'egrul.nalog.ru',
        })
    return out

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: egrul_lookup.py <INN|OGRN|name>'}, ensure_ascii=False))
        sys.exit(1)
    q = ' '.join(sys.argv[1:])
    try:
        print(json.dumps(search(q), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e), 'hint': 'rate-limited or captcha; slow down or use dadata_lookup.py'}, ensure_ascii=False))
