# Modo: scan-linkedin -- LinkedIn Job Scanner

Сканирует LinkedIn Jobs через WebSearch и Playwright, находит вакансии и генерирует outreach.

## Strategy

LinkedIn Jobs не имеет публичного API для поиска вакансий. Стратегия:

### Level 1 -- WebSearch (primary)

```
WebSearch: site:linkedin.com/jobs "CPO" OR "Head of AI" OR "VP Product" remote
WebSearch: site:linkedin.com/jobs "AI Product" OR "Chief Product Officer" Moscow OR remote
```

Extracts: title, company, location from search results.

### Level 2 -- Playwright (authenticated, if logged in)

If user has LinkedIn session in browser:
1. `browser_navigate` to `https://www.linkedin.com/jobs/search/?keywords={query}&location={location}`
2. `browser_snapshot` to read job cards
3. Extract: title, company, location, posted date, applicant count
4. Click into each relevant listing for full JD

### Level 3 -- ScrapeCreators LinkedIn skill

Use existing `linkedin` skill for:
- Company page enrichment
- Hiring manager identification
- Profile enrichment for outreach

## Workflow

1. **Read config**: `portals.yml` → `linkedin` section
2. **Read dedup sources**

3. **Execute WebSearch queries** from config
4. **Filter by title** (same keywords as global + Russian variants)
5. **Dedup against history**

6. **For each new vacancy:**
   - Add to `pipeline.md`
   - If score seems high (by title): fetch full JD via Playwright
   - Register in `scan-history.tsv`

7. **Output summary**

## LinkedIn outreach (post-evaluation)

After evaluation, if score >= 4.0:
1. Find hiring manager via WebSearch: `site:linkedin.com/in "{company}" "{role}" hiring manager`
2. Find recruiter: `site:linkedin.com/in "{company}" recruiter talent acquisition`
3. Generate connection request (300 chars max):

**Template (EN):**
```
Hi {name} — saw the {role} opening at {company}. I've been building AI products (led {metric} at {company}) and your team's approach to {specific} caught my eye. Would love to connect.
```

**Template (RU):**
```
Привет, {name} — увидел позицию {role} в {company}. Последние N лет строил AI-продукты ({metric}). Подход вашей команды к {specific} зацепил. Буду рад пообщаться.
```

## LinkedIn-specific notes

- **Easy Apply**: some vacancies allow applying directly -- use `modes/apply.md` workflow
- **Connection request limit**: 300 characters
- **InMail**: available with Premium, longer messages
- **Profile optimization**: generate per-JD suggestions in Block E of evaluation
- **"Open to Work" banner**: discuss with user whether to enable
- **Applicant count**: visible on some listings -- low count = higher chance
