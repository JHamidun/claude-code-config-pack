# Modo: scan-remoteok — RemoteOK Scanner (Global Remote)

Сканирует RemoteOK через их публичный JSON API. Нет auth, нет rate limit, идеально для автоматизации.

## API

**Endpoint:** `https://remoteok.com/api`

Возвращает массив JSON с первым элементом-метаданными (его пропустить) и далее вакансиями:

```json
[
  { "legal": "See remoteok.com/legal" },
  {
    "id": "987654",
    "slug": "company-role-slug",
    "epoch": 1712345678,
    "date": "2026-04-05T10:00:00+00:00",
    "company": "Acme AI",
    "company_logo": "https://...",
    "position": "Head of Product",
    "tags": ["product", "senior", "ai", "remote"],
    "logo": "...",
    "description": "<p>HTML description...</p>",
    "location": "Worldwide",
    "salary_min": 120000,
    "salary_max": 220000,
    "apply_url": "https://remoteok.com/remote-jobs/987654",
    "url": "https://remoteok.com/remote-jobs/987654"
  },
  ...
]
```

Единичный endpoint, возвращает ~100 последних. Для более полного покрытия — фильтр по тэгам:
`https://remoteok.com/api?tags=product,ai`
`https://remoteok.com/api?tags=senior,exec`

## Workflow

1. **Read config**: `portals.yml` → `remoteok` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Fetch с разных тэгов** (каждый запрос — отдельный WebFetch):
   - `?tags=product,ai`
   - `?tags=product,senior`
   - `?tags=exec,remote`
   - `?tags=cpo`
   - `?tags=ai,ml` (для AI Product ролей)

4. **Для каждой вакансии:**
   - Пропустить первый элемент (metadata)
   - Извлечь: `id`, `position`, `company`, `salary_min/max`, `tags`, `url`, `description`
   - Применить title_filter (positive/negative)
   - Dedup против `scan-history.tsv` по `id`

5. **Для каждой новой релевантной:**
   - Добавить в `pipeline.md`: `- [ ] {url} | {company} | {position} | ${salary_min}-${salary_max}`
   - Записать в `scan-history.tsv`

6. **Output:**

```
RemoteOK Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Queries: 5
Found: N total
Filtered by title: N relevant
Duplicates: N
New added to pipeline: N

  + {company} | {position} | ${salary_min}-${salary_max}
  ...
```

## Title filter

```yaml
positive_en:
  - "CPO"
  - "Chief Product"
  - "VP Product"
  - "VP of Product"
  - "Head of Product"
  - "Head of AI"
  - "Director of Product"
  - "AI Product"
  - "Product Lead"
  - "Senior Product Manager"
  - "Principal Product"
negative_en:
  - "Intern"
  - "Junior"
  - "Associate"
  - "Marketing"
  - "Sales"
  - "Customer Success"
```

## RemoteOK-specific notes

- Описания в HTML — конвертировать в plain text для pipeline
- Зарплаты часто отсутствуют (null) — не отбрасывать
- `apply_url` может редиректить на внешний ATS (Ashby, Lever, Greenhouse) — это нормально
- Теги структурированы — использовать для дополнительного скоринга (наличие "ai" + "senior" = буст)
- Все вакансии — remote (по определению)
- Локация `Worldwide` / `Americas` / `Europe` — важна для timezone-совместимости
