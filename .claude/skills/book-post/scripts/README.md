# book-post / scripts

Конвейер книжных проходов поверх двух CLI: `codex` (подписка ChatGPT) и `claude` (подписка Claude).
Ключи API не нужны — оба авторизуются своим логином.

**Зачем:** voice-keeper, proofreader, fact-checker — это длинные тяжёлые проходы по 3-5 КБ текста
главы. Если все главы гонять через Claude, дневной лимит подписки выгорает за один вечер.
Codex — отдельный лимит, он с Claude не пересекается. Дефолт — codex, fallback — claude на quota.
Codex не установлен — ставь `--provider claude` везде, конвейер работает целиком.

## Что внутри

| Файл | Назначение |
|------|-----------|
| `llm-runner.js` | Generic codex+claude wrapper. `dispatch({prompt, prefer})` — пробует codex, на quota падает в claude. |
| `prompts.js` | Промпты: VOICE_KEEPER, PROOFREADER, FACT_CHECKER, EDITOR. Сведений об авторе внутри нет — приходят параметрами. |
| `voice-pass.js` | Один прогон voice-keeper по одной главе. `node voice-pass.js --chapter 01-first-chapter` |
| `proofread.js` | Один прогон корректуры. `node proofread.js --chapter 01-first-chapter --input voice-pass` |
| `fact-check.js` | Один прогон fact-checker против SOURCES.md + MATERIALS.md. |
| `fact-check-web.js` | Проверка ссылок из SOURCES.md против живых страниц (жив ли URL, не уехал ли тезис). |
| `editor-audit.js` | AUDIT-ONLY редактура: вердикт по чек-листу, текст не переписывает. |
| `auto-loop.sh` | Watchdog. Держит N параллельных проходов, пока есть главы без OUT. |
| `package.json` | ES module setup. |

## Пререквизиты

```bash
# Claude CLI — основной путь (подписка)
claude --version

# Codex CLI — опционально, ради отдельного лимита на механические проходы
npm i -g @openai/codex
codex login
```

Никаких `npm install` — только Node stdlib (`child_process`, `fs`, `path`, `os`).
Бинарники `codex` и `claude` берутся из PATH (override через env `CODEX_CLI`, `CLAUDE_CLI`).

## Что скрипты читают из твоего конфига

| Переменная | По умолчанию | Что это |
|---|---|---|
| `BOOK_ROOT` | `~/book` | корень книги: `chapters/`, `extracted/`, `STYLE_GUIDE.md` |
| `VOICE_SAMPLE` | `~/.claude/voice-sample.md` | голос автора — **без него voice-pass выдаст усреднённый текст** |
| `AUTHOR_PROFILE` | `~/.claude/author-profile.md` | кто пишет: роль, темы, о чём молчит |
| `VOICE_SAMPLES_DIR` | — | необязательно: папка со своими опубликованными `*.md` как доп. образцы |

Шаблоны `voice-sample.md` и `author-profile.md` — в `~/.claude/templates/`.

## Типичный pipeline для одной главы

```bash
export BOOK_ROOT=~/book
cd ~/.claude/skills/book-post/scripts

# 1. Voice-pass
node voice-pass.js --chapter 01-first-chapter
# → пишет $BOOK_ROOT/chapters/01-first-chapter/DRAFT.voice-pass.md

# 2. Proofread поверх voice-pass
node proofread.js --chapter 01-first-chapter --input voice-pass
# → пишет DRAFT.proofread.md

# 3. Fact-check на финальной версии
node fact-check.js --chapter 01-first-chapter --input proofread --provider claude
# → пишет FACT-REPORT.md (PASS / PASS-WITH-CAVEATS / BLOCK)

# 4. Если FACT-REPORT = PASS → промоутим:
mv "$BOOK_ROOT/chapters/01-first-chapter/DRAFT.proofread.md" \
   "$BOOK_ROOT/chapters/01-first-chapter/FINAL.md"
```

## Параллельная обработка всех глав

```bash
# Voice-pass по всем главам, у которых ещё нет DRAFT.voice-pass.md
PROVIDER=codex PASS=voice PARALLEL=2 ./auto-loop.sh > /tmp/voice-loop.log 2>&1 &

# Когда voice-pass везде готов — proofread:
PROVIDER=codex PASS=proofread INPUT=voice-pass PARALLEL=2 ./auto-loop.sh > /tmp/proofread-loop.log 2>&1 &

# Fact-check лучше через claude (нужен точный reasoning на длинном контексте):
PROVIDER=claude PASS=fact-check INPUT=proofread PARALLEL=2 ./auto-loop.sh > /tmp/factcheck-loop.log 2>&1 &
```

Стоп: `touch /tmp/book-post.stop` — все loop'ы досмотрят активные runs и выйдут.

По умолчанию `auto-loop.sh` выставляет `BOOK_NO_CLAUDE=1`: если codex упал, проход не уходит
в Claude молча, а падает с ошибкой. Так лимит Claude остаётся на ручную литературную правку.
Нужен fallback — запускай с `BOOK_NO_CLAUDE=0`.

## Что выбирать: codex или claude?

| Задача | Дефолт | Почему |
|--------|--------|--------|
| Voice-keeper (стилизация прозы) | codex | большой объём; модель не любит проходы по своему же тексту |
| Proofreader (формальная корректура) | codex | механическая работа |
| Fact-checker (проверка против sources) | claude | требует точного reasoning на длинном контексте |
| Editor (структура / ритм) | codex | литературная задача |
| Writer (новая глава с нуля) | claude | книгу пишем главным голосом |

Если codex упрётся в quota — `dispatch()` падёт в claude. Видно в логе:
`[llm-runner] Codex quota exhausted — falling back to Claude`.

## Критические нюансы (оплачены отладкой)

1. `--output-last-message <file>` — codex иначе теряет результат в stdout
2. Уникальный outFile на каждый вызов (concurrent workers иначе перетрут)
3. `windowsHide: true` обязательно на Windows (cmd-окна на каждый spawn)
4. `--skip-git-repo-check` — codex без git context
5. timeout 360-600 с — voice/proofread на главу могут идти 3-5 минут
6. Fallback на claude через `isCodexQuotaError()` — codex отдаёт rate-limit без явной ошибки

## Проверка что всё работает

```bash
node voice-pass.js --chapter 01-first-chapter --dry-run
# → должен дампнуть промпт в /tmp/voice-pass-01-first-chapter-prompt.txt и выйти
# → ничего не вызовет, не потратит лимиты
```

Если dry-run работает — скрипт находит все файлы (DRAFT, OUTLINE, voice-sample). Можно запускать
настоящий прогон. Если в выводе есть `WARNING: … voice-sample.md не найден` — сначала заполни
образцы голоса, иначе получишь безликий текст и не поймёшь почему.

## Layout файлов одной главы после полного pipeline

```
$BOOK_ROOT/chapters/01-first-chapter/
├── OUTLINE.md             ← структура и тезисы
├── ANCHORS.md             ← Tier 1 (личные истории, опционально)
├── SOURCES.md             ← Tier 2 (открытые источники)
├── MATERIALS.md           ← Tier 3 (ссылки на extracted/)
├── DRAFT.md               ← writer'ом из главного навыка
├── DRAFT.voice-pass.md    ← voice-pass.js
├── DRAFT.proofread.md     ← proofread.js
├── FACT-REPORT.md         ← fact-check.js
└── FINAL.md               ← командой mv, когда FACT-REPORT=PASS
```

`DRAFT.md` всегда сохраняется как baseline — на каждый этап создаётся новый файл, не overwrite.
