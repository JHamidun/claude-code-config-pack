# Quickstart — примеры вызовов

Все скрипты — в `~/.claude/skills/sales-manager-audit/scripts/`.

## Один менеджер

```bash
# Полная аналитика Захарова за всю историю (текст в консоль)
python manager_report.py --manager "Захаров"

# За конкретный период, Excel-файл
python manager_report.py --manager "Ушаков" --period 2026-04-07:2026-05-13 --format xlsx --out ~/Downloads/ush.xlsx

# По ID менеджера, за квартал
python manager_report.py --manager 3956 --period 2026-Q2

# За последние 30 дней в markdown
python manager_report.py --manager "Коробкин" --period last-30d --format md
```

## Сравнение менеджеров

```bash
# Два менеджера, текст
python compare_managers.py --managers "Ушаков,Захаров"

# Вся команда TransformAI, xlsx
python compare_managers.py --managers "2813,3956,3910,3643,3341" --period 2026-Q2 --format xlsx

# Markdown для Notion
python compare_managers.py --managers "Ушаков,Захаров,Коробкин" --format md
```

## Аудит воронки

```bash
# Здоровье TransformAI
python funnel_audit.py --funnel 43

# Все воронки сводкой
python funnel_audit.py --funnel all

# С мягким порогом протухания
python funnel_audit.py --funnel 4 --stale-days 60
```

## Причины отказов

```bash
# Все LOSE в GPT B2B
python reasons_analyzer.py --funnel 4

# По конкретному менеджеру
python reasons_analyzer.py --funnel 43 --manager "Захаров"

# За период, xlsx
python reasons_analyzer.py --funnel 5 --period 2026-05 --format xlsx

# С ограничением выборки (для скорости)
python reasons_analyzer.py --funnel 43 --sample 100
```

## Конверсия по стадиям

```bash
# Простая конверсия для одного менеджера
python conversion_stages.py --funnel 4 --manager "Ушаков"

# Сравнение конверсий у нескольких
python conversion_stages.py --funnel 43 --compare-managers "Ушаков,Захаров,Коробкин"

# Вся команда воронки
python conversion_stages.py --funnel 5 --team
```

## Звонки

```bash
# Звонки одного менеджера за период
python calls_analyzer.py --manager "Захаров" --period 2026-05

# Только звонки по сделкам конкретной воронки
python calls_analyzer.py --manager "Ушаков" --funnel 43

# Вся команда за месяц
python calls_analyzer.py --team --period 2026-05
```

## Pipeline прогноз

```bash
# По одной воронке
python pipeline_forecast.py --funnel 5

# По конкретному менеджеру
python pipeline_forecast.py --funnel 4 --manager "Ушаков"

# Топ-20 сделок по взвешенному прогнозу
python pipeline_forecast.py --top 20
```

## Поиск ЛПР

```bash
# ЛПР всех WON-клиентов B2B
python lpr_finder.py --funnel 4 --status WON

# По списку клиентов
python lpr_finder.py --clients "Газпром,ClientCorp3,Русал" --funnel 4

# Excel-файл
python lpr_finder.py --funnel 4 --status WON --format xlsx
```

## Форматы вывода (--format)

- `text` — моноширинный текст в консоль (для чата, копирования, email)
- `md` — markdown для Notion/wiki
- `xlsx` — Excel с форматированием
- `docx` — Word для формальных отчётов
- `json` — сырые данные для программной обработки
- `csv` — только таблицы, для последующего анализа

## Форматы периода (--period)

- `2026-04-07:2026-05-13` — явный диапазон
- `2026-Q2` — квартал
- `2026-05` — месяц
- `last-30d` — последние N дней
- `today` — сегодня
- `all` — вся история (по умолчанию)
