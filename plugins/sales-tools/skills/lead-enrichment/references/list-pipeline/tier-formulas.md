# Tier formulas

Как считать tier A/B/C, какие стадии считаются «активными» / «закрытыми», edge-кейсы.

## Tier definition

```python
def compute_tier(inn: str, extracted_row: dict, bitrix_info: dict | None) -> str:
    """
    S — в CRM с активной историей
    B — в CRM как карточка, без активностей
    A — НЕ в CRM (приоритизация по выручке отдельно)
    """
    if bitrix_info is None:
        return "A"  # cold

    if bitrix_info["touch_count"] > 0:
        return "S"  # hot

    if bitrix_info["has_deals"] or bitrix_info["has_contacts"]:
        return "B"  # in CRM, but quiet

    # Edge: company card exists but absolutely empty (no deals, no contacts, no touches)
    # Still treat as B — someone created it for a reason
    return "B"
```

## Активные стадии (для вкладки «Активные сделки»)

```python
ACTIVE_STAGES = {
    "NEW",                  # Новая
    "PREPARATION",          # Подготовка документов
    "PREPAYMENT_INVOICE",   # Счёт на предоплату
    "EXECUTING",            # В работе
    "FINAL_INVOICE",        # Финальный счёт
}

def is_active(stage_id: str) -> bool:
    if not stage_id:
        return False
    # stage_id может быть "C5:UC_QWERTY" или просто "EXECUTING"
    s = stage_id.split(":")[-1] if ":" in stage_id else stage_id
    return s in ACTIVE_STAGES or s.startswith("UC_")
```

`UC_*` — custom intermediate stages в Bitrix (юзер мог создать «Демо назначено», «Согласование», ...). Все считаем активными по умолчанию.

## Закрытые стадии

```python
def is_won(stage_id: str) -> bool:
    return stage_id and stage_id.split(":")[-1] == "WON"

def is_lost(stage_id: str) -> bool:
    s = stage_id.split(":")[-1] if ":" in (stage_id or "") else (stage_id or "")
    return s in ("LOSE", "APOLOGY")
```

`APOLOGY` — стандартный отказной стейдж в Your CRM («Не сложилось»).

## Edge-кейсы

### 1. Несколько юрлиц на один ИНН

Один ИНН может соответствовать нескольким `company_id` в Bitrix (старые карточки, дубликаты, разные подразделения). Решение: **агрегировать всё по ИНН**, не по `company_id`. См. `aggregate_inn()` в `scripts/02_match_bitrix.py`.

В Excel столбцы `Bitrix компания` и `Bitrix ID` показывают все titles/IDs через `/` и `,`.

### 2. Сделка без `CATEGORY_ID`

Bitrix отдаёт `CATEGORY_ID = "0"` (общая воронка). В скрипте это рендерится как `"cat:0"` или из `categories["0"]` если резолвится через `crm.dealcategory.list`. Не баг.

### 3. Дата закрытия в будущем

Сделка `CLOSED = "Y"` + `CLOSEDATE > today` — Bitrix позволяет. Не фильтруй по `CLOSEDATE`, фильтруй по `STAGE_ID`.

### 4. Touch_count считает дубли

`touch_count = len(deals) + len(activities) + len(timeline)`. Активность может быть привязана и к сделке, и к компании (Bitrix дублирует). Не страшно — нужен порядок величины, не точность.

### 5. Реанимация без `last_touch`

Если есть `has_deals=True`, но `last_touch=""` (битые даты в Bitrix) — НЕ попадает в «Реанимация (90+ дней)». Скрипт проверяет:

```python
if info["touch_count"] == 0: continue
if not info["last_touch"]: continue
lt = parse_dt(info["last_touch"])
if not lt: continue
days = (today - lt.replace(tzinfo=None)).days
if days < 90: continue
```

### 6. Cold-tier по выручке: priority queue

В стадии 3 Tier A режется `--research-limit N` от верха по `rev2024`. Если у строки нет `rev2024` (пусто или 0) — она НЕ попадает в очередь Perplexity, но останется в холодняке Excel.

Резон: Perplexity дорог, выручка — самая дешёвая прокси для ICP-fit.

### 7. LinkedIn-матч ≠ Bitrix-матч

LinkedIn даёт **ЛПР** через имя компании. Матч через `fuzzy_match()` (см. `04_build_xlsx.py`):
- bidirectional substring
- token overlap ≥2 (skip короткие)
- словарь Latin↔Cyrillic (`fixprice` ↔ `фикс прайс`)

Результат: одна компания может попасть на лист «Готовый обзвон» дважды — раз через Bitrix-контакт, раз через LinkedIn. Это **фича**, не баг (LinkedIn часто свежее).

### 8. Несколько источников → дубли

Если в `extracted.json` ИНН встречается дважды с разных `source` — попадает на лист «Дубли источников» (приоритет №1, окраска `DUPE_FILL`). НЕ дублируется на «Пересечения» — там один ИНН одна строка (через `seen` set).

### 9. Что считать «менеджер Company»

Менеджеры собираются из:
- `companies[cid].ASSIGNED_BY_ID`
- `deals[*].ASSIGNED_BY_ID`

И резолвятся через `users` map. Один human = одна строка (sorted set). НЕ путать с `CREATED_BY` (кто создал карточку — обычно admin).

### 10. Множественные `phone` / `email` в Bitrix контакте

Bitrix отдаёт списком dict'ов `[{"VALUE": "+7...", "VALUE_TYPE": "WORK"}, ...]`. Скрипт джойнит через `; `. См. `fmt_phone()`, `fmt_email()` в `02_match_bitrix.py`.
