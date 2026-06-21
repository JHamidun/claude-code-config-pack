---
name: lead-enrichment
description: "Enrich and qualify B2B leads for the Russian market — two modes. Mode A (digital-trace qualification): given a fragment a lead left (email, phone, full name, @username, domain, UTM), figure out who the person is, which company, whether they are a decision-maker, their fit and how to reach them. Mode B (list enrichment): take a raw company/contact list (Excel/CSV) plus a Bitrix24 export, match by INN, pull legal/firmographic data (DaData, EGRUL, Rusprofile/Checko), find decision-makers (LinkedIn/HH/socials), score by tier, and package a multi-sheet enriched Excel. Reuses bitrix24, social-intel, linkedin, headhunter, maps-places, lead-research, perplexity. Trigger with: дообогати базу, обогати лиды, обогати список, квалифицируй контакт, кто оставил заявку, пробей по цифровому следу, кто этот человек по email/телефону, enrich leads, lead qualification, matched against Bitrix, checko, egrul, ЕГРЮЛ, DaData фирмографика. NOT for writing outreach copy (see draft-outreach), building a list from scratch by ICP (see lead-research), or pure social dossier when you already have the handle (see social-intel)."
allowed-tools: Bash, Read, Write, WebSearch, WebFetch, Skill
metadata:
  version: 1.0.0
  reuses: bitrix24, social-intel, linkedin, headhunter, maps-places, lead-research, perplexity, draft-outreach, call-prep
---

# Lead Enrichment (RU)

Engine for enriching and qualifying B2B leads on the Russian market. Two modes share the same connectors (firmographics, CRM-match, decision-maker lookup) and the same scoring/lineage discipline.

- **Mode A — digital-trace qualification.** Reverse path: a fragment → a person + company + verdict. Answers "who left us this trace and is it worth a salesperson's time?"
- **Mode B — list enrichment.** Forward path: a raw list + Bitrix export → a scored, segmented, multi-sheet Excel ready to call.

## When to Use

- "дообогати базу", "обогати список / лиды", "обогати контакты для обзвона" → **Mode B**
- "квалифицируй контакт", "кто оставил заявку", "пробей по цифровому следу", "кто этот человек по email/телефону", "понять что за человек" → **Mode A**
- Before a call (`call-prep`) or outreach (`draft-outreach`) when only a fragment is known
- Matching an external company list against your Bitrix24 base by INN

Do NOT use for: writing the outreach message (`draft-outreach`), building a fresh list from an ICP definition (`lead-research`), or a social-only dossier when the handle is already known (`social-intel`).

## Compliance (read once, applies to both modes)

Public and official sources only. Legal basis: the lead left *us* a trace, or the data is public B2B firmographics.

- Sources: corporate email → company → EGRUL/DaData; full name → LinkedIn/HH/public socials; phone → operator/region + match in **your own** Bitrix; phones/emails published on the company site, 2GIS, Yandex Business; a phone the lead gave you → consented Telegram resolve (their own privacy setting governs).
- For every enriched field, record **source + date** (152-ФЗ lineage). ≥2 independent sources = High confidence.
- For a B2B lead, focus on *which company, what role, what budget* — that is what qualification needs.

## Prerequisites

```bash
# Firmographics (Mode A company-leg + Mode B): DaData primary, EGRUL fallback (both supported)
grep DADATA_API_KEY ~/.claude/.credentials.master.env   # optional; EGRUL works key-free
grep SCRAPECREATORS_API_KEY ~/.claude/.credentials.master.env  # LinkedIn/socials (via social-intel/linkedin skills)
pip install openpyxl requests rapidfuzz phonenumbers  # build/match deps
```

---

## Mode A — Digital-trace qualification

Goal: from a fragment, produce a one-page dossier + a verdict (qualify / hand to manager / drop) in a few minutes.

### Pipeline

