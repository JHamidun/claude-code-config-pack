# Ingest Chat History

**Arguments:** $ARGUMENTS (optional: --force)

## Task

Index all Claude Code chat sessions into SQLite FTS5 database for search.

## Actions

1. **Incremental index (fast, skips already indexed):**

```bash
python ${WORKSPACE}/tools/search_chats.py index
```

2. **Force full re-index:**

```bash
python ${WORKSPACE}/tools/search_chats.py index --force
```

3. **Check stats after:**

```bash
python ${WORKSPACE}/tools/search_chats.py stats
```

## Info

- Chats are stored in `~/.claude/projects/` as JSONL files
- Archived chats in `~/.claude/projects/*/archive/`
- Both active and archived sessions are indexed
- Incremental: only new/modified files are re-indexed
- Database: `~/.claude/chats.db` (SQLite FTS5)

## After indexing

- `/search-chats query` to search chats
- `/memory-search query` to search knowledge base
