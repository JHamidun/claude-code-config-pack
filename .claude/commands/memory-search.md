# Search Memory

**Arguments:** $ARGUMENTS (search query [--type code|error|learning|decision])

## Task

Search across all chat history and accumulated knowledge using SQLite FTS5.

## Actions

1. **Search chats (full history):**

```bash
python ${WORKSPACE}/tools/search_chats.py search "$ARGUMENTS"
```

2. **Search knowledge base (extracted learnings, code, errors):**

```bash
python ${WORKSPACE}/tools/search_chats.py knowledge "$ARGUMENTS"
```

3. **Search only code snippets:**

```bash
python ${WORKSPACE}/tools/search_chats.py knowledge "$ARGUMENTS" --type code
```

4. **Search only errors:**

```bash
python ${WORKSPACE}/tools/search_chats.py knowledge "$ARGUMENTS" --type error
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
