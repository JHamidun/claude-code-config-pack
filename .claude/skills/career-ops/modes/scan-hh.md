# Modo: scan-hh -- hh.ru Scanner (Russian Job Market)

Сканирует hh.ru через публичный API, фильтрует по релевантности, добавляет в pipeline.

## hh.ru API

**Base URL:** `https://api.hh.ru`

### Search vacancies
```
GET /vacancies?text={query}&area={area_id}&salary={min}&per_page=100&page=0
```

**Key parameters:**
- `text` -- search query (supports boolean: `AND`, `OR`, `NOT`, quotes for exact match)
- `area` -- region ID: 1 (Moscow), 2 (SPb), 113 (Russia), 1001 (Other regions), 6 (Remote available via schedule)
- `salary` -- minimum salary
- `currency` -- RUR, USD, EUR
- `only_with_salary` -- true/false
- `experience` -- noExperience, between1And3, between3And6, moreThan6
- `schedule` -- fullDay, shift, flexible, remote, flyInFlyOut
- `employment` -- full, part, project, volunteer, probation
- `professional_role` -- numeric role IDs (96=PM, 160=Analyst, 10=Programmer, etc.)
- `per_page` -- up to 100
- `order_by` -- relevance, publication_time, salary_desc, salary_asc

### Get vacancy details
```
GET /vacancies/{id}
```

Returns full JD with: name, description (HTML), key_skills, salary, employer, area, schedule, experience, employment.

### Response structure
```json
{
  "items": [
    {
      "id": "123456",
      "name": "CPO / Head of AI Product",
      "url": "https://api.hh.ru/vacancies/123456",
      "alternate_url": "https://hh.ru/vacancy/123456",
      "salary": { "from": 500000, "to": 800000, "currency": "RUR" },
      "employer": { "name": "Company Name", "url": "..." },
      "snippet": { "requirement": "...", "responsibility": "..." },
      "schedule": { "id": "remote", "name": "Удалённая работа" },
      "experience": { "id": "moreThan6", "name": "Более 6 лет" },
      "area": { "id": "1", "name": "Москва" },
      "published_at": "2026-04-05T10:00:00+0300"
    }
  ],
  "found": 42,
  "pages": 1,
  "per_page": 100
}
```

## Workflow

1. **Read config**: `portals.yml` → `hh` section
2. **Read dedup**: `data/scan-history.tsv` + `data/applications.md` + `data/pipeline.md`

3. **For each search query in hh config:**
   a. Build API URL with parameters
   b. `WebFetch` the API endpoint (JSON response, no auth needed)
   c. Parse items, extract: id, name, company, salary, url, schedule, experience
   d. Apply title_filter (positive/negative keywords)
   e. Dedup against history

4. **For each new relevant vacancy:**
   a. Optionally fetch full JD via `/vacancies/{id}` for key_skills and full description
   b. Add to `pipeline.md`: `- [ ] https://hh.ru/vacancy/{id} | {company} | {title} | {salary}`
   c. Register in `scan-history.tsv`

5. **Output summary:**
```
hh.ru Scan -- {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Queries: N
Found: N total
Filtered by title: N relevant
Duplicates: N
New added to pipeline: N

  + {company} | {title} | {salary} RUR | remote
  ...

→ Run /career-ops pipeline to evaluate new offers.
```

## hh.ru-specific evaluation notes

When evaluating hh.ru vacancies:
- **Salary**: hh.ru shows gross (до вычета НДФЛ). Net = salary * 0.87
- **Schedule**: "Удалённая работа" = fully remote, "Гибкий график" = flexible
- **Key skills**: hh.ru has structured skills -- use for keyword matching
- **Company page**: `https://hh.ru/employer/{employer_id}` for reviews and info
- **Response letter**: hh.ru has a cover letter field -- always fill it
- **Tests**: some vacancies require completing a test before applying

## Title filter (Russian keywords)

Add to `portals.yml` title_filter:
```yaml
positive_ru:
  - "CPO"
  - "Chief Product"
  - "VP Product"
  - "Директор по продукту"
  - "Руководитель продукта"
  - "Head of Product"
  - "AI"
  - "ИИ"
  - "ML"
  - "Искусственный интеллект"
  - "Машинное обучение"
  - "Product Manager"
  - "Продуктовый менеджер"
  - "Продакт-менеджер"
negative_ru:
  - "Стажёр"
  - "Junior"
  - "Младший"
  - "Ассистент"
```
