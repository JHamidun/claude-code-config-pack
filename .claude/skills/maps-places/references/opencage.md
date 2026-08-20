# OpenCage Geocoding API — справочник

Геокодер-агрегатор поверх OSM + Mapbox + WhosOnFirst. **2500 запросов/день бесплатно**, 1 req/sec. Богатые annotations (timezone, валюта, sun rise/set, MGRS).

## Endpoints

| Метод | URL |
|-------|-----|
| Forward / Reverse | `GET https://api.opencagedata.com/geocode/v1/json` |

Один endpoint обслуживает оба направления — отличается по содержимому `q`.

## Авторизация

`?key=$OPENCAGE_API_KEY` в query.

## Примеры

```bash
# Forward (адрес → координаты)
curl "https://api.opencagedata.com/geocode/v1/json?\
q=Sample+District,+Brazil&\
key=$OPENCAGE_API_KEY&\
language=pt&\
pretty=1&\
no_annotations=0"

# Reverse (координаты → адрес) — q="lat,lon" или q="lat+lon"
curl "https://api.opencagedata.com/geocode/v1/json?\
q=-22.971,-43.182&\
key=$OPENCAGE_API_KEY&\
language=pt"

# С фильтром по стране + bbox
curl "https://api.opencagedata.com/geocode/v1/json?\
q=Тверская+1&\
countrycode=ru&\
bounds=37.4,55.6,37.8,55.9&\
language=ru&\
key=$OPENCAGE_API_KEY"
```

## Структура ответа

```json
{
  "status": {"code": 200, "message": "OK"},
  "total_results": 5,
  "results": [{
    "formatted": "Sample Beach, Sample City - ST, [REDACTED_CEP], Brasil",
    "components": {
      "ISO_3166-1_alpha-2": "BR",
      "ISO_3166-1_alpha-3": "BRA",
      "country": "Brasil",
      "country_code": "br",
      "state": "Sample State",
      "state_code": "PE",
      "county": "Microrregião de Suape",
      "city": "Sample City",
      "suburb": "Sample District",
      "road": "Sample Street",
      "postcode": "[REDACTED_CEP]",
      "_type": "residential"
    },
    "geometry": {"lat": -22.9714, "lng": -43.1824},
    "confidence": 9,
    "bounds": {"northeast": {...}, "southwest": {...}},
    "annotations": {
      "timezone": {"name": "UTC", "offset_string": "-0300", "now_in_dst": 0},
      "currency": {"iso_code": "BRL", "name": "Brazilian Real", "symbol": "R$"},
      "callingcode": 55,
      "sun": {
        "rise": {"apparent": 1716969720, "astronomical": 1716966240, "civil": 1716968640, "nautical": 1716967440},
        "set": {"apparent": 1717012620, ...}
      },
      "what3words": {"words": "patches.zoomed.example"},
      "MGRS": "25LDR8829208099",
      "Maidenhead": "GH71xj",
      "DMS": {"lat": "8° 18' 18.72'' S", "lng": "34° 56' 51.96'' W"},
      "Mercator": {"x": -3893415.2, "y": -1149621.6},
      "OSM": {
        "edit_url": "https://www.openstreetmap.org/edit?node=...",
        "url": "https://www.openstreetmap.org/?mlat=-22.9714&mlon=-43.1824"
      },
      "wikidata": "Q...",
      "qibla": 84.5,
      "roadinfo": {
        "drive_on": "right",
        "speed_in": "km/h",
        "maxspeed": 60,
        "road": "Sample Street"
      }
    }
  }],
  "rate": {"limit": 2500, "remaining": 2487, "reset": 1717113600}
}
```

## Confidence levels (1-10)

| Level | Что значит |
|-------|------------|
| 10 | Exact house number match |
| 9 | Exact street/road |
| 8 | Town/suburb |
| 5-7 | City/region |
| 1-4 | Country / fuzzy |

## Параметры

| Параметр | Описание |
|----------|----------|
| `q` | Адрес ИЛИ `lat,lon` (lat первая, разделитель `,` или `+`) |
| `language` | ISO `ru`, `pt`, `en`, `ar`, `zh`... |
| `countrycode` | ISO2: `br` или `br,ru,de` |
| `bounds` | `lon_sw,lat_sw,lon_ne,lat_ne` (lon-first!) |
| `proximity` | `lat,lon` для bias |
| `no_annotations` | `1` — выключить annotations (быстрее) |
| `pretty` | `1` — pretty-print JSON |
| `limit` | Max 100 |
| `min_confidence` | 1-10 — фильтр по confidence |
| `roadinfo` | `1` — добавить speed limit и road info |

## Регистрация

1. https://opencagedata.com/users/sign_up
2. Email + пароль + agree terms
3. Confirm email
4. Dashboard → **API Keys** → trial key выдан сразу
5. Trial = **2500 req/day, 1 req/sec**, без credit card

Платные тарифы:
- $50/мес → 10K/день
- $150/мес → 50K/день
- $1495/мес → unlimited

## Грабли

1. **`q` для reverse** — `lat,lon` или `lat+lon`, **lat первая** (как у Google)
2. **`bounds` — `lon_sw,lat_sw,lon_ne,lat_ne`** (longitude первая!), необычно
3. **`proximity` — `lat,lon`**, лат первая
4. **402 = quota exceeded**, 401 = bad key, 403 = key restricted
5. **annotations.timezone** требует `no_annotations=0` (default), иначе пустой
6. **annotations.roadinfo** только при `roadinfo=1`
7. **Brazil/CIS coverage хорошее** — base of OSM + Mapbox
8. **`confidence`** не индикатор полноты адреса (может быть 10 для пустыря) — combinare с `_type`
9. **`_type`** в components: `residential`, `commercial`, `road`, `village`, `attraction`, `historic`
10. **`rate.remaining`** в каждом ответе — мониторь квоту прямо из responses

## Use cases для User

- Bulk геокодинг адресов из CSV (например клиенты с Tilda-форм)
- Timezone+currency lookup для разных гео — ad-tech фичи
- Sun rise/set для travel-маршрутов
- Fallback когда Google квота кончилась

## Документация

- https://opencagedata.com/api
- https://opencagedata.com/api#forward
- https://opencagedata.com/api#reverse
