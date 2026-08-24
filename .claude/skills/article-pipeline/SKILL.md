---
name: article-pipeline
description: "Гонит статью по стадиям: рисёрч → драфт → фактчек → голос → корректура → редактура → обложка → docx. Триггеры «напиши статью на Habr/VC/РБК/LinkedIn», «прогони статью по конвейеру». НЕ один пост в канал → tg-post; НЕ глава книги → book-post."
---

# Article Pipeline — конвейер статей

Восемь стадий, каждая берёт файл от предыдущей и отдаёт следующей. Гонит их один
отдельный агент под конвейер (или сама сессия, если статья короткая).

## Что понадобится до старта

| Файл | Зачем | Откуда взять |
|---|---|---|
| `~/.claude/author-profile.md` | кто автор: имя, роль, продукт, площадки, о чём НЕ пишет | шаблон `~/.claude/templates/author-profile.md` |
| `~/.claude/voice-sample.md` | 2-3 своих текста — образец голоса для стадии 4 | шаблон `~/.claude/templates/voice-sample.md` |
| `~/.claude/business-context.md` | продукт, цифры, аудитория — источник фактов о своём бизнесе | шаблон `~/.claude/templates/business-context.md` |

Без первых двух конвейер работает, но выдаёт безликого «эксперта по AI».
Стадии 1, 2, 4, 6, 8 читают эти файлы; если файла нет — стадия обязана сказать
об этом прямо, а не выдумывать автора.

**Навыки-площадки** (`habr-post`, `vc-post`, `rbc-post`, `linkedin-post`) везутся
отдельно. Конвейер работает и без них — тогда стиль площадки задаётся вручную в
запуске, — но три готовых скрипта (сборка `.docx`, генерация обложки, security-скан)
лежат в `habr-post/templates/`. Нет `habr-post` — стадии 7 и 8 делаются руками
(см. фолбэки в их промптах).

## Карта конвейера

```
topic + platform + working_dir
        │
  1 researcher    →  RESEARCH.md            (+ QUESTIONS_FOR_AUTHOR.md — блокирует)
        │
  2 writer        →  DRAFT.md               (+ IMAGE-PROMPTS.md для habr)
        │
  3 fact-checker  →  FACT-REPORT.md         PASS / PASS-WITH-CAVEATS / BLOCK
        │                                    BLOCK → назад на 2
  4 voice-keeper  →  DRAFT-voiced.md, VOICE-NOTES.md
        │
  5 proofreader   →  DRAFT-proof.md, PROOF-LOG.md
        │
  6 editor        →  FINAL.md, EDIT-NOTES.md
        │
 6b security      →  SECURITY-SCAN.md       BLOCK → назад на 2
        │
  7 illustrator   →  cover.<ext>, ILLUSTRATION.md
        │
  8 publisher     →  <slug>.docx, <slug>.cover.<ext>, <slug>.meta.md
```

| # | Стадия | Вход | Выход | Промпт |
|---|--------|------|-------|--------|
| 1 | researcher | topic, platform | `RESEARCH.md` | `references/stage-1-researcher.md` |
| 2 | writer | `RESEARCH.md` | `DRAFT.md` | `references/stage-2-writer.md` |
| 3 | fact-checker | `DRAFT.md`, `RESEARCH.md` | `FACT-REPORT.md` | `references/stage-3-fact-checker.md` |
| 4 | voice-keeper | `DRAFT.md`, `FACT-REPORT.md` | `DRAFT-voiced.md`, `VOICE-NOTES.md` | `references/stage-4-voice-keeper.md` |
| 5 | proofreader | `DRAFT-voiced.md` | `DRAFT-proof.md`, `PROOF-LOG.md` | `references/stage-5-proofreader.md` |
| 6 | editor | `DRAFT-proof.md` + все notes | `FINAL.md`, `EDIT-NOTES.md` | `references/stage-6-editor.md` |
| 6b | security audit | `FINAL.md` | `SECURITY-SCAN.md` | `references/stage-6b-security-audit.md` |
| 7 | illustrator | `FINAL.md` | `cover.<ext>`, `ILLUSTRATION.md` | `references/stage-7-illustrator.md` |
| 8 | publisher | `FINAL.md` + cover | `.docx` + `.cover` + `.meta.md` | `references/stage-8-publisher.md` |

## Как запускать

Каждая стадия — отдельный `general-purpose` субагент на `fable`. Промпт стадии
берётся **целиком** из соответствующего `references/stage-*.md` и дополняется
конкретикой запуска:

