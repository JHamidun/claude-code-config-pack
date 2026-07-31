> [MERGED 2026-07-18] Бывший отдельный скилл `prospect-list-enrichment`, влит в `lead-enrichment` (Mode B, основной путь).
> Скрипты теперь живут в `~/.claude/skills/lead-enrichment/scripts/list_pipeline/` (упоминаемый ниже `SK=` путь обновлён).
> Тело сохранено дословно как канонический reference списочного пайплайна.

---
name: prospect-list-enrichment
description: "Обогащение списка B2B-проспектов (50-3000 компаний) — ИНН-матч с Your CRM, deep research через Perplexity по каждой, готовый Excel для отдела продаж с вкладками «Готовый обзвон», «Активные сделки», «Холодняк», «Реанимация» и приоритизацией A/B/C. Используй когда: пришёл xlsx/csv со списком компаний, ICP-список купленный/собранный, надо понять «кто уже в нашей базе и куда стучаться», подготовка к outbound-кампании. НЕ для одной компании (используй account-research), не для индивидуального лида (lead-enrichment), не для построения списка с нуля по ICP (lead-research). Триггеры: «обогати список», «список компаний пробить через CRM», «outbound по xlsx», «кто уже в Bitrix из этого списка», «приоритизируй проспектов», «prospect list», «account scoring», «список ClientCorp8 / ICP-таблица»."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
metadata:
  version: 1.0.0
  updated: 2026-06-21
  reuses: crm, perplexity, lead-enrichment
---

# Prospect List Enrichment

Оркестратор: внешний список B2B-проспектов → Excel под отдел продаж за 1-2 часа.

Вход: xlsx/csv 50-3000 строк с компаниями (имя + ИНН, опционально телефон/email/выручка).
Выход: один enriched.xlsx с 10-12 вкладками, приоритизация A/B/C, готовые ссылки в CRM, досье по топ-проспектам.

## Когда применять

**Применять:**
- Пришёл список 50+ компаний и нужно понять (1) кто уже в CRM, (2) что про них известно, (3) кому звонить первым с конкретным крюком
- Купленный/собранный ICP-список перед outbound-кампанией
- Account-based marketing: разметить целевой список под кампанию
- Подготовка к отраслевой конференции — список участников через CRM-фильтр

**Не применять:**
- Одна компания глубоко → `account-research`
- Один лид/контакт по фрагменту (email/телефон/имя) → `lead-enrichment` (Mode A)
- Построить список с нуля по описанию ICP → `lead-research`
- <20 компаний — быстрее руками
- Нет ИНН в источнике — сначала прогони через `lead-enrichment` чтобы достать

**Отличие от `lead-enrichment` (Mode B):** lead-enrichment покрывает индивидуальную квалификацию + базовый список. Наш скилл сфокусирован на **списке 100-3000** с упором на CRM-матч и приоритизацию. Финальный Excel — производственный артефакт для отдела продаж, не лоси-аналитика.

## Pipeline — 4 стадии

```
1. Extract  (xlsx/csv → extracted.json)         ~30 сек
2. Match    (ИНН → Bitrix bulk + 360°)          ~40 сек / 2500 ИНН
3. Enrich   (Perplexity досье по приоритету)    ~50-90 мин / 700 компаний
4. Build    (всё → enriched.xlsx 10-12 вкладок) ~30 сек
```

Все стадии **идемпотентны** — каждая пропускает уже сделанное. Если стадия 3 упала на 400-й — повторный запуск продолжит с того же места.

Подробная архитектура → `references/pipeline.md`.

## Быстрый старт

```bash
SK=~/.claude/skills/lead-enrichment/scripts/list_pipeline

# Полный прогон:
python $SK/orchestrate.py \
    --input "C:/path/my_list.xlsx" \
    --output "C:/path/enriched.xlsx" \
    --workdir "${HOME}/.claude/scratchpad/prospect-list-2026-06"

# Стадии можно гонять по одной:
python $SK/01_extract.py --input my_list.xlsx --output extracted.json --sheets "Лист1,Лист2"
python $SK/02_match_bitrix.py --input extracted.json --output bitrix_data.json
python $SK/03_research_perplexity.py --input extracted.json --bitrix bitrix_data.json --output research.json --limit 500
python $SK/04_build_xlsx.py --input extracted.json --bitrix bitrix_data.json --research research.json --linkedin linkedin.json --output enriched.xlsx
```

Минимальные опции `orchestrate.py`:

