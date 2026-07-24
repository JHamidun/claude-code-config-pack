"""
Полная аналитика одного менеджера.

Usage:
    python manager_report.py --manager "Захаров" --period 2026-04-07:2026-05-13
    python manager_report.py --manager 3956 --period all --format xlsx --out ~/Downloads/z.xlsx
    python manager_report.py --manager "Ушаков" --period 2026-Q2 --format md

Period formats:
    2026-04-07:2026-05-13  -- explicit range
    2026-Q2                 -- quarter
    2026-05                 -- month
    last-30d                -- last 30 days
    all                     -- all history
"""
import sys
import os
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import (
    bx, bx_all, safe_float, parse_dt,
    resolve_manager_id, parse_period, get_user_name, get_stage_names
)
from report_formatter import Report


CATEGORY_NAMES = {
    '0': 'Default', '3': 'Голосовой бот EdTech', '4': 'GPT B2B', '5': 'АПРО',
    '6': 'GPT B2C', '8': 'Аккаунтинг АПРО', '9': 'Казахстан АПРО',
    '19': 'Библиотека', '21': 'Продления', '40': 'EdTech продажи',
    '42': 'Голосовой бот GPT', '43': 'TransformAI 2026',
}


def collect_manager_data(manager_id, period_start=None, period_end=None):
    """Собрать все данные по менеджеру за период."""
    data = {'manager_id': manager_id}

    # Profile
    u = bx('user.get', {'ID': manager_id})
    user = u.get('result', [{}])[0]
    data['profile'] = {
        'name': f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
        'position': user.get('WORK_POSITION', ''),
        'email': user.get('EMAIL', ''),
        'department': user.get('UF_DEPARTMENT', []),
        'active': user.get('ACTIVE', ''),
        'registered': user.get('DATE_REGISTER', ''),
    }

    # Deal filter
    filt = {'ASSIGNED_BY_ID': manager_id}
    if period_start:
        filt['>=DATE_MODIFY'] = period_start
    if period_end:
        filt['<=DATE_MODIFY'] = period_end

    print(f'[collect] Loading deals for {data["profile"]["name"]}...', file=sys.stderr)
    deals = bx_all('crm.deal.list', {
        'filter': filt,
        'select': ['ID', 'TITLE', 'CATEGORY_ID', 'STAGE_ID', 'OPPORTUNITY',
                   'DATE_CREATE', 'DATE_MODIFY', 'CLOSEDATE', 'CONTACT_ID',
                   'COMPANY_ID', 'SOURCE_ID']
    })
    data['deals'] = deals
    print(f'[collect] Deals: {len(deals)}', file=sys.stderr)

    # Calls
    call_filt = {'PORTAL_USER_ID': int(manager_id)}
    if period_start:
        call_filt['>=CALL_START_DATE'] = period_start
    if period_end:
        call_filt['<=CALL_START_DATE'] = period_end

    print(f'[collect] Loading calls...', file=sys.stderr)
    calls = bx_all('voximplant.statistic.get', {
        'FILTER': call_filt,
        'SORT': 'CALL_START_DATE', 'ORDER': 'DESC'
    })
    data['calls'] = calls
    print(f'[collect] Calls: {len(calls)}', file=sys.stderr)

    # TODOs
    print(f'[collect] Loading TODOs...', file=sys.stderr)
    todo_filt = {'RESPONSIBLE_ID': manager_id, 'PROVIDER_ID': 'CRM_TODO'}
    todos = bx_all('crm.activity.list', {
        'filter': todo_filt,
        'select': ['ID', 'COMPLETED', 'DEADLINE', 'END_TIME', 'CREATED', 'SUBJECT']
    })
    # Filter to period by CREATED date
    if period_start or period_end:
        from datetime import datetime
        ps = parse_dt(period_start) if period_start else None
        pe = parse_dt(period_end) if period_end else None
        filtered = []
        for t in todos:
            dt = parse_dt(t.get('CREATED', '')) or parse_dt(t.get('END_TIME', ''))
            if not dt:
                continue
            if ps and dt < ps:
                continue
            if pe and dt > pe:
                continue
            filtered.append(t)
        todos = filtered
    data['todos'] = todos
    print(f'[collect] TODOs: {len(todos)}', file=sys.stderr)

    return data


