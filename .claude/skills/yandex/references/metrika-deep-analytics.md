# Metrika Deep Analytics Reference

> Проверенные на практике запросы для глубокого анализа сайта.

## Счётчики

Счётчик у каждого свой, и его ID нужен почти в каждом запросе ниже.
Узнать свои — одним вызовом, гадать не нужно.

### Список всех своих счётчиков
```
GET /management/v1/counters?per_page=100
```

### Поиск счётчика по имени
```
GET /management/v1/counters?per_page=100&search_string=мойсайт
```

Ответ содержит `id`, `name` и `site` каждого счётчика. Найденный ID положи в
`YANDEX_METRIKA_COUNTER_ID` — CLI навыка берёт его оттуда.

### Свой список (заполни для себя)
| ID | Название | Сайт |
|----|----------|------|
| [id] | [как назван в кабинете] | [домен] |

## Deep Analytics — полный набор запросов

### 1. Core Metrics (ежедневная динамика)
```python
params = {
    'ids': COUNTER_ID,
    'metrics': 'ym:s:visits,ym:s:pageviews,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds,ym:s:percentNewVisitors',
    'dimensions': 'ym:s:date',
    'date1': '7daysAgo',
    'date2': 'today',
    'sort': 'ym:s:date'
}
```

### 2. Источники трафика
```python
# Основные каналы
dimensions='ym:s:lastTrafficSource'
metrics='ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:pageviews,ym:s:avgVisitDurationSeconds'

# Поисковые системы
dimensions='ym:s:searchEngine'

# Соцсети
dimensions='ym:s:socialNetwork'

# Рефереры (откуда пришли)
dimensions='ym:s:referer'
# Limit 20, sort by -ym:s:visits
```

### 3. UTM-разметка (кампании)
```python
# UTM Source
dimensions='ym:s:lastUTMSource'

# UTM Medium
dimensions='ym:s:lastUTMMedium'

# UTM Campaign
dimensions='ym:s:lastUTMCampaign'

# Комбинация Source+Medium
dimensions='ym:s:lastUTMSource,ym:s:lastUTMMedium'
```

### 4. Демография
```python
# Возраст
dimensions='ym:s:ageInterval'

# Пол
dimensions='ym:s:gender'
metrics='ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds'

# Пол + Возраст (комбинация)
dimensions='ym:s:gender,ym:s:ageInterval'
```

### 5. География
```python
# Страны
dimensions='ym:s:regionCountry'

# Города
dimensions='ym:s:regionCity'

# Область/Регион
dimensions='ym:s:regionArea'
```

### 6. Устройства и технологии
```python
# Тип устройства (ПК/мобильный/планшет)
dimensions='ym:s:deviceCategory'
metrics='ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds'

# Браузеры
dimensions='ym:s:browser'

# ОС
dimensions='ym:s:operatingSystem'

# Разрешение экрана
dimensions='ym:s:screenResolution'
```

### 7. Страницы
```python
# Топ страниц
dimensions='ym:pv:URLPath'
metrics='ym:pv:pageviews,ym:pv:users'
# Namespace: ym:pv (page views), не ym:s (sessions)!

# Входные страницы (лендинги)
dimensions='ym:s:startURL'
metrics='ym:s:visits,ym:s:bounceRate,ym:s:avgVisitDurationSeconds'

# Выходные страницы
dimensions='ym:s:endURL'
```

### 8. Поисковые запросы
```python
dimensions='ym:s:searchPhrase'
metrics='ym:s:visits'
sort='-ym:s:visits'
limit=30
```

### 9. Глубина просмотра
```python
dimensions='ym:s:pageViews'
metrics='ym:s:visits,ym:s:users'
sort='-ym:s:visits'
```

### 10. Трафик по часам
```python
dimensions='ym:s:startURLPathLevel1,ym:s:hour'
# или просто по часам:
dimensions='ym:s:hour'
metrics='ym:s:visits'
```

### 11. Цели и конверсии
```python
# Список всех целей
GET /management/v1/counter/{counter}/goals

# Достижения целей (до 20 целей за запрос)
metrics='ym:s:goal{GOAL_ID}reaches'
# Для нескольких: 'ym:s:goal123reaches,ym:s:goal456reaches'

# ⚠ API лимит: максимум ~20 метрик в одном запросе
# Если целей > 20, разбивай на батчи
```

### 12. E-commerce
```python
# ⚠ Работает ТОЛЬКО если E-commerce включён на счётчике!
# Проверка: если metrics=ym:s:ecommercePurchases вернёт 400 — не включён

# Покупки
metrics='ym:s:ecommercePurchases,ym:s:ecommerceRevenue,ym:s:ecommerceRevenuePerPurchase,ym:s:ecommerceRevenuePerVisit'

# Товары
metrics='ym:s:productPurchasedQuantity,ym:s:productPurchasedRevenue'
dimensions='ym:s:productName'
```

