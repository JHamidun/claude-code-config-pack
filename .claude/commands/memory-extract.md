---
description: "Пакетное извлечение знаний из истории чатов по топикам (легаси chat_ingester_v2.py: extract-knowledge / dedupe / scan) — ошибки, код, решения, learnings. Триггеры: «извлеки знания из чатов», «сгруппируй знания по топикам». Повседневный поиск/индексация → /search-chats (канон)."
argument-hint: "[extract-knowledge | dedupe | scan]"
---

# Извлечь знания из памяти

> **Канон поиска/индексации — `~/.claude/tools/search_chats.py`** (SQLite FTS5, `~/.claude/chats.db`).
> Эта команда использует легаси-скрипт `chat_ingester_v2.py` для пакетного извлечения знаний по топикам.
> Для повседневного поиска и обновления индекса используй `/search-chats` (canonical).

## Задача

Автоматически извлечь и сгруппировать ключевые знания из всей истории чатов.

## Действия

1. **Извлечь знания по топикам:**
```bash
python ~/.claude/tools/chat_ingester_v2.py extract-knowledge
```

2. **Удалить дубликаты:**
```bash
python ~/.claude/tools/chat_ingester_v2.py dedupe
```

3. **Показать статистику:**
```bash
python ~/.claude/tools/chat_ingester_v2.py scan
```

## Что извлекается

- **Ошибки и их решения** (type: error)
- **Код и паттерны** (type: code)
- **Архитектурные решения** (type: decision)
- **Извлечённые знания** (type: learning)

## Автоматическая категоризация

Система автоматически определяет топики:
- `python`, `fastapi`, `django`
- `telegram`, `bot`
- `react`, `typescript`, `javascript`
- `postgresql`, `mongodb`, `redis`
- `docker`, `kubernetes`
- `heygen`, `elevenlabs`, `deepgram`
- и другие...

## Формат вывода

```markdown
## 📚 Extracted Knowledge by Topic:

### TELEGRAM (15 items)
  - [error] Webhook не работал из-за...
  - [code] async def handler(update)...
  - [decision] Выбрал aiogram вместо...

### FASTAPI (10 items)
  - [error] Streaming response зависал...
  - [code] @app.get("/stream")...
```
