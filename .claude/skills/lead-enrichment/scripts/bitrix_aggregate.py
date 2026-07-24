# -*- coding: utf-8 -*-
"""Aggregate Your CRM history per matched INN. Port of the proven Outreach×Bitrix aggregator.

Usage:  python bitrix_aggregate.py bitrix_data.json [--out aggregated.json] [--base https://we.company.example]

bitrix_data.json keys (see references/bitrix-export.md):
  companies, deals_by_company, contacts_by_company, deal_activities,
  activities_by_company, timeline_by_company, categories, stages, users, company_ids_to_inn

Output aggregated.json: {inn: {titles, urls, managers, products, stages_used, deals, contacts,
  activities, timeline, touch_count, last_touch, has_deals, has_contacts}}
"""
import sys, io, json, argparse
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ACT_TYPES = {1: 'Звонок', 2: 'Встреча', 3: 'Задача', 4: 'Email', 6: 'СМС', 7: 'Чат'}

def fmt_multi(lst):
    if not lst:
        return ''
    out = []
    for p in lst:
        out.append(p.get('VALUE', '') if isinstance(p, dict) else str(p))
    return '; '.join(filter(None, out))

def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return None

def fmt_date(s):
    d = parse_date(s)
    return d.strftime('%Y-%m-%d') if d else (s or '')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bitrix_json'); ap.add_argument('--out', default='aggregated.json')
    ap.add_argument('--base', default='https://we.company.example')
    a = ap.parse_args()
    bd = json.load(open(a.bitrix_json, encoding='utf-8'))
    BASE = a.base
    companies = bd['companies']; deals_by_company = bd.get('deals_by_company', {})
    contacts_by_company = bd.get('contacts_by_company', {}); deal_activities = bd.get('deal_activities', {})
    activities_by_company = bd.get('activities_by_company', {}); timeline_by_company = bd.get('timeline_by_company', {})
    categories = bd.get('categories', {}); stages = bd.get('stages', {}); users = bd.get('users', {})

    inn_to_companies = {}
    for cid, inn in bd['company_ids_to_inn'].items():
        if inn:
            inn_to_companies.setdefault(str(inn), []).append(cid)

    def aggregate_inn(inn):
        cids = inn_to_companies.get(inn, [])
        if not cids:
            return None
        titles, urls, bitrix_ids = [], [], []
        all_deals, all_contacts, all_activities, all_timeline = [], [], [], []
        managers = set()
        for cid in cids:
            comp = companies.get(cid, {})
            titles.append(comp.get('TITLE', '')); bitrix_ids.append(cid)
            urls.append(f'{BASE}/crm/company/details/{cid}/')
            if comp.get('ASSIGNED_BY_ID'):
                uid = str(comp['ASSIGNED_BY_ID']); managers.add(users.get(uid, {}).get('name') or uid)
            for d in deals_by_company.get(cid, []) or []:
                dc = dict(d); dc['_company_id'] = cid
                dc['_category_name'] = categories.get(str(d.get('CATEGORY_ID', '0')), 'cat:' + str(d.get('CATEGORY_ID')))
                dc['_stage_name'] = stages.get(d.get('STAGE_ID', ''), d.get('STAGE_ID', ''))
                uid = str(d.get('ASSIGNED_BY_ID', '')); dc['_manager'] = users.get(uid, {}).get('name', uid)
                if uid:
                    managers.add(users.get(uid, {}).get('name') or uid)
                all_deals.append(dc)
                for act in deal_activities.get(d['ID'], []) or []:
                    all_activities.append({'date': fmt_date(act.get('CREATED')),
                        'type': ACT_TYPES.get(int(act.get('TYPE_ID', 0) or 0), 'type' + str(act.get('TYPE_ID'))),
                        'subject': act.get('SUBJECT', ''), 'source': 'сделка #' + str(d['ID']),
                        'completed': act.get('COMPLETED') == 'Y'})
            for act in activities_by_company.get(cid, []) or []:
                all_activities.append({'date': fmt_date(act.get('CREATED')),
                    'type': ACT_TYPES.get(int(act.get('TYPE_ID', 0) or 0), 'type' + str(act.get('TYPE_ID'))),
                    'subject': act.get('SUBJECT', ''), 'source': 'компания #' + cid,
                    'completed': act.get('COMPLETED') == 'Y'})
            for t in timeline_by_company.get(cid, []) or []:
                all_timeline.append({'date': fmt_date(t.get('CREATED')), 'comment': (t.get('COMMENT') or '')[:200], 'company_id': cid})
            for c in contacts_by_company.get(cid, []) or []:
                full = ' '.join(filter(None, [c.get('LAST_NAME'), c.get('NAME'), c.get('SECOND_NAME')]))
                all_contacts.append({'id': c['ID'], 'name': full or '(без имени)', 'post': c.get('POST', ''),
                    'phone': fmt_multi(c.get('PHONE')), 'email': fmt_multi(c.get('EMAIL')),
                    'url': f'{BASE}/crm/contact/details/{c["ID"]}/', 'company_id': cid})
        all_activities.sort(key=lambda x: x['date'] or '', reverse=True)
        last_touch = ''
        deal_dates = [parse_date(d.get('DATE_CREATE')) for d in all_deals]
        deal_dates = [d for d in deal_dates if d]
        if deal_dates:
            last_touch = max(deal_dates).strftime('%Y-%m-%d')
        act_max = max((x['date'] for x in all_activities if x['date']), default='')
        if act_max and (not last_touch or act_max > last_touch):
            last_touch = act_max
        return {'inn': inn, 'bitrix_ids': bitrix_ids, 'titles': titles, 'urls': urls,
            'managers': sorted(managers), 'products': sorted(set(d['_category_name'] for d in all_deals)),
            'stages_used': sorted(set(d['_stage_name'] for d in all_deals)), 'deals': all_deals,
            'contacts': all_contacts, 'activities': all_activities, 'timeline': all_timeline,
            'touch_count': len(all_deals) + len(all_activities) + len(all_timeline), 'last_touch': last_touch,
            'has_deals': len(all_deals) > 0, 'has_contacts': len(all_contacts) > 0}

    agg = {inn: aggregate_inn(inn) for inn in inn_to_companies}
    json.dump(agg, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
    print('Aggregated INNs:', len(agg), '| with deals:', sum(1 for v in agg.values() if v and v['has_deals']),
          '| with touches:', sum(1 for v in agg.values() if v and v['touch_count'] > 0))
    print('Saved ->', a.out)

if __name__ == '__main__':
    main()