## Полный каталог метрик

### Sessions (ym:s:)
| Метрика | Описание |
|---------|----------|
| `ym:s:visits` | Визиты |
| `ym:s:pageviews` | Просмотры страниц |
| `ym:s:users` | Уникальные посетители |
| `ym:s:bounceRate` | % отказов |
| `ym:s:avgVisitDurationSeconds` | Ср. длительность визита (сек) |
| `ym:s:percentNewVisitors` | % новых посетителей |
| `ym:s:goal{ID}reaches` | Достижения цели |
| `ym:s:goal{ID}visits` | Визиты с достижением цели |
| `ym:s:goal{ID}users` | Пользователи достигшие цели |
| `ym:s:goal{ID}conversionRate` | Конверсия цели |

### Page Views (ym:pv:)
| Метрика | Описание |
|---------|----------|
| `ym:pv:pageviews` | Просмотры |
| `ym:pv:users` | Уникальные |

### E-commerce (ym:s:)
| Метрика | Описание |
|---------|----------|
| `ym:s:ecommercePurchases` | Покупки |
| `ym:s:ecommerceRevenue` | Выручка |
| `ym:s:ecommerceRevenuePerPurchase` | Средний чек |
| `ym:s:ecommerceRevenuePerVisit` | Выручка на визит |

## Полный каталог dimensions

### Трафик
| Dimension | Описание |
|-----------|----------|
| `ym:s:date` | Дата |
| `ym:s:hour` | Час дня |
| `ym:s:lastTrafficSource` | Источник (direct/organic/referral/ad/social/email) |
| `ym:s:searchEngine` | Поисковая система |
| `ym:s:socialNetwork` | Соцсеть |
| `ym:s:referer` | Реферер (полный URL) |
| `ym:s:searchPhrase` | Поисковый запрос |

### UTM
| Dimension | Описание |
|-----------|----------|
| `ym:s:lastUTMSource` | utm_source |
| `ym:s:lastUTMMedium` | utm_medium |
| `ym:s:lastUTMCampaign` | utm_campaign |
| `ym:s:lastUTMContent` | utm_content |
| `ym:s:lastUTMTerm` | utm_term |

### Аудитория
| Dimension | Описание |
|-----------|----------|
| `ym:s:gender` | Пол |
| `ym:s:ageInterval` | Возрастная группа |
| `ym:s:regionCountry` | Страна |
| `ym:s:regionCity` | Город |
| `ym:s:regionArea` | Область |

### Технологии
| Dimension | Описание |
|-----------|----------|
| `ym:s:deviceCategory` | Тип устройства |
| `ym:s:browser` | Браузер |
| `ym:s:operatingSystem` | ОС |
| `ym:s:screenResolution` | Разрешение экрана |

### Страницы
| Dimension | Описание |
|-----------|----------|
| `ym:s:startURL` | URL входа |
| `ym:s:endURL` | URL выхода |
| `ym:pv:URLPath` | Путь страницы (namespace ym:pv!) |

### Глубина
| Dimension | Описание |
|-----------|----------|
| `ym:s:pageViews` | Кол-во страниц за визит |

## Готовые рецепты аналитических отчётов

### Недельный отчёт (9 направлений)
1. Core metrics daily → `dimensions=date`, 6 метрик
2. Traffic sources → `dimensions=lastTrafficSource`, 5 метрик
3. UTM campaigns → `dimensions=lastUTMCampaign`, 3 метрики
4. Search engines → `dimensions=searchEngine`
5. Demographics → `dimensions=gender` + `dimensions=ageInterval`
6. Geography → `dimensions=regionCountry` + `dimensions=regionCity`
7. Devices → `dimensions=deviceCategory` + `dimensions=browser`
8. Goals → batch по 20 целей, `metrics=goal{ID}reaches`
9. Search phrases → `dimensions=searchPhrase`

### WoW сравнение
Два запроса с разными date1/date2 → считай дельту в Python.

## Gotchas (подводные камни)

1. **E-commerce метрики** — вернут 400 если модуль не включён на счётчике
2. **Page speed метрики** (`ym:pv:avgPageLoadTime`) — не работают в API, хотя есть в документации
3. **Лимит метрик** — max ~20 metrics в одном запросе, иначе 400
4. **Namespace** — для страниц используй `ym:pv:`, для сессий `ym:s:`
5. **Windows encoding** — добавляй `PYTHONIOENCODING=utf-8` и `sys.stdout.reconfigure(encoding='utf-8')`
6. **lastSignDirectClickOrder** — dimension существует, но может возвращать пустые данные
7. **Referer dimension** — `ym:s:referer` даёт полные URL источников, включая внутренние
   порталы компаний-клиентов. Срез ценный, но в отчёт наружу такие URL не класть:
   они выдают, кто именно к тебе ходит
