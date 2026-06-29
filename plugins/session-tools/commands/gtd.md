---
description: GTD orchestrator - умное управление задачами из Todoist с автоматическим workflow matching
argument-hint: [today|week|inbox|overdue|project:name|search:query]
---

# GTD Orchestrator: $ARGUMENTS

**Умный GTD workflow с интеграцией Todoist и параллельным выполнением задач**

## Твоя задача:

### Step 1: Fetch Tasks from Todoist

В зависимости от аргумента ($ARGUMENTS):

```python
from src.actions.tasks.todoist import TodoistClient, TodoistActions

todoist = TodoistActions()

# Варианты:
# today (default) - задачи на сегодня
# week - задачи на неделю
# inbox - входящие без проекта
# overdue - просроченные (URGENT!)
# project:name - задачи конкретного проекта
# search:query - поиск по тексту

if "$ARGUMENTS" == "today" or "$ARGUMENTS" == "":
    tasks = todoist.get_daily_digest()
elif "$ARGUMENTS" == "week":
    tasks = todoist.client.get_tasks_week()
elif "$ARGUMENTS" == "inbox":
    tasks = todoist.client.get_inbox_tasks()
elif "$ARGUMENTS" == "overdue":
    tasks = todoist.client.get_overdue_tasks()
elif "$ARGUMENTS".startswith("project:"):
    project_name = "$ARGUMENTS".replace("project:", "")
    tasks = todoist.client.get_tasks_by_project(project_name)
elif "$ARGUMENTS".startswith("search:"):
    query = "$ARGUMENTS".replace("search:", "")
    tasks = todoist.client.search_tasks(query)
```

### Step 2: Classify Tasks by Type

Категории задач и их workflows:

| Тип задачи | Keywords | Workflow |
|------------|----------|----------|
| **intro** | "intro", "познакомить", "представить", "connect" | `workflows/intro.md` |
| **cold_outreach** | "cold", "outreach", "написать незнакомому" | `workflows/cold_outreach.md` |
| **podcast** | "podcast", "подкаст", "interview", "гость" | `workflows/podcast.md` |
| **content** | "контент", "пост", "статья", "thread", "video" | `workflows/content.md` |
| **research** | "research", "найти", "изучить", "analyze" | `workflows/research.md` |
| **meeting_prep** | "подготовка", "prep", "agenda", "встреча" | `workflows/meeting_prep.md` |
| **follow_up** | "follow up", "напомнить", "проверить статус" | `workflows/follow_up.md` |
| **coding** | "код", "fix", "implement", "refactor", "bug" | `workflows/coding.md` |
| **admin** | "оплатить", "заказать", "подписать", "документ" | `workflows/admin.md` |
| **simple** | (всё остальное) | Выполнить напрямую |

### Step 3: Execute Workflows in Parallel

```python
# Группируем задачи по типу
task_groups = classify_tasks(tasks)

# Parallel execution для независимых задач
for task_type, task_list in task_groups.items():
    workflow = load_workflow(task_type)

    # Параллельный запуск агентов для каждой задачи в группе
    Task(
        subagent_type="general-purpose",
        prompt=f"""
        Выполни workflow '{task_type}' для задач:
        {json.dumps(task_list, indent=2)}

        Workflow steps:
        {workflow}

        Для каждой задачи:
        1. Выполни все шаги workflow
        2. Отметь прогресс
        3. Если задача завершена - пометь в Todoist как done
        """,
        description=f"GTD: {task_type} tasks",
        run_in_background=True  # Параллельное выполнение
    )
```

### Step 4: Monitor & Report

После выполнения всех задач:

1. **Summary Report**:
   - Сколько задач выполнено
   - Сколько в прогрессе
   - Какие заблокированы
   - Время на каждый тип

2. **Update Todoist**:
   - Пометить completed tasks как done
   - Добавить комментарии к задачам в прогрессе
   - Перенести blocked задачи с новым due date