```
Task(subagent_type="general-purpose", model="fable", prompt=f"""
{содержимое references/stage-2-writer.md}

---
## Запуск
- working_dir: {working_dir}
- platform: {platform}
- topic: {topic}
""")
```

Стадия 6b выполняется оркестратором инлайн (одна команда Bash), субагент не нужен.

Стадии идут **строго последовательно**. Параллелить нельзя: у стадий общий файл, и
параллельный прогон уже приводил к потере правок (см. Race condition ниже).

## Рабочая директория

Дефолт: `./work/<slug>/` в каталоге проекта. Если ведёшь заметки в своей базе
знаний — задай свой корень при запуске (`working_dir`), путь нигде не зашит.

```
RESEARCH.md, QUESTIONS_FOR_AUTHOR.md
DRAFT.md, IMAGE-PROMPTS.md
FACT-REPORT.md
EDIT-NOTES.md          (voice-keeper в habr-режиме)
PROOF-NOTES.md         (proofreader в habr-режиме)
EDITOR-NOTES.md        (editor в habr-режиме)
SECURITY-SCAN.md
ILLUSTRATION.md
FINAL.md
cover.jpg, cover.png, cover-1200.jpg
<slug>-FINAL.docx
```

Каждая стадия оставляет свой `<stage>-NOTES.md` с changelog (что изменено и почему) —
чтобы можно было откатить или повторить отдельную стадию.

**Имена файлов заметок расходятся между режимами.** В базовом режиме voice-keeper пишет
`VOICE-NOTES.md`, proofreader — `PROOF-LOG.md`, editor — `EDIT-NOTES.md`. В habr-режиме
voice-keeper пишет `EDIT-NOTES.md`, proofreader — `PROOF-NOTES.md`, editor — `EDITOR-NOTES.md`.
Выбери один набор на статью и держи его до конца.

## Правило остановки

Любой **BLOCK** (фактчек или security) → остановиться, сообщить автору список
блокеров, **не обходить**. Вопросы рисёрчера тоже блокируют: писать драфт, пока
`QUESTIONS_FOR_AUTHOR.md` не разобран, нельзя.

## Race condition

Один `FINAL.md` = один пишущий агент одновременно. Параллелизм — только на разных файлах.
Прецедент: voice-rewrite и code-snippets гнали параллельно, voice-проход
перетёр правки со сниппетами. Не повторять.

## Площадки

| platform | стиль-гайд | что меняется |
|----------|-----------|--------------|
| habr | `skills/habr-post/SKILL.md` | инженерный кейс, TL;DR, реальный код, расширенный RESEARCH.md, свои имена notes-файлов, шаблоны в `skills/habr-post/templates/` |
| vc | `skills/vc-post/SKILL.md` | рубрика «Личный опыт», тёплый B2C-голос, строгая типографика |
| rbc | `skills/rbc-post/SKILL.md` | только источники уровня 1, сдержанный тон, без CTA, каждый URL перепроверяется WebFetch |
| linkedin | `skills/linkedin-post-writer/SKILL.md` | ≤ 3000 знаков, hook первой строкой, обложка 1200×1200 / 1200×627, `.docx` необязателен |

Навыка площадки нет — не выдумывай её правила: спроси автора или возьми
минимальный набор (лид, подзаголовки каждые 300-400 слов, вывод) и пометь в
`EDIT-NOTES.md`, что стиль-гайд площадки не применялся.

Чистка от ИИ-клише для всех площадок — `skills/de-ai-ify`, ремесло текста и
анти-ИИ-паттерны — `skills/author-voice`.

## Готовые скрипты (habr-post/templates/)

```bash
python ~/.claude/skills/habr-post/templates/build_docx.py \
  --workdir ./work/myslug --md FINAL.md --cover cover.jpg --slug myslug-FINAL

python ~/.claude/skills/habr-post/templates/gen_cover.py \
  --workdir ./work/myslug --theme "personal AI workspace" \
  --visual-core "laptop with knowledge graph, lavalier mic on desk" --negative-extra ""

python ~/.claude/skills/habr-post/templates/security_scan.py FINAL.md   # 0 = clean, 1 = leaks
```

Плюс `series.json` (реестр серий и canonical URL), `cta_templates.md`, `habr_footer.md`
(генерация хабов и тегов).

## Границы

Это конвейер **статьи** — длинного текста под площадку, с рисёрчем и фактчеком.
Не для: одиночного поста в TG-канал (→ `tg-post`), главы книги (→ `book-post`),
коммента под чужим постом (→ `comment-replies`), рассылки (→ `content-engine`).
