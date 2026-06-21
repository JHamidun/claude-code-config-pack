# -*- coding: utf-8 -*-
"""Domain -> company. Scrape the site for INN/OGRN, then resolve via DaData/EGRUL.

Usage:  python domain_to_company.py example-corp.ru
Output: JSON {domain, inn_candidates:[...], ogrn_candidates:[...], emails:[...], firmographics:[...]}

Strategy: fetch homepage + common contact/legal pages, regex INN/OGRN/emails, then call
dadata_lookup / egrul_lookup on the first INN found. Russian sites put requisites in the footer
or /contacts, /about, /requisites, /privacy.
"""
import sys, io, re, json, subprocess, os
import urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SK = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
PAGES = ['', '/contacts', '/contact', '/about', '/o-kompanii', '/requisites', '/rekvizity',
         '/privacy', '/policy', '/legal', '/terms']
INN_RE = re.compile(r'\b(?:ИНН|INN)[:\s]*?(\d{10}|\d{12})\b', re.I)
INN_BARE = re.compile(r'\b(\d{10}|\d{12})\b')
OGRN_RE = re.compile(r'\b(?:ОГРН)[:\s]*?(\d{13}|\d{15})\b', re.I)
EMAIL_RE = re.compile(r'\b[\w.+-]+@[\w.-]+\.\w{2,}\b')

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(600000)
        return raw.decode('utf-8', errors='replace')
    except Exception:
        return ''

def scrape(domain):
    base = 'https://' + domain.rstrip('/')
    inns, ogrns, emails = set(), set(), set()
    for p in PAGES:
        html = fetch(base + p)
        if not html:
            continue
        for m in INN_RE.findall(html):
            inns.add(m)
        for m in OGRN_RE.findall(html):
            ogrns.add(m)
        for m in EMAIL_RE.findall(html):
            if not m.lower().endswith(('.png', '.jpg', '.svg', '.webp', '.gif')):
                emails.add(m.lower())
        if inns and emails:  # enough signal — stop early
            break
    # If labelled INN not found, take bare 10/12-digit numbers from homepage as weak candidates
    if not inns:
        home = fetch(base)
        inns = set(INN_BARE.findall(home)[:3])
    return sorted(inns), sorted(ogrns), sorted(emails)[:15]

def resolve(inn):
    for script in ('dadata_lookup.py', 'egrul_lookup.py'):
        try:
            r = subprocess.run(['python', os.path.join(SK, script), inn],
                               capture_output=True, text=True, timeout=40, encoding='utf-8')
            data = json.loads(r.stdout or '[]')
            if isinstance(data, list) and data:
                return data
        except Exception:
            continue
    return []

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: domain_to_company.py <domain>'}, ensure_ascii=False))
        sys.exit(1)
    dom = sys.argv[1].replace('https://', '').replace('http://', '').split('/')[0]
    inns, ogrns, emails = scrape(dom)
    firm = resolve(inns[0]) if inns else []
    print(json.dumps({'domain': dom, 'inn_candidates': inns, 'ogrn_candidates': ogrns,
                      'emails': emails, 'firmographics': firm}, ensure_ascii=False, indent=2))
