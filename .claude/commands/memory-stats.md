---
description: "Статистика единой памяти (search_chats.py stats): число сессий и сообщений, knowledge-записи по типам и источникам, размер БД. Триггеры: «memory stats», «статистика памяти», «сколько в базе знаний»."
---

# Memory Statistics

## Task

Show unified memory system statistics.

## Actions

```bash
python ~/.claude/tools/search_chats.py stats
```

## What it shows

- Sessions count and date range
- Messages count (user + assistant)
- Knowledge entries by type (learning, code, error, decision, discussion, question)
- Knowledge entries by source (qdrant, chromadb_v2, manual)
- Database size
