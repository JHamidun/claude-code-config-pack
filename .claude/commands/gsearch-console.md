# Google Search Console Operations

/gsearch-console - Работа с Google Search Console

## Описание
Анализ поисковой выдачи, запросов и карт сайта через Search Console API.

## Использование
```
/gsearch-console sites                     - Список сайтов
/gsearch-console analytics <site_url>      - Топ запросы
/gsearch-console sitemaps <site_url>       - Карты сайта
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
sc = build('searchconsole', 'v1', credentials=creds)
```

2. **Список сайтов:**
```python
sites = sc.sites().list().execute()
for site in sites.get('siteEntry', []):
    print(f"{site['siteUrl']} | {site['permissionLevel']}")
```

3. **Топ поисковых запросов (30 дней):**
```python
response = sc.searchanalytics().query(
    siteUrl='https://your-domain.com/',
    body={
        'startDate': '2026-02-06',
        'endDate': '2026-03-08',
        'dimensions': ['query'],
        'rowLimit': 25,
        'orderBy': [{'fieldName': 'clicks', 'sortOrder': 'DESCENDING'}]
    }
).execute()
for row in response.get('rows', []):
    query = row['keys'][0]
    clicks = row['clicks']
    impressions = row['impressions']
    ctr = row['ctr'] * 100
    position = row['position']
    print(f"{query} | clicks: {clicks} | impr: {impressions} | CTR: {ctr:.1f}% | pos: {position:.1f}")
```

4. **Топ страницы:**
```python
response = sc.searchanalytics().query(
    siteUrl='https://your-domain.com/',
    body={
        'startDate': '2026-02-06',
        'endDate': '2026-03-08',
        'dimensions': ['page'],
        'rowLimit': 25
    }
).execute()
for row in response.get('rows', []):
    page = row['keys'][0]
    print(f"{page} | clicks: {row['clicks']} | impr: {row['impressions']}")
```

5. **Запросы + страницы (комбинация):**
```python
response = sc.searchanalytics().query(
    siteUrl='https://your-domain.com/',
    body={
        'startDate': '2026-02-06',
        'endDate': '2026-03-08',
        'dimensions': ['query', 'page'],
        'rowLimit': 50,
        'dimensionFilterGroups': [{
            'filters': [{
                'dimension': 'query',
                'operator': 'contains',
                'expression': 'company'
            }]
        }]
    }
).execute()
```

6. **Карты сайта:**
```python
sitemaps = sc.sitemaps().list(siteUrl='https://your-domain.com/').execute()
for sm in sitemaps.get('sitemap', []):
    print(f"{sm['path']} | {sm.get('lastSubmitted', '')} | errors: {sm.get('errors', 0)}")
```

## Доступные dimensions
- `query` - поисковый запрос
- `page` - URL страницы
- `country` - страна
- `device` - desktop/mobile/tablet
- `date` - дата

## Метрики (всегда возвращаются)
- `clicks` - клики
- `impressions` - показы
- `ctr` - кликабельность (0-1)
- `position` - средняя позиция

## Примеры
- `/gsearch-console sites` - мои сайты
- `/gsearch-console analytics https://your-domain.com/` - топ запросы
- `/gsearch-console sitemaps https://your-domain.com/` - карты сайта
