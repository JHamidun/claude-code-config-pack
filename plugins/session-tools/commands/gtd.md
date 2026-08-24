---
description: GTD orchestrator - умное управление задачами из Todoist с автоматическим workflow matching
argument-hint: [today|week|inbox|overdue|project:name|search:query]
---

# GTD Orchestrator: $ARGUMENTS

**Умный GTD workflow с интеграцией Todoist и параллельным выполнением задач**

## Твоя задача:

### Step 1: Fetch Tasks from Todoist

**Нужен токен.** Todoist → Settings → Integrations → Developer → API token.
Положи его в окружение как `TODOIST_API_TOKEN` (в паке для этого есть
`.credentials.master.env`). Нет токена — скажи об этом и остановись, не
выдумывай задачи.

В паке нет python-клиента к Todoist: ходи в их публичный REST API v1 напрямую.
Все выборки — один эндпоинт `GET /api/v1/tasks/filter` с языком фильтров
Todoist в параметре `query`:

```bash
TOK="$TODOIST_API_TOKEN"
API="https://api.todoist.com/api/v1"

fetch() {  # fetch '<todoist filter query>'
  curl -sS --get "$API/tasks/filter" \
       -H "Authorization: Bearer $TOK" \
       --data-urlencode "query=$1" \
       --data-urlencode "limit=200"
}
```

Аргумент `$ARGUMENTS` → фильтр:

| `$ARGUMENTS` | вызов |
|---|---|
| пусто или `today` | `fetch 'today \| overdue'` |
| `week` | `fetch '7 days'` |
| `inbox` | `fetch '#Inbox'` |
| `overdue` | `fetch 'overdue'` |
| `project:NAME` | `fetch '#NAME'` |
| `search:QUERY` | `fetch 'search: QUERY'` |

Ответ: `{"results": [...], "next_cursor": "..."}`. Если `next_cursor` не `null` —
дотяни следующую страницу тем же вызовом с `--data-urlencode "cursor=<...>"`,
иначе часть задач молча потеряется.

Есть и официальный SDK, если предпочитаешь Python: `pip install todoist-api-python`.

Проверить, что токен живой, до всего остального:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $TODOIST_API_TOKEN" \
  https://api.todoist.com/api/v1/projects
# 200 — годен; 401 — токен неверный или просрочен
```

### Step 2: Classify Tasks by Type

Категории задач и их workflows:

Шаблоны лежат в `.claude/workflows/` — все десять файлов в паке есть.

| Тип задачи | Keywords | Workflow |
|------------|----------|----------|
| **intro** | "intro", "познакомить", "представить", "connect" | `.claude/workflows/intro.md` |
| **cold_outreach** | "cold", "outreach", "написать незнакомому" | `.claude/workflows/cold_outreach.md` |
| **podcast** | "podcast", "подкаст", "interview", "гость" | `.claude/workflows/podcast.md` |
| **content** | "контент", "пост", "статья", "thread", "video" | `.claude/workflows/content.md` |
| **research** | "research", "найти", "изучить", "analyze" | `.claude/workflows/research.md` |
| **meeting_prep** | "подготовка", "prep", "agenda", "встреча" | `.claude/workflows/meeting_prep.md` |
| **follow_up** | "follow up", "напомнить", "проверить статус" | `.claude/workflows/follow_up.md` |
| **coding** | "код", "fix", "implement", "refactor", "bug" | `.claude/workflows/coding.md` |
| **admin** | "оплатить", "заказать", "подписать", "документ" | `.claude/workflows/admin.md` |
| **simple** | (всё остальное) | `.claude/workflows/simple.md` |

### Step 3: Execute Workflows in Parallel

Сгруппируй задачи по типу и на **каждую группу** (не на каждую задачу) спавни
одного воркера. Одним сообщением — сколько групп, столько вызовов Task: они
поедут параллельно. Больше 4-5 одновременно не запускай (`rules/models.md`).

Прочитай файл воркфлоу сам (Read) и вставь его текст в промпт — воркер не обязан
знать, где лежат шаблоны:

```
Task(
  subagent_type="general-purpose",
  model="fable",
  description="GTD: <тип> tasks",
  prompt="""
    Выполни workflow '<тип>' для задач ниже.

    ЗАДАЧИ (JSON из Todoist, поля id/content/due/project_id/priority):
    <...>

    ШАГИ WORKFLOW (текст .claude/workflows/<тип>.md):
    <...>

    Для каждой задачи: выполни шаги, отметь результат.
    Закрывать задачу в Todoist САМ НЕ ДОЛЖЕН — верни список id, которые
    считаешь выполненными, закрытие делает вызывающий (Step 4).
  """
)
```

Закрытие вынесено из воркера намеренно: это необратимое действие в чужом
аккаунте, и решать его должен один центр, а не пять параллельных агентов.

### Step 4: Monitor & Report

После выполнения всех задач:

1. **Summary Report**:
   - Сколько задач выполнено
   - Сколько в прогрессе
   - Какие заблокированы
   - Время на каждый тип

2. **Update Todoist** — по одному вызову на задачу, тем же токеном:

   ```bash
   # закрыть выполненную (204 No Content в ответ)
   curl -sS -X POST "$API/tasks/$ID/close" -H "Authorization: Bearer $TOK"

   # комментарий к задаче в прогрессе
   curl -sS -X POST "$API/comments" -H "Authorization: Bearer $TOK" \
        -H "Content-Type: application/json" \
        -d "{\"task_id\":\"$ID\",\"content\":\"...\"}"

   # перенести заблокированную
   curl -sS -X POST "$API/tasks/$ID" -H "Authorization: Bearer $TOK" \
        -H "Content-Type: application/json" \
        -d '{"due_string":"tomorrow"}'
   ```

   **Спроси владельца перед первым закрытием в сессии.** Это чужой рабочий
   список и действие необратимое; `close` на рекуррентной задаче не удаляет её,
   а сдвигает на следующее повторение — это тоже изменение, которого могли не
   ждать.

3. **Learning** (опционально):
   - Сохранить паттерны заметкой в память проекта
   - Обновить файл воркфлоу в `.claude/workflows/`, если нашёлся лучший подход

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

Обязателен здесь только Todoist. Остальное — «если у тебя это подключено»;
ничего из этого команда не поднимает сама, и отсутствие любого пункта не повод
останавливаться.

### Todoist (Primary, обязателен)
- Fetch: `GET /api/v1/tasks/filter`, `/projects`, `/labels`, `/comments`
- Update: `POST /api/v1/tasks/{id}/close`, `POST /api/v1/tasks/{id}`, `POST /api/v1/comments`
- Create: `POST /api/v1/tasks` — новые задачи из результатов воркфлоу

### Research (опционально)
- `/deep-research` — если в паке настроен Perplexity
- Иначе обычный веб-поиск; для company/person lookup в intro-задачах хватает его

### Google Calendar (опционально)
- `/gcalendar` — свободные слоты и создание событий; требует своего OAuth-токена

### Трекер разработки (опционально)
- Coding-задачи можно заводить в трекер команды. В паке для этого есть `beads`
  (git-нативный, ничего внешнего не нужно); Linear/Jira — только если у тебя
  подключён соответствующий плагин или MCP, в паке их нет.

### Память
- Выводы сессии сохраняй в память проекта. Отдельного memory-MCP в паке
  не подключено — пиши заметкой в файл.

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
