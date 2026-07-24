"""
Конверсия по стадиям воронки — с расчётом drop на каждом переходе.

Usage:
    python conversion_stages.py --funnel 4
    python conversion_stages.py --funnel 43 --manager "Ушаков"
    python conversion_stages.py --funnel 4 --compare-managers "Ушаков,Захаров"
    python conversion_stages.py --funnel 43 --team
"""
import sys
import os
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, resolve_manager_id, resolve_manager_ids, get_stage_names, get_user_name
from report_formatter import Report


# Порядок стадий по воронкам (semantic ordering)
FUNNEL_ORDER = {
    3: [  # Голосовой бот EdTech
        ('C3:NEW', 'База на прозвон'),
        ('C3:PREPARATION', 'Звонок 1'),
        ('C3:PREPAYMENT_INVOICE', 'Звонок 2'),
        ('C3:EXECUTING', 'Звонок 3'),
        ('C3:UC_7NS06U', 'Бот дозвонился'),
        ('C3:UC_FVON9G', 'Согласие'),
    ],
    4: [  # GPT B2B
        ('C4:NEW', 'Новый лид'),
        ('C4:UC_T5BERE', 'Демо доступ назначен'),
        ('C4:EXECUTING', 'Демо назначено'),
        ('C4:UC_S3F2NM', 'Демо проведено'),
        ('C4:UC_CA3O7C', 'КП направлено'),
        ('C4:UC_Z5VDQD', 'Встреча назначена'),
        ('C4:UC_Z4ZPF5', 'Презентовано КП'),
        ('C4:UC_TK7EW1', 'Клиент думает'),
        ('C4:UC_RHZ818', 'Отложенная покупка'),
        ('C4:UC_KC92ZU', 'Согласование договора'),
        ('C4:FINAL_INVOICE', 'Договор подписан'),
    ],
    5: [  # АПРО
        ('C5:NEW', 'Получен новый лид'),
        ('C5:PREPARATION', 'Лид взят в работу'),
        ('C5:PREPAYMENT_INVOICE', 'Клиент квалифицирован'),
        ('C5:EXECUTING', 'Хороший лид'),
        ('C5:UC_HMT62X', 'Подготовка КП'),
        ('C5:UC_KRTGGS', 'КП отправлено клиенту'),
        ('C5:UC_WZV0XD', 'КП на утверждении'),
        ('C5:UC_NJOCFA', 'Договор отправлен'),
        ('C5:FINAL_INVOICE', 'Договор подписан'),
    ],
    6: [  # GPT B2C
        ('C6:NEW', 'Входящие лиды'),
        ('C6:PREPAYMENT_INVOICE', 'Демо доступ назначен'),
        ('C6:UC_92E7MS', 'Демо доступ окончен'),
        ('C6:EXECUTING', 'Прогрев / в работе'),
        ('C6:FINAL_INVOICE', 'Решение принято'),
        ('C6:UC_18VS6A', 'Сделка реализована'),
    ],
    19: [  # Библиотека
        ('C19:NEW', 'ВЗЯЛ В РАБОТУ'),
        ('C19:AMO_D46AA722', 'Ищу контакты'),
        ('C19:AMO_C1098820', 'Прогрев'),
        ('C19:UC_5XTJIE', 'Запрошен демо'),
        ('C19:AMO_E6E58936', 'КП отправлено'),
        ('C19:UC_B7QR13', 'Встреча проведена'),
        ('C19:AMO_25BEA848', 'В работе'),
        ('C19:AMO_CBEA2486', 'Решение принято'),
    ],
    21: [  # Продления
        ('C21:NEW', 'Новые клиенты'),
        ('C21:AMO_9A9AFD17', 'Активные клиенты'),
        ('C21:AMO_4AD2D956', 'Продление'),
    ],
    40: [  # EdTech продажи
        ('C40:NEW', 'КП отправлено'),
        ('C40:PREPARATION', 'В работе'),
        ('C40:UC_U7JH3Q', 'На следующий поток'),
        ('C40:FINAL_INVOICE', 'Счёт выставлен'),
        ('C40:EXECUTING', 'Клиент согласился'),
    ],
    43: [  # TransformAI
        ('C43:NEW', 'Взят в работу'),
        ('C43:REGISTERED', 'Зарегистрирован'),
        ('C43:GIFTS_SENT', 'Подарки отправлены'),
        ('C43:ATTENDED', 'Был на конференции'),
        ('C43:UC_KP_SENT', 'КП отправлено'),
        ('C43:UC_MEETING_SET', 'Встреча назначена'),
        ('C43:UC_MEETING_DONE', 'Встреча проведена'),
        ('C43:DEMO', 'Демо YourProduct'),
        ('C43:UC_NO_CALL', 'Недозвон'),
    ],
}


