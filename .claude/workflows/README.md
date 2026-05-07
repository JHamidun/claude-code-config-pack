# GTD Workflow Templates

Шаблоны для автоматического выполнения задач из Todoist.

## Доступные Workflows

| Workflow | Файл | Keywords |
|----------|------|----------|
| **Intro** | `intro.md` | intro, познакомить, представить, connect |
| **Cold Outreach** | `cold_outreach.md` | cold, outreach, написать незнакомому |
| **Podcast** | `podcast.md` | podcast, подкаст, interview, гость |
| **Content** | `content.md` | контент, пост, статья, thread, video |
| **Research** | `research.md` | research, найти, изучить, analyze |
| **Meeting Prep** | `meeting_prep.md` | подготовка, prep, agenda, встреча |
| **Follow Up** | `follow_up.md` | follow up, напомнить, проверить статус |
| **Coding** | `coding.md` | код, fix, implement, refactor, bug |
| **Admin** | `admin.md` | оплатить, заказать, подписать, документ |
| **Simple** | `simple.md` | всё остальное |

## Как использовать

### Команда `/gtd`

```bash
# Задачи на сегодня
/gtd today

# Задачи на неделю
/gtd week

# Входящие (inbox)
/gtd inbox

# Просроченные (срочно!)
/gtd overdue

# По проекту
/gtd project:Personal

# Поиск
/gtd search:John
```

### Автоматическая классификация

Каждая задача из Todoist автоматически классифицируется по keywords:

```
Задача: "Познакомить Васю с Петей"
→ Keyword: "познакомить"
→ Workflow: intro.md
```

### Parallel Execution

Задачи группируются по типу и выполняются параллельно:

```
Группа 1: intro tasks → Agent 1
Группа 2: research tasks → Agent 2
Группа 3: coding tasks → Agent 3
```

## Структура Workflow файла

```markdown
# Workflow: [Name]

> Короткое описание

## Keywords
`keyword1`, `keyword2`, `keyword3`

## Inputs
- **task**: описание задачи
- **context**: дополнительный контекст

## Steps
### 1. Step Name
Что делать...

### 2. Another Step
...

## Quality Checks
- [ ] Check 1
- [ ] Check 2

## Completion Criteria
Когда считать задачу выполненной

## Time Estimate
- **Typical**: X min
- **Max**: Y min

## Notes
Дополнительные заметки
```

## Добавление нового Workflow

1. Создай файл `workflow_name.md` в этой директории
2. Следуй структуре выше
3. Добавь keywords в начало файла
4. Обнови этот README

## Self-Learning

GTD система учится на каждом выполнении:

1. **Успешные выполнения** → сохраняются как примеры
2. **Корректировки** → обновляют workflow
3. **Время выполнения** → улучшает estimates
4. **Response rates** → оптимизирует templates

Данные сохраняются в Memory MCP для анализа.

## Интеграции

- **Todoist**: источник задач, обновление статусов
- **Memory MCP**: контекст, история, обучение
- **Linear**: work tasks (auto-route by keywords)
- **Calendar**: meeting-related tasks
- **Perplexity**: research tasks
- **Email/Telegram**: communication tasks

---

Created: see git history
Updated: see git history
