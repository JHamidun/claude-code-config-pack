# /session-save - Сохранить контекст сессии в Memory

**Назначение:** Сохраняет текущую работу в Memory MCP для доступа в будущих сессиях.

**Когда использовать:**
- После завершения работы над фичей
- Перед закрытием Claude Code
- После важных решений или достижений
- Когда нужно передать контекст в следующую сессию

**Аргументы:**
- `summary` - краткое описание что сделано (опционально)

**Примеры:**
```
/session-save "Completed payment integration"
/session-save "Fixed Safari login bug"
/session-save
```

---

## Задача для агента

Сохрани текущий контекст сессии в Memory MCP для использования в будущих сессиях.

**Шаги:**

### 1. Собери контекст текущей сессии
```python
# Определи что было сделано в этой сессии
context = {
    "date": datetime.now().isoformat(),
    "tasks_completed": [],  # список завершенных задач
    "files_modified": [],   # измененные файлы
    "decisions_made": [],   # важные решения
    "next_steps": [],       # что делать дальше
    "issues_found": [],     # найденные проблемы
    "tools_used": []        # использованные инструменты
}
```

### 2. Сохрани в Memory MCP через knowledge graph
```python
# Создай entities для основных концепций
mcp__memory__create_entities({
    "entities": [
        {
            "name": f"Session_{date}",
            "entityType": "work_session",
            "observations": [
                f"Date: {context['date']}",
                f"Tasks: {', '.join(context['tasks_completed'])}",
                f"Modified: {', '.join(context['files_modified'])}",
                f"Decisions: {', '.join(context['decisions_made'])}"
            ]
        }
    ]
})

# Создай relations для связей
mcp__memory__create_relations({
    "relations": [
        {
            "from": f"Session_{date}",
            "to": "Project_YourProject",
            "relationType": "works_on"
        },
        {
            "from": f"Session_{date}",
            "to": f"Session_{previous_date}",
            "relationType": "continues"
        }
    ]
})

# Добавь детали к проекту
mcp__memory__add_observations({
    "observations": [
        {
            "entityName": "Project_YourProject",
            "contents": [
                f"Latest work: {context['tasks_completed'][0]}",
                f"Last modified: {context['date']}",
                f"Next: {context['next_steps'][0]}"
            ]
        }
    ]
})
```

### 3. Сохрани специфичные контексты

#### Если работали над фичей:
```python
mcp__memory__create_entities({
    "entities": [
        {
            "name": f"Feature_{feature_name}",
            "entityType": "feature",
            "observations": [
                f"Status: {status}",
                f"Files: {files}",
                f"Tests: {test_status}",
                f"Deployed: {deployed}"
            ]
        }
    ]
})
```

#### Если фиксили баг:
```python
mcp__memory__create_entities({
    "entities": [
        {
            "name": f"Bug_{bug_id}",
            "entityType": "bug",
            "observations": [
                f"Issue: {description}",
                f"Root cause: {cause}",
                f"Fix: {fix_description}",
                f"Status: {status}"
            ]
        }
    ]
})
```

#### Если делали research:
```python
mcp__memory__create_entities({
    "entities": [
        {
            "name": f"Research_{topic}",
            "entityType": "research",
            "observations": [
                f"Topic: {topic}",
                f"Key findings: {findings}",
                f"Recommendations: {recommendations}",
                f"Sources: {sources}"
            ]
        }
    ]
})
```

### 4. Создай next steps entity
```python
mcp__memory__create_entities({
    "entities": [
        {
            "name": "Next_Steps",
            "entityType": "todo",
            "observations": context['next_steps']
        }
    ]
})
```

### 5. Верни summary
```markdown
## Session Saved ✅

**Date:** {date}

**Completed:**
{список завершенных задач}

**Modified Files:**
{список файлов}

**Key Decisions:**
{список решений}

**Next Steps:**
{список next steps}

**Сохранено в Memory MCP:**
- Session_{date} entity
- {N} relations created
- Project_YourProject updated

**Восстановить в следующей сессии:**
```
/session-restore
```
```

**ВАЖНО:**
- Сохраняй КАЖДУЮ важную работу
- Используй descriptive names для entities
- Создавай relations между связанными entities
- Обновляй Project_YourProject с latest info
- Добавляй next_steps для continuity