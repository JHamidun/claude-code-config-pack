"""
Взвешенный прогноз выручки по open pipeline.

Usage:
    python pipeline_forecast.py --funnel 5
    python pipeline_forecast.py --funnel 4 --weighted --manager "Ушаков"
    python pipeline_forecast.py --team --top 20
"""
import sys
import os
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, safe_float, resolve_manager_id, get_user_name
from report_formatter import Report


# Вероятность закрытия по стадиям — эмпирическая оценка (можно вынести в конфиг)
STAGE_PROBABILITY = {
    # GPT B2B
    'C4:NEW': 0.05,
    'C4:UC_T5BERE': 0.10,
    'C4:EXECUTING': 0.15,
    'C4:UC_S3F2NM': 0.25,
    'C4:UC_CA3O7C': 0.35,
    'C4:UC_Z5VDQD': 0.40,
    'C4:UC_Z4ZPF5': 0.50,
    'C4:UC_TK7EW1': 0.30,
    'C4:UC_RHZ818': 0.25,
    'C4:UC_KC92ZU': 0.75,
    'C4:FINAL_INVOICE': 0.90,
    # АПРО
    'C5:NEW': 0.05,
    'C5:PREPARATION': 0.10,
    'C5:PREPAYMENT_INVOICE': 0.20,
    'C5:EXECUTING': 0.30,
    'C5:UC_HMT62X': 0.40,
    'C5:UC_KRTGGS': 0.50,
    'C5:UC_WZV0XD': 0.65,
    'C5:UC_NJOCFA': 0.80,
    'C5:FINAL_INVOICE': 0.90,
    # Библиотека
    'C19:NEW': 0.05,
    'C19:AMO_D46AA722': 0.10,
    'C19:AMO_C1098820': 0.15,
    'C19:UC_5XTJIE': 0.25,
    'C19:AMO_E6E58936': 0.40,
    'C19:UC_B7QR13': 0.55,
    'C19:AMO_25BEA848': 0.65,
    'C19:AMO_CBEA2486': 0.80,
    # Продления
    'C21:NEW': 0.10,
    'C21:AMO_9A9AFD17': 0.30,
    'C21:AMO_4AD2D956': 0.60,
    # TransformAI
    'C43:NEW': 0.05,
    'C43:REGISTERED': 0.10,
    'C43:GIFTS_SENT': 0.15,
    'C43:ATTENDED': 0.20,
    'C43:UC_KP_SENT': 0.35,
    'C43:UC_MEETING_SET': 0.45,
    'C43:UC_MEETING_DONE': 0.55,
    'C43:DEMO': 0.50,
    # Default
    'NEW': 0.10,
    'PREPARATION': 0.20,
    'PREPAYMENT_INVOICE': 0.30,
    'EXECUTING': 0.40,
    'FINAL_INVOICE': 0.75,
}


def forecast(funnel_id=None, manager_id=None, weighted=True, top=None):
    """Прогноз по pipeline."""
    filt = {}
    if funnel_id is not None:
        filt['CATEGORY_ID'] = funnel_id
    if manager_id:
        filt['ASSIGNED_BY_ID'] = manager_id

    if funnel_id is not None:
        won_stage = f'C{funnel_id}:WON' if funnel_id > 0 else 'WON'
        lose_stage = f'C{funnel_id}:LOSE' if funnel_id > 0 else 'LOSE'
        filt['!STAGE_ID'] = [won_stage, lose_stage]
    else:
        # Все не WON и не LOSE — нужно обрабатывать после
        pass

    print(f'[forecast] Loading pipeline deals...', file=sys.stderr)
    deals = bx_all('crm.deal.list', {
        'filter': filt,
        'select': ['ID', 'TITLE', 'CATEGORY_ID', 'STAGE_ID', 'OPPORTUNITY',
                   'CURRENCY_ID', 'ASSIGNED_BY_ID', 'COMPANY_ID',
                   'DATE_CREATE', 'DATE_MODIFY']
    })

    # Filter out WON/LOSE if funnel not specified
    if funnel_id is None:
        deals = [d for d in deals if 'WON' not in d.get('STAGE_ID', '') and 'LOSE' not in d.get('STAGE_ID', '')]

    print(f'[forecast] Active deals: {len(deals)}', file=sys.stderr)

    # Sums
    total_pipeline = 0.0
    weighted_pipeline = 0.0
    by_stage = defaultdict(lambda: {'count': 0, 'sum': 0.0, 'weighted': 0.0})
    by_assigned = defaultdict(lambda: {'count': 0, 'sum': 0.0, 'weighted': 0.0})

    deal_list = []
    for d in deals:
        amt = safe_float(d.get('OPPORTUNITY'))
        stage = d.get('STAGE_ID')
        prob = STAGE_PROBABILITY.get(stage, 0.20)
        w = amt * prob

        total_pipeline += amt
        weighted_pipeline += w

        by_stage[stage]['count'] += 1
        by_stage[stage]['sum'] += amt
        by_stage[stage]['weighted'] += w

        uid = d.get('ASSIGNED_BY_ID', '0')
        by_assigned[uid]['count'] += 1
        by_assigned[uid]['sum'] += amt
        by_assigned[uid]['weighted'] += w

        deal_list.append({
            'id': d['ID'],
            'title': d.get('TITLE', '')[:60],
            'stage': stage,
            'amount': amt,
            'probability': prob,
            'weighted': w,
            'assigned': uid,
        })

    # Sort deals by weighted
    deal_list.sort(key=lambda x: -x['weighted'])

    return {
        'total_deals': len(deals),
        'total_pipeline': total_pipeline,
        'weighted_pipeline': weighted_pipeline,
        'by_stage': dict(by_stage),
        'by_assigned': dict(by_assigned),
        'top_deals': deal_list[:top or 30],
    }