```
1. normalize_input.py "<fragment>"   → identifiers (type, normalized value, derived: domain, inn-candidate, name variants)
2. Route by type:
   - corporate email / domain  → domain_to_company.py → INN → firmographics (step 4)
   - free email (gmail/ya/mail) → treat as individual: use name + WebSearch
   - phone                      → phone_lookup.py (operator/region) + check OUR Bitrix.
                                   If the lead GAVE you this number (inbound): phone_identify.py → Telegram native
                                   resolve (consented, respects their privacy) + web/CRM.
   - full name                  → WebSearch + social-intel + headhunter
   - @username / social url     → social-intel (forward dossier)
3. Person leg (public): social_discover.py → cross-network plan (VK/Сетка/TenChat/MAX/Telegram/OK + Western). Run its programmatic connectors (max-messenger, telegram, headhunter, social-intel) + WebSearch site: queries; WebFetch found profiles. See references/social-channels-ru.md.
4. Company leg: dadata_lookup.py <inn|name>  (or egrul_lookup.py)  → ИНН, ОГРН, гендир, выручка, численность, ОКВЭД, статус, аффилированность.
5. CRM cross: bitrix_match.py with a 1-row list, or query bitrix24 by email/phone/INN → existing deals, touches, manager, duplicate/reanimation flag.
6. Signals: recent posts/interviews/talks (social-intel, perplexity) → what they care about, what they react to.
7. Score: confidence "who is this" (1-10) + product-fit + reachability (references/scoring.md).
8. Output: write a dossier MD (assets/dossier-template below) + optional one-row xlsx via build_enriched_xlsx.py.
```

### Quick start

```bash
SK=~/.claude/skills/lead-enrichment/scripts
python $SK/normalize_input.py "i.ivanov@example-corp.ru"  # → {type:email, domain:example-corp.ru, ...}
python $SK/domain_to_company.py example-corp.ru           # → INN candidates from site/whois
python $SK/dadata_lookup.py 7707083893                     # → full firmographic card (JSON)
python $SK/phone_lookup.py "+7 916 123-45-67"              # → operator + region (no PII)
```

Then drive the public person/social research with the `social-intel`, `linkedin`, `headhunter` skills, and score per `references/scoring.md`. Emit the dossier using the template at the end of this file.

---

## Mode B — List enrichment (list × Bitrix pipeline)

Goal: raw list + Bitrix export → scored, segmented, multi-sheet enriched Excel.

### Pipeline (deterministic — low freedom, follow exactly)

```
1. Parse input list → normalize INNs/names → list.json  (rows: {name, inn, ul, phone, email, rev2024, segment, ...})
2. Export Bitrix24 → bitrix_data.json   (see references/bitrix-export.md; uses the bitrix24 skill)
3. python scripts/bitrix_match.py list.json bitrix_data.json   → matches_by_inn.json   (INN exact + fuzzy name via rapidfuzz)
4. python scripts/bitrix_aggregate.py bitrix_data.json matches_by_inn.json → aggregated.json
       (per company: touches, products, stages, last_touch, days_since, managers, contacts)
5. Firmographic fill for rows missing data:
       python scripts/firmographics_batch.py list.json --out firmographics.json   (DaData→EGRUL fallback, cached, 3 workers)
6. Decision-maker enrichment for Tier S/A: Skill linkedin / headhunter / social-intel → linkedin.json
7. Deep dossier (optional, priority queue): python scripts/research_companies.py aggregated.json  (Perplexity pro, cached by INN, 3 workers)
8. Tier model: S = active Bitrix history; A = cold, ranked by revenue; B = in Bitrix, no touches.
9. python scripts/build_enriched_xlsx.py --out "Enriched.xlsx"   → multi-sheet workbook (references/excel-schema.md)
```

### Tier model

| Tier | Definition | Action |
|------|------------|--------|
| **S** | In Bitrix WITH active touches/deals | Reanimate / continue with existing manager |
| **A** | Cold (not in Bitrix), ranked by 2024 revenue | Priority cold outreach |
| **B** | In Bitrix as a card, no touches | Light touch / verify |

### Output workbook (default sheets)

`Пересечения` (summary) · `Готовый обзвон` · `Активные сделки` · `Продажи и провалы` · `Холодняк (нет в базе)` · `Реанимация (90+ дней)` · `LinkedIn ЛПР` · `Глубокий рисёрч` · `Касания — лента`. Each: `freeze_panes`, `auto_filter`, color-coded priority. Full column spec in `references/excel-schema.md`.

---

## Scripts