| Флаг | Что делает |
|------|-----------|
| `--input PATH` | xlsx/csv со списком (обязательно) |
| `--output PATH` | финальный enriched.xlsx |
| `--workdir DIR` | где хранятся промежуточные JSON и кеш Perplexity |
| `--sheets "A,B"` | какие листы парсить (по умолчанию все) |
| `--research-limit N` | сколько компаний прогнать через Perplexity (S+B все + топ N холодных по выручке) |
| `--skip-research` | пропустить стадию 3 (только CRM-обогащение) |
| `--linkedin PATH` | внешний JSON c LinkedIn-ЛПР для мерджа |
| `--bitrix-url` | базовый URL Bitrix (по умолчанию `https://we.company.example`) |

## Приоритизация

Каждая компания получает один из 3 tier'ов:

| Tier | Определение | Действие |
|------|-------------|----------|
| **S** | В CRM с активной историей: сделки или активности (звонки/встречи/задачи) | Подключиться к менеджеру / реанимировать / ускорить сделку |
| **B** | В CRM как карточка, но без сделок/активностей | Лёгкое касание — возможно, лид не дожали |
| **A** | НЕ в CRM. Приоритизация по выручке 2024 + industry-fit | Cold outreach с верха по выручке |

Готовый обзвон сортируется S → B → A.

Формулы и edge-кейсы (несколько компаний на один ИНН, активные стадии, провалы за давностью) → `references/tier-formulas.md`.

## Структура итогового Excel (10-12 вкладок)

| Лист | Что в нём | Цвет |
|------|-----------|------|
| **Пересечения** | Главная сводка. Все ИНН-матчи отсортированы по приоритету. Заголовок с метриками. | Желтый/зеленый по tier |
| **Готовый обзвон** | Контакты с тел/email из CRM + LinkedIn. Колонка «Приоритет» A/B/C. Кликабельные ссылки. | Желтый/зеленый/фиолетовый |
| **Активные сделки** | Сделки в работе сейчас (`NEW`, `PREPARATION`, `EXECUTING`, `UC_*`). | Голубой |
| **Продажи и провалы** | Закрытые WON + LOSE. Для upsell + анализа отказов. | Зеленый/розовый |
| **Холодняк (нет в базе)** | Tier A, сортирован по выручке. Сырые телефоны/email из источника. | По умолчанию |
| **LinkedIn ЛПР** | Если есть linkedin.json — мердж с компаниями по нормализованному имени. | Фиолетовый |
| **Реанимация (90+ дней)** | Кого пора дожать (была история, давно молчат). | По умолчанию |
| **Сделки — детали** | Построчно все сделки (включая закрытые). | По умолчанию |
| **Касания — лента** | Все активности хронологически. | По умолчанию |
| **Дубли источников** | Если несколько листов: что в обоих. Приоритет №1. | Оранжевый |
| **Глубокий рисёрч** | Досье от Perplexity. Tier S/B/A в одном виде. | По tier |
| **Исходные листы (+ колонки)** | Оригинальные листы с дописанными колонками справа: Match Company, Bitrix URL, продукты, стадии, контакты, LinkedIn. | По tier |

Точные колонки, ширины, цвета → `references/excel-structure.md`.

## Цветовая палитра

| Hex | Что значит |
|-----|-----------|
| `FFE699` жёлтый | Tier S — горячие, есть касания |
| `E2EFDA` светло-зелёный | Tier B — в базе без касаний |
| `C6E0B4` тёмно-зелёный | Tier A — холодные топ-выручка, или WON |
| `BDD7EE` голубой | Активные сделки |
| `F4B6B6` розовый | Провалы (LOSE) |
| `D9D2E9` фиолетовый | LinkedIn-матч |
| `F8CBAD` оранжевый | Дубли (в нескольких источниках) |
| `1F3864` тёмно-синий | Шапка таблиц (белый текст) |

## Что отдаёт Perplexity (вкладка «Глубокий рисёрч»)

По каждой компании (150-400 слов):

- **ЛПР** — CDTO/CIO/CTO, HR/L&D-директор, директор по корпразвитию. Имя + должность + LinkedIn если есть. Если нет — «нет в открытых источниках» (важно — Perplexity не должна выдумывать).
- **Свежие новости** — события 2025-2026: M&A, реструктуризация, смена топов.
- **Сигналы под продукт** — обучение сотрудников, AI-инициативы, HR-tech (параметризуется под ICP).
- **Триггеры outreach** — что случилось за 3-6 мес. и даёт повод написать.
- **Пейн-поинты** — под конкретное предложение (YourProduct / EdTech / Продукт-2 и т.д.).

