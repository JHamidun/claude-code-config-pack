# Foursquare Places API — справочник

Глобальный POI-каталог с **10K+ категорий** и **100K req/мес бесплатно**. Сильнее Google в США/Европе, лучшая POI-таксономия.

## Endpoints

| Метод | URL |
|-------|-----|
| Place Search | `GET https://api.foursquare.com/v3/places/search` |
| Place Details | `GET https://api.foursquare.com/v3/places/{fsq_id}` |
| Place Photos | `GET https://api.foursquare.com/v3/places/{fsq_id}/photos` |
| Place Tips (отзывы) | `GET https://api.foursquare.com/v3/places/{fsq_id}/tips` |
| Place Nearby | `GET https://api.foursquare.com/v3/places/nearby` |
| Autocomplete | `GET https://api.foursquare.com/v3/autocomplete` |

## Авторизация

Заголовок `Authorization: fsq_$FOURSQUARE_API_KEY` (просто префикс `fsq_` + ключ, без Bearer).

## Примеры

```bash
# Search ресторанов в Москве
curl "https://api.foursquare.com/v3/places/search?ll=55.7558,37.6173&query=ресторан&radius=2000&limit=20&fields=fsq_id,name,location,geocodes,categories,rating,price,tel,website,hours,popularity" \
  -H "Authorization: fsq_$FOURSQUARE_API_KEY" \
  -H "Accept-Language: ru"

# Details + Photos + Tips для конкретного места
curl "https://api.foursquare.com/v3/places/4b1aa7b9f964a52040c823e3?fields=name,description,rating,stats,photos,tips" \
  -H "Authorization: fsq_$FOURSQUARE_API_KEY"

# Autocomplete для поиска
curl "https://api.foursquare.com/v3/autocomplete?query=мегобари&ll=55.7558,37.6173" \
  -H "Authorization: fsq_$FOURSQUARE_API_KEY"
```

## Структура ответа

```json
{
  "results": [{
    "fsq_id": "4b1aa7b9f964a52040c823e3",
    "name": "Megobari",
    "location": {
      "address": "ул. Маросейка 15",
      "locality": "Москва",
      "country": "RU",
      "formatted_address": "ул. Маросейка 15, 101000, Москва"
    },
    "geocodes": {
      "main": {"latitude": 55.7575, "longitude": 37.6411}
    },
    "categories": [
      {"id": 13236, "name": "Georgian Restaurant", "icon": {"prefix": "...", "suffix": ".png"}}
    ],
    "distance": 2354,
    "rating": 8.7,
    "price": 2,
    "tel": "+1234567890",
    "website": "https://megobari.ru",
    "hours": {
      "display": "Today 12:00–24:00",
      "is_local_holiday": false,
      "open_now": true,
      "regular": [
        {"day": 1, "open": "1200", "close": "2400"}
      ]
    },
    "popularity": 0.87
  }]
}
```

## Параметры (Search)

| Параметр | Описание |
|----------|----------|
| `ll` | `lat,lon` — **lat первая**, unlike Yandex/2GIS |
| `near` | Альтернатива ll: «Moscow, Russia» |
| `query` | Текстовый запрос |
| `radius` | Метры, max 100 000 |
| `categories` | comma-list category-id (см. ниже) |
| `fields` | comma-list полей в ответе — **обязательно явно указать** что нужно |
| `limit` | Max 50 |
| `sort` | `relevance` / `rating` / `distance` / `popularity` |
| `open_now` | `true` — только открытые сейчас |
| `min_price`+`max_price` | 1-4 ($-$$$$) |

## Категории

| ID | Категория |
|----|-----------|
| 13065 | Restaurant (общая) |
| 13236 | Georgian Restaurant |
| 13031 | Cafe / Coffee Shop |
| 13003 | Bar |
| 13145 | Italian Restaurant |
| 13276 | Sushi Restaurant |
| 19014 | Hotel |
| 11045 | Gas Station |
| 11046 | EV Charging Station |
| 17069 | Pharmacy |
| 11044 | Bank ATM |

Полный список: https://docs.foursquare.com/data-products/docs/categories

## Регистрация

1. https://location.foursquare.com (раньше developer.foursquare.com)
2. Sign up — email + password (Google/Apple SSO тоже есть)
3. Email verify
4. Dashboard → **Create Project** → имя, тип use case
5. Project → **API Keys** → Create → выбрать Service Key (бэкенд) или Session Token (фронт)
6. Service Key для бэкенда — не light-restrict сразу, потом ограничишь по IP/domain

Free tier: **100 000 запросов/месяц**.

## Грабли

1. **`ll` = `lat,lon`** (lat первая), НЕ как у Yandex/2GIS
2. **`Authorization: fsq_KEY`** — префикс `fsq_` обязателен, БЕЗ `Bearer`
3. **`fields=`** — **обязательно** запрашивать поля явно: без него только id+name+location базовый
4. **`hours.display`** локализован через `Accept-Language: ru` header
5. **`rating` 1-10**, не 1-5 (как у Google/Yelp). Делить пополам если нужно совместимо
6. **`price` 1-4** (1=$, 4=$$$$)
7. **Pagination** через `cursor` в response — передавать `&cursor=...` для следующей страницы
8. **API v2 deprecated 2024** — все примеры из старого инета не работают, используй v3
9. **Photos endpoint** возвращает `prefix + size + suffix` — собирать URL вручную: `${prefix}original${suffix}`
10. **Brazil**: средняя плотность POI, лучше Google. **РФ**: средняя, хуже Yandex/2GIS
11. **Rate limit** 50 QPS, 100K/мес — overage halts, апгрейд через биллинг

## Документация

- https://docs.foursquare.com/developer/reference/places-api-overview
- https://docs.foursquare.com/data-products/docs/places-api-overview
- Категории: https://docs.foursquare.com/data-products/docs/categories