| Script | Purpose | Freedom |
|--------|---------|---------|
| `normalize_input.py` | Classify + normalize a fragment (email/phone/inn/ogrn/domain/name/url) | low |
| `phone_lookup.py` | RU phone → operator + region (numbering plan, no PII) | low |
| `phone_identify.py` | A phone the lead GAVE you → identity: Telegram native resolve (consented) + web/CRM plan | low |
| `phone_discovery.py` | Company/decision-maker PUBLIC phones (site, 2GIS, Yandex, hh, EGRUL, Bitrix) | low |
| `domain_to_company.py` | Domain → site/whois scrape → INN/OGRN candidates | low |
| `dadata_lookup.py` | DaData findById/party → full firmographic card | low |
| `egrul_lookup.py` | egrul.nalog.ru official search (key-free fallback) | low |
| `firmographics_batch.py` | Batch firmographic fill (DaData→EGRUL), cached, parallel | low |
| `bitrix_match.py` | Match list × Bitrix by INN (exact) + name (fuzzy) | low |
| `bitrix_aggregate.py` | Aggregate Bitrix history per matched INN | low |
| `research_companies.py` | Perplexity deep dossier over priority queue | medium |
| `build_enriched_xlsx.py` | Build the multi-sheet enriched workbook | low |
| `qualify_trace.py` | Mode A orchestrator: normalize → route → assemble dossier skeleton | medium |
| `social_discover.py` | Cross-network plan (VK/Сетка/TenChat/MAX/Telegram/OK + Western) for name/handle/phone | medium |
| `vk_lookup.py` | VK `users.search`/`users.get` by name+city+company (VK_ACCESS_TOKEN, public profiles) | low |

## References

- `references/ru-firmographics.md` — DaData / EGRUL / Rusprofile / Checko: endpoints, the checko↔nalog combo, what each gives, caps, captcha notes. Read for the company-leg.
- `references/social-channels-ru.md` — RU + Western social coverage map (VK, Сетка, TenChat, MAX, Telegram, OK, hh + Western). Read for the person-leg; driven by `social_discover.py`.
- `references/oss-engines.md` — optional open-source connectors (holehe, Maigret, PhoneInfoga, ignorant, theHarvester, SpiderFoot) + the firmographic OSS landscape. Read to extend coverage.
- `references/scoring.md` — confidence / product-fit / reachability matrices and the color bands. Read before scoring (both modes).
- `references/excel-schema.md` — exact sheet + column spec for the enriched workbook. Read before `build_enriched_xlsx.py`.
- `references/bitrix-export.md` — how to produce `bitrix_data.json` via the `bitrix24` skill. Read at Mode B step 2.

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| DaData 403 | Missing/invalid `DADATA_API_KEY` | Fall back to `egrul_lookup.py` (key-free) |
| EGRUL empty / captcha | Rate limit on egrul.nalog.ru | Slow to 1 req/2s; cache; or use DaData |
| LinkedIn "private profile" | RU exec closed profile post-2022 | Correct insight, not a failure — don't bank on InMail; use HH/site |
| INN mismatch | List has org name only | `bitrix_match.py` fuzzy-matches by name; verify top candidate before trusting |
| Cyrillic in console | Windows cp1251 stdout | Scripts force UTF-8 stdout; if patching, keep the `TextIOWrapper` line |

## Dossier template (Mode A output)

```markdown
# Досье: <ФИО / @handle / email>
**Запрос:** <исходный фрагмент>  ·  **Дата:** <YYYY-MM-DD>  ·  **Confidence (кто это):** N/10

## Кто это
- ФИО · должность · компания · регион
- Контакты (публичные): email · телефон · LinkedIn · TG

## Компания
- Юрлицо · ИНН · ОГРН · гендир · выручка 2024 · численность · ОКВЭД · статус
- Источник: <DaData|EGRUL|сайт> · дата

## В нашей базе (Bitrix)
- Есть/нет · сделки · последнее касание · менеджер · дубль/реанимация

## Сигналы и темы
- О чём пишет / на что реагирует (1-3 пункта, со ссылкой)

## Вердикт
- Fit под продукт: <ваш продукт A | ваш продукт B | ваш продукт C> · score N/10
- Reachability: N/10 · точка входа: <...>
- Рекомендация: квалифицировать / отдать менеджеру <...> / отбросить — почему
```
