---
name: career-ops
description: "Поиск работы: скан hh.ru/LinkedIn/ATS, резюме под вакансию, оценка офферов, подготовка к собесу. Триггеры: «вакансии». НЕ поиск кандидатов → headhunter."
user_invocable: true
trigger: "career-ops"
arguments: "[command] [args]"
---

# Career-Ops -- AI Job Search Pipeline

> Based on [santifer/career-ops](https://github.com/santifer/career-ops). Extended with hh.ru, LinkedIn, and Russian market support.

## Что понадобится

| Нужно | Платно? | Без этого |
|---|---|---|
| `~/career-ops/config/profile.yml` — твой профиль (кто ты, какие роли, вилка) | — | навык не запустится: все оценки считаются относительно ТВОИХ целей |
| `~/career-ops/cv.md` — твоё резюме | — | не будет Block B (CV match) и PDF |
| hh.ru API | бесплатно, без ключа | нет российского рынка |
| LinkedIn cookies в браузере | бесплатно | `scan linkedin` и `contact` деградируют до WebSearch |
| Adzuna `app_id` + `app_key` — https://developer.adzuna.com | free tier 250 запросов/день | нет `scan adzuna` (16 стран) |
| Gmail OAuth (`~/.claude/tools/gmail_search.py`) | бесплатно | нет `track` — статусы заявок обновляешь руками |
| Node + `npm i puppeteer` | бесплатно | нет генерации PDF |

Всё личное живёт **вне навыка** — в `~/career-ops/`. Сам навык твоих данных не хранит,
поэтому его можно обновлять поверх, не боясь потерять резюме.

## Commands

| Command | What it does |
|---------|-------------|
| `/career-ops` | Show this help |
| `/career-ops evaluate <url-or-text>` | Full A-F evaluation + report + PDF + tracker |
| `/career-ops scan` | Scan all enabled portals in parallel (10 сканеров, включаются в `portals.yml`) |
| `/career-ops scan hh` | hh.ru (Russia + CIS, API) |
| `/career-ops scan linkedin` | LinkedIn (global, cookies required) |
| `/career-ops scan remoteok` | RemoteOK (JSON API, global remote) |
| `/career-ops scan wwr` | We Work Remotely (RSS, global remote) |
| `/career-ops scan wellfound` | Wellfound / AngelList (startups, AI-first) |
| `/career-ops scan yc` | YC Work at a Startup (YC companies) |
| `/career-ops scan aijobs` | ai-jobs.net (pure AI/ML focus) |
| `/career-ops scan adzuna` | Adzuna API (16 countries incl. BR+RU, free tier) |
| `/career-ops scan hiringcafe` | Hiring Cafe (remote-first) |
| `/career-ops scan startupjobs` | startup.jobs (EU startups) |
| `/career-ops track` | Gmail auto-update статусов заявок (interview/rejected/offer) |
| `/career-ops pipeline` | Process pending URLs from pipeline.md |
| `/career-ops batch` | Batch process multiple offers |
| `/career-ops pdf <company>` | Generate ATS-optimized PDF for a specific offer |
| `/career-ops apply` | Live form-filling assistant (Playwright) |
| `/career-ops contact <company>` | LinkedIn/hh.ru outreach message generation |
| `/career-ops compare` | Side-by-side comparison of 2+ offers (`modes/ofertas.md`) |
| `/career-ops analyze-skills` | Частотный анализ требований по роли — какими словами её ищут |
| `/career-ops deep <company>` | Deep company research |
| `/career-ops tracker` | Show application status overview |
| `/career-ops training <url>` | Evaluate a course/certification |
| `/career-ops project <url>` | Evaluate a portfolio project idea |
| `/career-ops interview <company>` | Interview prep with STAR stories |
| `/career-ops setup` | Initial onboarding (CV, profile, portals) |

## Working Directory

All career-ops data lives in: `~/career-ops/`

```
~/career-ops/
  cv.md                    # Canonical CV (source of truth)
  article-digest.md        # Proof points and case studies
  portals.yml              # Portal scanner config (hh.ru + LinkedIn + global)
  config/
    profile.yml            # Candidate identity, targets, salary
  data/
    applications.md        # Application tracker
    pipeline.md            # Inbox of pending URLs
    scan-history.tsv       # Scanner dedup history
  reports/                 # Evaluation reports
  output/                  # Generated PDFs (gitignored)
  jds/                     # Saved job descriptions
  interview-prep/
    story-bank.md          # STAR+R stories across evaluations
  batch/
    tracker-additions/     # TSV files for merge
```

## First Run

If `~/career-ops/` doesn't exist or is missing key files, enter onboarding —
**пошагово он расписан в `modes/setup.md`, начинай оттуда** (там же готовые `cp` для
примеров конфигов и разбор, какой из двух `portals.example.yml` брать). Коротко:

1. Create directory structure
2. Ask for CV (paste, LinkedIn URL, or dictate)
3. Fill `config/profile.yml` (name, targets, salary, location) — из `config/profile.example.yml`
4. Configure `portals.yml` — из `config/portals.example.yml` (не из `templates/`, см. `modes/setup.md`)
5. Create empty tracker
6. Get to know the user for better evaluations

## Portal Strategy (3 tiers)

### Tier 1: hh.ru (Russian market)

**API-based scanning** via hh.ru public API:
- `GET https://api.hh.ru/vacancies?text={query}&area={area_id}&salary={min}&only_with_salary=true`
- Area IDs: 1 (Moscow), 2 (SPb), 113 (Russia), 1001 (Remote)
- Filters: experience, schedule (remote/flexible), salary
- Returns JSON with structured data (title, company, salary, requirements)

**Playwright scanning** for full JD extraction:
- Navigate to `hh.ru/vacancy/{id}` for complete description
- Extract: requirements, responsibilities, conditions, skills, salary

**hh.ru specific fields in profile.yml** (значения — твои, из `config/profile.yml`):
```yaml
hh:
  area_ids: [113, 1001]  # Russia + Remote
  experience: "moreThan6"  # noExperience, between1And3, between3And6, moreThan6
  schedule: ["remote", "flexible"]
  search_queries:        # 3-5 формулировок ТВОЕЙ роли, как её пишут в вакансиях
    - "<твоя роль>"
    - "<синоним роли>"
    - "<роль на уровень выше — для стретч-вакансий>"
  salary_from: <нижняя граница вилки>   # в валюте ниже
  currency: "RUR"
  only_with_salary: false
```

> Формулировки берутся не из головы: прогони `/career-ops analyze-skills`, он соберёт
> частотный словарь требований по твоей роли с hh.ru и покажет, какими словами её ищут.

### Tier 2: LinkedIn (Global + Russia)

**Scanning strategy:**
1. WebSearch with `site:linkedin.com/jobs` + role keywords
2. Playwright for authenticated browsing (if logged in)
3. LinkedIn skill `linkedin` for profile enrichment and outreach

**LinkedIn-specific features:**
- Generate connection request messages (300 char limit)
- Find hiring managers and recruiters
- Profile optimization suggestions per JD
- Easy Apply form assistance

### Tier 3: Global ATS (Ashby, Greenhouse, Lever, Wellfound, Workable)

Same as original career-ops. See `modes/scan.md` for details.

## Evaluation Pipeline (Blocks A-F)

When user pastes a JD or URL:

1. **Extract JD** (Playwright > WebFetch > WebSearch > ask user)
2. **Block A** -- Role Summary (archetype, domain, function, seniority, remote, TL;DR)
3. **Block B** -- CV Match (requirements vs cv.md, gap analysis with mitigation)
4. **Block C** -- Level & Strategy (detected vs natural level, up/down-level plan)
5. **Block D** -- Comp & Demand (WebSearch for salary data, market trends)
6. **Block E** -- Personalization Plan (CV changes, LinkedIn changes)
7. **Block F** -- Interview Plan (6-10 STAR+R stories mapped to JD requirements)
8. **Block G** -- Draft Application Answers (if score >= 4.0)
9. **Save report** to `reports/`
10. **Generate PDF** (ATS-optimized, keyword-injected)
11. **Update tracker**

## Language Rules

- **JD in English** -> evaluation in English, CV in English
- **JD in Russian** -> evaluation in Russian, CV in Russian (separate template)
- **hh.ru** -> always Russian evaluation, but English CV option if company is international
- **LinkedIn** -> follow JD language
- Code and technical terms: always English

## Scoring

Score 1-5 based on:
- Role-archetype match (weight: 30%)
- Technical requirements match (weight: 25%)
- Seniority alignment (weight: 15%)
- Comp vs target (weight: 15%)
- Remote/location fit (weight: 10%)
- Growth potential (weight: 5%)

| Score | Recommendation |
|-------|---------------|
| 4.5-5.0 | Strong match -- auto-generate draft answers |
| 4.0-4.4 | Good match -- recommend applying |
| 3.5-3.9 | Decent -- apply if strategic reasons |
| 3.0-3.4 | Weak -- probably skip |
| < 3.0 | Skip -- don't waste time |

## PDF Generation

Uses `generate-pdf.mjs` (Puppeteer HTML->PDF):
```bash
node ~/.claude/skills/career-ops/generate-pdf.mjs input.html output.pdf --format=a4
```

Fonts: Space Grotesk (headings) + DM Sans (body). Single-column ATS layout.

## Ethical Rules

- **NEVER submit without user review** -- fill forms, draft answers, generate PDFs, but STOP before Submit
- **Discourage low-fit applications** (score < 3.5)
- **Quality over quantity** -- 5 targeted > 50 generic
- **NEVER invent experience or metrics**
- **NEVER modify cv.md without explicit permission**

## Integration with Existing Skills

| Need | Use |
|------|-----|
| LinkedIn research | Skill `linkedin` (ScrapeCreators) |
| Company research | Skill `account-research` |
| Deep web research | Command `/deep-research` (Perplexity) / Skill `last30days` |
| Interview prep video | Skill `heygen` (avatar practice) |
| Outreach emails | Skill `draft-outreach` |
| Telegram job channels | `python ~/.claude/tools/tg_client.py search "<запрос>"` |

> Этот навык — про **твоё** трудоустройство: ты кандидат. Обратная задача (искать
> кандидатов, читать чужие резюме) в пак не входит — там чужие персональные данные.

## Files Reference

| File | Purpose |
|------|---------|
| `modes/_shared.md` | Shared context, archetypes, scoring |
| `modes/oferta.md` | Full A-F evaluation |
| `modes/scan.md` | Portal scanner |
| `modes/apply.md` | Live form-filling |
| `modes/contacto.md` | LinkedIn outreach |
| `modes/pdf.md` | PDF generation |
| `modes/auto-pipeline.md` | Auto-detect and run full pipeline |
| `modes/batch.md` | Batch processing |
| `modes/pipeline.md` | Process pending URLs |
| `modes/deep.md` | Company deep research |
| `modes/tracker.md` | Tracker management |
| `modes/ofertas.md` | Compare multiple offers |
| `modes/training.md` | Evaluate courses |
| `modes/project.md` | Evaluate portfolio projects |
| `modes/analyze-skills.md` | Частотный анализ требований по роли (что писать в CV) |
| `modes/interview.md` | Interview prep, STAR+R story bank |
| `modes/setup.md` | Первый запуск: создать `~/career-ops/`, CV, профиль, порталы |
| `templates/cv-template.html` | HTML CV template |
| `templates/portals.example.yml` | Portal config example |
| `templates/states.yml` | Canonical application states |
