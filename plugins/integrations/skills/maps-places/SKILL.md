---
name: maps-places
description: "Поиск мест, ресторанов, организаций, адресов, EV-зарядок, Airbnb и геокодинг через 11 провайдеров (Google Places, Yandex Geosearch, 2GIS, HERE, Mapbox, Foursquare, OpenCage, OSM, Open Charge Map, SerpAPI, Apify). Плюс часы работы, телефоны, рейтинги."
---

# Maps & Places

Универсальный скилл для поиска организаций, мест, адресов через 11 провайдеров. Выбирает оптимальный по гео/задаче или мёрджит несколько.

## Когда использовать

- Поиск ресторанов, кафе, магазинов, заправок, аптек по запросу + локации
- Поиск конкурентов (organizations) в радиусе вокруг точки
- Геокодинг (адрес → координаты) и обратный (координаты → адрес)
- Получение часов работы, телефонов, рейтингов, рубрик, фото
- EV-зарядки на маршруте
- Airbnb-листинги с фильтром по датам и гостям
- Анализ плотности заведений / сетей в городе

## Провайдеры

| Провайдер | Лучше всего для | Лимиты бесплатно |
|-----------|------------------|------------------|
| **Google Places (New)** | Глобально, рейтинги, отзывы, цены ($), фото | $200/мес кредит ≈ 10K Text Search |
| **Yandex Geosearch** | РФ: часы, удобства, рубрики, телефоны | 1000/сутки |
| **2GIS Catalog** | РФ + СНГ: глубокая база, входы в здания, отделы | 1000/мес/сервис (demo) |
| **HERE Maps** | EU, Asia, Middle East, маршруты с трафиком | 250K транзакций/мес |
| **Mapbox** | Глобально, отличный dev-experience, навигация | 100K Search/Geocoding/мес |
| **Foursquare** | США/EU, 10K+ POI-категорий, Tips | $200 free credits/мес |
| **OpenCage** | Богатый геокодер: timezone, currency, sun rise | 2500/день |
| **OpenStreetMap Nominatim** | Free fallback геокодинг, bulk без квот | без ключа, 1 req/sec |
| **OpenStreetMap Overpass** | Bulk «все кафе в bbox», raw OSM queries | без ключа |
| **Open Charge Map** | EV-зарядки, community-managed | 100% free, no quota |
| **SerpAPI** | Fallback когда Places недоступен | 250/мес |
| **Apify Airbnb** | Airbnb-листинги с датами+гостями | pay-per-result ~$5/1K |

## Decision tree

```
Запрос пользователя
├── Геокодинг (адрес ↔ координаты)
│   ├── РФ → 2GIS + Yandex
│   ├── мир → Google + HERE + Mapbox
│   └── bulk без квот → Nominatim + OpenCage
├── Поиск организаций
│   ├── РФ → 2GIS (глубже) + Yandex (часы) + Google (рейтинги) [all]
│   ├── EU/Asia → HERE + Google + Foursquare [all+]
│   └── глобально → Google + Mapbox + Foursquare
├── EV-зарядки → ocm
├── Airbnb-листинги → airbnb (--check-in --check-out --guests)
└── Bulk POI экспорт → overpass
```

## Использование

### 1) CLI обёртка

