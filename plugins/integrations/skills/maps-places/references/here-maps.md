# HERE Maps API — справочник

Глобальный картсервис с **250 000 транзакций/мес бесплатно**. Сильнее Google в EU/Asia/Middle East. Есть EV-зарядки + трафик-маршруты.

## Endpoints

| Метод | URL |
|-------|-----|
| Discover (текстовый поиск) | `GET https://discover.search.hereapi.com/v1/discover` |
| Browse (по категориям) | `GET https://browse.search.hereapi.com/v1/browse` |
| Lookup (по ID) | `GET https://lookup.search.hereapi.com/v1/lookup` |
| Geocode | `GET https://geocode.search.hereapi.com/v1/geocode` |
| Reverse Geocode | `GET https://revgeocode.search.hereapi.com/v1/revgeocode` |
| Autosuggest | `GET https://autosuggest.search.hereapi.com/v1/autosuggest` |
| Routing v8 | `GET https://router.hereapi.com/v8/routes` |
| Matrix Routing v8 | `POST https://matrix.router.hereapi.com/v8/matrix` |
| EV Charging | `GET https://ev-v2.cc.api.here.com/ev/stations.json` |

## Авторизация

`?apiKey=$HERE_API_KEY` в query string. Альтернатива — OAuth Bearer (Authorization header).

## Примеры

```bash
# Discover ресторанов в Москве
curl "https://discover.search.hereapi.com/v1/discover?\
at=55.7558,37.6173&\
q=ресторан+грузинская+кухня&\
limit=20&\
lang=ru&\
apiKey=$HERE_API_KEY"

# Browse по категории (рестораны)
curl "https://browse.search.hereapi.com/v1/browse?\
at=55.7558,37.6173&\
categories=100-1000-0000&\
limit=50&\
apiKey=$HERE_API_KEY"

# Reverse геокодинг
curl "https://revgeocode.search.hereapi.com/v1/revgeocode?\
at=55.7558,37.6173&\
lang=ru&\
apiKey=$HERE_API_KEY"

# Маршрут с трафиком (EU)
curl "https://router.hereapi.com/v8/routes?\
transportMode=car&\
origin=52.5160,13.3779&\
destination=48.8566,2.3522&\
return=summary,polyline&\
apiKey=$HERE_API_KEY"
```

## Структура ответа (Discover)

```json
{
  "items": [{
    "title": "Megobari",
    "id": "here:pds:place:7000ll8x-...",
    "language": "ru",
    "resultType": "place",
    "address": {
      "label": "Maroseyka St 15, Moscow 101000, Russia",
      "countryCode": "RUS",
      "countryName": "Russia",
      "city": "Moscow",
      "street": "Maroseyka St",
      "postalCode": "101000",
      "houseNumber": "15"
    },
    "position": {"lat": 55.7575, "lng": 37.6411},
    "access": [{"lat": 55.7575, "lng": 37.6411}],
    "distance": 2354,
    "categories": [
      {"id": "100-1000-0000", "name": "Ресторан", "primary": true}
    ],
    "contacts": [{
      "phone": [{"value": "+1234567890"}],
      "www": [{"value": "https://megobari.ru"}]
    }],
    "openingHours": [{
      "text": ["Mo-Su 12:00-24:00"],
      "isOpen": true
    }],
    "foodTypes": [{"id": "850-064", "name": "Грузинская"}]
  }]
}
```

## Параметры (Discover)

| Параметр | Описание |
|----------|----------|
| `at` | `lat,lng` — центр поиска (**lat первая**) |
| `q` | Текстовый запрос |
| `in=circle:lat,lng;r=meters` | Альтернатива at: круг |
| `in=bbox:west,south,east,north` | Bbox |
| `in=countryCode:BRA,RUS` | Фильтр по ISO3-странам |
| `limit` | Max 100 |
| `lang` | `ru`, `en`, `pt-BR`, `de`, `fr`... |
| `categories` | HERE PCS-ID, comma-separated |

## Полезные категории (PCS)

| ID | Что |
|----|-----|
| `100-1000-0000` | Ресторан |
| `100-1000-0001` | Бар / Паб |
| `200-2000-0000` | Гостиница |
| `500-5520-0000` | АЗС |
| `700-7600-0322` | EV charging station |
| `600-6900-0096` | Аптека |
| `800-8000-0000` | Атракционы |

Полный список: https://developer.here.com/documentation/places/dev_guide/topics/categories.html

## Регистрация

1. https://platform.here.com/sign-up — email + пароль
2. Подтвердить email
3. Default workspace → **Access Manager → Apps → Register New App**
4. После создания App — REST API → Create credentials → **API Key**
5. Не назначать restrictions на старте — добавишь когда поймёшь deployment

Free Freemium: **250 000 транзакций/мес** на все Search/Geocoding/Routing endpoints (кроме EV — отдельный SKU).

## Грабли

1. **`at` = `lat,lng`** (lat первая) — НЕ как у Yandex/2GIS
2. **`apiKey` только в query string** — header не принимается
3. **lang= ISO2-два символа** для большинства, но `pt-BR` для бразильского португальского
4. **`countryCode` ISO3** (3 буквы: `BRA`, `RUS`), не ISO2
5. **401** = restrictions ключа конфликтуют с current request domain/IP — проверь Access Manager
6. **Coverage**: EU 5/5, Asia 5/5, MENA 5/5 (Mauritania хорошо!), USA 4/5, Brazil 4/5 в городах
7. **EV API на отдельном поддомене** — `ev-v2.cc.api.here.com` — отдельный SKU, не входит в 250K free
8. **Routing v8** возвращает encoded polyline (flexible polyline format) — декодировать через here-flexible-polyline lib
9. **Pricing tier change** в `developer.here.com/pricing` — Freemium → Pro → Plus
10. **Не путать с MapKit / Tiles API** — это разные продукты (для рендера карт)

## Документация

- Главная: https://developer.here.com/documentation
- Search API v7: https://developer.here.com/documentation/geocoding-search-api/dev_guide/index.html
- Routing v8: https://developer.here.com/documentation/routing-api/dev_guide/index.html
- Pricing: https://developer.here.com/pricing
