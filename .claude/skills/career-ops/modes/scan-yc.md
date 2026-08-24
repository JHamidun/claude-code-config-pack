# Modo: scan-yc — YC Work at a Startup Scanner

Сканирует Y Combinator Work at a Startup — вакансии всех YC-компаний (W10–W26), самых ранних AI стартапов.

## Почему YC важен

- **Самое плотное AI-покрытие** — каждый YC-батч с W23 содержит 30-50% AI-first компаний
- **Early access** — вакансии публикуются до того, как компании становятся известны
- **Founding roles** — часто founders ищут co-founders через этот канал
- **Качество фильтра** — если компания в YC, у неё уже есть funding + mentorship
- **Прозрачность** — указывают stage, team size, total funding, location

## Ограничения

- **Требует логин через YC account** для полного поиска (но можно Google/LinkedIn SSO)
- **Публичная страница компании** доступна всем без логина
- **Нет API** — только HTML через Playwright

## Strategy доступа

### Вариант 1 — Публичные страницы (без логина)

Каждая YC-компания имеет публичную страницу:
`https://www.ycombinator.com/companies/{slug}`

На ней есть секция "Jobs" с текущими открытыми ролями.

### Вариант 2 — Work at a Startup (требует логин)

`https://www.workatastartup.com/jobs?role_types=product&remote_only=true`

Фильтры:
- `role_types=product` | `eng_management`
- `remote_only=true`
- `salary_min=120000`
- `stage=seed` | `series_a` | `series_b`
- `funding=series_a`

### Вариант 3 — Список YC компаний по батчу + manual scan

`https://www.ycombinator.com/companies?batch=W26&industry=AI`

Это даёт список компаний — далее для каждой открыть careers страницу.

## Search queries

```yaml
queries:
  # Основной поиск
  - "https://www.workatastartup.com/jobs?role_types=product&remote_only=true"
  - "https://www.workatastartup.com/jobs?role_types=product&remote_only=false&salary_min=140000"
  - "https://www.workatastartup.com/jobs?role_types=eng_management&remote_only=true"
  # Фильтры по батчам (свежие YC)
  - "https://www.ycombinator.com/companies?batch=W26&industry=AI"
  - "https://www.ycombinator.com/companies?batch=S25&industry=AI"
  - "https://www.ycombinator.com/companies?batch=W25&industry=Artificial+Intelligence"
```

## Workflow

1. **Read config**: `portals.yml` → `yc` section

2. **Два уровня обхода:**

   **A) Work at a Startup (если есть cookies):**
   - `browser_navigate` → query URL
   - Scroll, извлечь job cards
   - Для каждой: title, company, YC batch, salary, location, tags

   **B) YC Companies directory (публично):**
   - `browser_navigate` → `/companies?batch=W26&industry=AI`
   - Извлечь список компаний
   - Для каждой → `/companies/{slug}` → секция Jobs
   - Если есть открытые позиции продукта/менеджмента → добавить

3. **Для каждой релевантной вакансии:**
   - Добавить в `pipeline.md` с меткой `[yc][{batch}]`:
     ```
     - [ ] {url} | {company} [{batch}] | {position} | ${salary}
     ```

4. **Output:**

```
YC Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: Work at a Startup / Companies directory
Batches scanned: W26, S25, W25
Companies checked: N
Found: N vacancies
Filtered: N relevant
Duplicates: N
New: N

  + {company} [W26] | {position} | ${salary}
  ...
```

## YC-specific evaluation notes

- **Batch сигнал:**
  - W26 / S25 (свежие) — максимальный рост, высокий риск
  - W23 / S22 — стадия Series A/B, sweet spot
  - Старые батчи (до 2020) — уже крупные компании (Stripe, Airbnb, DoorDash)
- **Company page метрики** — team size, HQ location, status (active/acquired/public)
- **Founding roles** — часто 1-5% equity
- **Industry tag AI / Artificial Intelligence / ML** — прямой фильтр на AI-first
- **Funding stage влияет на зарплату**: Seed = $150-200K, Series A = $200-280K, Series B+ = $280K+
- **Remote policy** — многие YC компании теперь hybrid (SF 3 дня/неделю), проверять отдельно
