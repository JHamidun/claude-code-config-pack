# /session-restore - Восстановить контекст из Memory

**Назначение:** Загружает контекст из предыдущих сессий из Memory MCP.

**Когда использовать:**
- В начале новой сессии
- Когда нужно вспомнить что делали раньше
- Перед продолжением работы над фичей

**Примеры:**
```
/session-restore
/session-restore last
/session-restore "payment feature"
```

---

## Задача для агента

Восстанови контекст из Memory MCP и покажи пользователю где остановились.

**Шаги:**

### 1. Загрузи knowledge graph
```python
# Получи весь граф
graph = mcp__memory__read_graph()

# Или поищи конкретные entities
results = mcp__memory__search_nodes({
    "query": "Session OR Project_YourProject OR Next_Steps"
})
```

### 2. Найди последнюю сессию
```python
# Найди последнюю work_session
sessions = [e for e in graph.entities if e.entityType == "work_session"]
latest_session = max(sessions, key=lambda s: s.observations[0])  # по дате

# Получи детали
session_details = mcp__memory__open_nodes({
    "names": [latest_session.name]
})
```

### 3. Загрузи контекст проекта
```python
# Получи текущее состояние проекта
project = mcp__memory__open_nodes({
    "names": ["Project_YourProject"]
})

# Получи next steps
next_steps = mcp__memory__open_nodes({
    "names": ["Next_Steps"]
})
```

### 4. Загрузи активные фичи/баги
```python
# Найди незавершенные фичи
active_features = mcp__memory__search_nodes({
    "query": "Feature AND Status:in_progress"
})

# Найди открытые баги
open_bugs = mcp__memory__search_nodes({
    "query": "Bug AND Status:open"
})

# Найди последние research
recent_research = mcp__memory__search_nodes({
    "query": "Research"
})
```

### 5. Верни comprehensive summary
```markdown
## 📚 Session Context Restored

### 🕐 Last Session: {date}

**What was done:**
{tasks from latest session}

**Files modified:**
{files list}

**Key decisions:**
{decisions}

---

### 📊 Project Status

**Current State:**
{project observations}

**Active Features:**
{list of in_progress features}

**Open Issues:**
{list of open bugs}

**Recent Research:**
{list of research topics}

---

### ✅ Next Steps (from last session):

1. {next step 1}
2. {next step 2}
3. {next step 3}

---

### 🔗 Related Context:

**Features in Progress:**
- {feature 1}: {status}
- {feature 2}: {status}

**Recent Decisions:**
- {decision 1}
- {decision 2}

**Tools & Configs:**
- MCP Servers: {list}
- AI Services: {list}
- Last used: {tools}

---

**Ready to continue! Что продолжаем?**
```

**ВАЖНО:**
- Всегда восстанавливай контекст в начале сессии
- Показывай ПОЛНУЮ картину что было сделано
- Выделяй next steps для continuity
- Упоминай важные решения и блокеры