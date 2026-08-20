# Booking.com Affiliate API (partner-only) — справочник

API для аффилиатов Booking.com: 28M+ properties, hotels/apartments/vacation rentals. Доступ через **Affiliate Partner Program**, требует established website с трафиком.

⚠️ **Cannot self-serve**: Booking review-ит сайт + бизнес-модель. Small affiliates frequently denied. Альтернативы для prototype — Apify scrapers или RapidAPI обёртки.

## Endpoints

| Метод | URL base |
|-------|----------|
| Demand API (REST + GraphQL) | `https://demandapi.booking.com/3.1/` |

Распространённые операции:

| Operation | Endpoint |
|-----------|----------|
| Hotels Search | `POST /3.1/hotels/search` |
| Hotel Details | `POST /3.1/hotels/details` |
| Hotel Availability | `POST /3.1/hotels/availability` |
| Reviews | `POST /3.1/hotels/reviews` |
| Photos | `POST /3.1/hotels/photos` |
| Locations / Cities | `POST /3.1/common/locations` |

## Авторизация

HTTP Basic Auth: username = **Affiliate ID**, password = **API Token**.

```
Authorization: Basic base64(affiliate_id:api_token)
```

## Примеры

```bash
# Hotels Search (POST с JSON body)
curl -X POST "https://demandapi.booking.com/3.1/hotels/search" \
  -u "$BOOKING_AFFILIATE_ID:$BOOKING_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "city_ids": [-647693],
    "checkin": "2026-07-01",
    "checkout": "2026-07-08",
    "guests": {"adults": 2, "children": []},
    "rows": 25,
    "currency": "BRL",
    "language": "pt"
  }'

# Hotel Details
curl -X POST "https://demandapi.booking.com/3.1/hotels/details" \
  -u "$BOOKING_AFFILIATE_ID:$BOOKING_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hotel_ids": [1234567], "currency": "BRL"}'
```

## Структура ответа (Search)

```json
{
  "data": [{
    "hotel_id": 1234567,
    "name": "Beach Class Internacional Resort",
    "address": "Av. Beira Mar, 1000",
    "city": "Sample City",
    "city_id": 647693,
    "country": "BR",
    "country_trans": "Brasil",
    "latitude": -22.971,
    "longitude": -43.182,
    "hotel_type": "hotel",
    "star_rating": 5,
    "review_score": 8.7,
    "review_score_word": "Fabulous",
    "review_nr": 1234,
    "preferred": true,
    "photo_urls": ["https://cf.bstatic.com/..."],
    "price_breakdown": {
      "gross_price": {"value": 1599.00, "currency": "BRL"},
      "all_inclusive_price": {"value": 1759.00},
      "excluded_amount": {"value": 160.00}
    },
    "checkin_from": "14:00",
    "checkout_until": "12:00",
    "facilities": ["Free WiFi", "Pool", "Beach access"],
    "distances": [{"to": "city center", "value": 5.2, "unit": "km"}],
    "free_cancellation": true,
    "breakfast_included": true,
    "url": "https://www.booking.com/hotel/br/beach-class.html?aid=YOUR_AID"
  }],
  "meta": {
    "next_page": null,
    "currency": "BRL",
    "total_count": 1
  }
}
```

## Аффилиат-комиссии

- Commission share: ~**25-40%** от Booking.com commission
- Booking.com commission на бронь: **15-18%** от gross
- Реальный affiliate cut: ~3-7% от booking value
- Payouts: monthly, через Wire / Wise / Payoneer
- Deeplinks ОБЯЗАНЫ содержать `?aid={your_affiliate_id}` для attribution

## Регистрация

⚠️ **Multi-step manual**:

1. https://www.booking.com/affiliate-program/v2/index.html
2. **Sign up** — указать сайт с трафиком (требуется!), бизнес-модель
3. Booking ревьюит **website quality + niche fit** (1-3 недели)
4. Approval email с Affiliate ID
5. Дополнительная заявка на **API access** — описать use case
6. **Staging credentials** выдают сначала, потом production после demo integration

Требования к сайту:
- Активный домен с реальным контентом
- Travel/hospitality focus
- Compliance с Booking.com brand guidelines
- Нет multi-vendor сравнения (Expedia, Hotels.com совместно — minus)

## Альтернативы (без affiliate hassle)

### Apify (рекомендую для прототипа)

```bash
# В нашем skill apify-scraping
curl -X POST "https://api.apify.com/v2/acts/voyager~booking-scraper/runs?token=$APIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "search": "Sample Beach, Brazil",
    "maxItems": 200,
    "currency": "BRL",
    "language": "pt",
    "minMaxPrice": "0-9999",
    "checkIn": "2026-07-01",
    "checkOut": "2026-07-08"
  }'
```

Цена: **~$5 за 1000 listings**. Для Sample District = $1-2.

### RapidAPI booking-com15

`booking-com15.p.rapidapi.com` — community wrapper. Тарифы $0-200/мес.

```bash
curl "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels?\
dest_id=-647693&\
search_type=CITY&\
arrival_date=2026-07-01&\
departure_date=2026-07-08&\
adults=2" \
  -H "X-RapidAPI-Key: $RAPIDAPI_KEY" \
  -H "X-RapidAPI-Host: booking-com15.p.rapidapi.com"
```

## Грабли

1. **Approval требует домен с трафиком** — фриланс/personal sites обычно reject
2. **REST + GraphQL варианты** — Booking рекомендует GraphQL, REST in maintenance
3. **`city_ids` — internal Booking ID** (отрицательные числа: `-647693` = Sample City) — Lookup через `common/locations`
4. **Currency conversion** на стороне Booking — указывай `currency` в request
5. **Photos URLs** обрезаны до 200×200 thumbnail, для бóльших — replace `square60` → `square240` в URL
6. **`aid` обязателен в deeplinks** — без него комиссия теряется
7. **Staging URL отличается** — `demand-api-sandbox.booking.com` или подобный
8. **Rate limits индивидуальны** — обсуждаются с Affiliate Manager
9. **Не путать с Vrbo** (тот же owner — Expedia/Booking, но другой program)

## Use cases для User

⚠️ **Прагматично**: для sample landing (your-domain.com/region) — Apify-скрапинг проще чем affiliate approval.

Когда оформлять affiliate:
- Если /region становится travel-aggregator с продажами
- Если запускаешь отдельный travel-site (your-travel-site.com)

Для прототипа: **Apify booking-scraper + Apify airbnb-scraper** — оба через skill `apify-scraping`.

## Документация

- https://www.booking.com/affiliate-program/v2/index.html
- https://developers.booking.com/
- Apify alternative: https://apify.com/voyager/booking-scraper
