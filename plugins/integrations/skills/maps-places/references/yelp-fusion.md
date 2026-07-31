# Yelp Fusion API — справочник

POI + рейтинги от Yelp. **5000 запросов/день free**. Сильнее Google в США/Канаде/EU для ресторанов/сервисов.

⚠️ Yelp **закрыл self-service signup** в большинстве стран в 2023. Новые регистрации требуют business verification и идут через approval queue. Существующие аккаунты могут создавать ключи.

## Endpoints

| Метод | URL |
|-------|-----|
| Business Search | `GET https://api.yelp.com/v3/businesses/search` |
| Business Details | `GET https://api.yelp.com/v3/businesses/{id}` |
| Reviews (3 excerpt) | `GET https://api.yelp.com/v3/businesses/{id}/reviews` |
| Autocomplete | `GET https://api.yelp.com/v3/autocomplete` |
| Phone Search | `GET https://api.yelp.com/v3/businesses/search/phone` |
| Categories | `GET https://api.yelp.com/v3/categories` |
| Match Business | `GET https://api.yelp.com/v3/businesses/matches` |

## Авторизация

Header: `Authorization: Bearer $YELP_API_KEY`.

## Примеры

```bash
# Search ресторанов в Нью-Йорке
curl "https://api.yelp.com/v3/businesses/search?\
term=pizza&\
latitude=40.7128&\
longitude=-74.0060&\
radius=2000&\
categories=pizza&\
limit=20&\
sort_by=rating" \
  -H "Authorization: Bearer $YELP_API_KEY"

# Details
curl "https://api.yelp.com/v3/businesses/joes-pizza-broadway-new-york" \
  -H "Authorization: Bearer $YELP_API_KEY"

# Phone lookup
curl "https://api.yelp.com/v3/businesses/search/phone?phone=+12124893000" \
  -H "Authorization: Bearer $YELP_API_KEY"
```

## Структура ответа

```json
{
  "businesses": [{
    "id": "joes-pizza-broadway-new-york",
    "alias": "joes-pizza-broadway-new-york",
    "name": "Joe's Pizza Broadway",
    "image_url": "https://s3-media...",
    "is_closed": false,
    "url": "https://www.yelp.com/biz/joes-pizza-broadway-new-york",
    "review_count": 4521,
    "rating": 4.5,
    "categories": [
      {"alias": "pizza", "title": "Pizza"}
    ],
    "price": "$",
    "coordinates": {"latitude": 40.7589, "longitude": -73.9851},
    "location": {
      "address1": "1435 Broadway",
      "city": "New York",
      "zip_code": "10018",
      "country": "US",
      "state": "NY",
      "display_address": ["1435 Broadway", "New York, NY 10018"]
    },
    "phone": "+12124893000",
    "display_phone": "(212) 489-3000",
    "distance": 234.5,
    "transactions": ["delivery", "pickup"],
    "attributes": {
      "business_temp_closed": null,
      "wheelchair_accessible": true,
      "outdoor_seating": false
    }
  }],
  "total": 240,
  "region": {"center": {"latitude": 40.7128, "longitude": -74.006}}
}
```

## Параметры (Search)

| Параметр | Описание |
|----------|----------|
| `latitude`+`longitude` | Координаты |
| `location` | Альтернатива: «San Francisco, CA» |
| `term` | Текстовый запрос («pizza», «coffee», бизнес-имя) |
| `radius` | Метры, max **40 000** (40 км) |
| `categories` | comma-list alias-ов (`pizza,italian,coffee`) |
| `limit` | Max 50 |
| `offset` | Max 1000 для pagination |
| `sort_by` | `best_match` / `rating` / `review_count` / `distance` |
| `price` | `1,2,3,4` или comma-list |
| `open_now` | `true` / `false` |
| `attributes` | comma: `hot_and_new`, `reservation`, `cashback`, `deals` |
| `locale` | `en_US`, `pt_BR`, `ru_RU`... |

## Категории (alias)

Yelp использует alias-based категории:

| Alias | Что |
|-------|-----|
| `restaurants` | Все рестораны |
| `pizza`, `italian`, `chinese`, `sushi`, `mexican`, `georgian` | По кухне |
| `cafes`, `coffee` | Кофейни |
| `bars`, `cocktailbars`, `pubs`, `wine_bars` | Бары |
| `hotels`, `bedbreakfast`, `hostels` | Жильё |
| `gas_stations` | АЗС |
| `pharmacy` | Аптеки |
| `banks` | Банки |

Полный список: GET `/v3/categories?locale=en_US`

## Регистрация

1. Открыть https://docs.developer.yelp.com (раньше yelp.com/developers)
2. **Manage App** → Create New App
3. Заполнить: App Name, Industry, Company, Email, Description
4. После создания — API Key выдаётся **сразу** (если account approved)
5. В новых странах signup может уйти на verification — приходит email

Альтернатива: **существующий аккаунт** Yelp Business — внутри есть Developer Portal.

Free: **5000 calls/day**. Beyond → upgrade plan через AWS Marketplace или прямой sales.

## Грабли

1. **`radius` max 40000** (40 км), беря больше — silently truncate
2. **`offset` max 1000** — для >1000 результатов нужны разные радиусы/локации
3. **Reviews endpoint** возвращает **только 3 excerpt**-а (по 160 символов) — полные отзывы scraping вне ToS
4. **`rating` 1-5 в 0.5 steps** (4.5, не 4.6)
5. **Yelp слабо в РФ/Brazil** — основа US/Canada/EU. Brazil только основные города
6. **`is_closed`** = постоянно закрыт (не «закрыт сейчас»). Для now → `hours[0].is_open_now`
7. **Pagination через offset**, не cursor
8. **`transactions`** = доступные опции (delivery/pickup/restaurant_reservation), фильтр через `&transactions=`
9. **Self-service signup закрыт** в большинстве стран с 2023 — нужен business case
10. **`Match Business`** для дедупликации между Yelp и другим источником (по name+address+phone)

## Документация

- https://docs.developer.yelp.com/docs/fusion-intro
- https://docs.developer.yelp.com/reference/v3_business_search
- Категории: `/v3/categories`
