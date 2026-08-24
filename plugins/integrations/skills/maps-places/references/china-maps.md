# China Maps (Amap + Baidu) — справочник

Amap (高德) и Baidu — единственные viable карты **в материковом Китае**. Google/HERE/Mapbox имеют data offset из-за **GCJ-02 coordinate shift** (50-500m error).

⚠️ **Auto-register не feasible**: оба требуют Chinese phone + national ID. Skip без китайского партнёра/телефона.

## Amap (高德地图, Gaode) — рекомендуется для English

Owned by **Alibaba**.

### Endpoints

| Метод | URL |
|-------|-----|
| Text Search | `GET https://restapi.amap.com/v3/place/text` |
| Around Search (по радиусу) | `GET https://restapi.amap.com/v3/place/around` |
| Geocode | `GET https://restapi.amap.com/v3/geocode/geo` |
| Reverse Geocode | `GET https://restapi.amap.com/v3/geocode/regeo` |
| Routing (driving) | `GET https://restapi.amap.com/v5/direction/driving` |
| District (admin areas) | `GET https://restapi.amap.com/v3/config/district` |

### Авторизация

`?key=$AMAP_API_KEY` в query.

### Пример

```bash
curl "https://restapi.amap.com/v3/place/text?\
keywords=餐厅&\
city=北京&\
key=$AMAP_API_KEY&\
extensions=all&\
output=json"
```

### Структура

```json
{
  "status": "1",
  "info": "OK",
  "count": "10",
  "pois": [{
    "id": "B000A856OP",
    "name": "全聚德烤鸭店",
    "type": "餐饮服务;中餐厅;中餐厅",
    "typecode": "050100",
    "location": "116.4046,39.9098",
    "address": "前门大街32号",
    "tel": "010-12345678",
    "pname": "北京市",
    "cityname": "北京市",
    "biz_ext": {"rating": "4.5", "cost": "200"}
  }]
}
```

### Координаты (важно!)

**GCJ-02** ("Mars Coordinates") — китайский standard, offset от WGS-84.

```python
# WGS-84 → GCJ-02
import math
def wgs84_to_gcj02(lng, lat):
    if not (73.66 < lng < 135.05 and 3.86 < lat < 53.55):
        return lng, lat  # outside China — no transform
    a = 6378245.0
    ee = 0.00669342162296594323
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat
```

`transformlat`/`transformlng` — standard helpers, готовые libs: `eviltransform` (Python pip).

### Pricing

- Personal Free: **5K req/day** для most APIs
- Business verified: **30K-100K/день**
- Beyond: ¥0.005-0.05/req

### Регистрация (требует Chinese phone)

1. https://lbs.amap.com
2. Sign up — **Chinese phone number** обязателен (SMS verification)
3. **Real-name verification** (实名认证) — Chinese national ID или business license
4. Console → Application → Create App → Type "Web服务" → API key выдаётся

## Baidu Maps

Owned by **Baidu**.

### Endpoints

| Метод | URL |
|-------|-----|
| Place Search v2 | `GET https://api.map.baidu.com/place/v2/search` |
| Place Detail | `GET https://api.map.baidu.com/place/v2/detail` |
| Geocoding v3 | `GET https://api.map.baidu.com/geocoding/v3/` |
| Reverse Geocoding | `GET https://api.map.baidu.com/reverse_geocoding/v3/` |
| Direction | `GET https://api.map.baidu.com/direction/v2/driving` |

### Авторизация

`?ak=$BAIDU_API_KEY` (ak = "API Key" по-китайски).

### Координаты

**BD-09** — Baidu's variant of GCJ-02. Дополнительная обфускация поверх GCJ-02.

```python
# GCJ-02 → BD-09
def gcj02_to_bd09(lng, lat):
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * math.pi * 3000.0 / 180.0)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * math.pi * 3000.0 / 180.0)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat

# Полная цепочка WGS-84 → BD-09: wgs84_to_gcj02() → gcj02_to_bd09()
```

### Pricing

- Personal: **30K req/day** (для most APIs)
- Verified Business: **100K-500K/день**

### Регистрация

1. https://lbsyun.baidu.com
2. Chinese phone + ID
3. Console → 应用管理 → 创建应用 → 服务端 → API key

## Когда использовать

✅ **Используй китайские maps:**
- Product targeted на China users
- Маппинг бизнес-точек в 北京/上海/深圳
- Trade analytics involving Chinese cities

❌ **Скип:**
- Не работаешь с китайским рынком
- Только эпизодические запросы по Китаю → можно жить с GCJ-02 offset (Google в Китае «съезжает» на ~100-300m, что терпимо для общего overview)

## Workaround без registration

- **SerpAPI** engine `baidu` — text search (не maps), доступен через наш `SERPAPI_API_KEY`
- **Apify actors**: `amap-poi-scraper`, `baidu-maps-scraper` — pay-per-result
- **Прокси через китайского партнёра** — если планируется long-term работа

## Грабли

1. **GCJ-02 ≠ WGS-84** — Google в Китае off by 100-500m
2. **BD-09 двойной shift** — даже больше расхождения с обычными mappers
3. **Координаты возвращаются как string `"lng,lat"`** в Amap (запятая разделитель!) — парсить
4. **`status: "1"`** = success в Amap (string `"1"`, не int 1)
5. **`info` в Amap** для ошибок: `"NO_PERMISSION"`, `"DAILY_QUERY_OVER_LIMIT"`, `"INVALID_USER_KEY"`
6. **Real-name verification (实名认证)** обязательна с 2018 для всех keys
7. **Без VPN-доступа** — для тестов API из вашего региона работает, но регистрация может требовать verification SMS из Китая
8. **Amap часто быстрее Baidu** для API-only use cases

## Почему мы скипаем auto-register

YourFirstName не имеет китайского телефона + кит. документов. Skill оставляет stubs для providers `amap` и `baidu`:

- Документация для справки
- Если в будущем подключение через китайскую дочку — функции в `places_search.py` готовы

## Документация

- Amap: https://lbs.amap.com/api/webservice/summary
- Baidu: https://lbsyun.baidu.com/index.php?title=webapi
- Coordinate conversion lib: https://github.com/wandergis/coordtransform
- Python eviltransform: `pip install eviltransform`
