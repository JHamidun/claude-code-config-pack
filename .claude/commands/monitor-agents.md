---
description: Мониторинг выполнения параллельных агентов
---

# Agent Execution Dashboard

## Показать статус всех running agents:

### 1. Active Agents
Перечисли все активные агенты и их текущие задачи:
- Имя агента
- Текущая задача
- Время работы
- Статус (running/blocked/waiting)

### 2. Progress Overview
- ✅ Completed tasks: [число]
- ⏳ Pending tasks: [число]
- 🔄 In progress: [число]
- ❌ Failed tasks: [число]

### 3. Token Usage
Для каждого агента:
- Использовано tokens
- Примерная стоимость
- % от лимита

### 4. Estimated Time Remaining
На основе текущего прогресса:
- ETA для каждой задачи
- Общий ETA для всего цикла

### 5. Recent Completions
Последние 5 завершённых задач:
- Timestamp
- Agent
- Task
- Duration
- Output location

### 6. Alerts
⚠️ Предупреждения:
- Агенты, которые работают слишком долго
- Token usage близок к лимиту
- Задачи в состоянии blocked

## Обновление
Обновляй этот дашборд каждые 30 секунд автоматически.

## Действия
Предложи quick actions:
- ⏸️ Pause all agents
- ▶️ Resume agents
- 🔄 Retry failed tasks
- 📊 Detailed report
