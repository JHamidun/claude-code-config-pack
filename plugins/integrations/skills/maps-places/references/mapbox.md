# Mapbox APIs (Search, Geocoding, Directions) — справочник

Глобальный гео-стек. **100K req/мес бесплатно** на Search/Geocoding. Сильнее в навигации/маршрутах, отличный dev-experience.

## Endpoints

| Метод | URL |
|-------|-----|
| Search Box Forward | `GET https://api.mapbox.com/search/searchbox/v1/forward` |
| Search Box Suggest | `GET https://api.mapbox.com/search/searchbox/v1/suggest` |
| Search Box Retrieve | `GET https://api.mapbox.com/search/searchbox/v1/retrieve/{mapbox_id}` |
| Search Box Category | `GET https://api.mapbox.com/search/searchbox/v1/category/{canonical_id}` |
| Geocoding v6 Forward | `GET https://api.mapbox.com/search/geocode/v6/forward` |
| Geocoding v6 Reverse | `GET https://api.mapbox.com/search/geocode/v6/reverse` |
| Directions | `GET https://api.mapbox.com/directions/v5/mapbox/driving/{coords}` |
| Matrix | `GET https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coords}` |
| Isochrone | `GET https://api.mapbox.com/isochrone/v1/mapbox/driving/{lon,lat}` |

## Авторизация

`?access_token=$MAPBOX_TOKEN` в query. Токены:

- `pk.eyJ...` — **public**, для фронта (можно палить в HTML)
- `sk.eyJ...` — **secret**, для бэка (НЕ коммитить, restrict по scope)

## Примеры

```bash
# Forward (POI + address)
curl "https://api.mapbox.com/search/searchbox/v1/forward?\
q=ресторан+грузинская+Москва&\
proximity=37.6173,55.7558&\
types=poi,address&\
language=ru&\
limit=10&\
access_token=$MAPBOX_TOKEN"

# Suggest + Retrieve (для UI-autocomplete)
SESSION=$(uuidgen)
curl "https://api.mapbox.com/search/searchbox/v1/suggest?\
q=Megobari&\
proximity=37.6173,55.7558&\
session_token=$SESSION&\
access_token=$MAPBOX_TOKEN"
# Затем по mapbox_id из ответа:
curl "https://api.mapbox.com/search/searchbox/v1/retrieve/dXJiYW46MTIzNDU?\
session_token=$SESSION&\
access_token=$MAPBOX_TOKEN"

# Geocoding v6 (адрес → координаты)
curl "https://api.mapbox.com/search/geocode/v6/forward?\
q=Sample+District,+Brazil&\
limit=5&\
access_token=$MAPBOX_TOKEN"

# Reverse
curl "https://api.mapbox.com/search/geocode/v6/reverse?\
longitude=-43.182&latitude=-22.971&\
language=pt&\
access_token=$MAPBOX_TOKEN"

# Directions (маршрут с трафиком)
curl "https://api.mapbox.com/directions/v5/mapbox/driving-traffic/-46.633,-23.550;-43.210,-22.905?\
geometries=geojson&\
access_token=$MAPBOX_TOKEN"
```

## Структура ответа (Search Box Forward)

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [37.6411, 55.7575]},
    "properties": {
      "mapbox_id": "dXJiYW46MTIzNDU",
      "name": "Megobari",
      "name_preferred": "Megobari",
      "feature_type": "poi",
      "full_address": "ул. Маросейка 15, 101000 Москва, Россия",
      "place_formatted": "101000 Москва, Россия",
      "context": {
        "country": {"name": "Россия", "country_code": "ru"},
        "region": {"name": "Москва"},
        "locality": {"name": "Москва"},
        "address": {"name": "ул. Маросейка 15"}
      },
      "coordinates": {"longitude": 37.6411, "latitude": 55.7575},
      "language": "ru",
      "maki": "restaurant",
      "poi_category": ["restaurant", "georgian_restaurant"],
      "external_ids": {
        "foursquare": "4b1aa7b9f964a52040c823e3",
        "safegraph": "..."
      },
      "metadata": {
        "phone": "+1234567890",
        "website": "https://megobari.ru",
        "open_hours": {"periods": [...]}
      }
    }
  }]
}
```

## Параметры (Search Box Forward)

| Параметр | Описание |
|----------|----------|
| `q` | Запрос |
| `proximity` | `lon,lat` — **lon первая** |
| `bbox` | `min_lon,min_lat,max_lon,max_lat` |
| `country` | `ru,br` — ISO2 список |
| `types` | `poi,address,place,locality,country,district,region` — comma |
| `language` | ISO `ru`, `pt`, `en` |
| `limit` | 1-10 |
| `poi_category` | `restaurant,cafe,hotel` — comma |
| `session_token` | UUID для Suggest+Retrieve billing |

## Regions / Brazil specifics

- Brazil: **очень хорошее покрытие** в городах (партнёрство с Locus)
- Небольшие города и посёлки: POI хуже Google (мало пользовательских данных), адресный геокодинг отличный
- РФ: средний POI (хуже Yandex/2GIS), адреса decent

## Регистрация

1. https://account.mapbox.com/auth/signup
2. Email + password
3. Account → **Tokens** → Create token
4. Имя токена + scopes (по default — все public scopes)
5. Token starts with `pk.eyJ...`
6. Для backend → создать **secret token** (`sk.eyJ...`) с минимальным набором scopes (только что нужно)

Free Pay-as-you-go (PAYG): **100K Search Box / 100K Geocoding / 100K Map Loads** в месяц.

## Грабли

1. **`proximity` = `lon,lat`** (longitude первая) — НЕ как у Google
2. **`coordinates` = `[lon, lat]`** в GeoJSON ответе (GeoJSON стандарт)
3. **v6 геокодинг изменил формат** vs v5 — `center` → `geometry.coordinates`
4. **`pk` можно палить, `sk` НЕЛЬЗЯ** — sk leak = биллинг от твоего имени
5. **Session token для Suggest+Retrieve** — без него каждый retrieve = новая транзакция (дороже)
6. **`types=poi,address`** обязательно для POI поиска, иначе только адреса
7. **Rate limit 600 req/min** на free tier
8. **`isochrone`** возвращает GeoJSON polygon (зона доезда за N минут)
9. **`Directions` matrix** ограничен 25×25 точек (625 пар), для больших — Matrix API
10. **POI слабее Google** в маленьких локациях — там в hybrid лучше Google
11. **`external_ids.foursquare`** — отличная фича для cross-merge с Foursquare

## Документация

- https://docs.mapbox.com/api/search
- https://docs.mapbox.com/api/search/geocoding-v6/
- https://docs.mapbox.com/api/navigation/directions/
- Pricing: https://www.mapbox.com/pricing