def build_report(result, funnel_id=None, manager_name='', top=30):
    from manager_report import CATEGORY_NAMES

    title = 'Прогноз выручки по pipeline'
    if funnel_id is not None:
        fname = CATEGORY_NAMES.get(str(funnel_id), f'ID {funnel_id}')
        title += f' — {fname}'
    if manager_name:
        title += f' ({manager_name})'

    r = Report(title=title)

    r.section('Итоги')
    r.kv('Активных сделок', result['total_deals'])
    r.kv('Общий pipeline', f'{result["total_pipeline"]:,.0f} ₽')
    r.kv('Взвешенный прогноз', f'{result["weighted_pipeline"]:,.0f} ₽',
         comment=f'~{result["weighted_pipeline"] / max(result["total_pipeline"], 1) * 100:.0f}% от общего')

    if result['by_stage']:
        r.section('По стадиям')
        rows = []
        for stage, s in sorted(result['by_stage'].items(), key=lambda x: -x[1]['weighted']):
            prob = STAGE_PROBABILITY.get(stage, 0.20)
            rows.append([
                stage, s['count'],
                f'{s["sum"]:,.0f}',
                f'{prob * 100:.0f}%',
                f'{s["weighted"]:,.0f}',
            ])
        r.table(['Стадия', 'Сделок', 'Pipeline ₽', 'Вероятн.', 'Взвешенный ₽'], rows)

    if result['by_assigned']:
        r.section('По менеджерам')
        rows = []
        for uid, s in sorted(result['by_assigned'].items(), key=lambda x: -x[1]['weighted'])[:15]:
            rows.append([
                get_user_name(uid), s['count'],
                f'{s["sum"]:,.0f}',
                f'{s["weighted"]:,.0f}',
            ])
        r.table(['Менеджер', 'Сделок', 'Pipeline ₽', 'Взвешенный ₽'], rows)

    if result['top_deals']:
        r.section(f'Топ-{top} сделок по взвешенному прогнозу')
        rows = []
        for d in result['top_deals'][:top]:
            rows.append([
                d['id'], d['title'], get_user_name(d['assigned']),
                d['stage'],
                f'{d["amount"]:,.0f}',
                f'{d["probability"] * 100:.0f}%',
                f'{d["weighted"]:,.0f}',
            ])
        r.table(['ID', 'Название', 'Менеджер', 'Стадия', 'Сумма', 'Вер.', 'Взвеш.'], rows)

    return r


def main():
    ap = argparse.ArgumentParser(description='Прогноз выручки по pipeline')
    ap.add_argument('--funnel', type=int, default=None, help='ID воронки (по умолчанию — все)')
    ap.add_argument('--manager', default=None)
    ap.add_argument('--team', action='store_true', help='Вся команда')
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--weighted', action='store_true', help='По умолчанию считаем и то, и то')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    manager_id = resolve_manager_id(args.manager) if args.manager and not args.team else None
    manager_name = get_user_name(manager_id) if manager_id else ''

    result = forecast(funnel_id=args.funnel, manager_id=manager_id, top=args.top)
    report = build_report(result, funnel_id=args.funnel, manager_name=manager_name, top=args.top)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
