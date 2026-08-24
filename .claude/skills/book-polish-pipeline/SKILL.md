---
name: book-polish-pipeline
description: "Финальная шлифовка нон-фикшн книги после того, как главы доведены до FINAL: 18 волн правки, каскад версий, cross-model review, тройная корректура, сборка EPUB+DOCX. Триггеры: «полируй книгу», «следующая версия книги», «книга готова, что дальше»."
---

# Book Polish Pipeline — пост-FINAL workflow

Финальная шлифовка нон-фикшн книги: главы уже написаны и проверены, дальше идёт
не «написать», а «довести» — 18 волн правки, каждая даёт новую версию текста.

Всё, что относится к конкретной книге (название, автор, издатель, состав глав,
сквозные термины), живёт в **`$BOOK_ROOT/book.json`** — не в скриптах и не в этом файле.
Образец: `templates/book.example.json`.

### Что тебе понадобится

| Что | Зачем | Обязательно? |
|---|---|---|
| `BOOK_ROOT` — папка с `chapters/` и `book.json` | все скрипты читают только оттуда | да |
| `~/.claude/voice-sample.md` | волна 6 (голос) без него бессмысленна — агент подставит усреднённого «эксперта» | для волны 6 — да |
| `~/.claude/author-profile.md` | WHITELIST/BLACKLIST имён и компаний для волны 3 | для волны 3 — да |
| `pip install ebooklib python-docx markdown` | сборка EPUB+DOCX | для сборки |
| Подписка/ключ модели для параллельных агентов | волны прогоняются субагентами | да |
| Навык `perplexity` (своя подписка или `PERPLEXITY_API_KEY`) | фактчек за пейволом | опционально |

Шаблоны `~/.claude/templates/{voice-sample,author-profile}.md` — скопируй и заполни
один раз, ими пользуется весь пак.

## КОГДА ЗАПУСКАТЬ

Pre-requisites — всё должно выполняться:

1. ✅ Все единицы текста (главы, интерлюдии, приложения) имеют `FINAL.md`
2. ✅ `FACT-REPORT.md` для каждой главы = PASS или PASS-WITH-CAVEATS
3. ✅ EPUB+DOCX уже собран хотя бы один раз через `build-book.py`
4. ✅ Хотя бы один живой читатель прочитал книгу (или будет читать по ходу шлифовки)

Если что-то не выполнено — вернись на написание глав (навык `book-post`, если он есть
в паке) и закрой пробел. Шлифовать недописанное бессмысленно: волны 1-5 переписывают
формулировки, а не достраивают отсутствующие куски.

## АРХИТЕКТУРНЫЙ ПРИНЦИП — КАСКАД ВЕРСИЙ

```
chapters/<slug>/
├── FINAL.md          ← после book-post (baseline для polish)
├── DRAFT.v8.md       ← bestseller wave 1
├── DRAFT.v9.md       ← bestseller wave 2
├── DRAFT.v10.md      ← bestseller wave 3
├── DRAFT.v11.md      ← reader-feedback wave 1
├── DRAFT.v12.md      ← craft-pass v1 (13 anti-AI паттернов)
├── DRAFT.v13.md      ← craft-pass v2 (22 паттерна + 9 задач + 54 принципа)
└── DRAFT.v13.2.md    ← cross-model fixes after Codex/fact-check
```

**Никогда не перезаписывать предыдущую версию.** Build pipeline (`build-book.py`) подхватит наивысшую.

Frontmatter каждой версии:
```yaml
---
draft_version: 13
voice_passes: 3
craft_pass: true
craft_pass_date: 2026-05-20
craft_pass_v2: true
craft_pass_v2_date: 2026-05-21
last_updated: 2026-05-21
---
```

---

---

## Волны: где что лежит

Сводная таблица всех 18 волн — ниже, в разделе «РЕЗЮМЕ ВОЛН». Разбор конкретной волны читай
только тогда, когда её запускаешь:

| Файл | Когда читать |
|---|---|
| `references/waves-1-5-bestseller.md` | волны 1–5: story-first, эпиграфы, сшивка с компанией автора, отзывы, уплотнение |
| `references/craft-pass-v13.md` | собираешь v13+, нужен список 22 паттернов или параллельный прогон по главам |
| `references/wave-6-de-ai-voice.md` | волна 6 — вычистка машинного голоса; читать целиком |
| `references/waves-7-18.md` | любая волна с 7-й по 18-ю |
| `references/review-and-proofreading.md` | версия готова, идёт кросс-модельное ревью, тройная корректура, фактчек |
| `references/metrics-and-sync.md` | перед сборкой версии: глоссарий, источники, кросс-главные метрики |

Шаблоны промптов в `templates/` подставляются в прогон как есть. Скрипты `scripts/` **запускаются**,
а не читаются: `python scripts/build-book.py --help`, `python scripts/cross_chapter_metrics.py --help`.

