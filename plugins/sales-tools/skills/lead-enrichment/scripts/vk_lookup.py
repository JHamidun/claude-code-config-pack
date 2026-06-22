# -*- coding: utf-8 -*-
"""VK people search via VK API users.search (needs VK_ACCESS_TOKEN).

Usage:
  python vk_lookup.py --q "Имя Фамилия" [--city "Москва"] [--company "Компания"]
  python vk_lookup.py --screen-name some_username   # users.get by screen_name/id

Token: VK_ACCESS_TOKEN in ~/.claude/.credentials.master.env. Get it (logged into vk.com):
  https://oauth.vk.com/authorize?client_id=2685278&scope=friends,groups,offline&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1&v=5.131
  → «Разрешить» → copy access_token from the blank.html#access_token=... URL.

Public profiles only — VK respects each user's privacy. No leaked data.
"""
import sys, io, os, json, argparse, urllib.parse, urllib.request
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API = 'https://api.vk.com/method/'
V = '5.199'
FIELDS = 'city,occupation,career,education,screen_name,photo_200,about,contacts'

def token():
    t = os.getenv('VK_ACCESS_TOKEN')
    if t:
        return t.strip().strip('"').strip("'")
    p = Path.home() / '.claude' / '.credentials.master.env'
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line.startswith('VK_ACCESS_TOKEN='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None

def call(method, params, tok):
    params = {**params, 'access_token': tok, 'v': V}
    url = API + method + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode('utf-8'))
    if 'error' in data:
        return {'error': data['error'].get('error_msg'), 'code': data['error'].get('error_code')}
    return data.get('response')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', default=''); ap.add_argument('--city', default=''); ap.add_argument('--company', default='')
    ap.add_argument('--screen-name', default=''); ap.add_argument('--count', type=int, default=15)
    a = ap.parse_args()
    tok = token()
    if not tok:
        print(json.dumps({'error': 'VK_ACCESS_TOKEN not set',
                          'how_to': 'open the oauth.vk.com authorize URL in this file header, copy access_token'},
                         ensure_ascii=False)); sys.exit(2)
    if a.screen_name:
        res = call('users.get', {'user_ids': a.screen_name, 'fields': FIELDS}, tok)
    elif a.q:
        p = {'q': a.q, 'count': a.count, 'fields': FIELDS}
        if a.city:
            p['hometown'] = a.city  # free-text hint; VK also has city_id via database.getCities
        if a.company:
            p['company'] = a.company
        res = call('users.search', p, tok)
    else:
        print(json.dumps({'error': 'need --q "ФИО" or --screen-name'}, ensure_ascii=False)); sys.exit(1)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
