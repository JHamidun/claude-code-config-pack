"""
Классификатор причин отказов через парсинг timeline и комментариев.

Usage:
    python reasons_analyzer.py --funnel 43
    python reasons_analyzer.py --funnel 43 --period 2026-05
    python reasons_analyzer.py --funnel 4 --manager "Ушаков"
    python reasons_analyzer.py --funnel 43 --by-manager --format xlsx
"""
import sys
import os
import re
import argparse
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bx_client import bx, bx_all, resolve_manager_id, parse_period, get_user_name
from report_formatter import Report


# === Классификатор ===

CLASSIFIER_RULES = [
    ('Не удалось связаться', ['нд,', 'нд ', 'недоз', 'некорректн', 'нет контактов', 'не берет', 'не отвеча', 'не дозвон', 'номер не верн']),
    ('Тест/дубль/свой сотрудник', ['тест ', 'наш сотрудник', 'дубл', 'дбуль', 'yourfirstname', 'yourname']),
    ('Не целевой (SMB/физлицо)', ['1 человек', 'один человек', ' ип.', ' ип ', 'самозанят', 'физ.лиц', 'физлиц', 'для себя', 'маленькая компан', 'смотрит для себя']),
    ('Сменил/покинул компанию', ['уволил', 'уже не в', 'сменил работ', 'уволен']),
    ('Есть своё решение', ['свои разработ', 'внут.продук', 'внутр', 'своё реш', 'своя платформ', 'уже есть', 'используют свои']),
    ('Уже клиент Company', ['уже пользует', 'уже клиент', 'корп. библиотек', 'пользуется платформ']),
    ('Нет потребности', ['не интересно', 'не готов', 'не актуальн', 'не надо', 'не требует', 'пропала потреб']),
    ('Нет времени/приоритета', ['нет времени', 'занят', 'некогда', 'не сейчас', 'сброс после', 'сброс ', 'не хочет говор']),
    ('Гос/нет бюджета', ['госку', 'госзак', 'мид', 'нет бюджет', 'бюджет не ']),
    ('Выбрали другого', ['выбрали друг', 'конкурент', 'другой провайд']),
    ('Дорого', ['дорого', 'слишком доро']),
]


def classify(text: str) -> str:
    """Классифицировать причину отказа по тексту."""
    t = text.lower()
    for category, keywords in CLASSIFIER_RULES:
        if any(k in t for k in keywords):
            return category
    if len(text.strip()) > 30 and not text.strip().startswith('['):
        return 'Прочее (есть коммент)'
    return 'Нет причины (только метаданные бота)'


