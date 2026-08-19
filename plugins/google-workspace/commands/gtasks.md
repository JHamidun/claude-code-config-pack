---
description: "Google Tasks: списки задач, создание/завершение, дедлайны. Триггеры: «задачи google», «добавь задачу в google». Todoist → /gtd."
argument-hint: "[lists | tasks <list_id> | create <список> <задача> | complete <list_id> <id>]"
---

# Google Tasks Operations

/gtasks - Работа с Google Tasks

## Описание
Управление задачами и списками задач через Google Tasks API.

## Использование
```
/gtasks lists                     - Списки задач
/gtasks tasks <list_id>           - Задачи из списка
/gtasks create <список> <задача>  - Создать задачу
/gtasks complete <list_id> <id>   - Завершить задачу
```

## Инструкции для Claude

1. **Загрузи credentials:**
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
tasks = build('tasks', 'v1', credentials=creds)
```

2. **Списки задач:**
```python
results = tasks.tasklists().list(maxResults=20).execute()
for tl in results.get('items', []):
    print(f"{tl['id']}: {tl['title']}")
```

3. **Задачи из списка:**
```python
results = tasks.tasks().list(
    tasklist='list_id_here',
    showCompleted=False,
    showHidden=False,
    maxResults=50
).execute()
for task in results.get('items', []):
    due = task.get('due', 'без срока')
    notes = task.get('notes', '')
    print(f"[{task['status']}] {task['title']} | {due}")
```

4. **Создать задачу:**
```python
task = tasks.tasks().insert(
    tasklist='list_id_here',
    body={
        'title': 'Подготовить отчёт',
        'notes': 'Детали задачи',
        'due': '2026-03-15T00:00:00.000Z'
    }
).execute()
print(f"Создана: {task['id']}")
```

5. **Завершить задачу:**
```python
task = tasks.tasks().get(tasklist='list_id', task='task_id').execute()
task['status'] = 'completed'
tasks.tasks().update(
    tasklist='list_id',
    task='task_id',
    body=task
).execute()
```

6. **Создать новый список:**
```python
new_list = tasks.tasklists().insert(
    body={'title': 'Проект YourProduct'}
).execute()
print(f"Список: {new_list['id']}")
```

## Статусы задач
- `needsAction` - не выполнена
- `completed` - завершена

## Примеры
- `/gtasks lists` - все списки задач
- `/gtasks tasks MTxxxxxxxx` - задачи конкретного списка
- `/gtasks create default "Позвонить клиенту"` - задача в дефолтный список
- `/gtasks complete MTxx task_id` - отметить выполненной
