# Modo: scan-startupjobs — startup.jobs Scanner

Сканирует startup.jobs — curated startup job board с фокусом на европейские и remote стартапы. Хороший дополнительный источник к Wellfound.

## Почему startup.jobs

- **Европейские стартапы** — лучшее покрытие EU startups, Wellfound там слабее
- **Remote-friendly** — 60%+ вакансий с remote опцией
- **Качественный фильтр** — только verified стартапы (не enterprise spam)
- **Простая структура** — HTML-based, лёгкий парсинг
- **Публичный** — нет авторизации

## Ограничения

- **Меньше trafic чем Wellfound/RemoteOK** — фокус на EU
- **Нет официального API** — парсим HTML

## URL patterns

Базовая структура:
```
https://startup.jobs/?q={query}&remote={true|false}&category={id}
```

Или через category pages:
```
https://startup.jobs/product-jobs
https://startup.jobs/remote-jobs
https://startup.jobs/management-jobs
https://startup.jobs/ai-ml-jobs
```

## Scraping approach

Два варианта:

### Вариант A — WebFetch (простой HTML)

startup.jobs отдаёт server-side rendered HTML, WebFetch работает без Playwright. Парсить через структурные паттерны:

- `<div class="job-listing">` / `<article>` — карточка
- `<h2>` внутри — title
- `<a class="company">` — company
- `<span class="salary">` — salary (если есть)
- `<span class="location">` — location / remote
- `<a href="...">` — apply URL

### Вариант B — Playwright (если добавят SPA)

Fallback если HTML structure сломается.

## Workflow

1. **Read config**: `portals.yml` → `startupjobs` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Для каждой query в config:**
   - WebFetch URL → HTML
   - Parse job cards через regex или cheerio-like подход
   - Extract: title, company, location, salary, url, posted_date

4. **Для каждой карточки:**
   - Применить title_filter
   - Dedup

5. **Для новых:**
   - Opt: fetch job page для full JD
   - Добавить в `pipeline.md` с меткой `[startup-jobs]`:
     ```
     - [ ] {url} | {company} | {title} | {location} | {salary}
     ```

6. **Output:**

```
startup.jobs Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Queries: 4
Found: N total
Filtered: N relevant
Duplicates: N
New: N

  + {company} | {title} | {location} | {salary}
  ...
```

## Search queries

```yaml
queries:
  - "https://startup.jobs/?q=product+manager&remote=true"
  - "https://startup.jobs/?q=head+of+product"
  - "https://startup.jobs/?q=CPO"
  - "https://startup.jobs/ai-ml-jobs"
  - "https://startup.jobs/product-jobs"
```

## startup.jobs-specific notes

- **Posted date** парсить — бывает "2 days ago", "1 week ago" — конвертировать в ISO
- **Company size signals** — обычно маленькие (1-50), team size не всегда указан
- **Funding stage** — часто в описании company, не структурировано, регекс
- **EU-heavy** — часто Berlin, Amsterdam, Paris, London locations
- **Remote fine print** — "Remote (EU only)", "Remote (CET timezone)" — парсить в tags
- **Зарплаты** — не всегда указаны, часто "Competitive" — помечать `[no salary]`
- **Rate limit** — неагрессивный, 1-2 query/sec ok
