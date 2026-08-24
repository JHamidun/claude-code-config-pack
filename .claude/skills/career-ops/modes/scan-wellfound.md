# Modo: scan-wellfound — Wellfound Scanner (AngelList Talent, Startups)

Сканирует Wellfound (бывший AngelList Talent) через Playwright. Золото для AI-first стартапов на seed/Series A/B, где CPO/VP Product ищут founders.

## Почему Wellfound критичен

- **Стартапы ищут C-level явно** — "Co-founder", "Founding PM", "Head of Product" — роли, которых нет на Indeed/LinkedIn
- **AI-first heavy** — много YC, a16z, OpenAI-fund компаний
- **Прозрачность equity** — показывают vesting, % equity в листинге
- **Фильтр по стадии** — seed / series A / series B
- **Нет спам-рекрутеров** — founders пишут напрямую

## Ограничения

- **Нет публичного API** (был GraphQL, закрыт в 2023)
- **Требует аккаунт** для полного доступа — без логина видно только первые 10-20 вакансий
- **Cloudflare-защита** — нужен Playwright с реальным browser fingerprint, не raw HTTP

## Stratgeia доступа

### Вариант 1 — Публичный поиск (без логина)

URL: `https://wellfound.com/jobs?roles=product-manager&remote=true`

Фильтры через query params:
- `roles=product-manager` | `product-manager-lead` | `head-of-product`
- `remote=true`
- `company_size=1-10` | `11-50` | `51-200` | `201-500`
- `stage=Seed` | `Series A` | `Series B`
- `salary_min=120000`

**Playwright workflow:**
1. `browser_navigate` → URL
2. `browser_snapshot` → получить структуру
3. Scroll для lazy-load (Wellfound использует infinite scroll)
4. Извлечь job cards: `[role="article"]`, внутри — title, company, salary, location, tags

### Вариант 2 — С логином (полный доступ)

Сохранить cookies после первого логина в `~/.claude/cookies/wellfound.json`, затем:

```
browser_context.add_cookies(...)
browser_navigate("https://wellfound.com/jobs")
```

## Search queries

```yaml
queries:
  - "https://wellfound.com/jobs?roles=product-manager&remote=true&salary_min=120000"
  - "https://wellfound.com/jobs?roles=head-of-product&remote=true"
  - "https://wellfound.com/jobs?roles=vp-of-product&remote=true"
  - "https://wellfound.com/jobs?roles=chief-product-officer&remote=true"
  - "https://wellfound.com/jobs?industries=artificial-intelligence&roles=product-manager"
  - "https://wellfound.com/jobs?industries=machine-learning&roles=product-manager"
  # Founding roles — уникальны для startups
  - "https://wellfound.com/jobs?roles=founding-product-manager"
```

## Workflow

1. **Read config**: `portals.yml` → `wellfound` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Для каждой query:**
   - `browser_navigate` через Playwright MCP
   - `browser_snapshot` для структуры
   - Scroll до конца страницы (или 3-5 раз для infinite scroll)
   - Извлечь все job cards

4. **Для каждой карточки:**
   - Title, company, location, salary range, equity %, company stage, company size
   - URL через `href` атрибут
   - Dedup против history

5. **Для новых:**
   - `browser_navigate` на job page → извлечь full JD
   - Добавить в `pipeline.md` с меткой `[wellfound][{stage}]`:
     ```
     - [ ] {url} | {company} | {position} | ${salary} + {equity}% | {stage}
     ```

6. **Output:**

```
Wellfound Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Queries: 7
Found: N total
Filtered: N relevant
Duplicates: N
New: N

  + {company} [{stage}] | {position} | ${salary} + {equity}%
  ...
```

## Wellfound-specific notes

- **Equity критична** — всегда указывать в pipeline (1% vs 0.1% — огромная разница)
- **Stage сигнал** — Seed = риск, Series A/B = sweet spot, Series C+ = scale-up
- **Company size < 50** = ранняя стадия, влияние на продукт выше
- **"Founding" в title** = co-founder equity (1-5% typically)
- **Cloudflare блок** — если `browser_navigate` возвращает challenge page → подождать 5 сек и повторить
- **Rate limit** — не более 1 запроса в 3 секунды, иначе IP блок на сутки
