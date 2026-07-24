"""
Поиск ЛПР по клиентам (обычно после сделок WON).

Usage:
    python lpr_finder.py --funnel 4 --status WON
    python lpr_finder.py --clients "Газпром,ClientCorp3,Русал" --funnel 4
    python lpr_finder.py --funnel 4 --status WON --format xlsx
"""
import sys
import os
import argparse
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, safe_float, get_user_name
from report_formatter import Report


ROLE_KEYWORDS = {
    'HR / T&D / Обучение': ['hr', 'обучен', 'персонал', 'talent', 'l&d', 'training', 'develop', 'академи', 'персональ'],
    'Маркетинг / PR': ['маркетинг', 'marketing', 'pr', 'бренд', 'brand', 'пиар', 'коммуникац', 'communication'],
    'IT / Цифровизация': ['it', 'цифров', 'digital', 'cto', 'cio', 'информационных технологий', 'разработк'],
    'Топ-менеджмент': ['директор', 'ceo', 'coo', 'президент', 'founder', 'управляющ', 'chief', 'руководитель компании'],
    'Продажи / BD': ['продаж', 'sales', 'business dev', 'бд', 'коммерческ'],
    'Финансы': ['финанс', 'finance', 'cfo', 'экономи'],
    'Закупки': ['закуп', 'снабжен', 'procurement'],
    'Юридический': ['юрид', 'legal', 'юрист'],
    'Операции / Производство': ['операц', 'производ', 'operations', 'coo'],
}


def classify_role(position: str) -> str:
    """Классифицировать должность в функциональную группу."""
    if not position:
        return 'Неизвестно'
    p = position.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(k in p for k in keywords):
            return role
    return 'Прочее'


def find_lpr(funnel_id=None, status=None, clients=None, period_start=None, period_end=None):
    """Найти ЛПР сделок."""
    filt = {}
    if funnel_id is not None:
        filt['CATEGORY_ID'] = funnel_id
    if status == 'WON':
        filt['STAGE_ID'] = f'C{funnel_id}:WON' if funnel_id and funnel_id > 0 else 'WON'
    elif status == 'LOSE':
        filt['STAGE_ID'] = f'C{funnel_id}:LOSE' if funnel_id and funnel_id > 0 else 'LOSE'
    elif status == 'active':
        if funnel_id is not None and funnel_id > 0:
            filt['!STAGE_ID'] = [f'C{funnel_id}:WON', f'C{funnel_id}:LOSE']
        else:
            filt['!STAGE_ID'] = ['WON', 'LOSE']
    if period_start:
        filt['>=DATE_MODIFY'] = period_start
    if period_end:
        filt['<=DATE_MODIFY'] = period_end

    print(f'[lpr] Loading deals...', file=sys.stderr)
    deals = bx_all('crm.deal.list', {
        'filter': filt,
        'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CONTACT_ID',
                   'COMPANY_ID', 'ASSIGNED_BY_ID']
    })

    # Filter by clients if specified
    if clients:
        client_names = [c.strip().lower() for c in clients.split(',')]
        deals = [d for d in deals if any(cn in d.get('TITLE', '').lower() for cn in client_names)]

    print(f'[lpr] Deals: {len(deals)}', file=sys.stderr)

    # Fetch contacts + companies
    contact_ids = list(set(d.get('CONTACT_ID', '0') for d in deals if d.get('CONTACT_ID') and d['CONTACT_ID'] != '0'))
    company_ids = list(set(d.get('COMPANY_ID', '0') for d in deals if d.get('COMPANY_ID') and d['COMPANY_ID'] != '0'))

    print(f'[lpr] Unique contacts: {len(contact_ids)}, companies: {len(company_ids)}', file=sys.stderr)

    # Fetch contact details
    contacts = {}
    for cid in contact_ids:
        c = bx('crm.contact.get', {'ID': cid})
        r = c.get('result', {})
        if r:
            contacts[cid] = r
        time.sleep(0.3)

    # Fetch company details
    companies = {}
    for cid in company_ids:
        c = bx('crm.company.get', {'ID': cid})
        r = c.get('result', {})
        if r:
            companies[cid] = r
        time.sleep(0.3)

    # Build LPR list
    lpr_list = []
    role_counter = Counter()
    for d in deals:
        contact = contacts.get(d.get('CONTACT_ID', ''), {})
        company = companies.get(d.get('COMPANY_ID', ''), {})
        position = contact.get('POST', '') or ''
        role = classify_role(position)
        role_counter[role] += 1

        phones = contact.get('PHONE') or []
        emails = contact.get('EMAIL') or []

        lpr_list.append({
            'deal_id': d['ID'],
            'deal_title': d.get('TITLE', '')[:60],
            'amount': safe_float(d.get('OPPORTUNITY')),
            'company': company.get('TITLE', '') or '(без компании)',
            'contact_name': f"{contact.get('NAME', '')} {contact.get('LAST_NAME', '')}".strip() or '(без контакта)',
            'position': position,
            'role': role,
            'email': emails[0]['VALUE'] if emails else '',
            'phone': phones[0]['VALUE'] if phones else '',
            'manager': get_user_name(d.get('ASSIGNED_BY_ID', '0')),
        })

    return {
        'total_deals': len(deals),
        'lpr_list': lpr_list,
        'role_counter': dict(role_counter),
        'total_won_sum': sum(l['amount'] for l in lpr_list),
    }


def build_report(result, funnel_id=None, status=None):
    from manager_report import CATEGORY_NAMES

    title = 'ЛПР клиентов'
    if funnel_id is not None:
        title += f' — {CATEGORY_NAMES.get(str(funnel_id), funnel_id)}'
    if status:
        title += f' ({status})'

    r = Report(title=title)

    r.section('Сводка')
    r.kv('Сделок', result['total_deals'])
    if status == 'WON':
        r.kv('Общая выручка', f'{result["total_won_sum"]:,.0f} ₽')

    if result['role_counter']:
        r.section('Функции ЛПР')
        rows = []
        total = sum(result['role_counter'].values())
        for role, cnt in sorted(result['role_counter'].items(), key=lambda x: -x[1]):
            rows.append([role, cnt, f'{cnt / total * 100:.0f}%'])
        r.table(['Функция', 'Кол-во', '%'], rows)

    r.section('Список ЛПР')
    rows = []
    for l in sorted(result['lpr_list'], key=lambda x: -x['amount']):
        rows.append([
            l['company'][:30],
            l['contact_name'],
            l['position'][:35],
            l['role'],
            l['phone'],
            l['email'],
            f'{l["amount"]:,.0f}' if l['amount'] else '—',
            l['manager'],
        ])
    r.table(['Компания', 'ЛПР', 'Должность', 'Функция', 'Телефон', 'Email', 'Сумма', 'Менеджер'], rows)

    return r


def main():
    ap = argparse.ArgumentParser(description='Поиск ЛПР по клиентам')
    ap.add_argument('--funnel', type=int, default=None)
    ap.add_argument('--status', default=None, choices=['WON', 'LOSE', 'active'])
    ap.add_argument('--clients', default=None, help='Список клиентов через запятую')
    ap.add_argument('--period', default='all')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    from bx_client import parse_period
    period_start, period_end = parse_period(args.period)

    result = find_lpr(funnel_id=args.funnel, status=args.status, clients=args.clients,
                      period_start=period_start, period_end=period_end)
    report = build_report(result, funnel_id=args.funnel, status=args.status)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