def get_funnel_order(funnel_id):
    """Получить порядок стадий, использовать fallback из API если не задано."""
    if funnel_id in FUNNEL_ORDER:
        return FUNNEL_ORDER[funnel_id]
    stages = get_stage_names(funnel_id)
    # Fallback: order by API sort
    api_stages = bx('crm.dealcategory.stage.list' if funnel_id > 0 else 'crm.status.list',
                    {'id': funnel_id} if funnel_id > 0 else {'filter': {'ENTITY_ID': 'DEAL_STAGE'}})
    result = api_stages.get('result', [])
    result_filtered = [(s['STATUS_ID'], s['NAME']) for s in result
                       if s.get('SEMANTICS') not in ('S', 'F')]  # skip WON/LOSE
    return result_filtered


def compute_conversion(funnel_id, manager_id=None, period_start=None, period_end=None):
    """Посчитать конверсию по этапам воронки."""
    filt = {'CATEGORY_ID': funnel_id}
    if manager_id:
        filt['ASSIGNED_BY_ID'] = manager_id
    if period_start:
        filt['>=DATE_MODIFY'] = period_start
    if period_end:
        filt['<=DATE_MODIFY'] = period_end

    deals = bx_all('crm.deal.list', {'filter': filt, 'select': ['ID', 'STAGE_ID']})
    by_stage = Counter(d['STAGE_ID'] for d in deals)

    won_stage = f'C{funnel_id}:WON' if funnel_id > 0 else 'WON'
    lose_stage = f'C{funnel_id}:LOSE' if funnel_id > 0 else 'LOSE'
    won_count = by_stage.get(won_stage, 0)
    lose_count = by_stage.get(lose_stage, 0)
    total = len(deals)

    order = get_funnel_order(funnel_id)
    order_stages = [s[0] for s in order]

    rows = []
    prev_reached = total  # everyone starts at first stage

    for i, (stage, name) in enumerate(order):
        current = by_stage.get(stage, 0)
        # Cumulative: this stage + all later stages + WON
        later_sum = sum(by_stage.get(s, 0) for s in order_stages[i + 1:])
        reached = current + later_sum + won_count
        if i == 0:
            reached = total  # first stage: everyone passed through

        conv = reached / prev_reached * 100 if prev_reached > 0 else 0
        drop = prev_reached - reached
        rows.append({
            'stage': name,
            'stage_id': stage,
            'current': current,
            'reached': reached,
            'conv_from_prev': conv,
            'drop': drop,
        })
        prev_reached = reached

    # WON row
    conv_won = won_count / prev_reached * 100 if prev_reached > 0 else 0
    rows.append({
        'stage': 'WON',
        'stage_id': won_stage,
        'current': won_count,
        'reached': won_count,
        'conv_from_prev': conv_won,
        'drop': prev_reached - won_count,
    })

    lose_rate = lose_count / total * 100 if total else 0

    return {
        'funnel_id': funnel_id,
        'total': total,
        'won': won_count,
        'lose': lose_count,
        'lose_rate': lose_rate,
        'rows': rows,
    }


