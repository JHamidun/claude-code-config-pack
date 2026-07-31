# -*- coding: utf-8 -*-
"""Stage 2 — Match: extracted.json → bulk INN match in Your CRM → 360° per match.

Usage:
    python 02_match_bitrix.py --input extracted.json --output bitrix_data.json
    python 02_match_bitrix.py --input extracted.json --output bitrix_data.json --refresh
    python 02_match_bitrix.py --input extracted.json --output bitrix_data.json --inn-field UF_CRM_INN

Loads CRM_WEBHOOK_URL from ~/.claude/.credentials.master.env or env.

Bulk strategy: 50 INNs per crm.company.list filter[UF_CRM_INN] call.
Then for each matched company_id: deals + contacts + activities + timeline.
Aggregates per INN (multiple company_ids on one INN are merged).
"""
import sys, io, os, re, json, time, argparse
from datetime import datetime
from urllib import request, parse as urlparse, error as urlerror

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ---------- Credentials ----------

def load_webhook():
    url = os.environ.get('CRM_WEBHOOK_URL')
    if url:
        return url.rstrip('/')
    creds_path = os.path.expanduser('~/.claude/.credentials.master.env')
    if os.path.exists(creds_path):
        with open(creds_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('CRM_WEBHOOK_URL='):
                    val = line.split('=', 1)[1].strip().strip('"').strip("'")
                    return val.rstrip('/')
    raise SystemExit('CRM_WEBHOOK_URL not found in env or ~/.claude/.credentials.master.env')


# ---------- Bitrix HTTP client ----------

class Bitrix:
    def __init__(self, webhook):
        self.webhook = webhook
        self.session_calls = 0

    def call(self, method, params=None, retries=3):
        url = f'{self.webhook}/{method}.json'
        data = urlparse.urlencode(params or {}, doseq=True).encode('utf-8')
        for attempt in range(retries):
            try:
                req = request.Request(url, data=data, method='POST')
                with request.urlopen(req, timeout=60) as r:
                    self.session_calls += 1
                    body = r.read().decode('utf-8')
                    resp = json.loads(body)
                    if 'error' in resp:
                        if resp.get('error') == 'QUERY_LIMIT_EXCEEDED':
                            time.sleep(2 ** attempt)
                            continue
                        raise RuntimeError(f'{method}: {resp.get("error")} — {resp.get("error_description")}')
                    return resp
            except (urlerror.URLError, TimeoutError) as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f'{method}: {e}')
        raise RuntimeError(f'{method}: exhausted retries')

    def list_all(self, method, params=None, page_size=50):
        """Paginate via start=N."""
        params = dict(params or {})
        out = []
        start = 0
        while True:
            params['start'] = start
            resp = self.call(method, params)
            chunk = resp.get('result') or []
            if isinstance(chunk, dict):
                chunk = list(chunk.values())
            out.extend(chunk)
            total = resp.get('total', 0)
            if not chunk or start + len(chunk) >= total:
                break
            start += len(chunk) if len(chunk) >= page_size else page_size
            if start > 100000:
                break
        return out


# ---------- Match logic ----------

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def match_inns(bx, inns, inn_field):
    """Returns {company_id: company_record}, {company_id: inn}."""
    companies = {}
    company_ids_to_inn = {}
    for batch in chunks(sorted(set(inns)), 50):
        # Bitrix needs filter[KEY][]=v1&filter[KEY][]=v2 for IN-list — build pairs
        encoded = []
        for inn in batch:
            encoded.append((f'filter[{inn_field}][]', inn))
        for s in ['ID', 'TITLE', inn_field, 'ASSIGNED_BY_ID', 'INDUSTRY', 'COMPANY_TYPE', 'PHONE', 'EMAIL', 'WEB']:
            encoded.append(('select[]', s))
        url = f'{bx.webhook}/crm.company.list.json'
        out = []
        start = 0
        while True:
            cur = encoded + [('start', str(start))]
            req = request.Request(url, data=urlparse.urlencode(cur).encode('utf-8'), method='POST')
            with request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode('utf-8'))
                bx.session_calls += 1
            if 'error' in resp:
                if resp.get('error') == 'QUERY_LIMIT_EXCEEDED':
                    time.sleep(2)
                    continue
                raise RuntimeError(f'crm.company.list: {resp.get("error_description")}')
            chunk = resp.get('result', []) or []
            out.extend(chunk)
            total = resp.get('total', 0)
            if not chunk or len(out) >= total:
                break
            start += 50
        for c in out:
            cid = str(c['ID'])
            companies[cid] = c
            inn = c.get(inn_field, '')
            inn = re.sub(r'\D', '', str(inn))
            if inn:
                company_ids_to_inn[cid] = inn
    return companies, company_ids_to_inn


