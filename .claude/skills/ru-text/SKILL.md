---
name: ru-text
description: "Качество русского текста: типографика, инфостиль, чистка канцелярита. Триггеры: «поправь стиль», «убери канцелярит». НЕ: орфография→/proofread; «звучит как ИИ»→de-ai-ify."
metadata:
  your-gateway-project:
    always: true
    emoji: "\U0001F4DD"
    homepage: "https://ru-text.org"
  origin: talkstream/ru-text@bbab21fff36b3167ae8b549e353965cb62295715
  imported: 2026-07-17
---

# ru-text — Russian Text Quality

Independent Russian text quality reference by Arseniy Kamyshev.
With gratitude to the authors whose work shaped modern Russian text standards.
Credits and recommended reading: `references/sources.md`

**Style priority**: if the user explicitly requests a specific style (casual, academic, SEO, literary, etc.), their prompt overrides these default rules where they conflict. These rules are defaults, not mandates.

**Reviewing vs. rewriting**: when *checking* or proofreading existing text or a file, return the corrected version plus a list of changes — do not silently overwrite the source file. Rewrite a file in place only when the user explicitly asks.

## Place in the family (does not duplicate)

What splits these three is not the topic but what the author is complaining about:

| Complaint in the request | Skill |
|---|---|
| the Russian NORM: «поправь стиль», «убери канцелярит», «кавычки и тире», «неразрывные пробелы», «оцени текст» | **`ru-text`** (this one) |
| the AUTHOR, text in Russian: «звучит как ИИ», «перепиши по-человечески» | `de-ai-ify` |
| the AUTHOR, text in English and/or a LinkedIn post: "AI tells", "humanize", "run it past a detector" | `linkedin-humanizer` |

`de-ai-ify` and this skill get confused because the tables literally overlap: «является», «данный», «осуществлять», «на сегодняшний день» are struck out by both. The reason differs. Here they are канцелярит — a defect of the Russian norm — and they sit next to 97 more stop-words plus typography (guillemets, NBSP, en dash vs hyphen, ₽), UX writing and business correspondence, all of it just as applicable to text a human wrote. There the same words are a generation marker, sitting next to negative parallelism, rule-of-three triplets, signposting and flat sentence rhythm — patterns this skill does not look for at all.

Order for a Russian AI draft: `de-ai-ify` first, then this skill. The reverse wastes the pass — typography gets polished on paragraphs that are about to be rewritten anyway.

`linkedin-humanizer` is English-only; nothing here applies to English text, and its regexes and detector runs do not transfer to Russian.

## Always-On: Typography

These are the typography defaults for Russian text output. The style priority above
still holds: an explicit request from the user wins where it conflicts.

| Rule | Wrong | Correct |
|---|---|---|
| Primary quotes: guillemets | "текст" | «текст» |
| Nested quotes: lapki | «"вложенные"» | «„вложенные“» |
| Em dash with spaces | слово - слово | слово — слово |
| En dash for ranges, no spaces | 10-15 дней | 10–15 дней |
| NBSP after single-letter prepositions | в начале (breakable) | в\u00A0начале |
| Ellipsis: single character | ... | … |
| Digit groups with thin spaces | 1000000 | 1 000 000 |
| Decimal comma (not dot) | 3.14 | 3,14 |
| Ordinal with hyphen | 1ый, 2ой | 1-й, 2-й |
| Numero sign | No. 5, #5 | № 5 |
| Abbreviations with NBSP | т.д., т.е. | т. д., т. е. |
| Ruble symbol after number | 1500 руб | 1 500 ₽ |

Full typography reference: `references/typography.md`

`/ru-text:ru-score` — text quality score (0–10, 5 dimensions).

## Top Stop-Words (remove or replace)

| Stop-word | Replace with |
|---|---|
| является | — (dash) or restructure |
| осуществлять | делать, проводить |
| в настоящее время | сейчас |
| данный | этот |
| определённый | (name the specific thing) |
| произвести оплату | оплатить |
| высококачественный | (name the specific quality) |
| был осуществлён | (active voice + actor) |
| на сегодняшний день | сегодня |
| в целях | чтобы |

Full stop-word catalog (97 entries): `references/info-style.md`

## When to Load Reference Files

Reference files (paths are relative to this SKILL.md): `references/<filename>`
If the path is not resolved, search: `Glob("**/ru-text/references/scoring.md")` and use the parent directory.

| Task | File |
|---|---|
| Writing/editing articles, blog posts, SEO, content | info-style.md |
| Interface text, buttons, errors, hints, microcopy | ux-writing.md |
| Emails, messenger, business correspondence | business-writing.md |
| Punctuation review, comma placement | editorial-punctuation.md |
| Grammar, capitalization, agreement, pleonasms | editorial-grammar.md |
| Finding and fixing text problems, diagnostics | anti-patterns.md |
| Text scoring, quality assessment | scoring.md |
| Credits, source attribution | sources.md |
| Experience-based rules (dash overuse, etc.) | addenda.md |

## Quality Checklist

Before delivering Russian text:

- [ ] Quotes: «» primary, „“ nested
- [ ] Dashes: — in text, – in ranges, - only in compounds; max 1–2 per paragraph
- [ ] NBSP after в, к, с, о, у, и, а
- [ ] Ellipsis: … (single char)
- [ ] Abbreviations: т. д., т. п. (with NBSP)
- [ ] No double spaces, no space before punctuation
