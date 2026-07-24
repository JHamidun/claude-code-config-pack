"""
Аудит здоровья воронки: мёртвые сделки, без суммы, без компании, дубли, протухшие лиды.

Usage:
    python funnel_audit.py --funnel 43
    python funnel_audit.py --funnel all --stale-days 90
    python funnel_audit.py --funnel 4 --format xlsx
"""
import sys
import os
import argparse
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, safe_float, parse_dt, get_user_name
from report_formatter import Report


def audit_funnel(funnel_id, stale_days=90):
    """Аудит одной воронки."""
    print(f'[audit] Loading funnel {funnel_id}...', file=sys.stderr)
    deals = bx_all('crm.deal.list', {
        'filter': {'CATEGORY_ID': funnel_id},
        'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'DATE_CREATE',
                   'DATE_MODIFY', 'CLOSEDATE', 'CONTACT_ID', 'COMPANY_ID',
                   'ASSIGNED_BY_ID']
    })

    total = len(deals)
    won_stage = f'C{funnel_id}:WON' if funnel_id > 0 else 'WON'
    lose_stage = f'C{funnel_id}:LOSE' if funnel_id > 0 else 'LOSE'

    won = [d for d in deals if d.get('STAGE_ID') == won_stage]
    lose = [d for d in deals if d.get('STAGE_ID') == lose_stage]
    active = [d for d in deals if d.get('STAGE_ID') not in (won_stage, lose_stage)]

    now = datetime.now()
    stale_threshold = now - timedelta(days=stale_days)

    # Stale active deals
    stale = []
    for d in active:
        dm = parse_dt(d.get('DATE_MODIFY', ''))
        if dm and dm < stale_threshold:
            stale.append(d)

    # No amount in late stages
    no_amount_won = sum(1 for d in won if safe_float(d.get('OPPORTUNITY')) == 0)
    no_amount_active = sum(1 for d in active if safe_float(d.get('OPPORTUNITY')) == 0)

    # No linkage
    no_company = sum(1 for d in deals if not d.get('COMPANY_ID') or d['COMPANY_ID'] == '0')
    no_contact = sum(1 for d in deals if not d.get('CONTACT_ID') or d['CONTACT_ID'] == '0')

    # By stage
    by_stage = Counter(d.get('STAGE_ID') for d in deals)

    # Empty stages (in category)
    if funnel_id > 0:
        all_stages_api = bx('crm.dealcategory.stage.list', {'id': funnel_id})
    else:
        all_stages_api = bx('crm.status.list', {'filter': {'ENTITY_ID': 'DEAL_STAGE'}})
    all_stages = all_stages_api.get('result', [])
    empty_stages = [s for s in all_stages if by_stage.get(s['STATUS_ID'], 0) == 0
                    and s.get('SEMANTICS') not in ('S', 'F')]

    # Stage bucket age
    stage_ages = {}
    for stg, cnt in by_stage.most_common():
        if stg in (won_stage, lose_stage):
            continue
        ages = []
        for d in deals:
            if d.get('STAGE_ID') != stg:
                continue
            dm = parse_dt(d.get('DATE_MODIFY', ''))
            if dm:
                ages.append((now - dm).days)
        if ages:
            ages.sort()
            stage_ages[stg] = {
                'count': cnt,
                'avg': sum(ages) / len(ages),
                'median': ages[len(ages) // 2],
                'max': max(ages),
                'stale_90d': sum(1 for a in ages if a > 90),
            }

    # Top assigned
    assigned = Counter(d.get('ASSIGNED_BY_ID', '0') for d in active)

    return {
        'funnel_id': funnel_id,
        'total': total,
        'won': len(won),
        'lose': len(lose),
        'active': len(active),
        'stale_active': len(stale),
        'stale_days': stale_days,
        'no_amount_won': no_amount_won,
        'no_amount_active': no_amount_active,
        'no_company_pct': no_company / total * 100 if total else 0,
        'no_contact_pct': no_contact / total * 100 if total else 0,
        'no_company': no_company,
        'no_contact': no_contact,
        'by_stage': dict(by_stage),
        'empty_stages': [{'id': s['STATUS_ID'], 'name': s['NAME']} for s in empty_stages],
        'stage_ages': stage_ages,
        'top_assigned': assigned.most_common(10),
        'stale_sample': [{
            'id': d['ID'], 'title': d.get('TITLE', '')[:60],
            'stage': d.get('STAGE_ID'), 'modified': d.get('DATE_MODIFY', '')[:10]
        } for d in stale[:20]],
    }


def build_report(audit, funnel_id):
    from manager_report import CATEGORY_NAMES
    fname = CATEGORY_NAMES.get(str(funnel_id), f'ID {funnel_id}')

    r = Report(title=f'Аудит воронки {fname} (ID {funnel_id})')

    r.section('Общая картина')
    r.kv('Всего сделок', audit['total'])
    r.kv('WON', audit['won'])
    r.kv('LOSE', audit['lose'])
    r.kv('Активных', audit['active'])
    win_rate = audit['won'] / (audit['won'] + audit['lose']) * 100 if (audit['won'] + audit['lose']) else 0
    r.kv('Win rate', f'{win_rate:.1f}%')

    r.section('Проблемы данных')
    r.kv('Протухших активных сделок',
         audit['stale_active'],
         comment=f'>= {audit["stale_days"]} дней без изменений',
         highlight='red' if audit['stale_active'] > audit['active'] * 0.5 else 'yellow' if audit['stale_active'] > 20 else None)
    r.kv('WON без суммы (=0)',
         audit['no_amount_won'],
         comment='Реальная выручка занижена' if audit['no_amount_won'] > 5 else None,
         highlight='red' if audit['no_amount_won'] > 20 else None)
    r.kv('Активные без суммы',
         audit['no_amount_active'],
         comment='Pipeline недооценён' if audit['no_amount_active'] > 20 else None)
    r.kv('Без привязки к компании',
         f'{audit["no_company"]} ({audit["no_company_pct"]:.0f}%)',
         highlight='red' if audit['no_company_pct'] > 80 else None)
    r.kv('Без контакта',
         f'{audit["no_contact"]} ({audit["no_contact_pct"]:.0f}%)')

    if audit['empty_stages']:
        r.section('Мёртвые стадии (0 сделок)')
        r.bullet([f'{s["name"]} ({s["id"]})' for s in audit['empty_stages']])

    # Stage age
    if audit['stage_ages']:
        r.section('Возраст сделок по стадиям')
        rows = []
        for stg, s in sorted(audit['stage_ages'].items(), key=lambda x: -x[1]['count']):
            rows.append([
                stg, s['count'],
                f'{s["avg"]:.0f}d',
                f'{s["median"]}d',
                f'{s["max"]}d',
                s['stale_90d'],
            ])
        r.table(['Стадия', 'Кол-во', 'Ср.возраст', 'Медиана', 'Макс', 'Протух.(>90d)'], rows)

    # Top assigned
    if audit['top_assigned']:
        r.section('Топ ответственных (активные сделки)')
        rows = []
        for uid, cnt in audit['top_assigned']:
            rows.append([get_user_name(uid), cnt])
        r.table(['Менеджер', 'Активных сделок'], rows)

    # Stale sample
    if audit['stale_sample']:
        r.section('Примеры протухших сделок')
        rows = [[d['id'], d['title'], d['stage'], d['modified']] for d in audit['stale_sample']]
        r.table(['ID', 'Название', 'Стадия', 'Последнее изменение'], rows)

    # Recs
    recs = []
    if audit['stale_active'] > 20:
        recs.append(f'Массово закрыть {audit["stale_active"]} протухших сделок в LOSE или реактивировать')
    if audit['no_amount_won'] > 10:
        recs.append(f'{audit["no_amount_won"]} WON-сделок без суммы — восстановить или очистить, реальная выручка занижена')
    if audit['no_company_pct'] > 50:
        recs.append('Робот на обязательную привязку компании для B2B воронок')
    if audit['empty_stages']:
        recs.append(f'{len(audit["empty_stages"])} мёртвых стадий — рассмотреть удаление или переиспользование')

    if recs:
        r.section('Рекомендации')
        r.bullet(recs)

    return r


def build_all_report(audits):
    """Сводка по всем воронкам."""
    r = Report(title='Аудит всех воронок')

    r.section('Сводка')
    rows = []
    for aud in audits:
        from manager_report import CATEGORY_NAMES
        fname = CATEGORY_NAMES.get(str(aud['funnel_id']), f'ID {aud["funnel_id"]}')
        rows.append([
            aud['funnel_id'], fname, aud['total'], aud['won'], aud['lose'], aud['active'],
            aud['stale_active'], aud['no_amount_active'], f'{aud["no_company_pct"]:.0f}%'
        ])
    r.table(
        ['ID', 'Воронка', 'Всего', 'WON', 'LOSE', 'Актив.', 'Протух.', 'Без сум.', '%без комп.'],
        rows,
    )

    return r


def main():
    ap = argparse.ArgumentParser(description='Аудит воронки продаж')
    ap.add_argument('--funnel', default='43', help='ID воронки или "all"')
    ap.add_argument('--stale-days', type=int, default=90, help='Порог для протухших сделок')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    if args.funnel == 'all':
        # All funnels
        cats = bx('crm.dealcategory.list').get('result', [])
        cats_ids = [0] + [int(c['ID']) for c in cats]
        audits = []
        for fid in cats_ids:
            print(f'[audit] Auditing funnel {fid}...', file=sys.stderr)
            audits.append(audit_funnel(fid, args.stale_days))
        report = build_all_report(audits)
    else:
        audit = audit_funnel(int(args.funnel), args.stale_days)
        report = build_report(audit, int(args.funnel))

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