```bash
# Отдельные провайдеры
python ~/.claude/tools/places_search.py google "ресторан грузинская" --lat 55.7558 --lon 37.6173
python ~/.claude/tools/places_search.py yandex "суши" --lat 55.7558 --lon 37.6173
python ~/.claude/tools/places_search.py 2gis "кофейня" --lat 55.7558 --lon 37.6173
python ~/.claude/tools/places_search.py here "georgian restaurant" --lat 55.7558 --lon 37.6173
python ~/.claude/tools/places_search.py mapbox "café" --lat 48.8566 --lon 2.3522
python ~/.claude/tools/places_search.py foursquare "pizza" --lat 40.7128 --lon -74.0060
python ~/.claude/tools/places_search.py opencage "Sample Beach, Brazil"
python ~/.claude/tools/places_search.py nominatim "Тверская 13"
python ~/.claude/tools/places_search.py overpass "cafe" --lat 55.7558 --lon 37.6173 --radius 1000 --limit 50
python ~/.claude/tools/places_search.py ocm "ev" --lat -8.305 --lon -34.948 --radius 50000
python ~/.claude/tools/places_search.py serpapi "pizza" --lat 40.71 --lon -74.00

# Airbnb
python ~/.claude/tools/places_search.py airbnb "Sample District, Brazil" --check-in 2026-07-01 --check-out 2026-07-08 --guests 2

# Гибридные merge-режимы
python ~/.claude/tools/places_search.py both "ресторан" --lat 55.7558 --lon 37.6173   # Yandex + Google
python ~/.claude/tools/places_search.py all  "кафе"     --lat 55.7558 --lon 37.6173   # +2GIS
python ~/.claude/tools/places_search.py all+ "ресторан" --lat 55.7558 --lon 37.6173   # +HERE + Foursquare + Mapbox (6 источников)

# JSON-выгрузка
python ~/.claude/tools/places_search.py all+ "пиццерия" --lat 55.75 --lon 37.62 --json > out.json

# Геокодинг (forward — все 6 провайдеров параллельно)
python ~/.claude/tools/places_search.py geocode "Мясницкая 13, Москва"

# Reverse геокодинг (все 6 параллельно)
python ~/.claude/tools/places_search.py reverse_geocode --lat 55.7558 --lon 37.6173
```

## Reference docs

- `references/google-places.md` — Places API (New): Text/Nearby Search, FieldMask, types
- `references/yandex-geosearch.md` — параметры spn/rspn, CompanyMetaData, Геокодер
- `references/2gis.md` — Catalog API, Places, Geocoder, Suggest
- `references/here-maps.md` — Discover/Browse, EV charging, PCS categories
- `references/mapbox.md` — Search Box, Geocoding v6, Directions, token types
- `references/foursquare.md` — v3 API, fsq_id, 10K+ категорий
- `references/opencage.md` — confidence levels, annotations (timezone, currency, sun)
- `references/nominatim.md` — User-Agent policy, polite 1 req/sec
- `references/overpass.md` — Overpass QL, amenity tags, bulk выборки
- `references/open-charge-map.md` — EV connection types, power tiers
- `references/serpapi-maps.md` — fallback scraping
- `references/yelp-fusion.md` — США/Canada/EU (требует business approval, ключа нет)
- `references/tripadvisor.md` — tourism (partner application only)
- `references/booking-affiliate.md` — hotels (partner only, альтернатива Apify)
- `references/china-maps.md` — Amap/Baidu (skip без кит. телефона)
- `references/geocoding.md` — forward/reverse normalization

## Грабли

1. **Yandex новые ключи активируются 30-45 минут**, не моментально — 403 «Invalid api key» после создания нормально, подожди
2. **2GIS demo key 1 месяц** и 1000/мес на каждый сервис. Перед production — оформить подписку
3. **Google `X-Goog-FieldMask` обязателен** — без него ошибка. Reviews/photos = другой ценовой SKU
4. **Yandex `ll` — `lon,lat`** (не lat,lon как у HERE/Google/Foursquare). **2GIS** тоже lon,lat. **Mapbox proximity** тоже lon,lat
5. **HERE billing требует $1 validation 3DS** на новые аккаунты — это auth-only, не списание; free 250K/мес
6. **Mapbox требует карту при signup** ($0 charge на free tier, но карта нужна для активации)
7. **Foursquare** — best signup via Google OAuth (избегает CAPTCHAs); требует прочитать Terms+Privacy перед Sign Up
8. **OCM требует User-Agent** в headers, иначе 403
9. **Nominatim User-Agent обязателен**, polite policy 1 req/sec — иначе блокирует
10. **Overpass timeout default 180s** — всегда `[timeout:25]`. `out center` для way/relation
11. **Merge tolerance 0.0005° (~50м)** — Google и Yandex могут давать одно место с >50м разницы
12. **Yandex Геокодер 403** — `YANDEX_GEOSEARCH_API_KEY` подключён только к Geosearch, для Geocoder API нужно «Привязать к API» в кабинете
13. **OpenCage оптимален для bulk address normalization** без POI-поиска

## Связано

- `~/.claude/projects/C--Users-youruser/memory/maps-api-setup-2026-05-28.md` — история ключей
- `~/.claude/tools/places_search.py` — основной CLI (shim к скиллу)
- Skill `yandex` — Метрика/Директ/Диск (не карты)
- Skill `apify-scraping` — для Airbnb actor
- Skill `serpapi` — SERP scraping (включая google_maps)