def fetch_company_360(bx, company_ids):
    """For each company_id collect deals, contacts, activities, timeline."""
    deals_by_company = {}
    contacts_by_company = {}
    activities_by_company = {}
    timeline_by_company = {}
    all_deals = []

    cids = sorted(set(map(str, company_ids)))
    n = len(cids)
    for i, cid in enumerate(cids, start=1):
        # Deals on company
        deals = bx.list_all('crm.deal.list', params={
            'filter[COMPANY_ID]': cid,
            'select[]': ['ID', 'TITLE', 'CATEGORY_ID', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID',
                         'ASSIGNED_BY_ID', 'DATE_CREATE', 'CLOSEDATE', 'CLOSED', 'COMPANY_ID'],
        })
        deals_by_company[cid] = deals
        all_deals.extend(deals)

        # Contacts on company
        contacts = bx.list_all('crm.contact.list', params={
            'filter[COMPANY_ID]': cid,
            'select[]': ['ID', 'NAME', 'LAST_NAME', 'SECOND_NAME', 'POST', 'PHONE', 'EMAIL'],
        })
        for c in contacts:
            c['company_id'] = cid
        contacts_by_company[cid] = contacts

        # Activities on the company
        acts = bx.list_all('crm.activity.list', params={
            'filter[OWNER_ID]': cid,
            'filter[OWNER_TYPE_ID]': 4,  # 4=COMPANY
            'select[]': ['ID', 'SUBJECT', 'TYPE_ID', 'CREATED', 'COMPLETED', 'AUTHOR_ID'],
        })
        activities_by_company[cid] = acts

        # Timeline comments on company (truncated)
        tline = bx.list_all('crm.timeline.comment.list', params={
            'filter[ENTITY_ID]': cid,
            'filter[ENTITY_TYPE]': 'company',
            'select[]': ['ID', 'COMMENT', 'CREATED', 'AUTHOR_ID'],
        })
        timeline_by_company[cid] = tline

        if i % 25 == 0 or i == n:
            print(f'  360°: {i}/{n} companies ({bx.session_calls} API calls so far)')

    # Activities on deals
    deal_activities = {}
    deal_ids = [str(d['ID']) for d in all_deals]
    for j, did in enumerate(deal_ids, start=1):
        acts = bx.list_all('crm.activity.list', params={
            'filter[OWNER_ID]': did,
            'filter[OWNER_TYPE_ID]': 2,  # 2=DEAL
            'select[]': ['ID', 'SUBJECT', 'TYPE_ID', 'CREATED', 'COMPLETED', 'AUTHOR_ID'],
        })
        deal_activities[did] = acts
        if j % 100 == 0 or j == len(deal_ids):
            print(f'  deal activities: {j}/{len(deal_ids)}')

    return deals_by_company, contacts_by_company, activities_by_company, timeline_by_company, deal_activities


def fetch_lookup_tables(bx):
    categories = {}
    for cat in bx.list_all('crm.dealcategory.list'):
        categories[str(cat['ID'])] = cat.get('NAME', f'cat:{cat["ID"]}')
    categories.setdefault('0', 'Общая')

    stages = {}
    # Default funnel stages
    for s in bx.list_all('crm.status.list', params={'filter[ENTITY_ID]': 'DEAL_STAGE'}):
        stages[s['STATUS_ID']] = s.get('NAME', s['STATUS_ID'])
    # Per-category stages
    for cat_id in categories:
        if cat_id == '0':
            continue
        try:
            for s in bx.list_all('crm.status.list', params={'filter[ENTITY_ID]': f'DEAL_STAGE_{cat_id}'}):
                stages[s['STATUS_ID']] = s.get('NAME', s['STATUS_ID'])
        except Exception:
            pass

    users = {}
    for u in bx.list_all('user.get'):
        uid = str(u['ID'])
        name = ' '.join(filter(None, [u.get('LAST_NAME'), u.get('NAME')]))
        users[uid] = {'name': name or u.get('EMAIL') or uid, 'email': u.get('EMAIL', '')}
    return categories, stages, users


