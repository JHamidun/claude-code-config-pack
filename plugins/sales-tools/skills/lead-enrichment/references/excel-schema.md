# Enriched workbook schema

Output of `scripts/build_enriched_xlsx.py`. Sheet order + columns below. Every data sheet:
`freeze_panes='A2'`, `auto_filter` on, header fill `1F3864`/white-bold, priority color via tier.

Tier colors: **S** green `C6EFCE` · **A** yellow `FFEB9C` · **B** grey `F2F2F2` (see `scoring.md`).

| # | Sheet | Columns |
|---|-------|---------|
| 1 | **Пересечения** | summary block: всего в списке, матчей, со сделками, холодняк, дата |
| 2 | **Готовый обзвон** | Приоритет, Компания, ИНН, ФИО контакта, Должность, Телефон, Email, LinkedIn, Менеджер, Продукты в работе, Последнее касание, Источник |
| 3 | **Активные сделки** | ИНН, Компания, ID сделки, Сделка, Продукт, Стадия, Сумма, Создана, Менеджер |
| 4 | **Продажи и провалы** | Результат (ПРОДАЖА/ПРОВАЛ), ИНН, Компания, Сделка, Продукт, Стадия, Сумма, Менеджер |
| 5 | **Холодняк (нет в базе)** | Компания, ИНН, ЮЛ, Выручка 2024, Телефон, Email, Сайт, Гендир, Сегмент |
| 6 | **Реанимация (N+ дней)** | ИНН, Компания, Дней с касания, Последнее касание, Продукты, Менеджер, Контакты |
| 7 | **LinkedIn ЛПР** | Компания, ИНН, В Bitrix?, ФИО, Должность, LinkedIn, Индустрия |
| 8 | **Глубокий рисёрч** | Tier, Компания, ИНН, Досье (Perplexity) — wrapped |
| 9 | **Касания — лента** | Дата, ИНН, Компания, Тип, Тема, Источник, Завершено? |

## Inputs

| Flag | File | Shape |
|------|------|-------|
| `--list` | list.json | `[{name, inn?, ul?, phone?, email?, site?, rev2024?, segment?}, ...]` |
| `--agg` | aggregated.json | output of `bitrix_aggregate.py` |
| `--firmographics` | firmographics.json (optional) | `{inn: {name_full, director, income, ...}}` |
| `--research` | research/results.json (optional) | `{inn: {tier, name, text}}` from `research_companies.py` |
| `--linkedin` | linkedin.json (optional) | `[{company, inn?, name, post, linkedin, industry}, ...]` |

## Stage classification

`stage_kind()` heuristic on stage NAME (Bitrix stage_ids vary per portal): name contains
`провал/fail/отказ` → lost · `успешн/won/оплач/выигр` → won · else active. Tune if a portal
uses other wording.

## Tiers

S = `touch_count > 0` (active Bitrix history) · A = cold (not matched), ranked by `rev2024` ·
B = in Bitrix, no touches.
