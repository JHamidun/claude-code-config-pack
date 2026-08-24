---
description: "Google Analytics 4: аккаунты, properties, отчёты по трафику (GA4 Data+Admin API). Триггеры: «GA4», «аналитика google», «трафик в GA»."
argument-hint: "[accounts | properties | report <property_id>]"
---

# Google Analytics (GA4) Operations

/ganalytics - Работа с Google Analytics 4

## Описание
Просмотр аккаунтов, ресурсов и получение отчётов через GA4 API.

## Использование
```
/ganalytics accounts              - Список аккаунтов
/ganalytics properties            - Ресурсы (properties)
/ganalytics report <property_id>  - Отчёт по ресурсу
```

## Инструкции для Claude

1. **Загрузи credentials:**
```python
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open(os.path.expanduser('~/.claude/google_oauth_token.json'), 'r') as f:
    token_data = json.load(f)
creds = Credentials.from_authorized_user_info(token_data)

# Data API (отчёты)
analytics_data = build('analyticsdata', 'v1beta', credentials=creds)
# Admin API (аккаунты, ресурсы)
analytics_admin = build('analyticsadmin', 'v1beta', credentials=creds)
```

2. **Список аккаунтов:**
```python
accounts = analytics_admin.accounts().list().execute()
for acc in accounts.get('accounts', []):
    print(f"{acc['name']} | {acc['displayName']}")
```

3. **Список ресурсов:**
```python
properties = analytics_admin.properties().list(
    filter="parent:accounts/123456789"
).execute()
for prop in properties.get('properties', []):
    print(f"{prop['name']} | {prop['displayName']}")
```

4. **Отчёт — трафик за 30 дней:**
```python
report = analytics_data.properties().runReport(
    property='properties/123456789',
    body={
        'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'pagePath'}],
        'metrics': [
            {'name': 'activeUsers'},
            {'name': 'screenPageViews'},
            {'name': 'averageSessionDuration'}
        ],
        'limit': 25,
        'orderBys': [{'metric': {'metricName': 'activeUsers'}, 'desc': True}]
    }
).execute()

for row in report.get('rows', []):
    page = row['dimensionValues'][0]['value']
    users = row['metricValues'][0]['value']
    views = row['metricValues'][1]['value']
    print(f"{page} | users: {users} | views: {views}")
```

5. **Отчёт — география:**
```python
report = analytics_data.properties().runReport(
    property='properties/123456789',
    body={
        'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'city'}, {'name': 'country'}],
        'metrics': [{'name': 'activeUsers'}, {'name': 'sessions'}],
        'limit': 20,
        'orderBys': [{'metric': {'metricName': 'activeUsers'}, 'desc': True}]
    }
).execute()
```

6. **Отчёт — источники трафика:**
```python
report = analytics_data.properties().runReport(
    property='properties/123456789',
    body={
        'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'sessionSource'}, {'name': 'sessionMedium'}],
        'metrics': [{'name': 'sessions'}, {'name': 'activeUsers'}, {'name': 'conversions'}],
        'limit': 25
    }
).execute()
```

## Популярные dimensions
- `pagePath`, `pageTitle`, `city`, `country`
- `sessionSource`, `sessionMedium`, `deviceCategory`
- `date`, `dayOfWeek`, `hour`

## Популярные metrics
- `activeUsers`, `sessions`, `screenPageViews`
- `averageSessionDuration`, `bounceRate`, `conversions`
- `newUsers`, `eventCount`, `engagementRate`

## Примеры
- `/ganalytics accounts` - мои GA4 аккаунты
- `/ganalytics report 123456789` - топ страницы за 30 дней
