# Pipeline — 4 стадии

Полный путь от xlsx до enriched Excel. Все стадии идемпотентны и пишут промежуточные JSON в `--workdir`.

## Layout рабочей директории

```
workdir/
├── extracted.json           # стадия 1
├── bitrix_data.json         # стадия 2 (raw + aggregated)
├── matches_by_inn.json      # стадия 2 (inn → bitrix_company_ids)
├── research/
│   ├── queue.json           # стадия 3 (priority queue)
│   ├── results.json         # стадия 3 (consolidated)
│   ├── 7700000000.md        # стадия 3 (per-INN markdown, кеш)
│   └── ...
├── linkedin.json            # опционально, внешний source
└── checkpoint.json          # orchestrate.py state
```

`orchestrate.py` пропускает уже сделанные стадии. Если `extracted.json` существует и старше входного xlsx — пересчёт. Если новее — пропуск.

---

## Стадия 1 — Extract

**Скрипт:** `scripts/01_extract.py`
**Вход:** xlsx или csv. Любые имена колонок (нормализуются через словарь-маппинг).
**Выход:** `extracted.json` — список dict'ов.

### Что делает

1. Открывает xlsx (`openpyxl.load_workbook`) или csv (`csv.DictReader`).
2. Для xlsx — берёт листы из `--sheets` или все.
3. Нормализует заголовки: `ИНН` / `INN` / `inn` → `inn`; `ОРГ` / `Компания` / `Name` → `name` и т.д. См. `HEADER_ALIASES` в скрипте.
4. Валидирует ИНН (10 или 12 цифр после `re.sub(r'\D', '', s)`).
5. Помечает каждую строку `source` = имя листа (для последующих дубль-проверок).
6. Парсит выручку (`rev2024`, `rev2023`) — терпит запятые, пробелы, `руб.`, `тыс.`, `млн`.

### Формат `extracted.json`

```json
[
  {
    "source": "Лист1",
    "row_idx": 2,
    "name": "ООО Альфа",
    "inn": "7700000000",
    "ul": "Общество с ограниченной ответственностью Альфа",
    "phone": "+1234567890",
    "email": "info@alfa.ru",
    "site": "alfa.ru",
    "rev2024": 1500000000.0,
    "rev2023": 1200000000.0,
    "industry": "Финансы",
    "segment": "Enterprise",
    "last_call_comment": "Не дозвонились 2 раза"
  },
  ...
]
```

### Идемпотентность

Файл перезаписывается каждый запуск (быстрая операция). Если структура входа изменилась — нужно начать заново.

---

## Стадия 2 — Match (Your CRM)

**Скрипт:** `scripts/02_match_bitrix.py`
**Вход:** `extracted.json` + Bitrix webhook из `~/.claude/.credentials.master.env`.
**Выход:** `bitrix_data.json` + `matches_by_inn.json`.

### Что делает

1. Собирает все уникальные ИНН (`{r['inn'] for r in extracted if r['inn']}`).
2. Bulk-запрос компаний по ИНН — `crm.company.list` с `filter[%UF_CRM_INN]={inn1,inn2,...}` по 50 ИНН на запрос. Время: 2500 ИНН за ~40 сек.
3. Для каждой найденной company_id:
   - `crm.deal.list` — все сделки (включая закрытые)
   - `crm.contact.list` по `COMPANY_ID` — контакты
   - `crm.activity.list` по `OWNER_ID + OWNER_TYPE_ID=4` — активности компании
   - `crm.activity.list` по `OWNER_ID + OWNER_TYPE_ID=2` для каждой сделки — активности сделок
   - `crm.timeline.comment.list` — комментарии таймлайна
4. Резолвит ID → имена: `crm.dealcategory.list`, `crm.status.list` (для стадий), `user.get` (для менеджеров).
5. Агрегирует по ИНН (несколько company_id могут быть на один ИНН):
   - titles, urls, bitrix_ids
   - all deals + категории + стадии (по name, не ID)
   - all contacts + phone/email/post
   - activities chronologically
   - touch_count = deals + activities + timeline
   - last_touch = max date across deals + activities
   - has_deals, has_contacts флаги

### Формат `bitrix_data.json`

