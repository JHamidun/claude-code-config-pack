# 2GIS Catalog API — справочник

## Endpoints

| Сервис | URL |
|--------|-----|
| Places (поиск организаций) | `GET https://catalog.api.2gis.com/3.0/items` |
| Place Details | `GET https://catalog.api.2gis.com/3.0/items/byid?id={id}` |
| Geocoder | `GET https://catalog.api.2gis.com/3.0/items/geocode` |
| Suggest (автодополнение) | `GET https://catalog.api.2gis.com/3.0/suggests` |
| Categories | `GET https://catalog.api.2gis.com/3.0/items/category` |
| Regions | `GET https://catalog.api.2gis.com/2.0/region/search` |
| Routing | `GET https://routing.api.2gis.com/routing/7.0.0/global` |

## Авторизация

`?key=$DGIS_API_KEY` — query string. Можно также `Authorization: Bearer` для приватных эндпоинтов.

## Places — пример

```bash
curl "https://catalog.api.2gis.com/3.0/items?\
q=ресторан+грузинская+кухня&\
location=37.6173,55.7558&\
radius=5000&\
fields=items.point,items.address,items.contact_groups,items.schedule,items.rubrics,items.reviews,items.flags,items.org&\
page_size=20&\
key=$DGIS_API_KEY"
```

## Параметры Places

| Параметр | Описание |
|----------|----------|
| `q` | Текстовый запрос (рубрика, бренд, название) |
| `location` | `lon,lat` — центр поиска (**долгота первая**) |
| `radius` | Метры (макс ~40000) |
| `point1`+`point2` | Альтернатива radius: bbox через две точки |
| `rubric_id` | Поиск по конкретной рубрике (см. /items/category) |
| `region_id` | Ограничить регионом |
| `page_size` | До 50 |
| `page` | Pagination, начиная с 1 |
| `sort` | `relevance` (default), `distance`, `rating` |
| `fields` | Какие поля вернуть. Без них — только базовое |
| `locale` | `ru_RU`, `en_US`, `kz_KZ`, `ar_AE` и др. |

## Поля `fields` (запрашивать явно)

- `items.point` — координаты
- `items.address` — полный адрес
- `items.contact_groups` — телефоны, сайт, email, соцсети
- `items.schedule` — часы работы + `is_24x7` + `working_status`
- `items.rubrics` — рубрики (категории 2GIS)
- `items.reviews` — общий рейтинг
- `items.flags` — `delivery`, `paid_parking`, `card_payments` и т.д.
- `items.org` — данные организации (если сеть)
- `items.adm_div` — административное деление
- `items.external_content` — фото, меню
- `search_attributes` — `tag_list` (теги)

## Структура ответа

```json
{
  "result": {
    "total": 142,
    "items": [{
      "id": "70000001020163459",
      "type": "branch",
      "name": "Megobari",
      "address_name": "Москва, ул. Маросейка, 15",
      "address": {
        "components": [{"type": "street_number_building", "street": "Маросейка", "number": "15"}],
        "building_id": "...",
        "post_code": "101000"
      },
      "point": {"lat": 55.756, "lon": 37.640},
      "contact_groups": [{
        "contacts": [
          {"type": "phone", "value": "+1234567890", "text": "+1234567890"},
          {"type": "website", "url": "megobari.ru", "value": "megobari.ru"}
        ]
      }],
      "schedule": {
        "is_24x7": false,
        "working_status": "Open",
        "tue": {"working_hours": [{"from": "12:00", "to": "00:00"}]},
        ...
      },
      "rubrics": [{"id": "169", "name": "Ресторан"}, ...],
      "reviews": {"general_review_count": 234, "general_rating": 4.7, ...},
      "flags": {"delivery": true, "card_payments": true}
    }]
  }
}
```

## Geocoder

```bash
# Адрес → координаты
curl "https://catalog.api.2gis.com/3.0/items/geocode?q=Москва,+ул.+Маросейка+15&fields=items.point,items.adm_div&key=$DGIS_API_KEY"

# Координаты → адрес
curl "https://catalog.api.2gis.com/3.0/items/geocode?lat=55.7558&lon=37.6173&fields=items.point,items.address,items.adm_div&key=$DGIS_API_KEY"
```

## Suggest (автодополнение)

```bash
curl "https://catalog.api.2gis.com/3.0/suggests?q=Меб&location=37.62,55.75&suggest_type=object&key=$DGIS_API_KEY"
```

## Тарификация demo-ключа

- **1 месяц** действия с момента выдачи
- **1000 запросов в месяц** на каждый сервис (Places, Geocoder, Suggest, Categories, Regions, Markers)
- **600 запросов в минуту** rate-limit
- Routing/Directions: **50/день** + 1000/мес

После demo — оформление подписки на https://platform.2gis.ru/ru/tariffs.

## Грабли

1. **`location=lon,lat`** (долгота первая), как у Yandex — НЕ как у Google
2. **`fields=` обязателен** для всего интересного: без него только id+name+address
3. **`type=branch`** = филиал/конкретное место, `type=org` = организация. Для UI обычно нужен `branch`
4. **Coordinates: `point.lat` + `point.lon`** — а не `coordinates: [...]` как у Yandex
5. **`schedule.is_24x7` + `working_status`** — быстрый чек открыто-сейчас
6. **Demo key expires** в `~/.claude/.credentials.master.env` стоит дата 28.06 — за неделю до неё пересоздавать или оформить подписку

## Документация

- https://docs.2gis.com/ru/api/search/places/overview
- https://docs.2gis.com/ru/api/search/geocoder/overview
- Кабинет: https://platform.2gis.ru/ru/keys
