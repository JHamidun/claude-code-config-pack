---
description: "Google Calendar: события на сегодня/неделю, создание событий, свободные слоты (Calendar API v3, OAuth). Триггеры: «календарь», «события на сегодня», «создай событие в календаре», «свободные слоты», «что у меня по расписанию»."
argument-hint: "[today | week | list <дней> | create <событие> | free]"
---

# Google Calendar Operations

/gcalendar - Работа с Google Календарём

## Описание
Просмотр, создание и управление событиями в Google Calendar.

## Использование
```
/gcalendar today              - События на сегодня
/gcalendar week               - События на неделю
/gcalendar list [дней]        - События на N дней
/gcalendar create <событие>   - Создать событие
/gcalendar free               - Свободные слоты
```

## Инструкции для Claude

1. **Загрузи credentials:**
```python
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('${HOME}/.claude/google_oauth_token.json', 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)
calendar = build('calendar', 'v3', credentials=creds)
```

2. **Получить события:**
```python
now = datetime.utcnow().isoformat() + 'Z'
end = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

events_result = calendar.events().list(
    calendarId='primary',
    timeMin=now,
    timeMax=end,
    maxResults=50,
    singleEvents=True,
    orderBy='startTime'
).execute()
events = events_result.get('items', [])

for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(f"{start}: {event['summary']}")
```

3. **Создать событие:**
```python
event = {
    'summary': 'Встреча с командой',
    'location': 'Zoom',
    'description': 'Обсуждение проекта',
    'start': {
        'dateTime': '2025-12-22T10:00:00',
        'timeZone': 'UTC',
    },
    'end': {
        'dateTime': '2025-12-22T11:00:00',
        'timeZone': 'UTC',
    },
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 10},
        ],
    },
}
event = calendar.events().insert(calendarId='primary', body=event).execute()
```

4. **Список календарей:**
```python
calendar_list = calendar.calendarList().list().execute()
for cal in calendar_list.get('items', []):
    print(f"{cal['summary']} ({cal['id']})")
```

5. **Удалить событие:**
```python
calendar.events().delete(calendarId='primary', eventId=event_id).execute()
```

## Форматы времени
- Полное: `2025-12-22T10:00:00+03:00`
- Весь день: `2025-12-22` (без времени)
- TimeZone: `UTC`, `UTC`

## Примеры
- `/gcalendar today` - что запланировано на сегодня
- `/gcalendar week` - расписание на неделю
- `/gcalendar create "Созвон в 15:00 завтра"` - создать событие
