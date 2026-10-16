---
description: "КАНОН поиска по истории чатов Claude Code (chats.db FTS5): search, titles, index. Триггеры: «найди в чатах», «как назывался тот чат». KB встреч → /kb."
argument-hint: "<запрос> [--days N] [--after DATE] [--limit N] | titles <имя> | knowledge <q> [--type code|error] | index [--force] | stats | archive"
---

# Search Chat History (SQLite FTS5)

**Arguments:** $ARGUMENTS

## Task

Full-text search across all Claude Code chat sessions using SQLite FTS5 with BM25 ranking.

## ⭐ Поиск чата по ИМЕНИ (ai-title) — начинать отсюда

Claude Code генерирует каждому чату короткое человекочитаемое имя («Разбор ошибки в сборке»,
«Find deployment meeting transcript and summarize»). **Именно его владелец
видит в списке чатов и в `/resume`, и именно по нему он ищет сессию** — не по содержимому.

Имя лежит в JSONL сессии записями `{"type":"ai-title","title":"..."}` — пишется многократно
по мере разговора, **актуально последнее**. В `first_prompt` его НЕТ (там сырой первый промпт),
поэтому раньше найти чат «по названию» было невозможно.

```bash
# Найти чат по имени → выдаёт имя, период, размер и готовую resume-команду
python ~/.claude/tools/search_chats.py titles "сборка"
python ~/.claude/tools/search_chats.py titles          # последние чаты с именами
python ~/.claude/tools/search_chats.py titles "сборка" --limit 20 --days 60

# Проставить имена уже проиндексированным сессиям (index берёт только изменённые файлы).
# Читает ТОЛЬКО хвост каждого JSONL, поэтому быстро даже на 19 ГБ истории.
python ~/.claude/tools/search_chats.py backfill-titles --days 120
```

Обычный `search` теперь тоже показывает строку `ЧАТ: «имя»` у каждого попадания — можно сразу
понять, из какого чата результат.

**Когда пользователь спрашивает «как назывался тот чат» / «найди чат где мы делали X»:**
сначала `titles`, и только если не нашлось — полнотекстовый `search` по содержимому.

## Полнотекст по чатам (3 ступени, token-aware)

Ступени идут по возрастанию цены контекста. Не прыгать сразу в `get`.

```bash
# 1) компактный индекс: id, дата, проект, 2-строчный сниппет + ИМЯ ЧАТА
python ~/.claude/tools/search_chats.py search "$ARGUMENTS"
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --days 30   # окно свежести (деф 90)
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --days 0    # без окна, за всё время
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --after 2026-02-01 --limit 20
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --include-newsbot  # снять фильтр шума ai-news-bot

# 2) контекст вокруг найденного сообщения
python ~/.claude/tools/search_chats.py timeline <msg_id> --before 5 --after 5

# 3) полные тексты — только выбранных id, последним
python ~/.claude/tools/search_chats.py get 12345,12346
```

Восстановить чат целиком (работает и для удалённых сессий):

```bash
python ~/.claude/tools/search_chats.py export <session_id_или_префикс> [--out FILE]
```

## Knowledge base (извлечённые знания: код, ошибки, решения)

Пополняется через `/memory-learn`.

```bash
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS"
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS" --type code
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS" --type error
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS" --limit 20
```

| `--type` | Что лежит |
|----------|-----------|
| `learning` | извлечённые знания |
| `code` | код, функции, конфиги |
| `discussion` | обсуждения |
| `error` | ошибки и их решения |
| `project_doc` | документы проектов |
| `question` | вопросы |
| `project` / `decision` / `memory` | проекты, архитектурные решения, память |

---

## Обслуживание индекса

```bash
python ~/.claude/tools/search_chats.py index                  # инкрементально: только новые/изменённые
python ~/.claude/tools/search_chats.py index --force          # полная переиндексация
python ~/.claude/tools/search_chats.py index --include-newsbot # не помечать сессии ai-news-bot как шум
python ~/.claude/tools/search_chats.py backfill-titles --days 120  # проставить имена уже проиндексированным
python ~/.claude/tools/search_chats.py stats                  # сессии, сообщения, knowledge, размер БД
python ~/.claude/tools/search_chats.py archive                # сессии старше 14 дней → archive/
python ~/.claude/tools/search_chats.py archive-large          # плюс крупные (>20 МБ, старше 3 дней)
```

`backfill-titles` читает ТОЛЬКО хвост каждого JSONL — быстро даже на 19 ГБ истории
(`index` берёт лишь изменённые файлы и старым сессиям имена не проставит).

`stats` показывает: число сессий и диапазон дат, сообщения (user/assistant), knowledge
по типам и по источникам, размер и путь БД.

**Где лежат данные:** сессии — `~/.claude/projects/**/*.jsonl`, архив —
`~/.claude/projects/*/archive/`; индексируются и активные, и архивные. БД —
`~/.claude/chats.db` (SQLite FTS5 + BM25).

## Search tips

| Syntax | Example | Description |
|--------|---------|-------------|
| Simple words | `telegram bot` | Match both words |
| Quoted phrase | `"vector memory"` | Exact phrase match |
| Prefix | `react*` | Words starting with react |
| OR | `sqlite OR postgres` | Either word |

Флага `--role user\|assistant` в движке НЕТ (был в старом argument-hint, в коде отсутствует).

## Examples

```
/search-chats titles сборка             # найти чат по ИМЕНИ (как в /resume)
/search-chats titles                    # последние чаты с именами
/search-chats sqlite fts5
/search-chats "extension crash" --after 2026-02-01
/search-chats telegram bot --days 0 --limit 20
/search-chats knowledge FastAPI streaming --type code
/search-chats index
/search-chats stats
```

## Зачем это нужно (типовой сценарий)

Запрос звучит как «мы же чинили ту сборку — в каком чате? найди его название».
Полнотекстовый `search` на такой запрос возвращает **идентификатор сообщения**, а не имя
чата: он ищет по содержимому и про заголовки ничего не знает. Имя живёт отдельно, в записях
`ai-title`, и достаётся только через `titles` — тем же текстом, который владелец видит
в списке чатов и в `/resume`.

Отсюда порядок: `titles` первым, `search` — только если по имени не нашлось.

## Соседи

- **Заметки памяти и поиск по знаниям** → `/memory-search`.
- **Запись знания** → `/memory-learn` (`search_chats.py learn`).
- **Готовый документ в 4 уровня памяти** → skill `save-knowledge-base`.
- **Связи, хронология, кейсы** → skill `graph-memory` (`memory_graph.py`).
- **Уборка и консолидация памяти** → skill `dream`.
- **Встречи, письма, Telegram** → `/kb`.
- **Одна текущая сессия** → `/prompt-log`; как я работаю вообще → skill `session-mentor`.
