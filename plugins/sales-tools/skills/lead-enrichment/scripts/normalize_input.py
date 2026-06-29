# -*- coding: utf-8 -*-
"""Classify and normalize a digital-trace fragment.

Usage:  python normalize_input.py "<fragment>"
Output: JSON {type, value, derived:{...}}  describing how to route it (Mode A step 1).

Types: email | phone | inn | ogrn | domain | url | username | name | unknown
Derived hints feed the router (domain->company, name variants, etc.).
"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FREE_MAIL = {'gmail.com', 'yandex.ru', 'ya.ru', 'mail.ru', 'bk.ru', 'list.ru',
             'inbox.ru', 'icloud.com', 'outlook.com', 'hotmail.com', 'proton.me', 'rambler.ru'}

def luhn_inn_ok(inn):
    """Validate RU INN checksum (10 or 12 digits)."""
    if not inn.isdigit():
        return False
    def cs(d, w):
        return str(sum(int(d[i]) * w[i] for i in range(len(w))) % 11 % 10)
    if len(inn) == 10:
        return cs(inn, [2, 4, 10, 3, 5, 9, 4, 6, 8]) == inn[9]
    if len(inn) == 12:
        ok1 = cs(inn, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == inn[10]
        ok2 = cs(inn, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == inn[11]
        return ok1 and ok2
    return False

def name_variants(name):
    """Cyrillic name -> simple translit variants for LinkedIn slug guessing."""
    table = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
             'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
             'с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
             'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'-'}
    lat = ''.join(str(table.get(c, c)) for c in name.lower())
    return list(dict.fromkeys([name, lat, lat.replace('-', ' ')]))

def classify(s):
    s = s.strip()
    low = s.lower()
    # url
    if re.match(r'^https?://', low):
        host = re.sub(r'^https?://(www\.)?', '', low).split('/')[0]
        d = {'host': host}
        if any(p in host for p in ('linkedin', 'instagram', 't.me', 'vk.com', 'facebook', 'tiktok', 'twitter', 'x.com')):
            return 'url', s, d  # social url -> social-intel
        return 'domain', host, d
    # email
    m = re.match(r'^[\w.+-]+@([\w.-]+\.\w+)$', s)
    if m:
        dom = m.group(1).lower()
        return 'email', s, {'domain': dom, 'corporate': dom not in FREE_MAIL}
    digits = re.sub(r'\D', '', s)
    has_sep = bool(re.search(r'[+\s().-]', s))
    # pure-digit string
    if s.isdigit():
        # bare mobile (10 digits, starts 9) or 11-digit 7/8 → phone first
        if len(s) == 10 and s[0] == '9':
            return 'phone', '+7' + s, {'national': s}
        if len(s) == 11 and s[0] in '78':
            return 'phone', '+7' + s[1:], {'national': s[1:]}
        if len(s) in (13, 15):
            return 'ogrn', s, {'kind': 'org' if len(s) == 13 else 'ip'}
        if len(s) in (10, 12):  # INN (valid flag from checksum)
            return 'inn', s, {'valid': luhn_inn_ok(s), 'kind': 'org' if len(s) == 10 else 'person/ip'}
    # formatted phone (+7…, 8 (916) …)
    if has_sep and 10 <= len(digits) <= 11:
        if len(digits) == 11 and digits[0] in '78':
            digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        return 'phone', '+' + digits, {'national': digits[1:]}
    # username (@handle, or a bare single-token handle without dots)
    if re.match(r'^@[A-Za-z][\w]{3,31}$', s):
        return 'username', s.lstrip('@'), {}
    if re.match(r'^[A-Za-z][\w]{3,31}$', s) and '.' not in s:
        return 'username', s, {}
    # domain (bare)
    if re.match(r'^[\w.-]+\.\w{2,}$', low) and '@' not in s:
        return 'domain', low, {}
    # name (has space or cyrillic letters)
    if ' ' in s or re.search(r'[а-яё]', low):
        return 'name', s, {'variants': name_variants(s)}
    return 'unknown', s, {}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: normalize_input.py "<fragment>"'}, ensure_ascii=False))
        sys.exit(1)
    t, v, d = classify(' '.join(sys.argv[1:]))
    print(json.dumps({'type': t, 'value': v, 'derived': d}, ensure_ascii=False, indent=2))
