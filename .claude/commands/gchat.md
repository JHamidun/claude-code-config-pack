# Google Chat Operations

/gchat - Работа с Google Chat

## Описание
Просмотр пространств, чтение и отправка сообщений через Google Chat API.

## Использование
```
/gchat spaces                    - Список пространств (чатов)
/gchat messages <space_id>       - Сообщения из пространства
/gchat send <space_id> <текст>   - Отправить сообщение
```

## Инструкции для Claude

1. **Загрузи credentials:**
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
chat = build('chat', 'v1', credentials=creds)
```

2. **Список пространств:**
```python
results = chat.spaces().list(pageSize=50).execute()
for space in results.get('spaces', []):
    stype = space.get('type', '')
    name = space.get('displayName', space.get('name'))
    print(f"{space['name']} | {stype} | {name}")
```

3. **Сообщения из пространства:**
```python
results = chat.spaces().messages().list(
    parent='spaces/AAAA_bbbb',
    pageSize=25,
    orderBy='createTime desc'
).execute()
for msg in results.get('messages', []):
    sender = msg.get('sender', {}).get('displayName', 'Unknown')
    text = msg.get('text', '')
    created = msg.get('createTime', '')
    print(f"[{created}] {sender}: {text}")
```

4. **Отправить сообщение:**
```python
result = chat.spaces().messages().create(
    parent='spaces/AAAA_bbbb',
    body={'text': 'Привет! Это сообщение из Claude Code.'}
).execute()
print(f"Отправлено: {result['name']}")
```

5. **Сообщение с карточкой:**
```python
result = chat.spaces().messages().create(
    parent='spaces/AAAA_bbbb',
    body={
        'cardsV2': [{
            'cardId': 'status-card',
            'card': {
                'header': {'title': 'Статус деплоя', 'subtitle': 'Production'},
                'sections': [{
                    'widgets': [{
                        'decoratedText': {
                            'topLabel': 'Статус',
                            'text': 'Успешно развёрнуто'
                        }
                    }]
                }]
            }
        }]
    }
).execute()
```

6. **Участники пространства:**
```python
members = chat.spaces().members().list(
    parent='spaces/AAAA_bbbb',
    pageSize=100
).execute()
for m in members.get('memberships', []):
    print(f"{m.get('member', {}).get('displayName', '')} | {m.get('role', '')}")
```

## Типы пространств
- `ROOM` - именованное пространство (группа)
- `DM` - личное сообщение
- `GROUP_CHAT` - групповой чат

## Примеры
- `/gchat spaces` - все мои чаты
- `/gchat messages spaces/AAAA_bbbb` - последние сообщения
- `/gchat send spaces/AAAA_bbbb "Деплой завершён"` - написать в чат
