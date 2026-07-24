# Open Charge Map (EV Charging Stations) — справочник

Глобальная open-source база EV-зарядок, community-managed. **100% бесплатно**, без paid tier. Регистрация опциональна (для стабильного rate limit).

## Endpoints

| Метод | URL |
|-------|-----|
| Поиск POI (зарядок) | `GET https://api.openchargemap.io/v3/poi` |
| Reference Data | `GET https://api.openchargemap.io/v3/referencedata/` |
| Submit comment | `POST https://api.openchargemap.io/v3/comment/` |
| Submit POI | `POST https://api.openchargemap.io/v3/poi/` |

## Авторизация

`?key=$OPENCHARGEMAP_API_KEY` опционально (выше rate limit). Без ключа работает, но строже throttle.

## Примеры

```bash
# Зарядки в радиусе 10 км от точки
curl "https://api.openchargemap.io/v3/poi?\
output=json&\
latitude=-8.305&\
longitude=-34.948&\
distance=10&\
distanceunit=KM&\
maxresults=50&\
key=$OPENCHARGEMAP_API_KEY"

# По стране (Brazil)
curl "https://api.openchargemap.io/v3/poi?output=json&countrycode=BR&maxresults=100&key=$OPENCHARGEMAP_API_KEY"

# Только Type 2 (CCS=25, Type 2=33, CHAdeMO=2)
curl "https://api.openchargemap.io/v3/poi?output=json&latitude=55.7558&longitude=37.6173&distance=20&connectiontypeid=33&maxresults=50&key=$OPENCHARGEMAP_API_KEY"

# Reference data (страны, операторы, типы коннекторов)
curl "https://api.openchargemap.io/v3/referencedata/?key=$OPENCHARGEMAP_API_KEY"
```

## Структура ответа

```json
[{
  "ID": 124567,
  "UUID": "6E5BC8B4-...",
  "DataProvider": {"Title": "Open Charge Map", "WebsiteURL": "..."},
  "OperatorInfo": {
    "ID": 22,
    "Title": "Tesla (Destination)",
    "WebsiteURL": "https://www.tesla.com/"
  },
  "UsageType": {"ID": 4, "Title": "Public", "IsPayAtLocation": false, "IsMembershipRequired": false, "IsAccessKeyRequired": false},
  "AddressInfo": {
    "ID": 124567,
    "Title": "Sample Beach Beach Resort",
    "AddressLine1": "Av. Beira Mar",
    "Town": "Sample City",
    "StateOrProvince": "PE",
    "Postcode": "54522-000",
    "CountryID": 33,
    "Country": {"ID": 33, "Title": "Brazil", "ISOCode": "BR"},
    "Latitude": -8.305,
    "Longitude": -34.948,
    "ContactTelephone1": "+55 XX XXXXX-XXXX",
    "ContactEmail": "info@example.com",
    "RelatedURL": "https://example.com",
    "DistanceUnit": 1
  },
  "Connections": [{
    "ID": 234567,
    "ConnectionType": {"ID": 33, "Title": "Type 2 (Socket Only)", "FormalName": "IEC 62196-2 Type 2"},
    "StatusType": {"ID": 50, "Title": "Operational"},
    "Level": {"ID": 2, "Title": "Medium (Over 2kW)", "Comments": "...", "IsFastChargeCapable": false},
    "Amps": 32,
    "Voltage": 230,
    "PowerKW": 7.4,
    "CurrentType": {"ID": 10, "Title": "AC (Single-Phase)"},
    "Quantity": 2
  }],
  "NumberOfPoints": 2,
  "GeneralComments": "Free for resort guests",
  "DatePlanned": null,
  "DateLastConfirmed": "2024-11-15T10:00:00Z",
  "StatusType": {"ID": 50, "Title": "Operational"},
  "DateLastStatusUpdate": "2024-11-15T10:00:00Z",
  "UsageCost": "Free for guests, R$0.50/kWh others",
  "DateLastVerified": "2024-11-15T10:00:00Z"
}]
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `output` | `json` / `xml` / `csv` / `geojson` / `kml` |
| `latitude`+`longitude` | Центр |
| `distance` | Радиус |
| `distanceunit` | `KM` / `Miles` |
| `maxresults` | Default 100, max 5000 |
| `countrycode` | ISO2: `BR`, `RU` |
| `boundingbox` | `(lat1,lon1),(lat2,lon2)` — alt to distance |
| `operatorid` | comma-list (из reference data) |
| `connectiontypeid` | comma-list — фильтр по разъёмам |
| `levelid` | 1=slow / 2=medium / 3=fast |
| `minpowerkw` | минимум мощности kW |
| `verbose` | `true`/`false` — урезать ответ |
| `compact` | `true` — без полных reference объектов |
| `includecomments` | `true` — пользовательские комменты |

## Connection Type IDs (часто нужны)

| ID | Title |
|----|-------|
| 2 | CHAdeMO |
| 25 | CCS (Type 2) |
| 27 | CCS (Type 1) |
| 33 | Type 2 (Mennekes, EU стандарт) |
| 1036 | Type 2 (Socket Only) |
| 1 | Type 1 (J1772) |
| 30 | Tesla Roadster |
| 8 | Tesla NACS / Supercharger |
| 32 | Type 3 (Scame) |

Полный список через `referencedata` endpoint.

## Power tiers

- **Slow** (Level 1): <3 kW — 12+ часов
- **Medium** (Level 2): 3-22 kW — 4-8 часов
- **Fast** (Level 3): 50-150 kW — 30-60 мин
- **Ultra-fast**: 150+ kW (Tesla Supercharger, IONITY) — 15-30 мин

## Регистрация

1. https://openchargemap.org/site/profile/applications
2. Sign in через Google / Microsoft / GitHub OAuth
3. **Register Application** — имя, описание, URL
4. API Key выдаётся **сразу**

Бесплатно навсегда. CC-BY-SA 4.0 — attribution «© OpenChargeMap.org contributors».

## Грабли

1. **`Latitude`+`Longitude` — capitalized** в ответе (не `lat`/`lon`)
2. **Coverage уравномерное**: EU 5/5, USA 5/5, UK 5/5. Brazil 3/5 (растёт), Russia 4/5
3. **`DateLastVerified`** — критично! Старше года = не доверять для live навигации
4. **Community-edited data** — могут быть устаревшие/неверные. Production: cross-check с OperatorInfo + DateLastConfirmed
5. **`PowerKW` иногда null** — обязательно проверять, бывают пустые поля
6. **`Connections[]` массив** — может быть несколько на одну станцию (разные коннекторы)
7. **`compact=true`** урезает response в 3-5 раз — для большинства задач достаточно
8. **CSV-output** для excel-импорта: `output=csv`
9. **Без `latitude`+`longitude` И без `countrycode`** возвращает только небольшую sample-выборку
10. **Free** реально free — никаких overage charges

## Use cases для User

- **«найди зарядки рядом»** команда в maps-places skill
- EV-роадтрип Miami → your region: маршрут + зарядки на пути
- Конкурентный анализ EV-инфраструктуры в Sample State для landing
- Mapping EV-зарядок для Tilda-блока «инфраструктура Sample District»

## Документация

- https://openchargemap.org/site/develop/api
- https://api.openchargemap.io/v3/referencedata/ — все справочники
- GitHub: https://github.com/openchargemap/ocm-api
