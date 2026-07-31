---
description: Self-learning mechanism - анализ ошибок и автоматическое улучшение (см. rules/auto-learning.md)
argument-hint: [analyze|session|daily|weekly]
---

# Self-Learning: $ARGUMENTS

> **Дублирует / расширяет `~/.claude/rules/auto-learning.md`** (авто-загружаемое правило AUTO-LEARNING + Auto Memory).
> Правило описывает постоянную стратегию памяти (`~/.claude/projects/<project>/memory/`, MEMORY.md, topic-файлы, dream consolidation).
> Эта команда — ручной триггер разбора сессии; сохраняй learnings в те же memory-файлы, что и правило.

**Анализирую сессию и сохраняю learnings для улучшения будущих взаимодействий**

## Концепция

Как в cybos: "LLM анализирует все ситуации где его исправляли и обновляет инструкции чтобы не повторять ошибки"

## Режимы работы

### `/self-learn` или `/self-learn analyze`
Анализ текущей сессии в реальном времени

### `/self-learn session`
Полный анализ текущей сессии с выводом learnings

### `/self-learn daily`
Ежедневный анализ за последние 24 часа (запускать в конце дня)

### `/self-learn weekly`
Еженедельный deep analysis (запускать в конце недели)

## Что анализируем

### 1. Corrections (Исправления)
```
Паттерны:
- Пользователь переформулировал запрос
- "Нет, я имел в виду..."
- "Не так, а вот так..."
- Explicit corrections
- Implicit corrections (user does it differently)

Сохраняем:
- Что было неправильно
- Как правильно
- Контекст (когда возникает)
```

### 2. Repeated Asks (Повторные запросы)
```
Паттерны:
- Те же вопросы/задачи
- Similar requests с разными формулировками

Сохраняем:
- Что часто спрашивают
- Какой ответ лучший
```

### 3. Workflow Adjustments
```
Паттерны:
- Пользователь пропускает шаги
- Пользователь добавляет шаги
- Workflow не подошёл

Сохраняем:
- Какой workflow нужно обновить
- Как именно
```

### 4. Preferences (Предпочтения)
```
Паттерны:
- Стиль коммуникации
- Формат outputs
- Tool preferences
- Timing preferences

Сохраняем:
- Preference category
- Specific preference
```

## Процесс анализа

### Step 1: Scan Session
```
Ищем в conversation:
- User corrections/feedback
- Repeated patterns
- Explicit preferences stated
- Implicit preferences shown
- What worked well
- What didn't work
```

### Step 2: Extract Learnings
```
Для каждого finding:
{
  "type": "correction|pattern|preference|workflow_update",
  "context": "what was happening",
  "issue": "what was wrong",
  "solution": "what's right",
  "confidence": 0.0-1.0,
  "category": "technical|tools|workflow|preference|project"
}
```

### Step 3: Validate & Filter
```
Criteria:
- Is this generalizable (не one-off)?
- Confidence > 0.6?
- Not already known?
- Actionable?
```

### Step 4: Save to Memory
```bash
# Для каждого validated learning:
python ~/.claude/tools/vector_memory.py learn "$LEARNING" "$CATEGORY"
```

### Step 5: Update Workflows (if applicable)
```
Если learning влияет на workflow:
1. Identify affected workflow file
2. Propose update
3. Apply if confirmed
```

### Step 6: Report
```
Output:

# Self-Learning Report
Date: [date]
Mode: [session|daily|weekly]

## Learnings Saved
1. [Learning 1] → category: [category]
2. [Learning 2] → category: [category]

## Workflow Updates Proposed
- `workflow_name.md`: [proposed change]

## Patterns Detected
- [Pattern 1]: [frequency], [recommendation]
- [Pattern 2]: [frequency], [recommendation]

## Stats
- Corrections analyzed: X
- Learnings extracted: Y
- Already known: Z
- Saved: W
```

## Learning Categories

| Category | Что включает | Пример |
|----------|--------------|--------|
| `technical` | Код, APIs, debugging | "OpenAI API требует async для streaming" |
| `tools` | Инструменты, CLI, сервисы | "Для PDF лучше использовать pdf-lib" |
| `workflow` | Процессы, последовательности | "Intro workflow: добавить шаг research" |
| `preference` | Стиль, формат, предпочтения | "Пользователь предпочитает краткие ответы" |
| `project` | Проект-специфичное | "YourProject: тесты через pytest -xvs" |
| `personal` | О пользователе | "Работает лучше утром" |

## Триггеры для auto-learn

Автоматически запускать learning когда:
- Пользователь явно исправляет
- 3+ похожих запроса за сессию
- Workflow отклонён/изменён
- Error был resolved нестандартно
- Session длится > 1 часа

## Интеграция с Memory MCP

### Сохранение
```python
# Structured learning entry
learning = {
    "content": "Описание learning",
    "category": "technical|tools|workflow|preference|project",
    "source": "self-learning",
    "confidence": 0.8,
    "context": "Когда это релевантно",
    "timestamp": "2025-01-08",
    "session_id": "xxx"
}

# Save via vector_memory.py
python ~/.claude/tools/vector_memory.py learn "{learning['content']}" "{learning['category']}"
```

### Retrieval перед ответами
```python
# Before responding, check Memory for relevant learnings:
relevant = search_memory(query=current_topic, category="all")

# Apply learnings to response
```

## Примеры Learnings

### Technical
```
- "При работе с Todoist API, due_string 'today' работает лучше чем datetime"
- "Для больших файлов использовать streaming, не загружать целиком"
```

### Workflow
```
- "Cold outreach: LinkedIn DM лучше чем email для tech людей"
- "Research workflow: всегда начинать с Memory search"
```

### Preference
```
- "Пользователь предпочитает сначала план, потом execution"
- "Формат: markdown с headers и bullets"
```

## Best Practices

1. **Не перегружать память** - сохраняем только actionable learnings
2. **Confidence threshold** - только если уверены >60%
3. **Dedupe** - проверяем что не дублируем
4. **Context** - всегда сохраняем когда применимо
5. **Review periodically** - чистить устаревшее

## Автоматизация

### Daily Cron (рекомендуется)
```bash
# В конце рабочего дня:
/self-learn daily
```

### Weekly Deep Dive
```bash
# В конце недели:
/self-learn weekly
```

### After Major Sessions
```bash
# После сложной задачи:
/self-learn session
```

---

**Начинаю self-learning анализ...**
