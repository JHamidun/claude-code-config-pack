---
description: "НЕ РАБОТАЕТ без настройки: нужны developer token и OAuth-скоуп AdWords. Google Ads по API (GAQL): аккаунты, кампании, отчёты по расходам. Триггеры: «гугл реклама», «отчёт google ads». НЕ Директ → yandex; VK Ads → vk-ads-pro-ru."
argument-hint: "[accounts | campaigns <customer_id> | report <customer_id>]"
---

# Google Ads Operations

> ⛔ **Команда НЕ РАБОТАЕТ из коробки.** Два независимых стопора:
> 1) developer token не выпущен — в конфиге ниже стоит плейсхолдер
>    `YOUR_DEVELOPER_TOKEN`, без реального токена Google Ads API отвечает
>    `DEVELOPER_TOKEN_NOT_APPROVED`;
> 2) OAuth-токена с правами Google Ads нет — общий `google_oauth_token.json`
>    несёт ТОЛЬКО скоуп `drive` и даёт 403.
>
> Не запускай шаги ниже «на пробу» — скажи пользователю, что нужно сперва выпустить
> developer token в MCC и завести `google_oauth_token_ads.json` со скоупом
> AdWords. Код ниже — заготовка на этот момент, а не рабочий маршрут.
> Стратегия и настройка кампаний без API — навык `google-ads-pro-ru`.

/gads - Работа с Google Ads

## Описание
Управление рекламными кампаниями и отчётами через Google Ads API.

## Использование
```
/gads accounts                   - Список аккаунтов
/gads campaigns <customer_id>    - Кампании аккаунта
/gads report <customer_id>       - Отчёт по кампаниям
```

## Инструкции для Claude

**ВАЖНО:** Google Ads использует собственную клиентскую библиотеку, а не стандартный `googleapiclient`.

### Установка
```bash
pip install google-ads
```

### 1. Загрузи credentials (Google Ads Client):
```python
import os
import json
from google.ads.googleads.client import GoogleAdsClient

with open(os.path.expanduser('~/.claude/google_oauth_token_ads.json'), 'r') as f:  # токена ещё нет — см. блок выше
    token_data = json.load(f)

# Google Ads требует developer token + login customer ID
config = {
    'developer_token': 'YOUR_DEVELOPER_TOKEN',
    'client_id': token_data.get('client_id'),
    'client_secret': token_data.get('client_secret'),
    'refresh_token': token_data.get('refresh_token'),
    'use_proto_plus': True,
    'login_customer_id': '1234567890'  # MCC ID без дефисов
}
client = GoogleAdsClient.load_from_dict(config)
```

### 2. Список доступных аккаунтов:
```python
customer_service = client.get_service('CustomerService')
accessible = customer_service.list_accessible_customers()
for resource_name in accessible.resource_names:
    print(resource_name)  # customers/1234567890
```

### 3. Кампании аккаунта (GAQL):
```python
ga_service = client.get_service('GoogleAdsService')
query = """
    SELECT campaign.id, campaign.name, campaign.status,
           campaign_budget.amount_micros
    FROM campaign
    WHERE campaign.status != 'REMOVED'
    ORDER BY campaign.id
"""
response = ga_service.search(customer_id='1234567890', query=query)
for row in response:
    c = row.campaign
    budget = row.campaign_budget.amount_micros / 1_000_000
    print(f"{c.id} | {c.name} | {c.status.name} | budget: {budget}")
```

### 4. Отчёт по метрикам:
```python
query = """
    SELECT campaign.name,
           metrics.impressions,
           metrics.clicks,
           metrics.cost_micros,
           metrics.conversions,
           metrics.average_cpc
    FROM campaign
    WHERE segments.date DURING LAST_30_DAYS
      AND campaign.status = 'ENABLED'
    ORDER BY metrics.cost_micros DESC
"""
response = ga_service.search(customer_id='1234567890', query=query)
for row in response:
    cost = row.metrics.cost_micros / 1_000_000
    cpc = row.metrics.average_cpc / 1_000_000
    print(f"{row.campaign.name} | impr: {row.metrics.impressions} "
          f"| clicks: {row.metrics.clicks} | cost: {cost:.2f} | cpc: {cpc:.2f}")
```

### 5. Ключевые слова:
```python
query = """
    SELECT ad_group_criterion.keyword.text,
           ad_group_criterion.keyword.match_type,
           metrics.impressions, metrics.clicks, metrics.cost_micros
    FROM keyword_view
    WHERE segments.date DURING LAST_7_DAYS
    ORDER BY metrics.impressions DESC
    LIMIT 25
"""
response = ga_service.search(customer_id='1234567890', query=query)
```

## GAQL (Google Ads Query Language)
- `DURING LAST_7_DAYS`, `LAST_30_DAYS`, `THIS_MONTH`
- `WHERE campaign.status = 'ENABLED'`
- Суммы в `_micros` — делить на 1,000,000

## Примеры
- `/gads accounts` - доступные рекламные аккаунты
- `/gads campaigns 1234567890` - кампании аккаунта
- `/gads report 1234567890` - метрики за 30 дней
