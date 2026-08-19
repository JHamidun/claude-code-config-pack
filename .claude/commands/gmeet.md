---
description: "Google Meet: создание встреч (OPEN/TRUSTED), информация о встрече, записи и участники конференций (Meet REST API v2). Триггеры: «google meet», «создай встречу meet», «ссылка на мит», «записи конференций». Zoom → skill zoom; Телемост → отдельный навык под Яндекс (в пак не входит)."
argument-hint: "[create <название> | list | get <space_name>]"
---

# Google Meet Operations

/gmeet - Работа с Google Meet

## Описание
Создание и управление видеовстречами через Google Meet REST API.

## Использование
```
/gmeet create [название]         - Создать встречу
/gmeet list                      - Записи конференций
/gmeet get <space_name>          - Информация о встрече
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
meet = build('meet', 'v2', credentials=creds)
```

2. **Создать встречу:**
```python
# Открытая встреча (любой с ссылкой может войти)
space = meet.spaces().create(body={
    'config': {
        'accessType': 'OPEN',
        'entryPointAccess': 'ALL'
    }
}).execute()
print(f"Ссылка: {space.get('meetingUri')}")
print(f"ID: {space.get('name')}")
print(f"Код: {space.get('meetingCode')}")

# Ограниченная встреча (нужно подтверждение)
space = meet.spaces().create(body={
    'config': {
        'accessType': 'TRUSTED',
        'entryPointAccess': 'ALL'
    }
}).execute()
```

3. **Информация о встрече:**
```python
space = meet.spaces().get(name='spaces/abc123').execute()
print(f"URI: {space.get('meetingUri')}")
print(f"Config: {space.get('config')}")
```

4. **Записи конференций:**
```python
# Список прошедших конференций
records = meet.conferenceRecords().list(
    pageSize=25
).execute()
for record in records.get('conferenceRecords', []):
    print(f"{record['name']} | start: {record.get('startTime')} | end: {record.get('endTime')}")
```

5. **Участники конференции:**
```python
participants = meet.conferenceRecords().participants().list(
    parent='conferenceRecords/abc123',
    pageSize=50
).execute()
for p in participants.get('participants', []):
    print(f"{p.get('signedinUser', {}).get('displayName', 'Anonymous')}")
```

## Типы доступа
- `OPEN` - любой с ссылкой
- `TRUSTED` - только приглашённые / с подтверждением
- `RESTRICTED` - только приглашённые из организации

## Примеры
- `/gmeet create` - быстро создать ссылку на встречу
- `/gmeet list` - прошедшие конференции
- `/gmeet get spaces/abc123` - детали встречи
