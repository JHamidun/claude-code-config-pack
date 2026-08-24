# Modo: scan-hiringcafe — Hiring Cafe Scanner

Сканирует hiring.cafe — remote-first job board с хорошим AI/tech покрытием и минимумом шума.

## Почему Hiring Cafe

- **Remote-first** — 80%+ вакансий fully remote
- **Качественные фильтры** — function, seniority, location, salary, visa, remote policy
- **AI/ML hub** — отдельная категория с топ-стартапами (Anthropic, OpenAI, Scale, Mistral, xAI)
- **Публичный доступ** — нет paywall, Cloudflare не агрессивный
- **Хороший UI** — легко парсится, структура стабильная

## Ограничения

- **Нет публичного API** — парсим через Playwright
- **SPA с React** — нужен snapshot, не raw HTML
- **Pagination через infinite scroll**

## URL patterns

Поиск через URL params:
```
https://hiring.cafe/?searchState={encoded_json}
```

Где `searchState` — urlencoded JSON с фильтрами. Проще использовать пресеты:

```
# AI Product Manager remote
https://hiring.cafe/?searchQuery=AI+Product+Manager&locationType=REMOTE

# Head of Product global
https://hiring.cafe/?searchQuery=Head+of+Product&seniority=senior

# VP Product startup
https://hiring.cafe/?searchQuery=VP+Product&companySize=small

# AI category direct
https://hiring.cafe/categories/ai-ml
```

## Playwright approach

1. `browser_navigate` → query URL
2. `browser_wait_for` → элемент `[data-testid="job-card"]` или `.job-list-item`
3. `browser_snapshot` → структура DOM
4. Scroll 3-5 раз для lazy-load больше результатов
5. Extract каждую карточку: title, company, location, salary, tags, apply_url

### Элементы для извлечения (селекторы примерные)

```javascript
document.querySelectorAll('[data-testid="job-card"]').forEach(card => {
  const title = card.querySelector('[data-testid="job-title"]')?.textContent;
  const company = card.querySelector('[data-testid="company-name"]')?.textContent;
  const location = card.querySelector('[data-testid="location"]')?.textContent;
  const salary = card.querySelector('[data-testid="salary-range"]')?.textContent;
  const url = card.querySelector('a')?.href;
  // tags, remote-only flag, seniority
});
```

Если селекторы не работают — использовать `browser_snapshot` и парсить по текстовому контенту структурно.

## Workflow

1. **Read config**: `portals.yml` → `hiringcafe` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Для каждой query:**
   - `browser_navigate`
   - `browser_wait_for` (job cards появятся)
   - Scroll через `browser_press_key("End")` × 3 раза с паузой 1с
   - `browser_snapshot` или `browser_evaluate` для извлечения
   - Собрать всё в JSON

4. **Для каждой карточки:**
   - Title, company, location, salary, remote policy, apply_url
   - Применить title_filter
   - Dedup

5. **Для новых:**
   - Optional: open job detail page для full JD
   - Добавить в `pipeline.md`:
     ```
     - [ ] {url} | {company} | {title} | ${salary} | {remote_policy} | [hiring-cafe]
     ```

6. **Output:**

```
Hiring Cafe Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Queries: 5
Found: N total
Filtered: N relevant
Duplicates: N
New: N

  + {company} | {title} | ${salary} | REMOTE
  ...
```

## Search queries

```yaml
queries:
  - url: "https://hiring.cafe/?searchQuery=AI+Product+Manager&locationType=REMOTE"
    label: "AI Product Remote"
  - url: "https://hiring.cafe/?searchQuery=Head+of+Product&seniority=senior"
    label: "Head of Product Senior+"
  - url: "https://hiring.cafe/?searchQuery=VP+Product&locationType=REMOTE"
    label: "VP Product Remote"
  - url: "https://hiring.cafe/?searchQuery=CPO+Chief+Product+Officer"
    label: "CPO"
  - url: "https://hiring.cafe/categories/ai-ml"
    label: "AI/ML category"
```

## Hiring Cafe-specific notes

- **Freshness** — большинство вакансий добавляются за неделю, reposted rate высокий
- **Remote policy** обязательно парсить: `Fully Remote`, `Remote US`, `Remote Europe`, `Hybrid`, `Onsite` — влияет на fit
- **Зарплата** — обычно in USD, иногда с ranges типа `$150K-$200K`, парсить через regex
- **Visa sponsorship** flag — если есть, сохранять (уникальная фича)
- **Company size** — filter полезен, маленькие компании = больше влияние на продукт
- **Анти-bot** — лёгкая проверка, Playwright с реальным browser fingerprint проходит без проблем
- **Rate limit** — нет официального, но не более 1 query в 2 секунды из вежливости
