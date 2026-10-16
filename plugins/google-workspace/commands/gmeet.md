---
description: "Google Meet (REST API v2): создание встреч, инфо, записи и участники конференций. Триггеры: «создай встречу meet», «ссылка на мит». Zoom → skill zoom; Телемост → yandex."
argument-hint: "[create <название> | list | get <space_name>]"
---

# Google Meet Operations

> ⚠️ Токена с правами Meet на машине нет. Общий `google_oauth_token.json` несёт
> ТОЛЬКО скоуп `drive` — Meet REST API с ним отдаёт 403 на первом же вызове.
> Сначала завести отдельный `google_oauth_token_meet.json` со скоупами Meet
> (OAuth-прогон с `google_oauth_client.json`, тем же путём, каким подняли
> `google_oauth_token_calendar.json`), и только потом идти по шагам ниже.
> Пока токена нет — сказать владельцу об этом, а не пробовать общий.

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
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open(os.path.expanduser('~/.claude/google_oauth_token_meet.json'), 'r') as f:
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
