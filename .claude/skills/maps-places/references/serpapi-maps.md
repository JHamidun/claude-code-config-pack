# SerpAPI Google Maps — справочник (fallback)

SerpAPI парсит выдачу Google Maps и возвращает структурированный JSON. Используем как fallback когда Places API недоступен или нужно дешевле проверить рейтинг/отзывы для не-РФ.

## Endpoint

```
GET https://serpapi.com/search.json?engine=google_maps&...&api_key=$SERPAPI_API_KEY
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `engine` | `google_maps` |
| `q` | Запрос («pizza», «coffee shop near Times Square») |
| `ll` | `@lat,lon,zoom` — например `@40.7128,-74.0060,15z` |
| `type` | `search` (default), `place` (по data_id) |
| `data_id` | ID места для `type=place` |
| `data` | Альтернатива data_id для деталей |
| `hl` | Язык: `ru`, `en`, `pt` |
| `gl` | Country: `ru`, `us`, `br` |
| `start` | Offset для пагинации (0, 20, 40...) |

## Пример

```bash
curl "https://serpapi.com/search.json?\
engine=google_maps&\
q=pizza+near+Times+Square&\
ll=@40.7575,-73.9857,14z&\
hl=en&gl=us&\
api_key=$SERPAPI_API_KEY"
```

## Структура ответа

```json
{
  "search_metadata": {...},
  "local_results": [{
    "position": 1,
    "title": "Joe's Pizza Broadway",
    "place_id": "ChIJN5NW...",
    "data_id": "0x89c2599...",
    "rating": 4.4,
    "reviews": 25580,
    "price": "$",
    "type": "Pizza restaurant",
    "address": "1435 Broadway, New York, NY 10018",
    "open_state": "Open ⋅ Closes 5 AM",
    "hours": "Open ⋅ Closes 5 AM",
    "operating_hours": {"thursday": "10am-5am", ...},
    "phone": "(212) 489-3000",
    "website": "joespizzanyc.com",
    "gps_coordinates": {"latitude": 40.755, "longitude": -73.986},
    "thumbnail": "https://...",
    "service_options": {"dine_in": true, "takeout": true, "no_contact_delivery": true}
  }],
  "place_results": {...},
  "place_topics": {...}
}
```

## Поля

- `local_results[]` — список мест (для type=search)
- `place_results{}` — один результат (для type=place)
- `place_topics{}` — темы отзывов
- `gps_coordinates` — координаты
- `rating` + `reviews` — рейтинг и количество отзывов
- `price` — `$` / `$$` / `$$$` / `$$$$`
- `operating_hours` — часы по дням недели
- `service_options` — `dine_in`, `takeout`, `delivery`, `wheelchair_accessible_entrance`

## Тарификация

- 250 поисков/мес бесплатно (Free plan)
- Дальше — $50+/мес от 5000 поисков
- 1 запрос с пагинацией = 1 search

## Когда использовать

✅ **Брать как fallback:**
- Places API заблокирован/недоступен в регионе
- Нужны Google рейтинги без оплаты Places New SKU
- 1-разовые ad-hoc проверки

❌ **Не брать как основной:**
- Дороже Places API на больших объёмах
- Нет официальной гарантии стабильности парсинга — Google может менять выдачу
- Лимит 250/мес очень мал для production

## Грабли

1. **`ll=@lat,lon,zoom`** — символ `@` и зум обязательны, формат отличается от других провайдеров
2. **`hl` + `gl`** обязательны для не-US региона — иначе будут не самые релевантные результаты
3. **`data_id` ≠ `place_id`** — два разных идентификатора Google. Для повторных запросов лучше `data_id`
4. **Часы в строке** (`operating_hours.monday = "10am-11pm"`) — не структурированные, нужен парсер
5. **Пагинация по 20** через `start`. Полная выдача ограничена 60 (3 страницы)

## Документация

- https://serpapi.com/google-maps-api
- https://serpapi.com/google-maps-local-results
