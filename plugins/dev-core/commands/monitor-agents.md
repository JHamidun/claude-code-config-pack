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

### 3. Источники данных
Бери только то, что реально читается: `TaskOutput` запущенных задач, файлы
прогресса воркеров (`workflows-progress/<волна>/`), логи. Расход токенов,
стоимость, % от лимита и ETA задач модели не видны — не выводи их вовсе,
даже приблизительно.

### 4. Recent Completions
Последние 5 завершённых задач:
- Timestamp
- Agent
- Task
- Duration
- Output location

### 5. Alerts
⚠️ Предупреждения:
- Агенты, которые работают слишком долго
- Задачи в состоянии blocked

## Обновление
Дашборд перечитывается по запросу владельца или по событию (агент завершился,
пришло уведомление о задаче). Фонового таймера у сессии нет.

## Действия
Предложи quick actions:
- ⏸️ Pause all agents
- ▶️ Resume agents
- 🔄 Retry failed tasks
- 📊 Detailed report
