# Google Places API (New) — справочник

## Endpoints

| Метод | URL |
|-------|-----|
| Text Search | `POST https://places.googleapis.com/v1/places:searchText` |
| Nearby Search | `POST https://places.googleapis.com/v1/places:searchNearby` |
| Place Details | `GET https://places.googleapis.com/v1/places/{placeId}` |
| Place Photos | `GET https://places.googleapis.com/v1/{photoName}/media` |
| Autocomplete | `POST https://places.googleapis.com/v1/places:autocomplete` |

## Авторизация

- Заголовок: `X-Goog-Api-Key: $GOOGLE_MAPS_API_KEY`
- Поля: `X-Goog-FieldMask: places.displayName,places.rating,places.formattedAddress` — **обязателен**

## Text Search — пример

```bash
curl -X POST 'https://places.googleapis.com/v1/places:searchText' \
  -H "X-Goog-Api-Key: $GOOGLE_MAPS_API_KEY" \
  -H 'X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.location,places.nationalPhoneNumber,places.websiteUri,places.regularOpeningHours' \
  -H 'Content-Type: application/json' \
  -d '{
    "textQuery": "ресторан грузинская кухня",
    "languageCode": "ru",
    "maxResultCount": 20,
    "locationBias": {
      "circle": {"center": {"latitude": 55.7558, "longitude": 37.6173}, "radius": 5000}
    }
  }'
```

## Nearby Search — пример

```json
{
  "includedTypes": ["restaurant"],
  "maxResultCount": 20,
  "locationRestriction": {
    "circle": {"center": {"latitude": 55.7558, "longitude": 37.6173}, "radius": 1500}
  },
  "rankPreference": "POPULARITY"
}
```

`includedTypes` (одно из ~200 значений): `restaurant, cafe, bar, bakery, fast_food_restaurant, italian_restaurant, sushi_restaurant, georgian_restaurant`, и т.д. — полный список: https://developers.google.com/maps/documentation/places/web-service/place-types

## FieldMask — что просить

| Категория | Поля |
|-----------|------|
| Essentials (IDs only) | `places.id, places.name` |
| Essentials | `places.displayName, places.formattedAddress, places.location, places.types, places.googleMapsUri, places.shortFormattedAddress` |
| Pro | `places.rating, places.userRatingCount, places.priceLevel, places.regularOpeningHours, places.nationalPhoneNumber, places.websiteUri, places.businessStatus` |
| Enterprise | `places.reviews, places.photos, places.editorialSummary` |
| Atmosphere | `places.servesBreakfast, places.allowsDogs, places.takeout, places.outdoorSeating, places.servesVegetarianFood, places.menuForChildren` |

## Pricing tiers (после $200/мес бесплатного кредита)

| SKU | $/1K | Бесплатно/мес |
|-----|------|---------------|
| Text Search Essentials | $2.83 | до 10K |
| Text Search Pro | дороже | — |
| Place Details Essentials | дешевле | |
| Place Details Pro + Atmosphere | дороже всего | |

## Поле `priceLevel`

`PRICE_LEVEL_FREE, PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_MODERATE, PRICE_LEVEL_EXPENSIVE, PRICE_LEVEL_VERY_EXPENSIVE`

## Поле `regularOpeningHours`

```json
{
  "openNow": true,
  "periods": [{"open": {"day": 1, "hour": 9, "minute": 0}, "close": {"day": 1, "hour": 22, "minute": 0}}],
  "weekdayDescriptions": ["Monday: 9:00 AM – 10:00 PM", ...]
}
```

## Грабли

1. **FieldMask обязателен** — без него возврат HTTP 400
2. **`searchText` vs `searchNearby`**: searchText принимает любую строку, searchNearby — только `includedTypes` + локация
3. **Locale**: `languageCode: "ru"` влияет на displayName и weekdayDescriptions
4. **`locationBias` vs `locationRestriction`**: `bias` смягчает (нестрого), `restriction` строго ограничивает кругом
5. **Pagination через `pageToken`** в ответе — для >20 результатов
6. **Reviews и Photos** в Pro+Atmosphere SKU — биллится отдельно и дороже

## Документация

- https://developers.google.com/maps/documentation/places/web-service/text-search
- https://developers.google.com/maps/documentation/places/web-service/place-types
