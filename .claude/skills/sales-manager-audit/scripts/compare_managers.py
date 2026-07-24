"""
Side-by-side сравнение 2-N менеджеров за один период.

Usage:
    python compare_managers.py --managers "Ушаков,Захаров" --period 2026-04-07:2026-05-13
    python compare_managers.py --managers 2813,3956,3910 --period 2026-Q2
    python compare_managers.py --managers "Захаров,Ушаков" --period last-30d --format xlsx
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import resolve_manager_ids, parse_period, get_user_name
from manager_report import collect_manager_data, analyze
from report_formatter import Report


def compare(managers_ids, period_start=None, period_end=None):
    """Собрать сравнительную аналитику."""
    results = {}
    for uid in managers_ids:
        name = get_user_name(uid)
        print(f'[compare] Loading {name}...', file=sys.stderr)
        data = collect_manager_data(uid, period_start, period_end)
        an = analyze(data, period_start, period_end)
        results[uid] = {'name': name, 'analytics': an}
    return results


def build_comparison_report(results, period_str=''):
    """Собрать Report сравнения."""
    r = Report(
        title=f'Сравнение менеджеров',
        period=period_str or 'вся история',
    )

    names = [results[uid]['name'] for uid in results]
    r.paragraph('Сравниваем: ' + ' · '.join(names))

    # Volume
    r.section('Объём работы')
    rows = []
    for uid in results:
        an = results[uid]['analytics']
        rows.append([
            results[uid]['name'],
            an.get('days_worked', '—'),
            an['calls_active_days'],
            an['total_deals'],
            round(an['total_deals'] / max(an.get('days_worked', 1), 1), 1),
            an['calls_total'],
            round(an['calls_total'] / max(an['calls_active_days'], 1)),
            f'{an["calls_total_dur_sec"] // 60}м',
        ])
    r.table(
        ['Менеджер', 'Дней', 'Актив.дней', 'Сделок', 'Сделок/день', 'Звонков', 'Звонков/день', 'Мин.разг.'],
        rows,
    )

    # Quality of calls
    r.section('Качество звонков')
    rows = []
    for uid in results:
        an = results[uid]['analytics']
        rows.append([
            results[uid]['name'],
            f'{an["calls_answer_rate"]:.1f}%',
            f'{an["calls_avg_dur"]:.0f}с',
            f'{an["calls_median_dur"]}с',
            f'{an["calls_max_dur"] // 60}м',
            an['calls_unique_phones'],
        ])
    r.table(['Менеджер', 'Дозвон', 'Средн', 'Медиана', 'Макс', 'Уник.номеров'], rows)

    # Money
    r.section('Результат (деньги)')
    rows = []
    for uid in results:
        an = results[uid]['analytics']
        lose_rate = an['lose_count'] / max(an['total_deals'], 1) * 100
        rows.append([
            results[uid]['name'],
            an['won_count'],
            f'{an["won_sum"]:,.0f} ₽',
            f'{an["avg_check"]:,.0f} ₽' if an['won_count'] else '—',
            an['lose_count'],
            f'{lose_rate:.0f}%',
            an['active_count'],
        ])
    r.table(['Менеджер', 'WON', 'Выручка', 'Ср.чек', 'LOSE', '%LOSE', 'Актив.'], rows)

    # Funnels breakdown
    all_cats = set()
    for uid in results:
        all_cats.update(results[uid]['analytics']['funnels'].keys())

    for cat_id in sorted(all_cats):
        from manager_report import CATEGORY_NAMES
        cat_name = CATEGORY_NAMES.get(str(cat_id), f'ID:{cat_id}')
        rows = []
        for uid in results:
            an = results[uid]['analytics']
            f = an['funnels'].get(cat_id, {'total': 0, 'won': 0, 'lose': 0, 'active': 0, 'won_sum': 0, 'lose_rate': 0})
            rows.append([
                results[uid]['name'],
                f['total'],
                f['won'],
                f'{f["won_sum"]:,.0f}' if f['won_sum'] else '—',
                f['lose'],
                f['active'],
                f'{f["lose_rate"]:.0f}%',
            ])
        r.table(['Менеджер', 'Всего', 'WON', 'Выручка', 'LOSE', 'Актив.', '%LOSE'],
                rows,
                name=f'Воронка: {cat_name} (ID {cat_id})')

    # TODO
    r.section('TODO дисциплина')
    rows = []
    for uid in results:
        an = results[uid]['analytics']
        rows.append([
            results[uid]['name'],
            an['todos_total'],
            an['todos_done'],
            f'{an["todos_done_rate"]:.0f}%',
            an['todos_pending'],
            an['todos_overdue'],
            f'{round(an["todos_overdue"] / max(an["todos_pending"], 1) * 100)}%',
        ])
    r.table(
        ['Менеджер', 'Всего', 'Готово', '%готово', 'Ожид.', 'Просроч.', '%просроч.'],
        rows,
    )

    # Automated conclusions
    r.section('Выводы')
    _add_comparison_conclusions(r, results)

    return r


def _add_comparison_conclusions(r, results):
    """Автоматические выводы по сравнению."""
    if len(results) < 2:
        return

    # Sort by different metrics
    by_uid = list(results.items())
    by_won = sorted(by_uid, key=lambda x: -x[1]['analytics']['won_count'])
    by_won_sum = sorted(by_uid, key=lambda x: -x[1]['analytics']['won_sum'])
    by_calls = sorted(by_uid, key=lambda x: -x[1]['analytics']['calls_total'])
    by_answer = sorted(by_uid, key=lambda x: -x[1]['analytics']['calls_answer_rate'])
    by_todo = sorted(by_uid, key=lambda x: -x[1]['analytics']['todos_done_rate'])
    by_lose_rate = sorted(by_uid, key=lambda x: x[1]['analytics']['lose_count'] / max(x[1]['analytics']['total_deals'], 1))

    def leader(sorted_list, metric_fn, format_fn):
        top = sorted_list[0]
        return f'{top[1]["name"]} ({format_fn(metric_fn(top[1]["analytics"]))})'

    r.bullet([
        f'По WON лидирует: {leader(by_won, lambda a: a["won_count"], lambda x: f"{x} побед")}',
        f'По выручке лидирует: {leader(by_won_sum, lambda a: a["won_sum"], lambda x: f"{x:,.0f} ₽")}',
        f'По объёму звонков лидирует: {leader(by_calls, lambda a: a["calls_total"], lambda x: f"{x} звонков")}',
        f'По дозваниваемости лидирует: {leader(by_answer, lambda a: a["calls_answer_rate"], lambda x: f"{x:.1f}%")}',
        f'По TODO дисциплине лидирует: {leader(by_todo, lambda a: a["todos_done_rate"], lambda x: f"{x:.0f}% выполнено")}',
        f'По низкой доле LOSE: {leader(by_lose_rate, lambda a: a["lose_count"] / max(a["total_deals"], 1), lambda x: f"{x * 100:.0f}%")}',
    ])

    # Role recommendations
    r.section('Ролевые рекомендации')
    for uid in results:
        an = results[uid]['analytics']
        role = classify_role(an)
        r.kv(results[uid]['name'], role['label'], comment=role['reason'])


def classify_role(an) -> dict:
    """Классифицировать менеджера по роли (SDR / Closer / Account manager / Callcenter)."""
    won = an['won_count']
    calls = an['calls_total']
    avg_dur = an['calls_avg_dur']
    active_days = max(an['calls_active_days'], 1)
    calls_per_day = calls / active_days
    lose_rate = an['lose_count'] / max(an['total_deals'], 1)

    # Closer: есть WON, длинные разговоры, мало звонков
    if won >= 2 and avg_dur >= 100:
        return {'label': 'Closer / Account manager',
                'reason': f'{won} WON, средний разговор {avg_dur:.0f}с — ведёт до закрытия'}
    # SDR / callcenter: много звонков, 0 WON
    if calls_per_day > 30 and won == 0:
        return {'label': 'SDR / Callcenter',
                'reason': f'{calls_per_day:.0f} звонков/день, 0 WON — работает на квалификации'}
    # Chunker: массовая чистка воронки
    if lose_rate > 0.6:
        return {'label': 'Воронка-чистильщик',
                'reason': f'{lose_rate * 100:.0f}% LOSE — массово квалифицирует унаследованную базу'}
    # Balanced
    if won > 0 and calls_per_day > 15:
        return {'label': 'Hunter (сбалансированный)',
                'reason': f'{won} WON и {calls_per_day:.0f} звонков/день'}
    return {'label': 'Junior / развивается',
            'reason': f'Пока без явной роли ({won} WON, {calls_per_day:.0f} звонков/день)'}


def main():
    ap = argparse.ArgumentParser(description='Сравнение менеджеров продаж')
    ap.add_argument('--managers', required=True, help='Список через запятую: "Ушаков,Захаров" или "2813,3956"')
    ap.add_argument('--period', default='all')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    manager_ids = resolve_manager_ids(args.managers)
    period_start, period_end = parse_period(args.period)
    period_str = args.period if args.period != 'all' else 'вся история'

    results = compare(manager_ids, period_start, period_end)
    report = build_comparison_report(results, period_str=period_str)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
