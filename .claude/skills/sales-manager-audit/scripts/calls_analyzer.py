"""
Аналитика звонков — по менеджеру или команде.

Usage:
    python calls_analyzer.py --manager "Захаров" --period 2026-05
    python calls_analyzer.py --team --period last-30d
    python calls_analyzer.py --manager 3956 --funnel 43
"""
import sys
import os
import argparse
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, resolve_manager_id, parse_period, get_user_name
from report_formatter import Report


def analyze_calls(manager_id=None, funnel_id=None, period_start=None, period_end=None):
    """Собрать статистику звонков."""
    if funnel_id and manager_id:
        # Calls linked to deals in specific funnel
        filt = {'CATEGORY_ID': funnel_id, 'ASSIGNED_BY_ID': manager_id}
        deals = bx_all('crm.deal.list', {'filter': filt, 'select': ['ID']})
        deal_ids = [int(d['ID']) for d in deals]
        calls = []
        for i in range(0, len(deal_ids), 30):
            chunk = deal_ids[i:i + 30]
            acts = bx_all('crm.activity.list', {
                'filter': {'RESPONSIBLE_ID': manager_id, 'OWNER_TYPE_ID': 2,
                           'OWNER_ID': chunk, 'PROVIDER_ID': 'VOXIMPLANT_CALL'},
                'select': ['ID', 'START_TIME', 'END_TIME']
            })
            # Convert activity format to call-like
            for a in acts:
                calls.append({
                    'CALL_START_DATE': a.get('START_TIME', ''),
                    'CALL_DURATION': _duration_from_activity(a),
                    'PHONE_NUMBER': '',  # Not available in activity
                    'CALL_TYPE': '1',
                    'CALL_FAILED_CODE': '',
                })
    else:
        # Direct voximplant calls
        call_filt = {}
        if manager_id:
            call_filt['PORTAL_USER_ID'] = int(manager_id)
        if period_start:
            call_filt['>=CALL_START_DATE'] = period_start
        if period_end:
            call_filt['<=CALL_START_DATE'] = period_end
        calls = bx_all('voximplant.statistic.get', {
            'FILTER': call_filt,
            'SORT': 'CALL_START_DATE', 'ORDER': 'DESC'
        })

    # Aggregate
    total = len(calls)
    answered = 0
    total_dur = 0
    durations = []
    by_day = defaultdict(lambda: {'total': 0, 'answered': 0, 'dur': 0})
    by_hour = Counter()
    by_dow = Counter()
    phones = Counter()
    direction = Counter()
    codes = Counter()

    for c in calls:
        d = c.get('CALL_START_DATE', '')[:10]
        h = c.get('CALL_START_DATE', '')[11:13]
        dur = int(c.get('CALL_DURATION', 0) or 0)
        ct = str(c.get('CALL_TYPE', '?'))
        code = c.get('CALL_FAILED_CODE', '')
        phone = c.get('PHONE_NUMBER', '')

        direction[ct] += 1
        codes[code] += 1

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

    result = {
        'total': total,
        'answered': answered,
        'answer_rate': answered / total * 100 if total else 0,
        'total_dur_sec': total_dur,
        'active_days': len(by_day),
        'unique_phones': len(phones),
        'direction': dict(direction),
        'codes': dict(codes),
        'by_day': {k: dict(v) for k, v in sorted(by_day.items())},
        'by_hour': dict(by_hour),
        'by_dow': {str(k): v for k, v in by_dow.items()},
        'phones_repeat': [{'phone': p, 'count': c} for p, c in phones.most_common(15)],
    }
    if durations:
        durations.sort()
        result['avg_dur'] = sum(durations) / len(durations)
        result['median_dur'] = durations[len(durations) // 2]
        result['max_dur'] = max(durations)
        # Duration buckets
        buckets = [(1, 10, '<10с'), (11, 30, '10-30с'), (31, 60, '30с-1м'), (61, 180, '1-3м'),
                   (181, 300, '3-5м'), (301, 600, '5-10м'), (601, 1800, '10-30м'), (1801, 99999, '>30м')]
        result['duration_buckets'] = {label: sum(1 for d in durations if lo <= d <= hi)
                                       for lo, hi, label in buckets}
    else:
        result['avg_dur'] = 0
        result['median_dur'] = 0
        result['max_dur'] = 0
        result['duration_buckets'] = {}

    return result


def _duration_from_activity(a):
    """Approximate call duration from activity START/END times."""
    st = a.get('START_TIME', '')
    et = a.get('END_TIME', '')
    if not st or not et or st == et:
        return 0
    try:
        s = datetime.fromisoformat(st.replace('Z', '+00:00').split('+')[0])
        e = datetime.fromisoformat(et.replace('Z', '+00:00').split('+')[0])
        return max(0, int((e - s).total_seconds()))
    except (ValueError, AttributeError):
        return 0


def build_report(result, manager_name='', funnel_id=None, period_str=''):
    from manager_report import CATEGORY_NAMES

    title = f'Аналитика звонков — {manager_name or "команда"}'
    if funnel_id:
        title += f' (воронка {CATEGORY_NAMES.get(str(funnel_id), funnel_id)})'

    r = Report(title=title, period=period_str or 'вся история')

    r.section('Общие цифры')
    r.kv('Всего звонков', result['total'])
    r.kv('Дозвон', result['answered'], comment=f'{result["answer_rate"]:.1f}% дозваниваемость',
         highlight='green' if result['answer_rate'] >= 75 else 'yellow' if result['answer_rate'] >= 50 else 'red')
    r.kv('Недозвон', result['total'] - result['answered'])
    r.kv('Общее время разговоров', f'{result["total_dur_sec"] // 60}м ({result["total_dur_sec"] // 3600}ч)')
    r.kv('Средняя длительность', f'{result["avg_dur"]:.0f}с', comment=f'медиана {result["median_dur"]}с')
    r.kv('Максимальный разговор', f'{result["max_dur"] // 60}м {result["max_dur"] % 60}с')
    r.kv('Уникальных номеров', result['unique_phones'])
    r.kv('Активных дней', result['active_days'])
    if result['active_days']:
        r.kv('Среднее звонков/день', round(result['total'] / result['active_days']))
    direct = result['direction']
    r.kv('Исход./входящ.', f'{direct.get("1", 0)} / {direct.get("2", 0)}')

    if result['by_day']:
        r.section('По дням')
        rows = [[day, s['total'], s['answered'], f'{s["dur"] // 60}м'] for day, s in result['by_day'].items()]
        r.table(['Дата', 'Всего', 'Дозвон', 'Время'], rows)

    if result['by_hour']:
        r.section('По часам')
        rows = [[f'{h}:00', c] for h, c in sorted(result['by_hour'].items())]
        r.table(['Час', 'Звонков'], rows)

    if result['by_dow']:
        r.section('По дням недели')
        dow_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        rows = [[dow_names[int(d)], c] for d, c in sorted(result['by_dow'].items(), key=lambda x: int(x[0]))]
        r.table(['День', 'Звонков'], rows)

    if result['duration_buckets']:
        r.section('Длительность разговоров')
        rows = [[label, c] for label, c in result['duration_buckets'].items() if c > 0]
        r.table(['Диапазон', 'Звонков'], rows)

    if result['phones_repeat']:
        r.section('Повторные звонки на один номер (топ-15)')
        rows = [[p['phone'], p['count']] for p in result['phones_repeat'] if p['count'] > 1]
        if rows:
            r.table(['Номер', 'Звонков'], rows)

    return r


def main():
    ap = argparse.ArgumentParser(description='Аналитика звонков')
    ap.add_argument('--manager', default=None)
    ap.add_argument('--funnel', type=int, default=None, help='Ограничить звонками по сделкам воронки')
    ap.add_argument('--team', action='store_true', help='Вся команда (без фильтра менеджера)')
    ap.add_argument('--period', default='all')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    period_start, period_end = parse_period(args.period)
    manager_id = None
    manager_name = ''
    if args.manager and not args.team:
        manager_id = resolve_manager_id(args.manager)
        manager_name = get_user_name(manager_id)

    result = analyze_calls(manager_id=manager_id, funnel_id=args.funnel,
                           period_start=period_start, period_end=period_end)
    report = build_report(result, manager_name=manager_name, funnel_id=args.funnel, period_str=args.period)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
