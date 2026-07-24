# Geocoding (forward / reverse) — справочник

Перевод адрес ↔ координаты по всем 4 провайдерам.

## Google Geocoding API

```bash
# Forward
curl "https://maps.googleapis.com/maps/api/geocode/json?address=Москва,+Тверская+1&language=ru&key=$GOOGLE_MAPS_API_KEY"

# Reverse
curl "https://maps.googleapis.com/maps/api/geocode/json?latlng=55.7558,37.6173&language=ru&key=$GOOGLE_MAPS_API_KEY"
```

Ответ:
```json
{
  "results": [{
    "formatted_address": "Тверская ул., 1, Москва, Россия, 125009",
    "geometry": {"location": {"lat": 55.757, "lng": 37.609}},
    "address_components": [
      {"long_name": "1", "types": ["street_number"]},
      {"long_name": "Тверская улица", "types": ["route"]}
    ],
    "place_id": "ChIJ...",
    "types": ["street_address"]
  }]
}
```

⚠️ Geocoding API использует **старый endpoint** `maps.googleapis.com/maps/api/geocode/json`, не новый `places.googleapis.com`. Это два разных продукта, оба биллятся отдельно.

## Yandex Геокодер

```bash
# Forward
curl "https://geocode-maps.yandex.ru/1.x/?apikey=$YANDEX_GEOSEARCH_API_KEY&geocode=Москва,+Тверская+1&format=json&lang=ru_RU"

# Reverse — sco=longlat обязательно!
curl "https://geocode-maps.yandex.ru/1.x/?apikey=$YANDEX_GEOSEARCH_API_KEY&geocode=37.6173,55.7558&sco=longlat&format=json&lang=ru_RU"
```

⚠️ `geocode=` принимает `lon,lat` если `sco=longlat`, иначе `lat,lon`.

Ответ (упрощённо):
```json
{
  "response": {
    "GeoObjectCollection": {
      "featureMember": [{
        "GeoObject": {
          "name": "Тверская улица, 1",
          "description": "Тверской район, Москва, Россия",
          "Point": {"pos": "37.609 55.757"},
          "metaDataProperty": {
            "GeocoderMetaData": {
              "kind": "house",
              "precision": "exact",
              "Address": {"country_code": "RU", "formatted": "...", "Components": [...]}
            }
          }
        }
      }]
    }
  }
}
```

## 2GIS Geocoder

```bash
# Forward
curl "https://catalog.api.2gis.com/3.0/items/geocode?q=Москва,+Тверская+1&fields=items.point,items.adm_div&key=$DGIS_API_KEY"

# Reverse — lat и lon отдельными параметрами
curl "https://catalog.api.2gis.com/3.0/items/geocode?lat=55.7558&lon=37.6173&fields=items.point,items.address,items.adm_div&key=$DGIS_API_KEY"
```

Ответ:
```json
{
  "result": {
    "items": [{
      "id": "70030076148781729",
      "type": "building",
      "name": "Тверская ул., 1",
      "full_name": "Москва, Тверская ул., 1",
      "point": {"lat": 55.757, "lon": 37.609},
      "adm_div": [
        {"id": "...", "type": "city", "name": "Москва"},
        {"id": "...", "type": "district", "name": "Тверской"}
      ]
    }]
  }
}
```

## Decision: какой geocoder брать

| Локация | Качество forward | Качество reverse |
|---------|------------------|------------------|
| РФ-город | **2GIS** > Yandex > Google | **Yandex** ≈ 2GIS > Google |
| СНГ-город (Минск, Алматы, Бишкек) | **2GIS** > Yandex > Google | **2GIS** > Yandex > Google |
| РФ-село/деревня | **Yandex** > 2GIS > Google | Yandex |
| Зарубежье | **Google** | Google |

## Стандартная нормализация

Все три провайдера возвращают разный формат — для cross-provider merge приведи к единому:

```python
def normalize_geocode(result, provider):
    if provider == 'google':
        loc = result['geometry']['location']
        return {'lat': loc['lat'], 'lon': loc['lng'], 'address': result['formatted_address']}
    if provider == 'yandex':
        pos = result['Point']['pos'].split()  # "lon lat"
        return {'lon': float(pos[0]), 'lat': float(pos[1]),
                'address': result['metaDataProperty']['GeocoderMetaData']['Address']['formatted']}
    if provider == '2gis':
        return {'lat': result['point']['lat'], 'lon': result['point']['lon'],
                'address': result.get('full_name') or result['name']}
```

## Грабли

1. **Yandex `geocode=` без `sco=longlat`** воспринимает координаты как `lat,lon` — обратно сломанному порядку у `ll=`
2. **Google `latlng`**, Yandex `geocode`, 2GIS `lat`+`lon` — три разных параметра для reverse
3. **2GIS reverse возвращает building, а не address** — `full_name` уже хорош, `address` — необязательное поле
4. **Google `address_components` структурирован** (по street_number / route / locality / country) — удобно для построения нормализованного адреса
5. **Биллинг отдельно**: Geocoding API и Places API — два разных продукта в Google Cloud

## Документация

- Google: https://developers.google.com/maps/documentation/geocoding/overview
- Yandex: https://yandex.ru/dev/geocode/doc/ru/
- 2GIS: https://docs.2gis.com/ru/api/search/geocoder/overview
