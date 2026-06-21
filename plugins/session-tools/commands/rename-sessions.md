# Rename Sessions Command

**Массовое переименование сессий Claude Code с информативными заголовками**

## Что делает

1. Сканирует все JSONL файлы сессий в `~/.claude/projects/C--Users-youruser/`
2. Фильтрует только пользовательские сессии (не agent-*, не warmup-*)
3. Извлекает глубокий контекст из каждой сессии:
   - Все user сообщения (до 10)
   - Все assistant ответы (до 5)
   - Использованные инструменты
4. Генерирует информативные заголовки через Sonnet субагенты (параллельно)
5. Применяет заголовки к первому user сообщению в формате `[Title] original text`

## Когда использовать

- Когда нужно переименовать все существующие сессии
- После накопления большого количества сессий без заголовков
- Для обновления заголовков с учётом нового контекста

## Процесс выполнения

### Шаг 1: Сканирование и фильтрация

```python
import glob
import json
import os

# Найти все сессии
session_files = glob.glob('${HOME}/.claude/projects/C--Users-youruser/*.jsonl')

# Фильтровать пользовательские
user_sessions = []
for fpath in session_files:
    fname = os.path.basename(fpath).replace('.jsonl', '')
    if not fname.startswith('agent-') and not fname.startswith('warmup-'):
        user_sessions.append(fname)

print(f"Найдено {len(user_sessions)} пользовательских сессий")
```

### Шаг 2: Извлечение контекста

```python
def extract_context(session_id):
    session_path = f"${HOME}/.claude/projects/C--Users-youruser/{session_id}.jsonl"

    with open(session_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    user_messages = []
    assistant_messages = []
    tools_used = set()

    for line in lines:
        try:
            item = json.loads(line.strip())

            # User messages
            if item.get('type') == 'user' and 'message' in item:
                msg = item['message']
                if 'content' in msg:
                    for content_item in msg['content']:
                        if content_item.get('type') == 'text':
                            text = content_item['text']
                            # Очистка от системных тегов
                            if '<system-reminder>' in text:
                                text = text.split('<system-reminder>')[0].strip()
                            if '<ide_selection>' in text:
                                text = text.split('<ide_selection>')[0].strip()
                            if '<ide_opened_file>' in text:
                                text = text.split('<ide_opened_file>')[0].strip()
                            if text and len(text) > 10:
                                user_messages.append(text[:500])

            # Assistant messages
            elif item.get('type') == 'assistant' and 'message' in item:
                msg = item['message']
                if 'content' in msg:
                    for content_item in msg['content']:
                        if content_item.get('type') == 'text':
                            text = content_item['text']
                            if text and len(text) > 10:
                                assistant_messages.append(text[:300])
                        elif content_item.get('type') == 'tool_use':
                            tools_used.add(content_item.get('name', 'unknown'))

        except json.JSONDecodeError:
            continue

    return {
        'session_id': session_id,
        'user_messages': user_messages[:10],
        'assistant_messages': assistant_messages[:5],
        'tools_used': list(tools_used)
    }

# Извлечь контекст для всех сессий
contexts = [extract_context(sid) for sid in user_sessions if has_user_message(sid)]
```

### Шаг 3: Генерация заголовков (параллельно)

```python
# Разбить на батчи по 40-50 сессий
batch_size = 45
batches = [contexts[i:i+batch_size] for i in range(0, len(contexts), batch_size)]

# Запустить Sonnet субагенты параллельно
all_titles = {}

for i, batch in enumerate(batches):
    # Сохранить batch в JSON
    batch_path = f"{scratchpad}/batch_{i+1}.json"
    with open(batch_path, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)

    # Запустить субагента
    task = Task(
        subagent_type="general-purpose",
        model="sonnet",
        prompt=f"""
Сгенерируй информативные заголовки для {len(batch)} сессий Claude Code.

Входной файл: {batch_path}

Каждая сессия содержит:
- user_messages: все сообщения пользователя
- assistant_messages: ответы ассистента
- tools_used: использованные инструменты

Заголовок должен:
- Отражать СУТЬ работы (не только первый вопрос)
- Быть кратким (3-7 слов) на русском
- Включать конкретику (названия проектов, технологий)

Примеры:
- "Разработка Telegram Mini App для YourProject"
- "Настройка интеграции Todoist и Google Calendar"
- "Презентация FM Logistic AI Overview"

Верни JSON:
{{"session-id": "Title", ...}}

Сохрани результат в: {scratchpad}/titles_{i+1}.json
"""
    )

    # Прочитать результат
    with open(f"{scratchpad}/titles_{i+1}.json", 'r', encoding='utf-8') as f:
        batch_titles = json.load(f)
        all_titles.update(batch_titles)

print(f"Сгенерировано {len(all_titles)} заголовков")
```

### Шаг 4: Применение заголовков

```python
def apply_title(session_id, title):
    session_path = f"${HOME}/.claude/projects/C--Users-youruser/{session_id}.jsonl"

    with open(session_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        try:
            item = json.loads(line.strip())

            # Найти первое user сообщение
            if not modified and item.get('type') == 'user' and 'message' in item:
                msg = item['message']
                if 'content' in msg:
                    for content_item in msg['content']:
                        if content_item.get('type') == 'text':
                            text = content_item['text']

                            # Пропустить системные теги
                            if ('<ide_opened_file>' in text or
                                '<ide_selection>' in text or
                                '<ide_closed_file>' in text or
                                len(text.strip()) < 5):
                                continue

                            # Убрать старый заголовок
                            if text.startswith('[') and '] ' in text[:200]:
                                bracket_end = text.find('] ')
                                text = text[bracket_end+2:]

                            # Добавить новый заголовок
                            content_item['text'] = f'[{title}] {text}'
                            modified = True
                            break

            new_lines.append(json.dumps(item, ensure_ascii=False) + '\n')

        except json.JSONDecodeError:
            new_lines.append(line)

    if modified:
        with open(session_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

# Применить все заголовки
applied = 0
for session_id, title in all_titles.items():
    if apply_title(session_id, title):
        applied += 1

print(f"Применено {applied} заголовков")
```

### Шаг 5: Статистика

```python
# Финальная проверка
total_sessions = len(user_sessions)
sessions_with_titles = count_sessions_with_titles()
sessions_without_titles = total_sessions - sessions_with_titles - empty_sessions

print(f"""
=== ИТОГИ ===
Всего пользовательских сессий: {total_sessions}
✅ С заголовками: {sessions_with_titles}
❌ Без заголовков: {sessions_without_titles}
⚠️  Пустых/технических: {empty_sessions}

Перезапусти VS Code для обновления sidebar!
""")
```

## Требования

- Claude Code Max подписка (для Sonnet субагентов)
- Python 3.7+
- Доступ к `~/.claude/projects/`

## Результат

- Все валидные сессии получают информативные заголовки
- Заголовки отображаются в VS Code sidebar
- Формат: `[Информативный заголовок] исходный текст`

## Notes

- Обработка происходит батчами по 40-50 сессий
- Используется параллельное выполнение Sonnet субагентов
- Пустые и технические сессии пропускаются
- Старые заголовки автоматически заменяются
