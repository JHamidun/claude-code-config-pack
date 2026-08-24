# Nominatim (OpenStreetMap) — справочник

Бесплатный гео-сервис на базе OSM. Без ключа, без регистрации. Лучший fallback для геокодинга когда платная квота кончилась.

## Endpoints

| Метод | URL |
|-------|-----|
| Forward (адрес → координаты) | `GET https://nominatim.openstreetmap.org/search` |
| Reverse (координаты → адрес) | `GET https://nominatim.openstreetmap.org/reverse` |
| Lookup (по OSM id) | `GET https://nominatim.openstreetmap.org/lookup` |
| Status | `GET https://nominatim.openstreetmap.org/status` |

## Авторизация

Ключа нет. **Обязателен** заголовок `User-Agent` с описанием приложения и **своим рабочим контактом** (email или URL), иначе блокировка. Polite policy: **max 1 req/sec**.

`places_search.py` берёт контакт из `NOMINATIM_CONTACT` в `~/.claude/.credentials.master.env`; без него он работает, но пишет предупреждение в stderr. Подставлять чужой или общий адрес нельзя: Nominatim банит по User-Agent целиком, и у всех, кто оставил дефолт, поиск отвалится разом.

## Примеры

```bash
# Forward
curl -A "maps-places-skill/1.0 ($NOMINATIM_CONTACT)" \
  "https://nominatim.openstreetmap.org/search?q=Sample+District,+Sample+City&format=json&limit=5&addressdetails=1&accept-language=pt-BR,en"

# Reverse
curl -A "maps-places-skill/1.0 ($NOMINATIM_CONTACT)" \
  "https://nominatim.openstreetmap.org/reverse?lat=-22.971&lon=-43.182&format=json&accept-language=pt-BR"
```

## Структура ответа

```json
[{
  "place_id": 12345,
  "osm_type": "node",
  "osm_id": 67890,
  "lat": "-22.97139",
  "lon": "-43.18239",
  "display_name": "Sample Beach, Sample City, Sample State, Brasil",
  "address": {
    "road": "Sample Street",
    "suburb": "Sample District",
    "city": "Sample City",
    "state": "Sample State",
    "postcode": "22070-000",
    "country": "Brasil",
    "country_code": "br"
  },
  "boundingbox": ["-22.98", "-22.96", "-43.19", "-43.17"],
  "importance": 0.5,
  "type": "beach"
}]
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `q` | Текстовый запрос (forward) |
| `lat`+`lon` | Координаты (reverse) |
| `format` | `json` / `jsonv2` / `xml` / `geocodejson` |
| `limit` | Кол-во результатов (max 50) |
| `addressdetails` | `1` — добавить структурированный address |
| `extratags` | `1` — wikipedia, opening_hours и др. |
| `namedetails` | `1` — имена на других языках |
| `accept-language` | `pt-BR,en` — локаль display_name |
| `countrycodes` | Ограничить страной: `br,us` |
| `viewbox` | Bbox `lon1,lat1,lon2,lat2` для bias |
| `bounded` | `1` — strict bbox |

## Bulk POI выборки → Overpass

Nominatim — это **геокодинг**, не POI-поиск. Для запросов «все кафе в bbox» — см. `overpass.md`.

## Грабли

1. **User-Agent обязателен** — без него блок без warning
2. **1 req/sec** — иначе IP в блок (не 429, а silent 503/timeout)
3. `lat`/`lon` возвращаются как **string**, парсить через `float()`
4. `country_code` — нижний регистр ISO (`br`, `ru`), не `BR`
5. **Поиск адресов хорош, поиск POI — слабый**: «ресторан грузинская кухня» вернёт мусор
6. Для production >1 req/sec — поднять свой инстанс: `docker run -d -e PBF_URL=... mediagis/nominatim:4.4`
7. Покрытие OSM: отличное в крупных городах, среднее в малых населённых пунктах
8. **Не использовать для адресов-RU с опечатками** — Yandex Геокодер сильнее

## Документация

- https://nominatim.org/release-docs/develop/api/Overview/
- Policy: https://operations.osmfoundation.org/policies/nominatim/
- Self-host: https://hub.docker.com/r/mediagis/nominatim
