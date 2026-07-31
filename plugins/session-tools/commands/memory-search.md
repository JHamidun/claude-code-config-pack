---
description: "Поиск по истории чатов + извлечённым знаниям (search_chats.py search/knowledge; --type code|error|learning|decision). Алиас-надстройка над /search-chats с доп. слоем knowledge base. Триггеры: «поищи в памяти», «memory search», «найди в базе знаний ошибку/код»."
argument-hint: "<запрос> [--type code|error|learning|decision]"
---

# Search Memory

> **Алиас `/search-chats`.** Обе команды используют один движок — `~/.claude/tools/search_chats.py` (SQLite FTS5, `~/.claude/chats.db`).
> `/memory-search` дополнительно ищет по извлечённым знаниям (knowledge base); `/search-chats` — базовый полнотекстовый поиск + управление индексом/архивом.

**Arguments:** $ARGUMENTS (search query [--type code|error|learning|decision])

## Task

Search across all chat history and accumulated knowledge using SQLite FTS5.

## Actions

1. **Search chats (full history):**

```bash
python ~/.claude/tools/search_chats.py search "$ARGUMENTS"
```

2. **Search knowledge base (extracted learnings, code, errors):**

```bash
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS"
```

3. **Search only code snippets:**

```bash
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS" --type code
```

4. **Search only errors:**

```bash
python ~/.claude/tools/search_chats.py knowledge "$ARGUMENTS" --type error
```

## Content Types

| Type | Description |
|------|-------------|
| `code` | Code, functions, configs |
| `error` | Errors and solutions |
| `learning` | Extracted knowledge |
| `decision` | Architectural decisions |
| `discussion` | Discussions |
| `question` | Questions |

## Examples

```
/memory-search FastAPI streaming
/memory-search telegram bot errors --type error
/memory-search ChromaDB vector --type code
```
