# Save to Memory

**Arguments:** $ARGUMENTS (what to remember)

## Task

Save new knowledge to long-term memory (SQLite FTS5).

## Format

```
/memory-learn [category]: [content]
```

## Categories

- `technical` - technical knowledge (code, patterns, debugging)
- `tools` - tools and usage
- `workflow` - work processes
- `preference` - user preferences
- `project` - project info

## Actions

1. **Parse arguments:**
   - If contains ":" - first part = category
   - Otherwise category = "general"

2. **Save:**
```bash
python ${WORKSPACE}/tools/search_chats.py learn "$CONTENT" "$CATEGORY"
```

3. **Confirm:**
   - Show what was saved
   - Category
   - Timestamp

## Examples

```
/memory-learn technical: ChromaDB crashes Extension Host on Windows
/memory-learn preference: User prefers TypeScript for frontend
/memory-learn Always use uv instead of pip for Python projects
```

## Auto-Learning Prompt

If just `/memory-learn` without arguments:
1. Analyze current session
2. Suggest what to save
3. Ask for confirmation
