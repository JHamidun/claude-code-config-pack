# AUTO-LEARNING

## Auto Memory (built-in)

**При КАЖДОЙ сессии** перед завершением обнови `~/.claude/projects/<project>/memory/`:

1. **MEMORY.md** — краткий индекс (до 200 строк), ссылки на topic-файлы
2. **Topic-файлы** — детальные заметки по темам (debugging.md, patterns.md, etc.)

### Что ВСЕГДА сохранять в auto memory:
- Решения багов и их root cause
- Новые паттерны, конвенции, архитектурные решения
- Ключевые команды и конфигурации которые работают
- Решения пользователя ("выбрал X потому что Y")
- Неочевидное поведение инструментов/библиотек
- Рабочие конфигурации (docker, deploy, CI/CD)

### When to update (immediately):
- Сразу после исправления бага
- Сразу после настройки нового инструмента
- Когда пользователь принимает решение
- Когда найдено неочевидное поведение
- В конце сессии — проверь, есть ли что сохранить
- **Record from SUCCESS too** — если подход сработал и был неочевиден, сохрани. Иначе будешь помнить только ошибки и станешь слишком осторожным

### Dream Consolidation (периодическая)
Раз в несколько сессий проводи "dream" — рефлексивный проход по памяти:
1. **Orient** — ls memory dir, прочитай MEMORY.md, просмотри topic-файлы
2. **Gather** — найди новую информацию: drifted memories, противоречия с кодом
3. **Consolidate** — обнови/создай файлы, конвертируй даты в абсолютные, удали противоречия
4. **Prune** — держи MEMORY.md под 200 строк и ~25KB, убери stale записи

### Формат:
- В MEMORY.md: краткая строка + ссылка на topic-файл если нужны детали
- Topic-файлы: структурированные заметки с примерами кода
- Не дублируй — сначала проверь существующие файлы

## Дополнительно: Vector Memory (ручной вызов)

```bash
python ${WORKSPACE}/tools/search_chats.py learn "knowledge" "category"
```

Категории: technical, tools, project

## Memory commands

- `/memory-search query` - search memory
- `/memory-learn content` - save knowledge
- `/memory-stats` - memory statistics
- `/memory-ingest` - index chat history
- `/search-chats query` - full-text search across all chats
