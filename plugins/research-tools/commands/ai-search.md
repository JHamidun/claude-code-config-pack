# /ai-search - Глубокий поиск с Perplexity AI

**Назначение:** Используй Perplexity AI для глубокого поиска и исследования по любой теме.

**Когда использовать:**
- Нужна актуальная информация из интернета
- Исследование новых технологий и API
- Анализ конкурентов и рынка
- Поиск best practices и решений

**Аргументы:**
- `query` - запрос для поиска (обязательно)

**Пример использования:**
```
/ai-search latest improvements in Claude API 2025
/ai-search Telegram bot best practices authentication
/ai-search PostgreSQL async performance optimization
```

---

## Задача для агента

Ты используешь **Perplexity AI** (`sonar` модель) для глубокого поиска информации.

**Шаги:**

1. **Получи query** из аргументов команды
2. **Используй perplexity_helper.py** для research:
   ```bash
   # ВСЕГДА используй этот путь:
   python "${WORKSPACE}\tools\perplexity_helper.py" tech "{query}"

   # Или для глубокого research:
   python "${WORKSPACE}\tools\perplexity_helper.py" research "{query}"
   ```

3. **Верни результат** в формате:
   ```markdown
   ## Результаты поиска: {query}

   {answer}

   ### Источники:
   {список источников с ссылками}
   ```

**ВАЖНО:** Всегда включай источники и ссылки!