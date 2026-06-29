# Memory Statistics

## Task

Show unified memory system statistics.

## Actions

```bash
python ${WORKSPACE}/tools/search_chats.py stats
```

## What it shows

- Sessions count and date range
- Messages count (user + assistant)
- Knowledge entries by type (learning, code, error, decision, discussion, question)
- Knowledge entries by source (qdrant, chromadb_v2, manual)
- Database size
