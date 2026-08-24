# habr-post — механика пайплайна (templates, рабочая директория, скрипты)

Читать при запуске редколлегии и на стадии publisher.

## Рабочая директория

Одна папка на статью. Путь задаёшь ты — переменная `ARTICLES_ROOT`, по умолчанию
`./articles/<YYYY-MM>/<slug>/`. Держишь заметки в Obsidian или другом хранилище —
пропиши свой путь один раз здесь и в промптах стадий; главное, чтобы **все девять
стадий писали в одну папку**, иначе следующая не найдёт артефактов предыдущей:

```
RESEARCH.md, QUESTIONS_FOR_AUTHOR.md
DRAFT.md, IMAGE-PROMPTS.md
FACT-REPORT.md
EDIT-NOTES.md          (voice-keeper)
PROOF-NOTES.md         (proofreader)
EDITOR-NOTES.md        (editor)
SECURITY-SCAN.md       (security-audit)
ILLUSTRATION.md        (illustrator)
FINAL.md
cover.jpg, cover.png, cover-1200.jpg
<slug>-FINAL.docx
_gen_cover.py, _build_docx.py   (симлинк/копия из templates/)
```

Каждая стадия оставляет `<stage>-NOTES.md` с changelog (что изменено, почему) — для отката/повтора.

## Templates (`~/.claude/skills/habr-post/templates/`)

| Файл | Назначение |
|------|-----------|
| `build_docx.py` | Сборка .docx из FINAL.md + cover.jpg (CLI args) |
| `gen_cover.py` | Обложка через Gemini 3.1 Flash Image (слоты visual core) |
| `security_scan.py` | Grep сенситивных паттернов перед публикацией |
| `series.json` | Реестр серий и canonical URL |
| `cta_templates.md` | CTA: «забери каркас», P.S.+P.P.S., series footer |
| `habr_footer.md` | Авто-генерация хабов и тегов из topics |

### Вызовы

```bash
python ~/.claude/skills/habr-post/templates/build_docx.py \
  --workdir ./article-myslug --md FINAL.md --cover cover.jpg --slug myslug-FINAL

python ~/.claude/skills/habr-post/templates/gen_cover.py \
  --workdir ./article-myslug --theme "personal AI workspace" \
  --visual-core "laptop with knowledge graph, lavalier mic on desk, hand-drawn diagram in notebook" \
  --negative-extra ""

python ~/.claude/skills/habr-post/templates/security_scan.py FINAL.md
# exit 0 = clean, 1 = leaks (список с line numbers)
```

## Пайплайн из 9 стадий (последовательный)

Полные промпты стадий живут в соседнем навыке `article-pipeline`
(`~/.claude/skills/article-pipeline/references/stage-*.md`) — он же их и гоняет, спавня
`general-purpose` с промптом стадии. **Навыка нет в паке — пайплайн всё равно рабочий:**
описания девяти стадий ниже достаточно, чтобы вести их вручную или своими субагентами,
а весь инструментарий (`templates/*`) лежит здесь.

Каждая стадия читает артефакты предыдущей, работает со своим фокусом, передаёт дальше.

1. **researcher** (`stage-1-researcher.md`) → `RESEARCH.md` с явным разделением: `## Verifiable Facts` (каждый факт с `[Source]`), `## Narrative Anchors` (личные истории, требуют user confirm), поля `length: short|medium|long|flagship` и `format: case|tutorial|review|opinion|guide`. Вопросы → блокирует, пишет `QUESTIONS_FOR_AUTHOR.md`.
2. **writer** (`stage-2-writer.md`) → `DRAFT.md` строго по фактам RESEARCH.md, по target-длине. Image prompts — в `IMAGE-PROMPTS.md`, НЕ в DRAFT.md.
3. **fact-checker** (`stage-3-fact-checker.md`) → независимо верифицирует каждую цифру/имя/код. Каналы: live SSH на свой сервер (`ssh "$SERVER"`), GitHub API, WebFetch, локальные репо. Вердикт PASS / PASS-WITH-CAVEATS / BLOCK + `FACT-REPORT.md`.
4. **voice-keeper** (`stage-4-voice-keeper.md`) → чистит ИИ-штампы, применяет ДНК голоса. ОБЯЗАТЕЛЬНО до старта читает VOICE_CORPUS. → `EDIT-NOTES.md`.
5. **proofreader** (`stage-5-proofreader.md`) → 3 прохода: орфография → пунктуация → типографика.
6. **editor** (`stage-6-editor.md`) → структура, ритм, заголовок, CTA; ловит логически шаткие формулировки.
7. **security-audit** (`stage-6b-security-audit.md`) → `templates/security_scan.py` на FINAL.md. BLOCK если найдено.
8. **illustrator** (`stage-7-illustrator.md`) → обложка через `templates/gen_cover.py`.
9. **publisher** (`stage-8-publisher.md`) → `.docx` через `templates/build_docx.py`; резолвит `series:slug` ссылки.

**Правило остановки:** любой BLOCK → остановиться, сообщить пользователю со списком блокеров, не обходить.

**Race condition:** один FINAL.md = один writer одновременно. Параллелизм только на разных файлах. История (RAG-v2): voice-rewrite + code-snippets параллельно, voice перетёр snippets — не повторять.

### VOICE_CORPUS (обязательное чтение для voice-keeper)

```yaml
voice_corpus:
  - ~/.claude/voice-sample.md       # ГЛАВНОЕ: твои тексты. Шаблон — ~/.claude/templates/voice-sample.md
  - ~/.claude/author-profile.md     # регалии, стоп-лист, тон. Шаблон — ~/.claude/templates/author-profile.md
  - skills/de-ai-ify/SKILL.md       # список штампов, общий для всех площадок
  - reference_articles:   # 2-3 СВОИ опубликованные статьи как образец формата Habr
      - <путь к своей статье 1>/FINAL.md
      - <путь к своей статье 2>/FINAL.md
```

`voice-sample.md` не заполнен → voice-keeper обязан **остановиться и сказать об этом**.
Подражать нечему: без образца он выдаст усреднённый «экспертный» текст, тот самый,
который читатель узнаёт как машинный с третьего предложения.

### VOICE_PROMPT_TABOO (запрещённые слова В ПРОМПТЕ voice-агента)

Триггерят Anthropic Usage Policy refusal: "critical review", "paranoid", "exploit", "attack vector", "HAL 9000" (в промпт-инструкции; в самой статье упоминание ОК), "kill", "destroy", "weaponize". Нейтральные замены: «полировка стиля», «удаление AI-штампов», «синхронизация с голосом», «edge case» вместо «attack vector».

## Формат вывода (от publisher)

Пользователь получает: `<slug>-FINAL.docx` (обложка+заголовок+подпись), `cover.jpg`+`cover-1200.jpg` (native+web), `SECURITY-SCAN.md` (должен быть PASS), `EDIT-NOTES.md`+`FACT-REPORT.md` (аудит), список хабов и тегов в чате. Промежуточные артефакты остаются в work-директории.