def analyze(data, period_start=None, period_end=None):
    """Провести аналитику."""
    from datetime import datetime

    deals = data['deals']
    calls = data['calls']
    todos = data['todos']

    an = {'profile': data['profile']}

    # === Deals ===
    an['total_deals'] = len(deals)
    won = [d for d in deals if 'WON' in d.get('STAGE_ID', '')]
    lose = [d for d in deals if 'LOSE' in d.get('STAGE_ID', '')]
    an['won_count'] = len(won)
    an['lose_count'] = len(lose)
    an['active_count'] = len(deals) - len(won) - len(lose)
    an['won_sum'] = sum(safe_float(d.get('OPPORTUNITY')) for d in won)
    an['won_deals'] = [{
        'id': w['ID'],
        'title': w.get('TITLE', '')[:80],
        'cat': w.get('CATEGORY_ID'),
        'amount': safe_float(w.get('OPPORTUNITY')),
    } for w in won]
    an['avg_check'] = an['won_sum'] / len(won) if won else 0

    # Cycle time
    cycles = []
    for w in won:
        c = parse_dt(w.get('DATE_CREATE'))
        cl = parse_dt(w.get('CLOSEDATE'))
        if c and cl:
            days = (cl - c).days
            if 0 <= days < 3650:
                cycles.append(days)
    an['avg_cycle_days'] = sum(cycles) / len(cycles) if cycles else 0
    an['median_cycle_days'] = sorted(cycles)[len(cycles) // 2] if cycles else 0

    # By category
    by_cat = Counter(d.get('CATEGORY_ID', '?') for d in deals)
    an['by_cat'] = dict(by_cat)

    # By stage
    an['by_stage'] = dict(Counter(d.get('STAGE_ID', '?') for d in deals))

    # Per funnel breakdown
    funnels = {}
    for cat_id in by_cat:
        cat_deals = [d for d in deals if d.get('CATEGORY_ID') == cat_id]
        cat_won = [d for d in cat_deals if 'WON' in d.get('STAGE_ID', '')]
        cat_lose = [d for d in cat_deals if 'LOSE' in d.get('STAGE_ID', '')]
        funnels[cat_id] = {
            'name': CATEGORY_NAMES.get(str(cat_id), f'ID:{cat_id}'),
            'total': len(cat_deals),
            'won': len(cat_won),
            'won_sum': sum(safe_float(d.get('OPPORTUNITY')) for d in cat_won),
            'lose': len(cat_lose),
            'active': len(cat_deals) - len(cat_won) - len(cat_lose),
            'lose_rate': len(cat_lose) / len(cat_deals) * 100 if cat_deals else 0,
        }
    an['funnels'] = funnels

    # Linkage
    an['no_company'] = sum(1 for d in deals if not d.get('COMPANY_ID') or d['COMPANY_ID'] == '0')
    an['no_contact'] = sum(1 for d in deals if not d.get('CONTACT_ID') or d['CONTACT_ID'] == '0')

    # === Calls ===
    an['calls_total'] = len(calls)
    answered = 0
    total_dur = 0
    durations = []
    by_day = defaultdict(lambda: {'total': 0, 'answered': 0, 'dur': 0})
    by_hour = Counter()
    by_dow = Counter()
    phones = Counter()
    direction = Counter()

    for c in calls:
        d = c.get('CALL_START_DATE', '')[:10]
        h = c.get('CALL_START_DATE', '')[11:13]
        dur = int(c.get('CALL_DURATION', 0) or 0)
        ct = str(c.get('CALL_TYPE', '?'))
        phone = c.get('PHONE_NUMBER', '')
        direction[ct] += 1
        if d:
            by_day[d]['total'] += 1
            by_hour[h] += 1
            try:
                dt = datetime.fromisoformat(c['CALL_START_DATE'].replace('Z', '+00:00').split('+')[0])
                by_dow[dt.weekday()] += 1
            except (ValueError, AttributeError, KeyError):
                pass
        if phone:
            phones[phone] += 1
        if dur > 0:
            answered += 1
            total_dur += dur
            durations.append(dur)
            if d:
                by_day[d]['answered'] += 1
                by_day[d]['dur'] += dur

    an['calls_answered'] = answered
    an['calls_answer_rate'] = answered / len(calls) * 100 if calls else 0
    an['calls_total_dur_sec'] = total_dur
    an['calls_active_days'] = len(by_day)
    an['calls_unique_phones'] = len(phones)
    an['calls_direction'] = dict(direction)
    an['calls_by_day'] = {k: dict(v) for k, v in sorted(by_day.items())}
    an['calls_by_hour'] = dict(by_hour)
    an['calls_by_dow'] = {str(k): v for k, v in by_dow.items()}
    if durations:
        durations.sort()
        an['calls_avg_dur'] = sum(durations) / len(durations)
        an['calls_median_dur'] = durations[len(durations) // 2]
        an['calls_max_dur'] = max(durations)
    else:
        an['calls_avg_dur'] = 0
        an['calls_median_dur'] = 0
        an['calls_max_dur'] = 0

    # === TODOs ===
    an['todos_total'] = len(todos)
    an['todos_done'] = sum(1 for t in todos if t.get('COMPLETED') == 'Y')
    an['todos_pending'] = len(todos) - an['todos_done']
    an['todos_done_rate'] = an['todos_done'] / len(todos) * 100 if todos else 0
    # Overdue
    now = datetime.now()
    overdue = 0
    future = 0
    for t in todos:
        if t.get('COMPLETED') != 'N':
            continue
        dl = t.get('DEADLINE') or t.get('END_TIME', '')
        dt = parse_dt(dl)
        if dt:
            if dt < now:
                overdue += 1
            else:
                future += 1
    an['todos_overdue'] = overdue
    an['todos_future'] = future

    # === Days worked ===
    if period_start and period_end:
        ps = parse_dt(period_start)
        pe = parse_dt(period_end)
        an['days_worked'] = (pe - ps).days if ps and pe else 0
    else:
        # From registration to today
        reg = parse_dt(data['profile'].get('registered', ''))
        if reg:
            an['days_worked'] = (datetime.now() - reg).days
        else:
            an['days_worked'] = 0

    return an


def build_report(an, period_str='', manager_name=''):
    """Собрать Report из analytics dict."""
    r = Report(
        title=f'{manager_name or an["profile"]["name"]} — аналитика продаж',
        period=period_str or 'вся история',
        subtitle=an['profile'].get('position', ''),
    )

    # Key numbers
    r.section('Ключевые цифры')
    r.kv('Дней в периоде', an.get('days_worked', 0))
    r.kv('Активных дней (звонки)', an['calls_active_days'],
         comment=f'{round(an["calls_active_days"] / max(an.get("days_worked", 1), 1) * 100)}% от календарных' if an.get('days_worked') else '')
    r.kv('Всего сделок', an['total_deals'])
    r.kv('WON', an['won_count'],
         comment=f'{an["won_sum"]:,.0f} RUB, средний чек {an["avg_check"]:,.0f}' if an['won_count'] else '0 побед',
         highlight='red' if an['won_count'] == 0 else 'green')
    r.kv('LOSE', an['lose_count'],
         comment=f'{round(an["lose_count"] / max(an["total_deals"], 1) * 100)}% всех сделок',
         highlight='yellow' if an['lose_count'] > an['total_deals'] * 0.5 else None)
    r.kv('Активных сделок', an['active_count'])
    if an['avg_cycle_days']:
        r.kv('Средний цикл сделки', f'{an["avg_cycle_days"]:.0f}d', comment=f'медиана {an["median_cycle_days"]}d')

    # Won deals list
    if an['won_deals']:
        r.section('Выигранные сделки')
        rows = [[w['title'], f'{w["amount"]:,.0f}'] for w in sorted(an['won_deals'], key=lambda x: -x['amount'])]
        rows.append(['ИТОГО', f'{an["won_sum"]:,.0f}'])
        r.table(['Сделка', 'Сумма (RUB)'], rows)

    # Funnels
    r.section('Разбивка по воронкам')
    rows = []
    for cat_id, f in sorted(an['funnels'].items(), key=lambda x: -x[1]['total']):
        rows.append([
            f['name'],
            f['total'],
            f['won'],
            f'{f["won_sum"]:,.0f}' if f['won_sum'] else '0',
            f['lose'],
            f['active'],
            f'{f["lose_rate"]:.0f}%',
        ])
    r.table(['Воронка', 'Всего', 'WON', 'Сумма', 'LOSE', 'Активных', '%LOSE'], rows)

    # Calls
    r.section('Звонки')
    r.kv('Всего звонков', an['calls_total'])
    r.kv('Дозвон', an['calls_answered'],
         comment=f'{an["calls_answer_rate"]:.1f}% дозваниваемость')
    r.kv('Недозвон', an['calls_total'] - an['calls_answered'])
    r.kv('Общее время', f'{an["calls_total_dur_sec"] // 60}м ({an["calls_total_dur_sec"] // 3600}ч)')
    r.kv('Средняя длительность', f'{an["calls_avg_dur"]:.0f}с', comment=f'медиана {an["calls_median_dur"]}с')
    r.kv('Уникальных номеров', an['calls_unique_phones'])
    if an['calls_active_days']:
        r.kv('Среднее звонков/активный день', round(an['calls_total'] / an['calls_active_days']))
    direct = an['calls_direction']
    r.kv('Исход./входящ.', f'{direct.get("1", 0)} / {direct.get("2", 0)}')

    # By day
    if an['calls_by_day']:
        rows = []
        for day, s in list(an['calls_by_day'].items())[:30]:  # limit for readability
            rows.append([day, s['total'], s['answered'], f'{s["dur"] // 60}м'])
        r.table(['Дата', 'Всего', 'Дозвон', 'Время'], rows, name='Активность по дням')

    # By hour
    if an['calls_by_hour']:
        rows = [[f'{h}:00', c] for h, c in sorted(an['calls_by_hour'].items())]
        r.table(['Час', 'Звонков'], rows, name='По часам')

    # By DOW
    if an['calls_by_dow']:
        dow_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        rows = [[dow_names[int(d)], c] for d, c in sorted(an['calls_by_dow'].items(), key=lambda x: int(x[0]))]
        r.table(['День', 'Звонков'], rows, name='По дням недели')

    # TODOs
    r.section('TODO дисциплина')
    r.kv('Всего задач', an['todos_total'])
    r.kv('Выполнено', an['todos_done'], comment=f'{an["todos_done_rate"]:.0f}%')
    r.kv('Ожидает', an['todos_pending'])
    r.kv('Просрочено', an['todos_overdue'],
         comment=f'{round(an["todos_overdue"] / max(an["todos_pending"], 1) * 100)}% от pending',
         highlight='red' if an['todos_overdue'] > an['todos_pending'] * 0.5 else None)
    r.kv('С будущим дедлайном', an['todos_future'])

    # Data quality
    r.section('Качество данных в CRM')
    r.kv('Без компании', f'{round(an["no_company"] / max(an["total_deals"], 1) * 100)}%',
         comment='Критично для B2B' if an['no_company'] > an['total_deals'] * 0.5 else '')
    r.kv('Без контакта', f'{round(an["no_contact"] / max(an["total_deals"], 1) * 100)}%')

    # Auto-conclusions
    strong = []
    weak = []
    questions = []
    recs = []

    if an['calls_answer_rate'] >= 75:
        strong.append(f'Высокая дозваниваемость {an["calls_answer_rate"]:.1f}%')
    if an['calls_median_dur'] >= 50:
        strong.append(f'Содержательные разговоры (медиана {an["calls_median_dur"]}с)')
    if an['won_count'] > 0:
        strong.append(f'{an["won_count"]} WON на {an["won_sum"]:,.0f} RUB (ср. чек {an["avg_check"]:,.0f})')
    if an['todos_done_rate'] >= 70:
        strong.append(f'TODO дисциплина {an["todos_done_rate"]:.0f}% выполнено')

    if an['won_count'] == 0 and an['total_deals'] > 20:
        weak.append(f'0 побед при {an["total_deals"]} сделках — не дожимает в WON')
    if an['no_company'] > an['total_deals'] * 0.5:
        weak.append(f'{round(an["no_company"] / an["total_deals"] * 100)}% сделок без компании — невозможен account-based подход')
    if an['todos_overdue'] > an['todos_pending'] * 0.5:
        weak.append(f'{an["todos_overdue"]} просроченных TODO ({round(an["todos_overdue"] / max(an["todos_pending"], 1) * 100)}% от pending)')
    if an['calls_answer_rate'] < 60 and an['calls_total'] > 50:
        weak.append(f'Низкая дозваниваемость ({an["calls_answer_rate"]:.1f}%)')

    if an['won_count'] == 0:
        questions.append('Что мешает закрывать в WON — процесс, скрипт, продукт?')
    if an['active_count'] > 20:
        questions.append(f'Что с {an["active_count"]} активными сделками — двигаются или зависли?')
    if an['todos_overdue'] > 50:
        questions.append(f'Почему {an["todos_overdue"]} TODO просрочено — не успевает или забывает?')

    if an['no_company'] > an['total_deals'] * 0.5:
        recs.append('Привязать активные сделки к компаниям — обязательно для B2B')
    if an['todos_overdue'] > 30:
        recs.append(f'Массовая ревизия {an["todos_overdue"]} просроченных TODO')
    if an['won_count'] == 0 and an['active_count'] > 10:
        recs.append(f'1-на-1 разбор {an["active_count"]} активных сделок — что мешает движению')

    if strong or weak or questions or recs:
        r.conclusion(strong=strong, weak=weak, questions=questions, recs=recs)

    return r


def main():
    ap = argparse.ArgumentParser(description='Аналитика менеджера продаж')
    ap.add_argument('--manager', required=True, help='ФИО или ID менеджера')
    ap.add_argument('--period', default='all', help='Период: YYYY-MM-DD:YYYY-MM-DD | YYYY-QN | YYYY-MM | last-30d | all')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None, help='Путь файла (для xlsx/docx/csv/json)')
    args = ap.parse_args()

    manager_id = resolve_manager_id(args.manager)
    period_start, period_end = parse_period(args.period)
    period_str = args.period if args.period != 'all' else 'вся история'

    print(f'[main] Manager: {get_user_name(manager_id)} (ID {manager_id})', file=sys.stderr)
    print(f'[main] Period: {period_str} ({period_start} - {period_end})', file=sys.stderr)

    data = collect_manager_data(manager_id, period_start, period_end)
    an = analyze(data, period_start, period_end)
    report = build_report(an, period_str=period_str)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