3. **Learning** (опционально):
   - Сохранить паттерны в Memory MCP
   - Обновить workflow если найден лучший подход

## Workflow Templates

Каждый workflow template содержит:

```markdown
# Workflow: [Type]

## Inputs
- task: описание задачи
- context: дополнительный контекст из Todoist

## Steps
1. Step 1: [description]
   - Tool: [tool to use]
   - Output: [expected output]

2. Step 2: [description]
   ...

## Quality Checks
- [ ] Check 1
- [ ] Check 2

## Completion Criteria
- Что значит "задача выполнена"

## Time Estimate
- Typical: X minutes
- Max: Y minutes
```

## Специальные команды:

### Quick Actions
- `/gtd` - задачи на сегодня с автоматическим workflow
- `/gtd inbox` - разбор входящих
- `/gtd overdue` - срочное: просроченные задачи
- `/gtd week` - планирование недели

### Project Focus
- `/gtd project:Personal` - личные задачи
- `/gtd project:Work` - рабочие задачи
- `/gtd project:YourProject` - задачи по проекту YourProject

### Search
- `/gtd search:John` - все задачи связанные с John
- `/gtd search:email` - все email-related задачи

## Output Format

```json
{
  "session": {
    "started_at": "timestamp",
    "argument": "$ARGUMENTS",
    "total_tasks": 15
  },
  "task_groups": {
    "intro": {
      "count": 3,
      "tasks": ["...", "...", "..."],
      "workflow": "intro.md",
      "status": "completed|in_progress|pending"
    },
    "research": {
      "count": 2,
      "tasks": ["...", "..."],
      "workflow": "research.md",
      "status": "completed"
    }
  },
  "execution": {
    "completed": 8,
    "in_progress": 4,
    "blocked": 2,
    "skipped": 1
  },
  "time_spent": {
    "total": "45 min",
    "by_type": {
      "intro": "15 min",
      "research": "20 min",
      "content": "10 min"
    }
  },
  "todoist_updates": {
    "marked_done": ["task_id_1", "task_id_2"],
    "rescheduled": ["task_id_3"],
    "comments_added": ["task_id_4"]
  },
  "learnings": [
    "Intro template работает лучше с LinkedIn context",
    "Research tasks нужно разбивать на subtasks"
  ]
}
```

## Integration Points

### Todoist (Primary)
- Fetch: tasks, projects, labels, comments
- Update: complete, reschedule, add comments
- Create: new tasks from workflow outputs

### Memory MCP (Context)
- Store: workflow learnings, contact info, past interactions
- Recall: relevant context для каждой задачи

### Perplexity/AI Search (Research)
- Deep research для research tasks
- Company/person lookup для intro tasks

### Linear (Work Tasks)
- Route work-related coding tasks to Linear
- Sync status between Todoist и Linear

### Google Calendar
- Check availability для meeting-related tasks
- Create calendar events для scheduled outcomes

## Пример использования:

**Input:** `/gtd today`

**Claude выполняет:**

1. Получает задачи на сегодня из Todoist (12 задач)

2. Классифицирует:
   - 3 intro tasks
   - 2 cold outreach
   - 4 coding tasks
   - 1 research
   - 2 admin

3. Запускает parallel agents:
   ```
   Agent 1: Intro workflow (3 tasks)
   Agent 2: Cold outreach workflow (2 tasks)
   Agent 3: Coding workflow (4 tasks)
   Agent 4: Research workflow (1 task)
   Agent 5: Admin workflow (2 tasks)
   ```

4. Каждый agent:
   - Загружает свой workflow template
   - Выполняет steps для каждой задачи
   - Отмечает прогресс
   - Завершает или переносит задачу

5. Собирает результаты:
   - 10 задач completed
   - 2 в прогрессе (ждут ответа)
   - Обновляет Todoist
   - Сохраняет learnings

---

**Начинаем GTD сессию!**
