# Modo: scan-aijobs — AI-Jobs.net Scanner

Сканирует ai-jobs.net — специализированный борд для AI/ML ролей, включая product и leadership. Чистый сигнал, минимум шума.

## Почему ai-jobs.net

- **100% AI/ML фокус** — нет "generic product manager"
- **Качественные компании** — от Scale AI, HuggingFace, Anthropic, OpenAI, Mistral до AI-first startups
- **Seniority указана** — Junior/Mid/Senior/Staff/Principal/Lead/Manager/Director/VP
- **Глобальная база** — US, EU, Remote, APAC
- **Простой HTML** — легко скрейпится, нет Cloudflare

## API / Структура

**Base URL:** `https://ai-jobs.net`

### Список вакансий

`https://ai-jobs.net/?cat=30&reg=5`

Параметры:
- `cat` — категория (30 = AI/ML Product Manager, 31 = AI Product Lead, 10 = ML Engineer, etc.)
- `reg` — регион (1=US, 2=EU, 3=UK, 5=Remote, 8=APAC, 9=Latam)
- `sen` — seniority (1=Junior, 2=Mid, 3=Senior, 4=Lead, 5=Manager, 6=Director, 7=VP, 8=C-level)
- `sal` — min salary USD

### Примеры запросов

```
# AI Product Manager remote
https://ai-jobs.net/?cat=30&reg=5

# Head of AI / VP Product, global
https://ai-jobs.net/?cat=30&sen=7

# C-level AI (CPO, CTO)
https://ai-jobs.net/?sen=8

# ML Engineering Manager (если рассматриваешь)
https://ai-jobs.net/?cat=10&sen=5&reg=5
```

### JSON feed (если работает)

Пробовать `https://ai-jobs.net/feed/json/` — отдают последние ~50 вакансий в JSON. Если 404 — парсить HTML.

## Workflow

1. **Read config**: `portals.yml` → `aijobs` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Для каждой query в конфиге:**
   - WebFetch HTML
   - Парсить job listings: title, company, location, salary range, posted date, URL
   - Применить filters (title, salary min)

4. **Для каждой новой вакансии:**
   - Опционально открыть detail page для full JD
   - Добавить в `pipeline.md` с меткой `[ai-jobs]`
   - Записать в `scan-history.tsv`

5. **Output:**

```
AI-Jobs.net Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Categories: AI Product Manager, Head of AI
Regions: Remote, EU, US
Seniority: Senior+
Found: N
Filtered: N
Duplicates: N
New: N

  + {company} | {position} | {seniority} | ${salary} | {location}
  ...
```

## Title filter

```yaml
positive_en:
  - "AI Product"
  - "ML Product"
  - "Head of AI"
  - "VP AI"
  - "Director AI"
  - "Chief AI Officer"
  - "Principal Product"
  - "Staff Product"
  - "Senior Product Manager"
  - "AI Strategy"
negative_en:
  - "Engineer" # если фильтруешь только на product
  - "Data Scientist"
  - "Research Scientist"
  - "Intern"
```

## ai-jobs.net-specific notes

- **Freshness** — вакансии пропадают через 30 дней, сканер ловит только активные
- **Зарплаты** в USD всегда, даже для EU ролей (нужно делать конверсию для оценки покупательной способности)
- **Remote по умолчанию** глобально — но проверять timezone requirement в JD
- **Нет rate limit** официально, но быть разумным (не >1 req/sec)
- **Company research** — каждая компания имеет страницу `/company/{slug}` с историей вакансий
- **Лучший сигнал качества** — наличие серии из 5+ вакансий от одной компании = активный рост