```json
{
  "by_inn": {
    "7700000000": {
      "inn": "7700000000",
      "bitrix_ids": ["12345"],
      "titles": ["ООО Альфа"],
      "urls": ["https://we.company.example/crm/company/details/12345/"],
      "managers": ["John Doe"],
      "products": ["YourProduct", "Продукт-2"],
      "stages_used": ["В работе", "Сделано"],
      "deals": [
        {
          "ID": "987",
          "TITLE": "YourProduct — пилот",
          "STAGE_ID": "C5:WON",
          "OPPORTUNITY": "500000",
          "DATE_CREATE": "2025-09-12T10:00:00+03:00",
          "_category_name": "YourProduct",
          "_stage_name": "Сделано",
          "_manager": "John Doe",
          "_company_id": "12345"
        }
      ],
      "contacts": [
        {"id": "777", "name": "Сидоров А.А.", "post": "CIO", "phone": "+7...", "email": "a@alfa.ru", "company_id": "12345"}
      ],
      "activities": [
        {"date": "2025-12-01", "type": "Звонок", "subject": "Демо YourProduct", "source": "сделка #987", "completed": true}
      ],
      "touch_count": 17,
      "last_touch": "2025-12-01",
      "has_deals": true,
      "has_contacts": true
    }
  },
  "categories": {"5": "YourProduct"},
  "stages": {"C5:WON": "Сделано"},
  "users": {"42": {"name": "John Doe"}}
}
```

### Идемпотентность

Если `bitrix_data.json` есть и не указан `--refresh-bitrix` — стадия пропускается. Bitrix-пулл занимает время, мы кешируем.

### Гочи

- `QUERY_LIMIT_EXCEEDED` — Bitrix лимит 50 элементов в одном `filter[%...]`. Скрипт сам бьёт.
- Несколько юрлиц на один ИНН — скрипт мержит, не дублирует. Правильный подход — агрегировать по ИНН, не по company_id.
- Сделки без `CATEGORY_ID` попадают в категорию 0 (общая) — это нормально.

---

## Стадия 3 — Enrich (Perplexity)

**Скрипт:** `scripts/03_research_perplexity.py`
**Вход:** `extracted.json` + `bitrix_data.json` + `PERPLEXITY_API_KEY`.
**Выход:** `research/queue.json` + `research/results.json` + `research/<inn>.md` (кеш per-INN).

### Очередь приоритетов

```python
queue = []

# 1. Tier S: in CRM AND touch_count > 0
for inn in bitrix_data["by_inn"]:
    info = bitrix_data["by_inn"][inn]
    if info["touch_count"] > 0:
        queue.append({"tier": "S", "inn": inn, "name": ..., "reason": f"Активная история. {products}, last_touch={info['last_touch']}"})

# 2. Tier B: in CRM, no touches
    else:
        queue.append({"tier": "B", "inn": inn, "name": ..., "reason": "В Bitrix как карточка, без касаний"})

# 3. Tier A: NOT in CRM, top N by rev2024
cold = [r for r in extracted if r["inn"] not in bitrix_data["by_inn"] and r.get("rev2024")]
cold.sort(key=lambda r: -r["rev2024"])
for r in cold[:limit]:
    queue.append({"tier": "A", "inn": r["inn"], "name": r["name"], "reason": f"Холодняк, выручка 2024: {rev:,.0f}"})
```

`--research-limit N` режет ТОЛЬКО tier A (S+B всегда полные).

### Batch research

- `--batch 5 --workers 3` (default) — быстро. 700 компаний за ~60 мин.
- `--batch 3 --workers 1 --mode auto` — gentle, для retry на упавшие. Не блокирует Perplexity rate-limit.
- На каждый ИНН результат пишется в `research/<inn>.md`. При повторном запуске скрипт пропускает уже готовые (если md > 300 байт и без `ERROR:` / `TIMEOUT:` в начале).

### Промпт-шаблон

