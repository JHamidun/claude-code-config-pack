# Search Chat History (SQLite FTS5)

**Arguments:** $ARGUMENTS (search query [--after DATE] [--limit N] [--role user|assistant])

## Task

Full-text search across all Claude Code chat sessions using SQLite FTS5 with BM25 ranking.

## Actions

### Search

```bash
python ${WORKSPACE}/tools/search_chats.py search "$ARGUMENTS"
```

### Search with date filter

```bash
python ${WORKSPACE}/tools/search_chats.py search "$ARGUMENTS" --after 2026-02-01
```

### Search with limit

```bash
python ${WORKSPACE}/tools/search_chats.py search "$ARGUMENTS" --limit 20
```

### Update index (incremental)

```bash
python ${WORKSPACE}/tools/search_chats.py index
```

### Show stats

```bash
python ${WORKSPACE}/tools/search_chats.py stats
```

### Archive old sessions (>14 days)

```bash
python ${WORKSPACE}/tools/search_chats.py archive
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
/search-chats sqlite fts5
/search-chats "extension crash" --after 2026-02-01
/search-chats telegram bot --limit 20
/search-chats index
/search-chats stats
```
