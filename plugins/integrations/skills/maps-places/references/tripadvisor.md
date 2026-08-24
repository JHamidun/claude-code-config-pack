# TripAdvisor Content API (partner-only) — справочник

Глобальные hotels/restaurants/attractions с отзывами TripAdvisor. **5K req/день free после approval**. Регистрация через partner application.

⚠️ **Cannot self-serve**: applicant подаёт заявку с описанием use case, TripAdvisor одобряет вручную (1-2 недели). Требует attribution (логотип + ссылка на web_url).

## Endpoints

| Метод | URL |
|-------|-----|
| Location Search | `GET https://api.content.tripadvisor.com/api/v1/location/search` |
| Nearby Search | `GET https://api.content.tripadvisor.com/api/v1/location/nearby_search` |
| Location Details | `GET https://api.content.tripadvisor.com/api/v1/location/{locationId}/details` |
| Location Photos | `GET https://api.content.tripadvisor.com/api/v1/location/{locationId}/photos` |
| Location Reviews | `GET https://api.content.tripadvisor.com/api/v1/location/{locationId}/reviews` |

## Авторизация

`?key=$TRIPADVISOR_API_KEY` в query.

## Примеры

```bash
# Search отелей в Sample District
curl "https://api.content.tripadvisor.com/api/v1/location/search?\
key=$TRIPADVISOR_API_KEY&\
searchQuery=Sample+District&\
category=hotels&\
language=pt"

# Nearby restaurants
curl "https://api.content.tripadvisor.com/api/v1/location/nearby_search?\
key=$TRIPADVISOR_API_KEY&\
latLong=-22.971,-43.182&\
category=restaurants&\
radius=5&\
radiusUnit=km&\
language=pt"

# Details + Photos + Reviews по location_id
curl "https://api.content.tripadvisor.com/api/v1/location/12345678/details?key=$TRIPADVISOR_API_KEY&language=en"
curl "https://api.content.tripadvisor.com/api/v1/location/12345678/photos?key=$TRIPADVISOR_API_KEY&limit=10"
curl "https://api.content.tripadvisor.com/api/v1/location/12345678/reviews?key=$TRIPADVISOR_API_KEY&limit=5&language=en"
```

## Структура ответа (Search)

```json
{
  "data": [{
    "location_id": "12345678",
    "name": "Sample Beach Resort",
    "distance": "0.5",
    "rating": "4.5",
    "address_obj": {
      "street1": "Av. Atlântica, 1000",
      "city": "Sample City",
      "state": "ST",
      "country": "Brazil",
      "postalcode": "22070-000",
      "address_string": "Av. Atlântica, 1000, Sample City, ST 22070-000, Brazil"
    },
    "latitude": "-22.971",
    "longitude": "-43.182"
  }]
}
```

## Структура ответа (Details)

```json
{
  "location_id": "12345678",
  "name": "Sample Beach Resort",
  "description": "Luxurious beachfront resort...",
  "web_url": "https://www.tripadvisor.com/Hotel_Review-...",
  "rating": "4.5",
  "num_reviews": "1234",
  "rating_image_url": "https://...",
  "ranking_data": {
    "geo_location_id": "...",
    "ranking_string": "#3 of 15 hotels in Sample City",
    "ranking": 3,
    "ranking_out_of": 15
  },
  "price_level": "$$$",
  "amenities": ["Pool", "Free WiFi", "Breakfast included", "Spa", "Beach access"],
  "cuisine": [],
  "hours": {"week_ranges": [...]},
  "phone": "+55 XX XXXXX-XXXX",
  "email": "reservations@example.com",
  "website": "https://...",
  "address_obj": {...},
  "ancestors": [
    {"name": "Sample City", "level": "City"},
    {"name": "Sample State", "level": "Province"},
    {"name": "Brazil", "level": "Country"}
  ],
  "booking_partners": [],
  "awards": [
    {"award_type": "Travelers Choice", "year": "2024"}
  ],
  "subratings": {
    "0": {"name": "RATE_VALUE", "value": "4.5", "localized_name": "Value"},
    "1": {"name": "RATE_ROOMS", "value": "4.5"}
  }
}
```

## Категории

| Category | Применение |
|----------|------------|
| `hotels` | Отели + резорты + B&B |
| `restaurants` | Все заведения еды |
| `attractions` | Достопримечательности + activities |
| `geos` | Города/страны (для geo lookup) |

## Параметры (Search)

| Параметр | Описание |
|----------|----------|
| `searchQuery` | Текст |
| `category` | hotels / restaurants / attractions / geos |
| `language` | en, pt, ru, es, fr, de... (доступность зависит от location) |
| `latLong` | `lat,lon` — для location bias |
| `address` | Альтернатива latLong |
| `phone` | Поиск по телефону |
| `radius`+`radiusUnit` | `km` / `mi` (только nearby_search) |
| `limit` | Max 50 |

## Регистрация

⚠️ **Manual application**:

1. https://www.tripadvisor.com/developers
2. **Create Account** или Sign In через TripAdvisor account
3. **Submit Application** — заполнить:
   - Company name + website
   - Use case description (1-2 параграфа): зачем нужен API, какие endpoints, expected volume
   - User base size
4. Жди email approval (1-2 недели)
5. После approval — Dashboard → Developer Portal → API Key

Free: **5000 req/day** после approval. Beyond — кастомный sales contract.

**Attribution REQUIRED**: показ TripAdvisor логотипа + кликабельная ссылка на `web_url` каждого location.

## Грабли

1. **`latLong` slash-separator** = `lat,lon` (lat первая)
2. **`location_id` как string** в ответе, не int
3. **Reviews endpoint возвращает только excerpts** (~250 символов), не полные тексты
4. **`language` availability varies** — Portugal/Brazil поддержка pt отличная, для small location язык может fallback на en
5. **Quota strict 5K/день** — overage = 429
6. **Attribution policy строгая** — без логотипа TA может отозвать ключ
7. **`subratings`** — числовые ключи, не named (parse как dict)
8. **`amenities`** — массив строк на en всегда (нет локализации)
9. **Photos endpoint** возвращает thumbnail+small+medium+large+original — выбирать нужный размер
10. **Awards** только для top-rated locations — не all hotels имеют
11. **Cannot auto-register** — заявку нужно подать самому

## Альтернатива без approval

- **SerpAPI** имеет engine `tripadvisor` (scrape-based) — не official, но работает: `engine=tripadvisor&q=Sample District+hotels`
- **Apify** актор `tripadvisor-scraper` — pay-per-result

## Use case для User

- Hotels/restaurants в **Sample District** для /region landing
- Reviews снапшот для конкурентного анализа Sample Beach Hotel
- Attractions для travel-карточек в yourname-multi-publish

## Документация

- https://tripadvisor-content-api.readme.io/reference/overview
- https://www.tripadvisor.com/developers
