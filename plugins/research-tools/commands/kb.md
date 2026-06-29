# Knowledge Base Search

**Arguments:** $ARGUMENTS

## Task

Search the local knowledge base (meetings, emails, chats) using SQLite FTS5 with BM25 ranking.

## Actions

### Search all sources

```bash
python ${WORKSPACE}/tools/kb.py search "$ARGUMENTS"
```

### Search specific source

```bash
python ${WORKSPACE}/tools/kb.py search "$ARGUMENTS" --source tldv
```

### Search with date filter

```bash
python ${WORKSPACE}/tools/kb.py search "$ARGUMENTS" --after 2025-01-01
```

### Search by speaker

```bash
python ${WORKSPACE}/tools/kb.py search "$ARGUMENTS" --speaker "Name"
```

### Show stats

```bash
python ${WORKSPACE}/tools/kb.py stats
```

### Show sources

```bash
python ${WORKSPACE}/tools/kb.py sources
```

### Ingest new data

```bash
python ${WORKSPACE}/tools/kb.py ingest tldv                # tl;dv transcripts
python ${WORKSPACE}/tools/kb.py ingest spark                # Spark Mail transcripts
python ${WORKSPACE}/tools/kb.py ingest telegram <file.json> # Telegram export
python ${WORKSPACE}/tools/kb.py ingest gmail [days]         # Gmail emails (default: 90)
python ${WORKSPACE}/tools/kb.py ingest gcalendar [days]     # Google Calendar (default: 365)
python ${WORKSPACE}/tools/kb.py ingest outlook [days]       # Outlook/Exchange (default: 90)
```

### Show full document

```bash
python ${WORKSPACE}/tools/kb.py doc <id>
```

## Search tips

| Syntax | Example | Description |
|--------|---------|-------------|
| Simple words | `спринт планирование` | Match both words |
| Quoted phrase | `"example-query"` | Exact phrase match |
| Prefix | `react*` | Words starting with react |
| OR | `zoom OR meet` | Either word |

## Sources

| Source | Description | Documents |
|--------|-------------|-----------|
| tldv | tl;dv meeting transcripts | XXX |
| gmail | Gmail emails | XXX |
| spark | Spark Mail AI meeting summaries | XXX |
| gcalendar | Google Calendar events | XXX |
| telegram | Telegram chat exports | (on demand) |
| outlook | Outlook/Exchange emails | XXX |

## Examples

```
/kb example-query
/kb спринт --source tldv --after 2025-01-01
/kb "ExampleGPT" --source spark
/kb stats
/kb sources
```