Промпт настраивается через `--product-hint "YourProduct, EdTech, HR-tech"`.

## Подготовка перед запуском

```bash
# 1. Кредиты
grep CRM_WEBHOOK_URL  ~/.claude/.credentials.master.env   # должен быть webhook на акк с правами на CRM
grep PERPLEXITY_API_KEY    ~/.claude/.credentials.master.env   # либо подписка Max через локальный gateway

# 2. Зависимости (один раз)
pip install openpyxl rapidfuzz python-dotenv

# 3. Вход — ожидаемые колонки (имена нечувствительны к регистру и языку):
#   Обязательно: name | company | ОРГ | компания, AND inn | ИНН
#   Опционально: ul | юр.лицо, phone, email, site, rev2024, rev2023, industry, segment, last_call_comment

# 4. Если есть LinkedIn-таблица с ЛПР — преобразуй в JSON формата:
#   [{"name": "...", "role": "...", "company": "...", "linkedin": "...", "reaction": "...", "segment": "..."}]
```

## Гочи и решения

| Симптом | Причина | Что делать |
|---------|---------|-----------|
| `UnicodeEncodeError` на Windows | cp1251 в stdout | Скрипты уже шлют `sys.stdout = io.TextIOWrapper(...)`. Если патчишь — не убирай. |
| Perplexity timeout на 5-batch | Слишком жадно | `03_research_perplexity.py --batch 3 --workers 1 --mode auto` (gentle retry mode) |
| Bitrix `QUERY_LIMIT_EXCEEDED` | >50 ИНН в одном фильтре | Скрипт сам бьёт по 50, не патчь руками |
| Сделки/контакты пропали | Несколько юрлиц на один ИНН — разные company_id | `02_match_bitrix.py` агрегирует по ИНН, не по company_id. Не используй `find_by_company_id` напрямую |
| LinkedIn-имена не матчатся | Латиница vs кириллица + ООО/ПАО префиксы | `LATIN_TO_CYRILLIC` map в `04_build_xlsx.py`, расширь если нужно |
| Несколько листов с пересечениями | Один ИНН в двух источниках | Вкладка «Дубли источников» подсвечивает оранжевым — это **приоритет №1** |
| 80% Perplexity-ответов оборваны | Жадный батч и большой prompt | Уменьши `--batch` до 3, режим `auto`, увеличь timeout |
| Excel не открывается | openpyxl version | `pip install -U openpyxl>=3.1` |

## Связь с другими скиллами

- **`crm`** — стадия 2 (CRM bulk match + company 360°). Если нужно расширить — добавь `references/lead-list-matching.md` в crm.
- **`perplexity`** — стадия 3 (batch deep research). Шаблон промптов и batching → `references/batch-research.md` в perplexity.
- **`lead-enrichment`** — индивидуальная квалификация (Mode A). Если в списке нет ИНН → сначала прогоняй через lead-enrichment чтобы их добыть.
- **`account-research`** — глубокое погружение в одну компанию. Используется как «второй ход» по Tier S после нашего скилла.
- **`draft-outreach`** — после того как enriched.xlsx собран и приоритеты понятны — генерация писем по каждой строке.

## Quality bar

Через месяц новый sales-инженер (Company или другая компания со своим CRM) приходит со своим xlsx со списком 500 компаний, запускает `orchestrate.py --input my_list.xlsx --output result.xlsx`, и через 1-2 часа получает готовый enriched.xlsx с приоритетной сегментацией и готовыми списками «куда звонить сегодня».

## References

- `references/pipeline.md` — детальная архитектура 4 стадий, что каждая делает и какие checkpoint'ы пишет
- `references/excel-structure.md` — все 12 вкладок, точные колонки, ширины, цвета, форматирование
- `references/tier-formulas.md` — формулы Tier A/B/C, активные/закрытые стадии, edge-кейсы

## Scripts

- `scripts/01_extract.py` — xlsx/csv → нормализованный JSON
- `scripts/02_match_bitrix.py` — bulk ИНН-матч + сборка 360° по каждому матчу
- `scripts/03_research_perplexity.py` — приоритезированный batch research через perplexity skill
- `scripts/04_build_xlsx.py` — финальный enriched.xlsx
- `scripts/orchestrate.py` — оркестратор: 01→02→03→04 с checkpoint'ами
