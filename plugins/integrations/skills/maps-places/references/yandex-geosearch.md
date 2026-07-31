# Yandex Geosearch (API Поиска по организациям) — справочник

## Endpoints

| Метод | URL |
|-------|-----|
| Geosearch | `GET https://search-maps.yandex.ru/v1/` |
| Геокодер (HTTP) | `GET https://geocode-maps.yandex.ru/1.x/` |

Оба используют один ключ `YANDEX_GEOSEARCH_API_KEY`, если он подключён к обоим API в кабинете https://developer.tech.yandex.ru/services.

## Параметры Geosearch

| Параметр | Тип | Описание |
|----------|-----|----------|
| `apikey` | string | **обяз.** |
| `text` | string | **обяз.** Запрос (рубрика, название, бренд) |
| `type` | `biz` / `geo` / `toponym` / `street` / `metro` | `biz` для организаций |
| `ll` | `lon,lat` | Центр поиска. ⚠️ долгота первая |
| `spn` | `dlon,dlat` | Размер bbox в градусах |
| `bbox` | `lon1,lat1~lon2,lat2` | Альтернатива spn |
| `rspn` | `1` / `0` | 1 = ограничить только bbox'ом |
| `results` | int ≤500 | Кол-во результатов |
| `skip` | int | Offset для пагинации |
| `lang` | `ru_RU` / `en_US` / `uk_UA` / `tr_TR` | Локаль |
| `format` | `json` / `xml` | |

## Пример

```bash
curl "https://search-maps.yandex.ru/v1/?apikey=$YANDEX_GEOSEARCH_API_KEY&text=ресторан+грузинская+кухня&type=biz&ll=37.6173,55.7558&spn=0.3,0.3&rspn=1&results=20&lang=ru_RU&format=json"
```

## Структура ответа

```json
{
  "type": "FeatureCollection",
  "properties": {
    "ResponseMetaData": {
      "SearchResponse": {"found": 51, "display": "multiple"},
      "SearchRequest": {...}
    }
  },
  "features": [{
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [lon, lat]},
    "properties": {
      "name": "Megobari",
      "description": "Москва, ул. Маросейка, 15",
      "boundedBy": [[lon1,lat1],[lon2,lat2]],
      "CompanyMetaData": {
        "id": "1041647937",
        "name": "Megobari",
        "address": "Москва, улица Маросейка, 15",
        "url": "megobari.ru",
        "Phones": [{"type": "phone", "formatted": "+1234567890"}],
        "Categories": [{"class": "restaurants", "name": "Ресторан"}, ...],
        "Hours": {
          "text": "ежедневно, 12:00–00:00",
          "Availabilities": [{"Everyday": true, "Intervals": [{"from": "12:00:00", "to": "24:00:00"}]}],
          "State": {"text": "Открыто до 24:00", "isOpenNow": true}
        },
        "Features": [
          {"id": "wi_fi", "name": "Wi-Fi", "value": true},
          {"id": "wheelchair_accessible", "value": true},
          {"id": "parking_personal", "value": true}
        ]
      }
    }
  }]
}
```

## Полезные `Features` (удобства)

- `wi_fi` — Wi-Fi
- `wheelchair_accessible` — доступ для инвалидной коляски
- `parking_personal` — собственная парковка
- `payment_by_credit_card` — оплата картой
- `takeaway` — еда с собой
- `delivery_food` — доставка
- `kids_room` — детская комната
- `pets_allowed` — можно с животными

## Геокодер (отдельный endpoint)

```bash
# адрес → координаты
curl "https://geocode-maps.yandex.ru/1.x/?apikey=$YANDEX_GEOSEARCH_API_KEY&geocode=Москва,+Тверская+1&format=json&lang=ru_RU"

# координаты → адрес (sco=longlat — важно)
curl "https://geocode-maps.yandex.ru/1.x/?apikey=$YANDEX_GEOSEARCH_API_KEY&geocode=37.6173,55.7558&sco=longlat&format=json&lang=ru_RU"
```

## Грабли

1. **Новый ключ активируется 30-45 минут** — 403 «Invalid api key» сразу после создания нормально
2. **`ll` = `lon,lat`** (долгота первая), не как у Google
3. **`spn` тоже `dlon,dlat`** — двойная привычка
4. **Без `rspn=1` bbox только подсказка** — результаты могут быть за его пределами
5. **`lang=ru_RU`** влияет на `name`, `description`, `Categories[].name`, `Hours.text`
6. **Тариф «Бесплатный» = 1000/сутки** на один сервис, без баланса на ЛС. Сверх — нужен платный тариф
7. **Старые ключи в кабинете могут иметь IP/Referer ограничения** — проверь Настройки → пусто значит работает откуда угодно

## Документация

- https://yandex.ru/maps-api/docs/geosearch-api/
- https://yandex.ru/dev/geocode/doc/ru/
- Кабинет: https://developer.tech.yandex.ru/services/12