## BUILD PIPELINE (EPUB + DOCX)

Финальная сборка через `scripts/build-book.py`. Параметры:

```bash
python scripts/build-book.py --version v13.2
# Создаёт:
#   dist/<book-slug>-v13.2.epub
#   dist/<book-slug>-v13.2.docx
```

### Preference версий внутри build_chapter

Скрипт ищет файл главы в порядке (берёт первый найденный):

```
v13.2.md → v13.1.md → v13.md → v12.md → ... → v8.md → FINAL.md → proofread.md → voice-pass.md → DRAFT.md
```

### Что strip перед сборкой

- Frontmatter YAML (между `---`)
- `<!-- source-trace: -->` HTML-блоки
- `EDIT-NOTES:` блоки
- `PROOFREAD-NOTES:` блоки
- Первый H1 (заменяется на заголовок из CHAPTERS table)

### Cover & illustrations

- **Обложка:** путь задаётся полем `cover` в `book.json`, ищется внутри `dist/`
  (по умолчанию `dist/cover/cover.png`). Файла нет — титул соберётся текстом, сборка не упадёт.
- **Иллюстрации к главам:** `dist/illustrations/*.png`; имя файла — 4-й элемент строки главы в `book.json`
- **Генерация:** навыки `nano-banana-pro` или `openai-dalle` (оба требуют своего платного ключа)

CSS и раскладка страницы — в `scripts/build-book.py`; состав книги — в `book.json`.

---

## ПОЛНЫЙ WORKFLOW СБОРКИ ВЕРСИИ V-N+1

Для каждой новой версии шлифовки:

```
1. ОПРЕДЕЛИТЬ ЦЕЛЬ
   Что эта версия даёт сверх предыдущей? (одна из 5 волн + cross-model fix?)

2. НАПИСАТЬ BRIEFING
   templates/craft-pass-briefing.md → ./work/book-v{N}-briefing.md
   Указать: версия-источник, версия-выход, конкретные задачи, что НЕ трогать

3. ЗАПУСТИТЬ 5 OPUS АГЕНТОВ ПАРАЛЛЕЛЬНО
   Распределение по таблице выше. Каждому — briefing + список своих глав.

4. ОЖИДАНИЕ ВОЗВРАТА
   ~60-90 мин на 5 параллельных Opus при 3 главах каждый

5. SELF-READ ВСЕХ ИЗМЕНЁННЫХ ГЛАВ
   Читать целиком, не grep. Искать:
   - Стыки cliffhanger → opening
   - Фабрикованные «личные» числа автора
   - Синтетические сенсорные детали
   - Дублирование действий в концовках
   - Перебор сенсорики (>4 на сцену)
   - Жанровые сбои

6. РУЧНЫЕ FACT-FIXES
   grep по подозрительным паттернам, Edit/PowerShell sed для NBSP-aware замен

7. CROSS-MODEL REVIEW (опционально, для крупных версий)
   Codex CLI на 3 chapter sample

8. FACT-CHECK DISPATCH (фоном)
   агент book-fact-checker на все главы книги

9. APPLY CRITICAL FIXES
   Из codex-review + fact-checker — править руками

10. TRIPLE PROOFREADER (фоном, ВСЕГДА ПОСЛЕДНИМ)
    2 агента, главы поделены между ними примерно поровну

11. RE-VERIFY CONTENT FIXES
    Корректор мог откатить — переприменить через PowerShell sed

12. GLOSSARY + SOURCES SYNC (фоном)
    Если v-N добавила новые термины/исследования

13. CROSS-CHAPTER METRICS
    Прогнать scripts/cross_chapter_metrics.py — проверить плотность терминов, стыки, side-blocks

14. BUILD EPUB + DOCX
    python scripts/build-book.py --version v{N}.M

15. FINAL REPORT
    Статистика по словам v-N-1 → v-N (с процентами)
    Какие critical-правки применены
    Что осталось автору (WARNING + UNKNOWN из fact-check + STRUCTURAL из codex)
```

---

## TEMPLATES

В подкаталоге `templates/`:

- **`craft-pass-briefing.md`** — шаблон briefing для 5 Opus агентов под v-N
- **`codex-review-prompt.md`** — промпт для Codex CLI (cross-model review)
- **`proofreader-prompt.md`** — промпт для тройного корректора
- **`glossary-sync-prompt.md`** — промпт для glossary+sources sync агента
- **`fact-check-dispatch-prompt.md`** — промпт для book-fact-checker

## SCRIPTS

В подкаталоге `scripts/`:

- **`build-book.py`** — сборка EPUB+DOCX (preference v-N → ... → DRAFT)
- **`cross_chapter_metrics.py`** — плотность терминов, side-blocks, cliffhanger-стыки
- **`grep_suspicious_facts.sh`** — поиск фабрикованных «личных» цифр после агентов