def build_single_report(result, manager_name='', period_str=''):
    from manager_report import CATEGORY_NAMES
    fname = CATEGORY_NAMES.get(str(result['funnel_id']), f'ID {result["funnel_id"]}')

    title = f'Конверсия воронки {fname}'
    if manager_name:
        title += f' — {manager_name}'

    r = Report(title=title, period=period_str or 'вся история')

    r.section('Итоги воронки')
    r.kv('Всего сделок', result['total'])
    r.kv('WON', result['won'], highlight='green' if result['won'] > 0 else 'red')
    r.kv('LOSE', result['lose'], comment=f'{result["lose_rate"]:.0f}%')

    r.section('Конверсия по стадиям')
    rows = []
    for row in result['rows']:
        rows.append([
            row['stage'],
            row['current'],
            row['reached'],
            f'{row["conv_from_prev"]:.1f}%',
            row['drop'],
        ])
    r.table(['Стадия', 'Текущая позиция', 'Прошло (cum.)', 'Конв. от пред.', 'Drop'], rows)

    # Best / worst
    stages_only = [row for row in result['rows'] if row['stage'] != 'WON']
    if stages_only:
        best = max(stages_only[1:], key=lambda x: x['conv_from_prev'], default=None)
        worst = min(stages_only[1:], key=lambda x: x['conv_from_prev'], default=None)

        highlights = []
        if best:
            highlights.append(f'Лучшая конверсия: «{best["stage"]}» → {best["conv_from_prev"]:.1f}% (drop {best["drop"]})')
        if worst:
            highlights.append(f'Худшая конверсия: «{worst["stage"]}» → {worst["conv_from_prev"]:.1f}% (drop {worst["drop"]})')

        won_row = result['rows'][-1]
        if won_row['conv_from_prev'] == 0:
            highlights.append('От последней стадии до WON — 0%. Не дожимаем сделки в оплату.')

        r.section('Точки внимания')
        r.bullet(highlights)

    return r


def build_comparison_report(results_by_manager, funnel_id, period_str=''):
    """Сравнение конверсий по стадиям между менеджерами."""
    from manager_report import CATEGORY_NAMES
    fname = CATEGORY_NAMES.get(str(funnel_id), f'ID {funnel_id}')

    r = Report(
        title=f'Конверсия по воронке {fname} — сравнение менеджеров',
        period=period_str or 'вся история',
    )

    # Aggregate stages
    all_stage_names = []
    seen = set()
    for res in results_by_manager.values():
        for row in res['rows']:
            if row['stage'] not in seen:
                all_stage_names.append(row['stage'])
                seen.add(row['stage'])

    # Build cross-table: rows = stages, columns = managers
    r.section('Конверсия от предыдущей стадии (% дошедших)')
    headers = ['Стадия'] + list(results_by_manager.keys())
    rows = []
    for sname in all_stage_names:
        row = [sname]
        for mgr, res in results_by_manager.items():
            match = next((r for r in res['rows'] if r['stage'] == sname), None)
            if match:
                row.append(f'{match["conv_from_prev"]:.1f}%')
            else:
                row.append('—')
        rows.append(row)
    r.table(headers, rows)

    # Overall
    r.section('Итоги')
    rows = []
    for mgr, res in results_by_manager.items():
        rows.append([
            mgr,
            res['total'],
            res['won'],
            res['lose'],
            f'{res["lose_rate"]:.0f}%',
        ])
    r.table(['Менеджер', 'Всего', 'WON', 'LOSE', '%LOSE'], rows)

    return r


def main():
    ap = argparse.ArgumentParser(description='Конверсия по стадиям воронки')
    ap.add_argument('--funnel', type=int, required=True)
    ap.add_argument('--manager', default=None)
    ap.add_argument('--compare-managers', default=None, help='Список через запятую для сравнения')
    ap.add_argument('--team', action='store_true', help='Все активные менеджеры воронки')
    ap.add_argument('--period', default='all')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    from bx_client import parse_period
    period_start, period_end = parse_period(args.period)

    if args.compare_managers or args.team:
        if args.team:
            # Get all managers with deals in this funnel
            deals = bx_all('crm.deal.list', {
                'filter': {'CATEGORY_ID': args.funnel},
                'select': ['ID', 'ASSIGNED_BY_ID']
            })
            uid_counter = Counter(d.get('ASSIGNED_BY_ID', '0') for d in deals)
            manager_ids = [uid for uid, cnt in uid_counter.most_common() if uid and uid != '0' and cnt >= 5][:10]
        else:
            manager_ids = resolve_manager_ids(args.compare_managers)

        results = {}
        for uid in manager_ids:
            name = get_user_name(uid)
            print(f'[stages] Computing for {name}...', file=sys.stderr)
            results[name] = compute_conversion(args.funnel, manager_id=uid,
                                                period_start=period_start, period_end=period_end)

        report = build_comparison_report(results, args.funnel, period_str=args.period)
    else:
        manager_id = resolve_manager_id(args.manager) if args.manager else None
        manager_name = get_user_name(manager_id) if manager_id else ''
        result = compute_conversion(args.funnel, manager_id=manager_id,
                                     period_start=period_start, period_end=period_end)
        report = build_single_report(result, manager_name=manager_name, period_str=args.period)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
