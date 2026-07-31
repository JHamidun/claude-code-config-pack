---
description: "Сохранить знание в долгосрочную память (search_chats.py learn; категории technical/tools/workflow/preference/project). Без аргументов — анализ текущей сессии и предложение что сохранить. Триггеры: «memory learn», «сохрани в базу знаний», «запиши знание». Полный 4-уровневый пайплайн запоминания → skill save-knowledge-base."
argument-hint: "[категория]: <что запомнить>"
---

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
python ~/.claude/tools/search_chats.py learn "$CONTENT" "$CATEGORY"
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
