---
description: "КАНОН поиска по истории чатов Claude Code (chats.db FTS5): search, titles, index. Триггеры: «найди в чатах», «как назывался тот чат». KB встреч → /kb."
argument-hint: "<запрос> [--after DATE] [--limit N] [--role user|assistant] | titles <имя> | index | stats | archive"
---

# Search Chat History (SQLite FTS5)

**Arguments:** $ARGUMENTS (search query [--after DATE] [--limit N] [--role user|assistant])

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

# Проставить имена уже проиндексированным сессиям (index берёт только изменённые файлы).
# Читает ТОЛЬКО хвост каждого JSONL, поэтому быстро даже на 19 ГБ истории.
python ~/.claude/tools/search_chats.py backfill-titles --days 120
```

Обычный `search` теперь тоже показывает строку `ЧАТ: «имя»` у каждого попадания — можно сразу
понять, из какого чата результат.

**Когда пользователь спрашивает «как назывался тот чат» / «найди чат где мы делали X»:**
сначала `titles`, и только если не нашлось — полнотекстовый `search` по содержимому.

## Actions

### Search

```bash
python ~/.claude/tools/search_chats.py search "$ARGUMENTS"
```

### Search with date filter

```bash
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --after 2026-02-01
```

### Search with limit

```bash
python ~/.claude/tools/search_chats.py search "$ARGUMENTS" --limit 20
```

### Update index (incremental)

```bash
python ~/.claude/tools/search_chats.py index
```

### Show stats

```bash
python ~/.claude/tools/search_chats.py stats
```

### Archive old sessions (>14 days)

```bash
python ~/.claude/tools/search_chats.py archive
```

## Search tips

| Syntax | Example | Description |
|--------|---------|-------------|
| Simple words | `telegram bot` | Match both words |
| Quoted phrase | `"vector memory"` | Exact phrase match |
| Prefix | `react*` | Words starting with react |
| OR | `sqlite OR postgres` | Either word |

## Examples

```
/search-chats titles сборка             # найти чат по ИМЕНИ (как в /resume)
/search-chats titles                    # последние чаты с именами
/search-chats sqlite fts5
/search-chats "extension crash" --after 2026-02-01
/search-chats telegram bot --limit 20
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