```
Подготовь краткие досье (по 150-200 слов на каждую) для B2B-продаж по этим N российским компаниям на 2026 год:

1. **<Имя1>** (юр. лицо: <UL1>) — ИНН <inn1> — <industry1>
2. **<Имя2>** ... — ИНН <inn2>
...

Для **каждой** компании дай ровно такую структуру:

## Компания {N}: {Название} [{ИНН}]

**ЛПР:** имя + должность (CDTO/CIO/CTO, HR/L&D-директор, директор по корпоративному развитию). Если данных нет — пиши "нет в открытых источниках".

**Свежие новости (2025-2026):** ключевые события, сделки, реструктуризация, смена топов.

**Сигналы для <product_hint>:** обучение сотрудников, AI-инициативы, HR-tech.

**Триггеры для outreach:** что произошло за 3-6 месяцев и даёт повод написать.

Со ссылками на источники [1][2]. Очень кратко по делу. Не пропускай ни одну компанию из списка.
```

`product_hint` параметризуется через `--product-hint "YourProduct, EdTech, HR-tech"` (дефолт пустой → generic «AI-инициативы, HR-tech»).

### Парсинг batch-ответа

Perplexity возвращает текст с разделителями `## Компания N:`. Скрипт разбивает по regex `r'\n(?=## ?(?:Компания|Company)\s*\d)'`, маппит номер N → batch[N-1], пишет в файл.

### Финальная агрегация

После всех батчей `sync_results.py` (вшит в `03_research_perplexity.py` как функция) пересобирает `results.json` из всех `.md` файлов. Это даёт независимый кеш — даже если batch завершился частично, после следующего запуска state восстановится.

### Идемпотентность

- `--limit N` менялся — пересоберётся только queue, существующие .md сохранятся.
- Каждый ИНН одиножды попадает в Perplexity. Повторный запуск = no-op для уже исследованных.

---

## Стадия 4 — Build (Excel)

**Скрипт:** `scripts/04_build_xlsx.py`
**Вход:** `extracted.json`, `bitrix_data.json`, опц. `research/results.json`, опц. `linkedin.json`.
**Выход:** `enriched.xlsx`.

### Что делает

1. Копирует входной xlsx (если был) как базу, чтобы сохранить оригинальные листы.
2. К каждому оригинальному листу справа дописывает 13 колонок: `Match Company`, `Bitrix компания`, `Bitrix URL`, `Все продукты (категории)`, `Стадии сделок`, `Сделок всего`, `Контактов в Bitrix`, `Касаний всего`, `Последнее касание`, `Дней с касания`, `Менеджер(ы)`, `Контакты Bitrix`, `LinkedIn ЛПР`.
3. Создаёт 9 новых листов в порядке: `Пересечения`, `Готовый обзвон`, `Активные сделки`, `Продажи и провалы`, `Холодняк (нет в базе)`, `Дубли источников`, `LinkedIn ЛПР`, `Реанимация (90+ дней)`, `Сделки — детали`, `Касания — лента`.
4. Если есть `research/results.json` — добавляет вкладку `Глубокий рисёрч` + столбец `Свежий рисерч (Perplexity)` на лист `Пересечения`.
5. Каждая строка окрашивается по tier (см. палитру в SKILL.md).
6. Все вкладки получают `freeze_panes` на шапку и `auto_filter`.
7. Bitrix URL и LinkedIn — кликабельные ссылки (`cell.hyperlink = url`).

Полная схема колонок → `references/excel-structure.md`.

### Идемпотентность

Перезаписывает финал каждый запуск (быстрая операция, ~30 сек на 2500 строк).

---

## Checkpoint и восстановление

`orchestrate.py` пишет `checkpoint.json`:

```json
{
  "started_at": "2026-06-21T10:00:00",
  "input_path": "C:/.../my_list.xlsx",
  "input_mtime": 1718956800,
  "stages": {
    "extract":  {"done": true, "ts": "2026-06-21T10:00:30", "rows": 2528},
    "match":    {"done": true, "ts": "2026-06-21T10:01:10", "matched": 698},
    "research": {"done": false, "in_progress": true, "completed": 432, "total": 698},
    "build":    {"done": false}
  }
}
```

При повторном запуске:
- Если `input_mtime` совпадает и stage `done: true` — skip
- Если research `in_progress` — продолжить с того же queue (per-INN кеш .md решает всё)
- Если build не done — перестроить

`--force` гонит всё с нуля.
