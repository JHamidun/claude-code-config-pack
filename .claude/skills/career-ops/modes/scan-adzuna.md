# Modo: scan-adzuna — Adzuna API Scanner (16 Countries)

Сканирует Adzuna через официальный API — бесплатный тир (250 запросов/день), покрывает 16 стран включая Россию и Бразилию.

## Почему Adzuna

- **Официальный API** — не скрейп, стабильно, быстро
- **16 стран**: US, UK, DE, FR, IT, ES, NL, PL, **BR**, **RU**, AU, CA, AT, CH, SG, ZA, MX, IN
- **Бесплатный тир**: 250 calls/day, 5 calls/sec — достаточно для 7 queries × 10 стран через день
- **Прозрачные зарплаты** — имеет specific salary_min/max fields, API их нормализует
- **Структурированные фильтры** — без парсинга HTML

## Registration

Регистрация бесплатная: https://developer.adzuna.com/

Получишь:
- `APP_ID` — ID приложения
- `APP_KEY` — API ключ

Положить в переменные окружения (или в свой `.credentials.master.env` — шаблон
лежит в `~/.claude/templates/.credentials.master.env.example`):
```bash
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
```

## API

**Base URL pattern:**
```
https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id={ID}&app_key={KEY}&{params}
```

**Country codes:** `us`, `gb`, `de`, `fr`, `it`, `es`, `nl`, `pl`, `br`, `ru`, `au`, `ca`, `at`, `ch`, `sg`, `za`, `mx`, `in`

**Key parameters:**
- `what` — search terms (exact match with quotes, OR supported)
- `what_and` — all words must appear
- `what_phrase` — exact phrase match
- `where` — location
- `salary_min` / `salary_max` — в локальной валюте страны
- `full_time=1` / `part_time=1` / `permanent=1`
- `results_per_page` — max 50
- `sort_by` — `relevance` | `date` | `salary`

### Example queries

```bash
# US remote AI Product
https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=X&app_key=Y&what_or=CPO%20%22Head%20of%20Product%22%20%22AI%20Product%22&where=remote&salary_min=120000&results_per_page=50

# Germany Berlin senior product (та же схема для любой из 16 стран — меняется код страны)
https://api.adzuna.com/v1/api/jobs/de/search/1?app_id=X&app_key=Y&what=Product%20Manager&where=Berlin&salary_min=140000&results_per_page=50

# Russia Moscow Product Manager
https://api.adzuna.com/v1/api/jobs/ru/search/1?app_id=X&app_key=Y&what=Product%20Manager&where=Moscow
```

### Response structure

```json
{
  "results": [
    {
      "id": "4725841234",
      "title": "Head of Product — AI Platform",
      "company": { "display_name": "Acme AI" },
      "location": {
        "display_name": "San Francisco, CA",
        "area": ["US", "California", "San Francisco"]
      },
      "salary_min": 140000,
      "salary_max": 180000,
      "salary_is_predicted": "0",
      "contract_type": "permanent",
      "contract_time": "full_time",
      "category": { "tag": "it-jobs", "label": "IT Jobs" },
      "redirect_url": "https://www.adzuna.com/land/ad/...",
      "description": "Short snippet of JD (250 chars)...",
      "created": "2026-04-10T14:00:00Z"
    }
  ],
  "count": 1247,
  "mean": 195000
}
```

## Workflow

1. **Read config**: `portals.yml` → `adzuna` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Для каждой страны + query combination:**
   - Собрать URL с `{country}`, `{what_or}`, salary_min, page=1
   - WebFetch с app_id+app_key
   - Parse `results[]`, извлечь: id, title, company, location, salary_min/max, redirect_url, created
   - **ВАЖНО:** проверять `salary_is_predicted` — если "1", зарплата оценочная, не реальная
   - Применить title_filter (positive/negative)
   - Dedup

4. **Rate limit discipline:**
   - Max 5 calls/sec (добавлять 250ms delay между запросами)
   - Max 250 calls/day (чекать `data/adzuna-usage.tsv`)
   - Если превышен лимит — остановить сканер, отметить в логе

5. **Для каждой новой вакансии:**
   - Добавить в `pipeline.md` с меткой `[adzuna][{country}]`:
     ```
     - [ ] {redirect_url} | {company} | {title} | ${salary_min}-${salary_max} | {country}
     ```

6. **Output:**

```
Adzuna Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Countries: us, gb, de, br, ru, au, ca
Queries: 3
API calls used: 21/250
Found: N total
Filtered: N relevant
Duplicates: N
New: N

  + [us] {company} | {title} | ${salary_min}-${salary_max}
  + [br] {company} | {title} | R${salary_min}-${salary_max}
  + [ru] {company} | {title} | RUB
  ...
```

## Country-specific notes

- **US/UK/DE/AU/CA** — хорошее покрытие, много CPO/VP Product ролей
- **BR** — покрытие среднее, лучше Gupy/Vagas, но Adzuna тянет их агрегатом в английском тексте
- **RU** — меньше hh.ru, но ловит английские постинги российских tech-компаний для international кандидатов
- **Сингапур (SG) / Индия (IN)** — для APAC-вакансий tech компаний

## Salary considerations

- Adzuna показывает зарплаты в **локальной валюте**:
  - US/CA/SG: USD
  - UK: GBP
  - EU: EUR
  - BR: BRL
  - RU: RUB
  - IN: INR
  - AU: AUD
- **Нормализовать в USD** для сравнения в скоринге (текущий курс захардкодить в config или использовать API)
- **`salary_is_predicted: "1"`** — ML-оценка Adzuna, не реальная цифра из JD. Помечать в pipeline как `[predicted]`

## Title filter (global)

```yaml
positive_en_adzuna:
  - "Chief Product"
  - "Head of Product"
  - "VP Product"
  - "Director of Product"
  - "AI Product"
  - "Product Lead"
  - "Principal Product"
  - "Senior Product Manager"
  - "Head of AI"
```

## API limits discipline

Adzuna даёт:
- **Free tier:** 250 calls/day
- **Starter tier ($0/mo):** 5000 calls/day (после регистрации с подтверждением)

Наша стратегия:
- 7 queries × 5 приоритетных стран (US, GB, DE, BR, RU) = 35 calls/run
- Запускать 1x в день через `/loop 24h`
- Backup — если 250/день превышен, использовать другие сканеры
