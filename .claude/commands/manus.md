---
description: "Делегирование многоступенчатых задач платформе Manus AI через manus_helper.py: создание задач (режимы speed/quality/balanced), мониторинг, получение результатов. Триггеры: «manus», «делегируй манусу», «задача для manus». API-референс и capabilities платформы → skill manus (одноимённый)."
argument-hint: "\"<задача>\" [speed|quality|balanced]"
---

# Manus AI Agent - Автоматизация сложных задач

Используй Manus AI для делегирования сложных многоступенчатых задач AI агенту.

## 🎯 Для каких задач использовать Manus

### ✅ Идеально подходит для:

1. **Автоматизация рабочих процессов**
   - Обработка писем в Gmail и составление summary
   - Синхронизация данных между Notion и Google Calendar
   - Автоматические отчёты из разных источников
   - Планирование встреч и задач

2. **Многоступенчатые задачи**
   - Исследование + анализ + отчёт
   - Сбор данных + обработка + визуализация
   - Мониторинг + анализ + алерты

3. **Интеграции**
   - Gmail: чтение, отправка, организация писем
   - Notion: создание страниц, базы данных
   - Google Calendar: управление событиями
   - Slack: отправка уведомлений

4. **Задачи с ожиданием**
   - Долгосрочные задачи (часы/дни)
   - Задачи требующие external API calls
   - Задачи с асинхронным выполнением

### ❌ НЕ подходит для:

- Простые вопросы (используй обычный промпт)
- Задачи требующие мгновенного ответа
- Задачи не требующие внешних интеграций

---

## 🚀 Использование

### Инструкции для Claude:

Когда пользователь просит выполнить задачу через Manus:

1. **Используй Python helper** `tools/manus_helper.py`
2. **API ключ уже настроен** через переменную окружения `MANUS_API_KEY`
3. **Выбери режим выполнения:**
   - `speed` - быстрое выполнение (по умолчанию)
   - `quality` - качественное выполнение (для сложных задач)
   - `balanced` - баланс скорости и качества

### Пример 1: Создать задачу

```python
import sys
sys.path.append('~/.claude/tools')
from manus_helper import ManusClient

client = ManusClient()

# Создать задачу
task = client.create_task(
    prompt="Проанализируй все письма в Gmail за последнюю неделю и составь summary по проектам",
    mode="quality"
)

print(f"Задача создана: {task['id']}")
print(f"Статус: {task['status']}")
```

### Пример 2: Проверить статус задачи

```python
# Получить информацию о задаче
task = client.get_task(task_id="abc123")

print(f"Статус: {task['status']}")
if task['status'] == 'completed':
    print(f"Результат: {task['result']}")
```

### Пример 3: Список задач

```python
# Получить последние задачи
tasks = client.list_tasks(limit=10)

for task in tasks:
    print(f"{task['id']}: {task['status']} - {task['prompt']}")
```

---

## 📋 Типичные сценарии

### Сценарий 1: Еженедельный отчёт из Gmail

**Задача:**
> "Создай задачу в Manus: проанализируй все письма в Gmail за последнюю неделю и составь отчёт с важными темами и действиями"

**Решение:**
```python
task = client.create_task(
    prompt="""
    Проанализируй все письма в Gmail за последние 7 дней:
    1. Группируй по проектам
    2. Выдели важные действия (action items)
    3. Определи приоритеты
    4. Составь structured отчёт
    """,
    mode="quality"
)
```

### Сценарий 2: Синхронизация Notion + Calendar

**Задача:**
> "Синхронизируй все задачи из Notion database с Google Calendar"

**Решение:**
```python
task = client.create_task(
    prompt="""
    1. Получи все задачи из Notion database "Projects"
    2. Для каждой задачи с дедлайном:
       - Создай событие в Google Calendar
       - Установи напоминание за 1 день
       - Добавь ссылку на Notion в описание
    3. Верни summary созданных событий
    """,
    mode="balanced"
)
```

### Сценарий 3: Автоматический мониторинг

**Задача:**
> "Настрой автоматический мониторинг упоминаний компании в Gmail"

**Решение:**
```python
# Создать задачу с webhook для уведомлений
task = client.create_task(
    prompt="""
    Каждый день в 9:00:
    1. Проверяй новые письма в Gmail
    2. Ищи упоминания компании "YourCompany"
    3. Если найдены - отправь алерт
    """,
    mode="speed",
    webhook_url="https://your-webhook.com/manus-alerts"
)
```

---

## 🔧 CLI команды

Альтернативно можно использовать через CLI:

```bash
# Установить API ключ
export MANUS_API_KEY="sk-..."

# Создать задачу
python tools/manus_helper.py create "Задача для Manus" --mode quality

# Проверить статус
python tools/manus_helper.py get <task-id>

# Список задач
python tools/manus_helper.py list --status completed
```

---

## ⚙️ Конфигурация

### API ключ уже настроен:

```bash
MANUS_API_KEY=YOUR_MANUS_API_KEY
```

Ключ должен быть в `.env` файле или переменной окружения.

---

## 📊 Best Practices

### 1. Выбор режима:

- **speed** - для простых задач (< 5 минут)
- **balanced** - для средних задач (5-30 минут)
- **quality** - для сложных задач (> 30 минут)

### 2. Формулирование задач:

✅ **Хорошо:**
```
Проанализируй все письма в Gmail за неделю:
1. Группируй по отправителям
2. Выдели важные темы
3. Составь summary с action items
```

❌ **Плохо:**
```
Посмотри почту
```

### 3. Использование webhooks:

Для долгих задач добавь webhook:
```python
task = client.create_task(
    prompt="...",
    webhook_url="https://n8n.example.com/webhook/manus"
)
```

---

## 🔗 Интеграции

Manus имеет встроенные connectors:

- **Gmail** - чтение/отправка писем
- **Notion** - управление базами данных
- **Google Calendar** - события и напоминания
- **Slack** - отправка сообщений

Просто укажи в prompt какой сервис использовать.

---

## 📚 Документация

- **API Reference:** https://open.manus.ai/docs
- **Helper код:** `tools/manus_helper.py`
- **Полный гайд:** `MANUS_INTEGRATION_GUIDE.md`

---

## Примеры для быстрого старта

### Email Summary:
```
/manus "Проанализируй важные письма за последние 3 дня и составь краткий отчёт"
```

### Notion + Calendar Sync:
```
/manus "Синхронизируй все задачи с дедлайнами из Notion в Google Calendar"
```

### Weekly Report:
```
/manus "Составь еженедельный отчёт по всем проектам из Notion database"
```

---

**Готово! Используй Manus для автоматизации сложных задач! 🚀**