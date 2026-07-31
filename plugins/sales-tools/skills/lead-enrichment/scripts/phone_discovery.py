# -*- coding: utf-8 -*-
"""Discover a company's / decision-maker's PUBLIC phone numbers — legitimate sources only.

Usage:  python phone_discovery.py --domain company.ru
        python phone_discovery.py --inn 7700000000
        python phone_discovery.py --name "Company Паблишер" --city Москва

Pulls phones that the company/person published themselves or that come from official
registries. Public/published sources only — no reverse phone→identity lookups.

Sources covered here directly:
  - company website (homepage + /contacts) regex for RU phone patterns
  - EGRUL/DaData company card (firmographics, sometimes a phone)
Sources to drive via skills (printed as a plan, not scraped here):
  - 2GIS / Yandex Business  -> Skill maps-places
  - hh.ru employer page     -> Skill headhunter
  - LinkedIn contact info    -> Skill linkedin / social-intel
  - public Telegram profile  -> tg_client.py user-info
  - OUR Bitrix contacts      -> Skill crm
"""
import sys, io, re, json, os, subprocess, argparse
import urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SK = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
PHONE_RE = re.compile(r'(?:\+7|8)[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}')

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read(500000).decode('utf-8', errors='replace')
    except Exception:
        return ''

def norm_phone(p):
    d = re.sub(r'\D', '', p)
    if len(d) == 11 and d[0] in '78':
        d = '7' + d[1:]
    return '+' + d if len(d) == 11 else p

def from_site(domain):
    base = 'https://' + domain.rstrip('/')
    found = set()
    for p in ('', '/contacts', '/contact', '/o-kompanii', '/about'):
        html = fetch(base + p)
        for m in PHONE_RE.findall(html):
            found.add(norm_phone(m))
        if found:
            break
    return sorted(found)

def from_firmographics(inn):
    """Resolve by INN only (exact). Never pass a domain/free-text — that gives wrong fuzzy matches."""
    for script in ('dadata_lookup.py', 'egrul_lookup.py'):
        try:
            r = subprocess.run(['python', os.path.join(SK, script), inn],
                               capture_output=True, text=True, timeout=40, encoding='utf-8')
            data = json.loads(r.stdout or '[]')
            if isinstance(data, list) and data:
                return data[0]
        except Exception:
            continue
    return {}

def inn_from_domain(domain):
    try:
        r = subprocess.run(['python', os.path.join(SK, 'domain_to_company.py'), domain],
                           capture_output=True, text=True, timeout=60, encoding='utf-8')
        d = json.loads(r.stdout or '{}')
        cands = d.get('inn_candidates') or []
        return cands[0] if cands else None
    except Exception:
        return None

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--domain'); ap.add_argument('--inn'); ap.add_argument('--name'); ap.add_argument('--city', default='')
    a = ap.parse_args()
    out = {'phones_site': [], 'firmographics': {}, 'plan': []}
    inn = a.inn
    if a.domain:
        out['phones_site'] = from_site(a.domain)
        if not inn:
            inn = inn_from_domain(a.domain)
            out['inn_from_site'] = inn
    if inn:
        out['firmographics'] = from_firmographics(inn)
    elif a.name:
        out['firmographics_hint'] = f"нет ИНН — найди через: python dadata_lookup.py --suggest \"{a.name}\""
    label = a.name or a.domain or a.inn or ''
    out['plan'] = [
        f"Skill maps-places: 2GIS/Яндекс.Бизнес по '{label} {a.city}'.strip() — телефон, часы, адрес (публичные).",
        f"Skill headhunter: страница работодателя '{label}' — иногда телефон HR/приёмной.",
        "Skill linkedin / social-intel: contact info ЛПР (если открыт).",
        "tg_client.py user-info <@username> — публичный ТГ-профиль (если есть).",
        "Skill crm: контакты компании в НАШЕЙ базе (телефоны уже собранных контактов).",
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))
