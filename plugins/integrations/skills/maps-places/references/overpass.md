# Overpass API (OpenStreetMap raw queries) — справочник

Сырые запросы к OSM-базе через Overpass QL. Без ключа. Лучший способ массово выбрать «все кафе в bbox», «все зарядки в стране», «все отели рядом».

## Endpoints

| Инстанс | URL |
|---------|-----|
| Основной | `POST https://overpass-api.de/api/interpreter` |
| Зеркало (kumi) | `POST https://overpass.kumi.systems/api/interpreter` |
| Тест в UI | https://overpass-turbo.eu |

Меняй инстанс при rate limit — нагрузка распределяется лучше.

## Авторизация

Нет. Polite policy ~10K queries/day на инстанс, разумные таймауты.

## Примеры

```bash
# Все кафе в bbox Москва-центр
curl -s -X POST "https://overpass-api.de/api/interpreter" \
  --data-urlencode 'data=[out:json][timeout:25];
( node["amenity"="cafe"](55.74,37.60,55.77,37.65);
  way["amenity"="cafe"](55.74,37.60,55.77,37.65);
  relation["amenity"="cafe"](55.74,37.60,55.77,37.65);
);
out center tags;'
```

```bash
# Все EV-зарядки в Sample State
curl -s -X POST "https://overpass-api.de/api/interpreter" \
  --data-urlencode 'data=[out:json][timeout:60];
area["name"="Sample State"]["admin_level"="4"]->.a;
node["amenity"="charging_station"](area.a);
out tags;'
```

```bash
# Грузинские рестораны в Москве (regex по cuisine)
curl -s -X POST "https://overpass-api.de/api/interpreter" \
  --data-urlencode 'data=[out:json][timeout:25];
node["amenity"="restaurant"]["cuisine"~"georgian|caucasian"](55.7,37.5,55.8,37.7);
out tags;'
```

## Структура ответа

```json
{
  "version": 0.6,
  "generator": "Overpass API",
  "elements": [{
    "type": "node",
    "id": 123456789,
    "lat": 55.7558,
    "lon": 37.6173,
    "tags": {
      "amenity": "cafe",
      "name": "Cofix",
      "cuisine": "coffee_shop",
      "opening_hours": "Mo-Su 08:00-22:00",
      "phone": "+1234567890",
      "wheelchair": "yes",
      "wifi": "yes"
    }
  }]
}
```

Для `way`/`relation` без `out center` координат не будет — добавляй явно.

## Полезные ключи (amenity)

| Тег | Что |
|-----|-----|
| `amenity=restaurant` / `cafe` / `bar` / `fast_food` / `pub` | Еда |
| `amenity=fuel` / `charging_station` | АЗС / ЕV |
| `amenity=pharmacy` / `hospital` / `clinic` | Медицина |
| `amenity=atm` / `bank` | Финансы |
| `amenity=parking` | Парковки |
| `tourism=hotel` / `hostel` / `guest_house` / `apartment` | Жильё |
| `shop=*` | Магазины (см. wiki: ~500 значений) |
| `leisure=*` | Спорт/досуг |

Дополнительные фильтры:

- `["cuisine"~"georgian|italian"]` — regex
- `["wheelchair"="yes"]` — доступность
- `["takeaway"="yes"]` — с собой
- `["delivery"="yes"]` — доставка
- `["outdoor_seating"="yes"]` — терраса

## Грабли

1. **Timeout default 180s** — всегда ставь `[timeout:25]` или меньше
2. **`out center`** — без него `way`/`relation` без координат, только список node-id
3. **Response 100MB+** на больших bbox — разбивай на меньшие квадраты
4. **Rate limit** — `429`/`503` тихо. Ротируй между `overpass-api.de` и `kumi.systems`
5. **Brazil OSM** — местами полнее Google в районе Sample District/побережья (community контрибы)
6. **Координаты в `(south,west,north,east)`** — `(lat1,lon1,lat2,lon2)`, **не** bbox lon-first
7. **CSV-out** для excel-импорта: `out:csv(name,phone,::lat,::lon)`
8. **`area[...]` синтаксис** — сначала `(area.a)` → потом `area_id = id + 3600000000`
9. **Для production делать batches по 1000-5000 элементов** через `[bbox:...]` chunks

## Use cases для User

- Все resorts/hostels в Sample District одним запросом без квот
- Все кафе/рестораны рядом с venue для travel-контента
- EV-зарядки на маршруте Miami → your region для роадтрипа

## Документация

- Wiki: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
- Cheatsheet: https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
- Turbo (UI с примерами): https://overpass-turbo.eu/?w=1