def clean_html(text: str) -> str:
    """Убрать HTML и BBcode."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[/?[a-z]+[^\]]*\]', '', text)
    return text.strip()


def analyze_reasons(funnel_id, period_start=None, period_end=None, manager_id=None, sample_size=None):
    """Проанализировать причины отказов в воронке."""
    filt = {'CATEGORY_ID': funnel_id, 'STAGE_ID': f'C{funnel_id}:LOSE' if funnel_id > 0 else 'LOSE'}
    if period_start:
        filt['>=DATE_MODIFY'] = period_start
    if period_end:
        filt['<=DATE_MODIFY'] = period_end
    if manager_id:
        filt['ASSIGNED_BY_ID'] = manager_id

    print(f'[reasons] Loading LOSE deals...', file=sys.stderr)
    lose_deals = bx_all('crm.deal.list', {
        'filter': filt,
        'select': ['ID', 'TITLE', 'ASSIGNED_BY_ID', 'COMMENTS', 'UF_REASON_FOR_REFUSAL', 'DATE_MODIFY']
    })
    print(f'[reasons] Found {len(lose_deals)} LOSE deals', file=sys.stderr)

    if sample_size and len(lose_deals) > sample_size:
        lose_deals = lose_deals[:sample_size]

    # Check UF field fill rate
    uf_filled = sum(1 for d in lose_deals if d.get('UF_REASON_FOR_REFUSAL'))

    # Process each deal
    by_manager = defaultdict(Counter)
    total = Counter()
    sample_comments = []

    print(f'[reasons] Processing {len(lose_deals)} deals...', file=sys.stderr)
    for i, d in enumerate(lose_deals):
        # Fetch timeline
        tc = bx('crm.timeline.comment.list', {
            'filter': {'ENTITY_ID': d['ID'], 'ENTITY_TYPE': 'deal'}
        })
        comments = tc.get('result', [])
        all_text = ' | '.join(str(c.get('COMMENT', '')) for c in comments)
        if d.get('COMMENTS'):
            all_text += ' | ' + str(d['COMMENTS'])
        clean = clean_html(all_text)

        category = classify(clean)
        mgr_name = get_user_name(d.get('ASSIGNED_BY_ID', '0'))
        by_manager[mgr_name][category] += 1
        total[category] += 1

        if category not in ('Нет причины (только метаданные бота)',) and len(sample_comments) < 30:
            sample_comments.append({
                'id': d['ID'],
                'title': d.get('TITLE', '')[:60],
                'manager': mgr_name,
                'category': category,
                'text': clean[:200],
            })

        if (i + 1) % 40 == 0:
            print(f'[reasons] {i + 1}/{len(lose_deals)}', file=sys.stderr)
        time.sleep(0.15)

    return {
        'total_lose': len(lose_deals),
        'uf_filled': uf_filled,
        'categories': dict(total),
        'by_manager': {k: dict(v) for k, v in by_manager.items()},
        'sample_comments': sample_comments,
    }


def build_report(result, funnel_id, period_str=''):
    """Собрать отчёт по причинам отказов."""
    from manager_report import CATEGORY_NAMES
    funnel_name = CATEGORY_NAMES.get(str(funnel_id), f'ID {funnel_id}')

    r = Report(
        title=f'Причины отказов — {funnel_name} (воронка {funnel_id})',
        period=period_str or 'вся история',
    )

    r.section('Ключевые цифры')
    r.kv('Всего сделок в LOSE', result['total_lose'])
    r.kv('Заполнено поле "Причина отказа"',
         f'{result["uf_filled"]} из {result["total_lose"]}',
         comment=f'{round(result["uf_filled"] / max(result["total_lose"], 1) * 100)}%',
         highlight='red' if result['uf_filled'] < result['total_lose'] * 0.1 else None)
    if result['uf_filled'] < result['total_lose'] * 0.1:
        r.paragraph('Поле UF_REASON_FOR_REFUSAL практически не заполняется — классификация через парсинг timeline.', style='warning')

    r.section('Структура причин (классификация парсингом)')
    rows = []
    total = result['total_lose']
    for cat, cnt in sorted(result['categories'].items(), key=lambda x: -x[1]):
        pct = cnt / total * 100 if total else 0
        rows.append([cat, cnt, f'{pct:.1f}%'])
    r.table(['Категория', 'Кол-во', '% от LOSE'], rows)

    r.section('По менеджерам (топ-3 причины)')
    rows = []
    for mgr, counter in sorted(result['by_manager'].items(), key=lambda x: -sum(x[1].values())):
        mgr_total = sum(counter.values())
        top3 = sorted(counter.items(), key=lambda x: -x[1])[:3]
        top_str = [f'{c} ({n})' for c, n in top3]
        while len(top_str) < 3:
            top_str.append('—')
        rows.append([mgr, mgr_total] + top_str)
    r.table(['Менеджер', 'Отказов', 'Топ-1', 'Топ-2', 'Топ-3'], rows)

    # Sample comments
    if result['sample_comments']:
        r.section('Примеры содержательных комментариев (первые 20)')
        rows = [[c['manager'], c['category'], c['text']] for c in result['sample_comments'][:20]]
        r.table(['Менеджер', 'Категория', 'Комментарий'], rows)

    # Recs
    recs = []
    if result['uf_filled'] < result['total_lose'] * 0.1:
        recs.append('СРОЧНО — робот на обязательное заполнение UF_REASON_FOR_REFUSAL при переходе в LOSE.')
    no_reason = result['categories'].get('Нет причины (только метаданные бота)', 0)
    if no_reason > result['total_lose'] * 0.5:
        recs.append(f'{no_reason} сделок ({round(no_reason / result["total_lose"] * 100)}%) закрыты без пояснения — обучить менеджеров писать причину.')
    if result['categories'].get('Не целевой (SMB/физлицо)', 0) > 10:
        recs.append('SMB/физлица массово попадают в воронку — фильтр на уровне регистрации/лид-формы.')
    if result['categories'].get('Есть своё решение', 0) > 3:
        recs.append('Собрать конкурентный разбор по клиентам с «есть своё решение».')
    if result['categories'].get('Тест/дубль/свой сотрудник', 0) > 5:
        recs.append('Запретить создание тестовых сделок в prod и наладить дедуп.')

    if recs:
        r.section('Рекомендации')
        r.bullet(recs)

    return r


def main():
    ap = argparse.ArgumentParser(description='Анализ причин отказов')
    ap.add_argument('--funnel', type=int, required=True, help='ID воронки')
    ap.add_argument('--period', default='all')
    ap.add_argument('--manager', default=None, help='ФИО или ID менеджера (опц.)')
    ap.add_argument('--sample', type=int, default=None, help='Ограничить размер выборки (для скорости)')
    ap.add_argument('--format', default='text', choices=['text', 'md', 'xlsx', 'docx', 'json', 'csv'])
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    period_start, period_end = parse_period(args.period)
    manager_id = resolve_manager_id(args.manager) if args.manager else None

    result = analyze_reasons(args.funnel, period_start, period_end, manager_id, sample_size=args.sample)
    report = build_report(result, args.funnel, period_str=args.period)

    output = report.output(format=args.format, path=args.out)
    if args.format in ('text', 'md', 'json'):
        print(output)
    else:
        print(f'Сохранено: {output}', file=sys.stderr)


if __name__ == '__main__':
    main()