# ---------- Aggregation per INN ----------

ACT_TYPES = {1: 'Звонок', 2: 'Встреча', 3: 'Задача', 4: 'Email', 6: 'СМС', 7: 'Чат'}


def fmt_phone(phone_list):
    if not phone_list:
        return ''
    parts = []
    for p in phone_list:
        if isinstance(p, dict):
            parts.append(p.get('VALUE', ''))
        else:
            parts.append(str(p))
    return '; '.join(filter(None, parts))


def fmt_email(email_list):
    return fmt_phone(email_list)


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return None


def fmt_date(s):
    d = parse_dt(s)
    return d.strftime('%Y-%m-%d') if d else (str(s) if s else '')


def aggregate(bitrix_base, inn_to_companies, companies, deals_by_company,
              contacts_by_company, activities_by_company, timeline_by_company,
              deal_activities, categories, stages, users):
    by_inn = {}
    for inn, cids in inn_to_companies.items():
        titles, urls, bitrix_ids = [], [], []
        all_deals, all_contacts, all_activities, all_timeline = [], [], [], []
        managers = set()
        for cid in cids:
            comp = companies.get(cid, {})
            titles.append(comp.get('TITLE', ''))
            bitrix_ids.append(cid)
            urls.append(f'{bitrix_base}/crm/company/details/{cid}/')
            if comp.get('ASSIGNED_BY_ID'):
                uid = str(comp['ASSIGNED_BY_ID'])
                managers.add(users.get(uid, {}).get('name') or uid)

            for d in deals_by_company.get(cid, []):
                d_copy = dict(d)
                d_copy['_company_id'] = cid
                d_copy['_category_name'] = categories.get(str(d.get('CATEGORY_ID', '0')),
                                                          f'cat:{d.get("CATEGORY_ID")}')
                d_copy['_stage_name'] = stages.get(d.get('STAGE_ID', ''), d.get('STAGE_ID', ''))
                uid = str(d.get('ASSIGNED_BY_ID', ''))
                d_copy['_manager'] = users.get(uid, {}).get('name', uid)
                if uid:
                    managers.add(users.get(uid, {}).get('name') or uid)
                all_deals.append(d_copy)
                for a in deal_activities.get(str(d['ID']), []):
                    all_activities.append({
                        'date': fmt_date(a.get('CREATED')),
                        'type': ACT_TYPES.get(int(a.get('TYPE_ID', 0) or 0), f'type{a.get("TYPE_ID")}'),
                        'subject': a.get('SUBJECT', ''),
                        'source': f'сделка #{d["ID"]}',
                        'completed': a.get('COMPLETED') == 'Y',
                    })
            for a in activities_by_company.get(cid, []):
                all_activities.append({
                    'date': fmt_date(a.get('CREATED')),
                    'type': ACT_TYPES.get(int(a.get('TYPE_ID', 0) or 0), f'type{a.get("TYPE_ID")}'),
                    'subject': a.get('SUBJECT', ''),
                    'source': f'компания #{cid}',
                    'completed': a.get('COMPLETED') == 'Y',
                })
            for t in timeline_by_company.get(cid, []):
                all_timeline.append({
                    'date': fmt_date(t.get('CREATED')),
                    'comment': (t.get('COMMENT') or '')[:200],
                    'company_id': cid,
                })
            for c in contacts_by_company.get(cid, []):
                full_name = ' '.join(filter(None, [c.get('LAST_NAME'), c.get('NAME'), c.get('SECOND_NAME')]))
                all_contacts.append({
                    'id': str(c['ID']),
                    'name': full_name or '(без имени)',
                    'post': c.get('POST', ''),
                    'phone': fmt_phone(c.get('PHONE')),
                    'email': fmt_email(c.get('EMAIL')),
                    'url': f'{bitrix_base}/crm/contact/details/{c["ID"]}/',
                    'company_id': cid,
                })

        all_activities.sort(key=lambda x: x['date'] or '', reverse=True)

        last_touch = ''
        deal_dates = [parse_dt(d.get('DATE_CREATE')) for d in all_deals]
        deal_dates = [d for d in deal_dates if d]
        if deal_dates:
            last_touch = max(deal_dates).strftime('%Y-%m-%d')
        if all_activities:
            act_max = max((a['date'] for a in all_activities if a['date']), default='')
            if act_max and (not last_touch or act_max > last_touch):
                last_touch = act_max

        by_inn[inn] = {
            'inn': inn,
            'bitrix_ids': bitrix_ids,
            'titles': titles,
            'urls': urls,
            'managers': sorted(managers),
            'products': sorted({d['_category_name'] for d in all_deals}),
            'stages_used': sorted({d['_stage_name'] for d in all_deals}),
            'deals': all_deals,
            'contacts': all_contacts,
            'activities': all_activities,
            'timeline': all_timeline,
            'touch_count': len(all_deals) + len(all_activities) + len(all_timeline),
            'last_touch': last_touch,
            'has_deals': len(all_deals) > 0,
            'has_contacts': len(all_contacts) > 0,
        }
    return by_inn


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='extracted.json from stage 1')
    ap.add_argument('--output', default='bitrix_data.json')
    ap.add_argument('--inn-field', default='UF_CRM_INN', help='Bitrix custom field for INN')
    ap.add_argument('--bitrix-url', default='https://we.company.example', help='Bitrix base URL (no trailing slash)')
    ap.add_argument('--refresh', action='store_true', help='re-fetch even if output exists')
    args = ap.parse_args()

    out_path = os.path.abspath(args.output)
    if os.path.exists(out_path) and not args.refresh:
        print(f'Already exists: {out_path}. Pass --refresh to re-fetch.')
        return

    with open(args.input, encoding='utf-8') as f:
        extracted = json.load(f)
    inns = sorted({r['inn'] for r in extracted if r.get('inn')})
    print(f'Loaded {len(extracted)} rows, {len(inns)} unique INNs')

    webhook = load_webhook()
    print(f'Webhook: {webhook[:60]}…')
    bx = Bitrix(webhook)

    t0 = time.time()
    print(f'\n[1/3] Bulk-matching INNs (50 per call)...')
    companies, company_ids_to_inn = match_inns(bx, inns, args.inn_field)
    print(f'  → matched {len(companies)} company cards on {len(set(company_ids_to_inn.values()))} INNs ({time.time()-t0:.0f}s)')

    inn_to_companies = {}
    for cid, inn in company_ids_to_inn.items():
        inn_to_companies.setdefault(inn, []).append(cid)

    print(f'\n[2/3] Fetching 360° per company...')
    t1 = time.time()
    deals_by_company, contacts_by_company, activities_by_company, \
        timeline_by_company, deal_activities = fetch_company_360(bx, list(companies))
    print(f'  → 360° done ({time.time()-t1:.0f}s)')

    print(f'\n[3/3] Fetching lookup tables (categories, stages, users)...')
    categories, stages, users = fetch_lookup_tables(bx)
    print(f'  → {len(categories)} categories, {len(stages)} stages, {len(users)} users')

    by_inn = aggregate(args.bitrix_url, inn_to_companies, companies, deals_by_company,
                       contacts_by_company, activities_by_company, timeline_by_company,
                       deal_activities, categories, stages, users)

    output = {
        'by_inn': by_inn,
        'companies': companies,
        'company_ids_to_inn': company_ids_to_inn,
        'categories': categories,
        'stages': stages,
        'users': users,
        'bitrix_base': args.bitrix_url,
        'fetched_at': datetime.now().isoformat(),
    }
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    matched_inns = len(by_inn)
    with_touches = sum(1 for v in by_inn.values() if v['touch_count'] > 0)
    print(f'\n=== Saved: {out_path} ===')
    print(f'  INNs matched: {matched_inns} / {len(inns)} ({100*matched_inns/max(len(inns),1):.0f}%)')
    print(f'  With active touches: {with_touches}')
    print(f'  Total API calls: {bx.session_calls}')
    print(f'  Total time: {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
