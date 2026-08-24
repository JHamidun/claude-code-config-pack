# Modo: analyze-skills — Skill Frequency Analysis for ATS Optimization

Анализирует частоту ключевых скиллов в вакансиях (и опционально в резюме топов) под целевую роль. Используется для ATS-оптимизации CV — какие keywords добавить чтобы не отсеяли алгоритмом и попасть к живому HR.

**Inspired by:** 2r.ru (top-skills-and-resumes) — берёт идею частотного анализа. **Upgrade:** анализирует **employer-side** требования (что просят), а не candidate-side (что у других есть) → лучший сигнал для ATS.

## Зачем

ATS-системы (HR Assistant, Поток, hh.ru auto-screen) фильтруют резюме по keyword-match. Кандидат с релевантным опытом, но без правильных слов → отсев на первом шаге. Этот мод:
1. Берёт целевую роль (e.g. "Head of Product AI")
2. Скрейпит N вакансий с hh.ru
3. Извлекает `key_skills` из каждой
4. Строит частотный рейтинг
5. Сравнивает с твоим CV → показывает какие добавить

## Workflow

### 1. Read inputs

- `~/career-ops/config/profile.yml` — target roles, location
- `~/career-ops/cv.md` — твои текущие skills
- Аргумент команды — target role (override profile)

### 2. Search hh.ru vacancies

Используем public API hh.ru:
```
GET https://api.hh.ru/vacancies?text={role}&area={area}&per_page=100&page=0
```

Параметры по умолчанию:
- `text` = target role string (e.g. "CPO AI" or "Head of Product")
- `area` = 113 (Russia) или 1001 (Other) или 1 (Moscow)
- `per_page` = 100
- Загрузить 3-5 страниц → 300-500 вакансий

### 3. Fetch full JD для каждой вакансии

Для каждой `id` в результатах:
```
GET https://api.hh.ru/vacancies/{id}
```

Извлечь:
- `key_skills[]` — список структурированных скиллов (важнее всего)
- `description` (HTML) — для extraction unstructured keywords
- `professional_roles[]` — official role codes
- `experience` — required level
- `employer.name` — для дедупликации

**Rate limit discipline:** hh.ru — 5 req/sec max, 200ms delay между запросами. На 300 вакансий = 60 секунд.

### 4. Tabulate skill frequency

Из `key_skills[]`:

```python
from collections import Counter
skill_counts = Counter()
for vacancy in vacancies:
    for skill in vacancy.get('key_skills', []):
        normalized = skill['name'].lower().strip()
        skill_counts[normalized] += 1
```

Из `description` — bonus extraction для unstructured keywords (опционально):
- Стек: Python, SQL, Tableau, Figma, JIRA, AWS, Docker, etc.
- Методологии: Agile, Scrum, OKR, Jobs-to-be-Done, Lean
- Софт-скиллы: stakeholder management, cross-functional, mentoring

Использовать NER (named entity recognition) или простой regex-based whitelist из `~/.claude/skills/career-ops/templates/skill-dictionary.yml`.

### 5. Cross-check with CV

Прочитать `cv.md`, извлечь skills section. Сравнить с топ-50:

```
TOP REQUESTED SKILLS (n=300 vacancies for "Head of Product AI")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rank  Skill                          Freq    %     In CV?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1    Product Management              247    82%    ✓
 2    Agile                           198    66%    ✓
 3    Stakeholder Management          187    62%    ✓
 4    Roadmap Planning                176    59%    ✓
 5    AI/ML Product Strategy          165    55%    ✗ ← ADD
 6    OKR                             142    47%    ✗ ← ADD
 7    Data-Driven Decision Making     138    46%    ✓
 8    Jobs-to-be-Done                 124    41%    ✗ ← ADD
 9    A/B Testing                     119    40%    ✓
10    Customer Development            115    38%    ✗ ← ADD
...
```

### 6. Recommendations

Output structured advice:

```markdown
## Skills Gap Analysis — Head of Product AI

### Critical adds (>50% frequency, not in CV)
- AI/ML Product Strategy (55%)
- OKR (47%)

### Recommended adds (30-50% frequency, not in CV)
- Jobs-to-be-Done (41%)
- Customer Development (38%)
- Product Discovery (34%)

### Already covered (>30% frequency, in CV)
- Product Management, Agile, Stakeholder Management, Roadmap Planning, A/B Testing

### Low-priority adds (<30%, optional)
- Mixpanel, Amplitude, JIRA, Confluence

### Suggested CV edits
1. Add "AI/ML Product Strategy" to top skills section
2. Replace "KPIs" → "OKR" in achievements
3. Add bullet: "Led product discovery using Jobs-to-be-Done framework..."
```

### 7. Save report

`~/career-ops/reports/skill-analysis-{role-slug}-{YYYY-MM-DD}.md`

Также обновить `~/career-ops/data/skill-frequency-history.tsv`:
```tsv
date	role	area	vacancies_n	top10_skills	cv_match_percent
2026-04-12	<твоя роль>	1001	327	"product mgmt|agile|..."	68
```

## Бонус: открытые резюме топов (advanced)

Если у тебя есть доступ к hh.ru Open Resume Search API (выдаётся аккаунтам работодателя,
обычному соискателю — нет; проверь в кабинете разработчика hh):

1. Поиск открытых резюме по той же specialty + seniority
2. Извлечь skills из топ-50 (по релевантности / зарплате)
3. Compare с CV пользователя
4. Найти "what they have, you don't" gap

**Caveat:** показывает что у конкурентов, но это слабее сигнал чем что просят работодатели. Использовать как secondary.

## Commands

```
/career-ops analyze-skills "Head of Product"
/career-ops analyze-skills "AI Product Manager" --area 1001
/career-ops analyze-skills --from-profile        # читает target_roles из profile.yml
/career-ops analyze-skills --include-resumes     # доп. анализ открытых резюме
/career-ops analyze-skills --vs-cv               # сравнить с текущим cv.md (default ON)
```

## Integration с другими модами

- **Перед `pdf`** — анализировать вакансию + roles из profile → автоматически добавлять missing keywords в tailored PDF
- **После `scan`** — после набора вакансий в pipeline, анализировать их совокупно для master CV
- **Перед `evaluate`** — показывать gap по конкретной вакансии (что добавить если решит подавать)

## Russian vs English skills

hh.ru `key_skills` — на русском и английском вперемешку. Нормализация:
- "Управление продуктом" / "Product Management" → один кластер
- "Аналитика данных" / "Data Analysis" → один кластер
- Использовать `templates/skill-aliases.yml` для маппинга

Output: показывать обе версии — для русских вакансий писать RU, для международных — EN.