Базовые скрипты предыдущего этапа (`voice-pass`, `proofread`, `fact-check`, `editor-audit`,
`llm-runner`) лежат в навыке `book-post`. Если его в паке нет — соответствующие шаги
делаются субагентами по промптам из `templates/`, отдельного кода для них не требуется.

---

## SAMOPROVERKA для готовой версии v-N+1

### Структура

- [ ] DRAFT.v{N+1}.md создан рядом с DRAFT.v{N}.md (не перезаписан)
- [ ] Frontmatter обновлён (draft_version, last_updated, craft_pass_v2 + дата)
- [ ] Обработаны все единицы из `chapters` в `book.json` — без пропусков
- [ ] Главы, вырезанные намеренно, отмечены как вырезанные (а не «забыли»)

### Содержание

- [ ] Все CRITICAL фиксы fact-check применены
- [ ] Все CRITICAL фиксы Codex применены
- [ ] Корректор не откатил content-правки (verify через grep)
- [ ] Glossary дополнен новыми терминами v-N
- [ ] Sources дополнен новыми источниками v-N

### Голос и стиль

- [ ] Все 22 паттерна anti-ai-tells проверены
- [ ] Privacy decision tree соблюдён (whitelist/blacklist)
- [ ] AI/ИИ convention сохранена
- [ ] Сквозные герои не противоречат себе между главами (имена, роли, хронология)
- [ ] Сквозная врезка (заголовок из `book.json` → `metrics.side_block`) во всех содержательных главах
- [ ] Сквозные термины — плотность в норме (cross-chapter metrics)

### Финал

- [ ] EPUB+DOCX собраны
- [ ] Финальный отчёт пользователю составлен с указанием:
  - Статистика word count
  - Какие правки применены
  - Что осталось автору на финальную вычитку (WARNING + UNKNOWN)

---

## CHANGES IN SKILL ARCHITECTURE — РЕЗЮМЕ ВОЛН

| Wave | Что | Когда запускать | Output |
|---|---|---|---|
| 1 | Story-first + cliffhanger + tweet-line | v8 | content polish |
| 2 | Epigraphs + recurring characters + mirrors | v9 | depth |
| 3 | Сшивка со сквозным кейсом + отраслевые видеоинтервью | v10 | integration |
| 4 | Reader feedback systematization | v11 | external eyes |
| 5 | Tightening (-10-15%) | v12 | density |
| 6 | **De-AI Voice Authentication** | v13+ | живой голос |
| 7 | **Reader personas (3 призмы)** | v14 | audience fit |
| 8 | **Emotional arc tracking** | v14 | reader journey |
| 9 | **Readability metrics** | после v12 | numbers |
| 10 | **Critique from archetype** | после v13 | adversarial eyes |
| 11 | **Glossary drift + timeline consistency** | после v13 | internal coherence |
| 12 | **PR-fragment extraction** | после gold-standard | marketing |
| 13 | **Translation-readiness** | optional | future-proof |
| 14 | **Publication checklist** | перед сдачей | final gate |
| 15 | **Conversion hook (первые 3 страницы)** | после WAVE 6 | sales conversion |
| 16 | **Chapter → tg-post extraction** | после WAVE 12 | content marketing |
| 17 | **A/B-кандидаты для названий** | перед WAVE 14 | titles decision |
| 18 | **Neurosymbolic hook check** | после WAVE 8 | memorability |

**Логика финальная:** waves 1-5 (content) → 6 (voice) → 7-8 (audience fit + journey) → 9-11 (внутренняя гигиена) → 12, 16 (marketing material) → 13 (future-proof) → 15, 17, 18 (sales + titles + memorability) → 14 (final gate).

---

## ИСТОРИЯ

Навык — переплавка реального книжного проекта: 18 волн правки за три недели.
Все паттерны и anti-patterns взяты из практики, а не из теории; номера версий в примерах
(v8, v13, iter 18) — оттуда же, у твоей книги нумерация будет своя.

Эволюция:
- v1: каскад v8 → v13, 22 паттерна, multi-agent parallel, cross-model review через Codex
- **v2: добавлена WAVE 6 (De-AI Voice Authentication). Повод: книга, чистая по содержанию, набрала больше половины шкалы по машинности текста — и вся она сидела в intros и outros, куда редактор смотрит последним. Расширен AI-blacklist до 20+ типов. Добавлены positive intro/outro patterns из лучших non-fiction (Mollick/Hao/Witt/Suleyman/Narayanan). VOICE_CORPUS обязательное чтение. Добавлен anti-pattern «натянутая человечность» — синтетическая «личная» сцена, которую субагент дописывает, чтобы текст выглядел живым.**

Каждая новая книга добавляет 1-2 паттерна. Записывай их сюда же — и дублируй в свою
память (`~/.claude/projects/<project-slug>/memory/`), иначе следующая книга начнётся с нуля.
