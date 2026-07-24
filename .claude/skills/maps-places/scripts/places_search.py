#!/usr/bin/env python3
"""
Places search & geocoding — Google + Yandex + 2GIS + SerpAPI.

Providers:
    google   — Google Places (New)
    yandex   — Yandex Geosearch
    2gis     — 2GIS Catalog
    serpapi  — SerpAPI Google Maps (fallback)
    both     — Google + Yandex merge
    all      — Google + Yandex + 2GIS merge

Commands:
    <provider> <query>           — поиск мест
    geocode <address>            — адрес → координаты
    reverse_geocode --lat --lon  — координаты → адрес

Usage:
    python places_search.py google "ресторан" --lat 55.7558 --lon 37.6173
    python places_search.py all "кофейня" --lat 55.7558 --lon 37.6173 --limit 30
    python places_search.py geocode "Москва, Тверская 1"
    python places_search.py reverse_geocode --lat 55.7558 --lon 37.6173
"""
import sys
import json
import argparse
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]


def load_credentials():
    cred_file = Path.home() / ".claude" / ".credentials.master.env"
    if not cred_file.exists():
        return {}
    creds = {}
    for line in cred_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        creds[k.strip()] = v.strip().strip('"').strip("'")
    return creds


CREDS = load_credentials()


def _http_get(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _http_post(url, payload, headers, timeout=15):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _require_key(name):
    key = CREDS.get(name)
    if not key:
        raise RuntimeError(f"{name} not in credentials.master.env")
    return key


# ---------- Google Places (New) ----------

def google_text_search(query, lat=None, lon=None, radius_m=5000, limit=20, lang="ru"):
    key = _require_key("GOOGLE_MAPS_API_KEY")
    payload = {
        "textQuery": query,
        "maxResultCount": min(limit, 20),
        "languageCode": lang,
    }
    if lat is not None and lon is not None:
        payload["locationBias"] = {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": radius_m,
            }
        }

    data = _http_post(
        "https://places.googleapis.com/v1/places:searchText",
        payload,
        headers={
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.rating,places.userRatingCount,places.priceLevel,"
                "places.location,places.regularOpeningHours,places.websiteUri,"
                "places.nationalPhoneNumber,places.primaryType,places.types,"
                "places.googleMapsUri"
            ),
        },
    )

    results = []
    for p in data.get("places", []):
        results.append({
            "source": "google",
            "id": p.get("id"),
            "name": (p.get("displayName") or {}).get("text"),
            "address": p.get("formattedAddress"),
            "rating": p.get("rating"),
            "reviews": p.get("userRatingCount"),
            "price_level": p.get("priceLevel"),
            "phone": p.get("nationalPhoneNumber"),
            "website": p.get("websiteUri"),
            "type": p.get("primaryType"),
            "categories": p.get("types", []),
            "lat": (p.get("location") or {}).get("latitude"),
            "lon": (p.get("location") or {}).get("longitude"),
            "maps_url": p.get("googleMapsUri"),
            "hours": (p.get("regularOpeningHours") or {}).get("weekdayDescriptions"),
        })
    return results


# ---------- Yandex Geosearch ----------

def yandex_geosearch(query, lat=None, lon=None, span=(0.3, 0.3), limit=20, lang="ru_RU"):
    key = _require_key("YANDEX_GEOSEARCH_API_KEY")

    params = {
        "apikey": key,
        "text": query,
        "type": "biz",
        "results": min(limit, 500),
        "lang": lang,
        "format": "json",
    }
    if lat is not None and lon is not None:
        params["ll"] = f"{lon},{lat}"
        params["spn"] = f"{span[0]},{span[1]}"
        params["rspn"] = 1

    url = "https://search-maps.yandex.ru/v1/?" + urllib.parse.urlencode(params)
    data = _http_get(url)

    results = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        cmd = p.get("CompanyMetaData", {})
        coords = (f.get("geometry") or {}).get("coordinates", [None, None])
        phones = [ph.get("formatted") for ph in cmd.get("Phones", [])]
        hours = cmd.get("Hours", {})
        results.append({
            "source": "yandex",
            "id": cmd.get("id"),
            "name": p.get("name"),
            "address": cmd.get("address") or p.get("description"),
            "categories": [c.get("name") for c in cmd.get("Categories", [])],
            "phones": phones,
            "website": cmd.get("url"),
            "hours_text": hours.get("text"),
            "is_open_now": (hours.get("State") or {}).get("isOpenNow"),
            "features": {
                ft.get("id"): ft.get("value")
                for ft in cmd.get("Features", [])
                if "id" in ft
            },
            "lat": coords[1],
            "lon": coords[0],
        })
    return results


# ---------- 2GIS Catalog ----------

def dgis_search(query, lat=None, lon=None, radius_m=5000, limit=20, lang="ru_RU"):
    key = _require_key("DGIS_API_KEY")

    params = {
        "q": query,
        "page_size": min(limit, 50),
        "fields": (
            "items.point,items.address,items.contact_groups,items.schedule,"
            "items.rubrics,items.reviews,items.flags,items.adm_div"
        ),
        "locale": lang,
        "key": key,
    }
    if lat is not None and lon is not None:
        params["location"] = f"{lon},{lat}"
        if radius_m:
            params["radius"] = radius_m

    url = "https://catalog.api.2gis.com/3.0/items?" + urllib.parse.urlencode(params)
    try:
        data = _http_get(url)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"2GIS HTTP {e.code}: {body}")

    if data.get("meta", {}).get("code") not in (None, 200):
        raise RuntimeError(f"2GIS error: {data.get('meta', {}).get('error')}")

    results = []
    for it in (data.get("result") or {}).get("items", []):
        contacts = []
        phones = []
        website = None
        for cg in it.get("contact_groups", []) or []:
            for c in cg.get("contacts", []) or []:
                if c.get("type") == "phone":
                    phones.append(c.get("text") or c.get("value"))
                elif c.get("type") == "website":
                    website = c.get("url") or c.get("value")
                contacts.append(c)
        sched = it.get("schedule", {})
        results.append({
            "source": "2gis",
            "id": it.get("id"),
            "name": it.get("name"),
            "address": it.get("address_name") or (it.get("address") or {}).get("name"),
            "categories": [r.get("name") for r in it.get("rubrics", []) or []],
            "phones": phones,
            "website": website,
            "rating": (it.get("reviews") or {}).get("general_rating"),
            "reviews": (it.get("reviews") or {}).get("general_review_count"),
            "hours_24x7": sched.get("is_24x7"),
            "working_status": sched.get("working_status"),
            "flags": it.get("flags") or {},
            "lat": (it.get("point") or {}).get("lat"),
            "lon": (it.get("point") or {}).get("lon"),
        })
    return results


# ---------- SerpAPI Google Maps ----------

def serpapi_maps(query, lat=None, lon=None, zoom=14, limit=20, hl="ru", gl="ru"):
    key = _require_key("SERPAPI_API_KEY")

    params = {
        "engine": "google_maps",
        "q": query,
        "hl": hl,
        "gl": gl,
        "api_key": key,
    }
    if lat is not None and lon is not None:
        params["ll"] = f"@{lat},{lon},{zoom}z"

    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    data = _http_get(url, timeout=30)

    if data.get("error"):
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    results = []
    for p in (data.get("local_results") or [])[:limit]:
        gps = p.get("gps_coordinates") or {}
        results.append({
            "source": "serpapi",
            "id": p.get("place_id") or p.get("data_id"),
            "name": p.get("title"),
            "address": p.get("address"),
            "rating": p.get("rating"),
            "reviews": p.get("reviews"),
            "price_level": p.get("price"),
            "phone": p.get("phone"),
            "website": p.get("website"),
            "type": p.get("type"),
            "hours_text": p.get("hours") or p.get("open_state"),
            "thumbnail": p.get("thumbnail"),
            "lat": gps.get("latitude"),
            "lon": gps.get("longitude"),
        })
    return results


# ---------- Nominatim (OpenStreetMap) ----------

def _user_agent():
    return "maps-places-skill/1.0 (your-email@gmail.com)"


def nominatim_search(query, lat=None, lon=None, limit=20, lang="ru,en"):
    """Forward geocoding via OSM Nominatim. No key required."""
    params = {
        "q": query,
        "format": "json",
        "limit": min(limit, 50),
        "addressdetails": 1,
        "extratags": 1,
        "accept-language": lang,
    }
    if lat is not None and lon is not None:
        delta = 0.5
        params["viewbox"] = f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}"
        params["bounded"] = 1

    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    results = []
    for it in data:
        addr = it.get("address", {})
        results.append({
            "source": "nominatim",
            "id": f"{it.get('osm_type')}-{it.get('osm_id')}",
            "name": it.get("display_name", "").split(",")[0],
            "address": it.get("display_name"),
            "lat": float(it.get("lat", 0)),
            "lon": float(it.get("lon", 0)),
            "type": it.get("type"),
            "categories": [it.get("class"), it.get("type")] if it.get("class") else [],
            "country": addr.get("country"),
            "city": addr.get("city") or addr.get("town") or addr.get("village"),
        })
    return results


# ---------- Overpass (OSM raw queries) ----------

# Map amenity-text -> overpass amenity values
_OVERPASS_AMENITY_MAP = {
    "restaurant": "restaurant",
    "ресторан": "restaurant",
    "cafe": "cafe",
    "кафе": "cafe",
    "bar": "bar",
    "бар": "bar",
    "pub": "pub",
    "fast food": "fast_food",
    "fast_food": "fast_food",
    "pharmacy": "pharmacy",
    "аптека": "pharmacy",
    "fuel": "fuel",
    "АЗС": "fuel",
    "заправка": "fuel",
    "atm": "atm",
    "банкомат": "atm",
    "bank": "bank",
    "банк": "bank",
    "charging": "charging_station",
    "зарядка": "charging_station",
}


def overpass_search(query, lat=None, lon=None, radius_m=5000, limit=50, lang="ru"):
    """Overpass raw POI search by amenity. Best for bulk extraction."""
    amenity = None
    qlow = query.lower()
    for k, v in _OVERPASS_AMENITY_MAP.items():
        if k in qlow:
            amenity = v
            break
    if not amenity:
        amenity = "restaurant"  # default

    if lat is None or lon is None:
        raise RuntimeError("Overpass requires --lat and --lon")

    # bbox from radius
    delta_lat = radius_m / 111000
    delta_lon = radius_m / (111000 * max(0.1, abs(__import__("math").cos(__import__("math").radians(lat)))))
    south, west = lat - delta_lat, lon - delta_lon
    north, east = lat + delta_lat, lon + delta_lon

    q = f"""[out:json][timeout:25];
(
  node["amenity"="{amenity}"]({south},{west},{north},{east});
  way["amenity"="{amenity}"]({south},{west},{north},{east});
  relation["amenity"="{amenity}"]({south},{west},{north},{east});
);
out center tags {limit};
"""
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=q.encode("utf-8"),
        headers={"User-Agent": _user_agent()},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    results = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        coords = (el.get("lat"), el.get("lon")) if el.get("lat") else (el.get("center", {}).get("lat"), el.get("center", {}).get("lon"))
        results.append({
            "source": "overpass",
            "id": f"{el.get('type')}-{el.get('id')}",
            "name": tags.get(f"name:{lang}") or tags.get("name"),
            "address": ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber")])),
            "categories": [tags.get("amenity"), tags.get("cuisine")] if tags.get("amenity") else [],
            "phones": [tags.get("phone")] if tags.get("phone") else [],
            "website": tags.get("website") or tags.get("contact:website"),
            "hours_text": tags.get("opening_hours"),
            "features": {
                "wheelchair": tags.get("wheelchair"),
                "wifi": tags.get("internet_access"),
                "outdoor_seating": tags.get("outdoor_seating"),
                "takeaway": tags.get("takeaway"),
                "delivery": tags.get("delivery"),
            },
            "lat": coords[0],
            "lon": coords[1],
        })
    return results[:limit]


# ---------- HERE Maps Discover ----------

def here_discover(query, lat=None, lon=None, radius_m=5000, limit=20, lang="ru"):
    key = _require_key("HERE_API_KEY")
    if lat is None or lon is None:
        raise RuntimeError("HERE requires --lat and --lon")
    params = {
        "q": query,
        "limit": min(limit, 100),
        "lang": lang,
        "apiKey": key,
    }
    # Use either at OR in:circle, not both. Circle implies at.
    if radius_m:
        params["in"] = f"circle:{lat},{lon};r={radius_m}"
    else:
        params["at"] = f"{lat},{lon}"

    url = "https://discover.search.hereapi.com/v1/discover?" + urllib.parse.urlencode(params)
    data = _http_get(url)

    results = []
    for it in data.get("items", []):
        contacts = (it.get("contacts") or [{}])[0]
        addr = it.get("address", {})
        pos = it.get("position", {})
        cats = [c.get("name") for c in it.get("categories", [])]
        phones = [p.get("value") for p in contacts.get("phone", [])]
        webs = [w.get("value") for w in contacts.get("www", [])]
        oh = it.get("openingHours", [{}])
        hours_text = (oh[0].get("text") if oh else None)
        results.append({
            "source": "here",
            "id": it.get("id"),
            "name": it.get("title"),
            "address": addr.get("label"),
            "categories": cats,
            "phones": phones,
            "website": webs[0] if webs else None,
            "hours_text": "; ".join(hours_text) if isinstance(hours_text, list) else hours_text,
            "distance": it.get("distance"),
            "lat": pos.get("lat"),
            "lon": pos.get("lng"),
        })
    return results


# ---------- Mapbox Search Box ----------

def mapbox_search(query, lat=None, lon=None, radius_m=5000, limit=10, lang="ru"):
    token = _require_key("MAPBOX_TOKEN")
    params = {
        "q": query,
        "language": lang,
        "limit": min(limit, 10),
        "types": "poi,address,place",
        "access_token": token,
    }
    if lat is not None and lon is not None:
        params["proximity"] = f"{lon},{lat}"

    url = "https://api.mapbox.com/search/searchbox/v1/forward?" + urllib.parse.urlencode(params)
    data = _http_get(url)

    results = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        coords = p.get("coordinates") or {}
        meta = p.get("metadata") or {}
        cats = p.get("poi_category") or []
        results.append({
            "source": "mapbox",
            "id": p.get("mapbox_id"),
            "name": p.get("name"),
            "address": p.get("full_address"),
            "categories": cats,
            "type": p.get("feature_type"),
            "phone": meta.get("phone"),
            "website": meta.get("website"),
            "lat": coords.get("latitude"),
            "lon": coords.get("longitude"),
        })
    return results


# ---------- Foursquare Places ----------

def foursquare_search(query, lat=None, lon=None, radius_m=5000, limit=20, lang="ru"):
    key = _require_key("FOURSQUARE_API_KEY")
    params = {
        "query": query,
        "limit": min(limit, 50),
    }
    if lat is not None and lon is not None:
        params["ll"] = f"{lat},{lon}"
        if radius_m:
            params["radius"] = min(radius_m, 100000)

    url = "https://places-api.foursquare.com/places/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "X-Places-Api-Version": "2025-06-17",
        "Accept-Language": lang,
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    results = []
    for p in data.get("results", []):
        results.append({
            "source": "foursquare",
            "id": p.get("fsq_place_id"),
            "name": p.get("name"),
            "address": (p.get("location") or {}).get("formatted_address") or (p.get("location") or {}).get("address"),
            "categories": [c.get("name") for c in p.get("categories", [])],
            "rating": p.get("rating"),
            "price_level": p.get("price"),
            "phone": p.get("tel"),
            "website": p.get("website"),
            "hours_text": (p.get("hours") or {}).get("display"),
            "distance": p.get("distance"),
            "lat": p.get("latitude"),
            "lon": p.get("longitude"),
        })
    return results


# ---------- OpenCage Geocoding ----------

def opencage_search(query, lat=None, lon=None, radius_m=None, limit=10, lang="ru"):
    """OpenCage is geocoder only — not POI search. Returns addresses with rich annotations."""
    key = _require_key("OPENCAGE_API_KEY")
    params = {
        "q": query,
        "key": key,
        "language": lang,
        "limit": min(limit, 100),
        "no_annotations": 0,
    }
    if lat is not None and lon is not None:
        params["proximity"] = f"{lat},{lon}"

    url = "https://api.opencagedata.com/geocode/v1/json?" + urllib.parse.urlencode(params)
    data = _http_get(url)

    results = []
    for r in data.get("results", []):
        comp = r.get("components", {})
        geom = r.get("geometry", {})
        ann = r.get("annotations", {})
        results.append({
            "source": "opencage",
            "id": str(r.get("bounds", {})),
            "name": (comp.get("road") or comp.get("city") or comp.get("village") or r.get("formatted", "").split(",")[0]),
            "address": r.get("formatted"),
            "confidence": r.get("confidence"),
            "type": comp.get("_type"),
            "country": comp.get("country"),
            "timezone": (ann.get("timezone") or {}).get("name"),
            "currency": (ann.get("currency") or {}).get("iso_code"),
            "lat": geom.get("lat"),
            "lon": geom.get("lng"),
        })
    return results


# ---------- Open Charge Map (EV stations) ----------

def ocm_search(query, lat=None, lon=None, radius_m=20000, limit=50, lang="ru"):
    """Open Charge Map — EV charging stations. query is ignored, lat+lon required."""
    key = _require_key("OPENCHARGEMAP_API_KEY")
    if lat is None or lon is None:
        raise RuntimeError("Open Charge Map requires --lat and --lon")

    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lon,
        "distance": radius_m / 1000,
        "distanceunit": "KM",
        "maxresults": min(limit, 500),
        "compact": "true",
        "key": key,
    }

    url = "https://api.openchargemap.io/v3/poi?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())

    results = []
    for s in data if isinstance(data, list) else []:
        ai = s.get("AddressInfo") or {}
        op = s.get("OperatorInfo") or {}
        conns = s.get("Connections", []) or []
        max_kw = max((c.get("PowerKW") or 0 for c in conns), default=0)
        conn_types = list(set((c.get("ConnectionType") or {}).get("Title") for c in conns if c.get("ConnectionType")))
        results.append({
            "source": "ocm",
            "id": s.get("UUID"),
            "name": ai.get("Title"),
            "address": ", ".join(filter(None, [ai.get("AddressLine1"), ai.get("Town"), ai.get("StateOrProvince")])),
            "operator": op.get("Title") if op else None,
            "categories": conn_types,
            "phone": ai.get("ContactTelephone1"),
            "website": ai.get("RelatedURL"),
            "max_kw": max_kw,
            "num_points": s.get("NumberOfPoints"),
            "usage_cost": s.get("UsageCost"),
            "lat": ai.get("Latitude"),
            "lon": ai.get("Longitude"),
        })
    return results


# ---------- Airbnb via Apify ----------

def airbnb_search(query, lat=None, lon=None, limit=20, lang="ru", check_in=None, check_out=None, guests=2):
    """Airbnb listings via Apify actor. Pay-per-result ~$5/1000."""
    key = _require_key("APIFY_API_KEY")
    # Use voyager/airbnb-scraper actor
    actor = "voyager~airbnb-scraper"
    payload = {
        "locationQuery": query,
        "maxListings": min(limit, 100),
        "currency": "USD",
    }
    if check_in:
        payload["checkIn"] = check_in
    if check_out:
        payload["checkOut"] = check_out
    if guests:
        payload["adults"] = guests

    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={key}"
    data = _http_post(url, payload, headers={}, timeout=120)

    results = []
    for it in (data if isinstance(data, list) else []):
        results.append({
            "source": "airbnb",
            "id": it.get("id") or it.get("listingId"),
            "name": it.get("name") or it.get("title"),
            "address": it.get("address") or it.get("location"),
            "rating": it.get("rating") or (it.get("reviews") or {}).get("avgRating"),
            "reviews": it.get("reviewsCount") or (it.get("reviews") or {}).get("count"),
            "price_level": it.get("price"),
            "thumbnail": (it.get("images") or [None])[0] if it.get("images") else None,
            "website": it.get("url"),
            "lat": (it.get("coordinates") or {}).get("latitude") or it.get("lat"),
            "lon": (it.get("coordinates") or {}).get("longitude") or it.get("lng"),
        })
    return results


# ---------- Geocoding ----------

def geocode(address, lang="ru"):
    """Forward geocoding: address → coordinates. Order: 2GIS → Yandex → Google."""
    out = {}
    # Try 2GIS first for RU/CIS
    try:
        params = {"q": address, "fields": "items.point,items.adm_div,items.full_name", "locale": "ru_RU", "key": _require_key("DGIS_API_KEY")}
        d = _http_get("https://catalog.api.2gis.com/3.0/items/geocode?" + urllib.parse.urlencode(params))
        items = (d.get("result") or {}).get("items", [])
        if items:
            it = items[0]
            out["2gis"] = {"lat": (it.get("point") or {}).get("lat"), "lon": (it.get("point") or {}).get("lon"), "address": it.get("full_name") or it.get("name")}
    except Exception as e:
        out["2gis"] = {"error": str(e)[:200]}

    # Yandex
    try:
        params = {"apikey": _require_key("YANDEX_GEOSEARCH_API_KEY"), "geocode": address, "format": "json", "lang": "ru_RU", "results": 1}
        d = _http_get("https://geocode-maps.yandex.ru/1.x/?" + urllib.parse.urlencode(params))
        fm = (d.get("response") or {}).get("GeoObjectCollection", {}).get("featureMember", [])
        if fm:
            go = fm[0]["GeoObject"]
            pos = go["Point"]["pos"].split()  # "lon lat"
            addr = ((go.get("metaDataProperty") or {}).get("GeocoderMetaData") or {}).get("Address", {})
            out["yandex"] = {"lon": float(pos[0]), "lat": float(pos[1]), "address": addr.get("formatted") or go.get("description")}
    except Exception as e:
        out["yandex"] = {"error": str(e)[:200]}

    # Google
    try:
        params = {"address": address, "language": lang, "key": _require_key("GOOGLE_MAPS_API_KEY")}
        d = _http_get("https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(params))
        if d.get("results"):
            r = d["results"][0]
            loc = r["geometry"]["location"]
            out["google"] = {"lat": loc["lat"], "lon": loc["lng"], "address": r["formatted_address"]}
    except Exception as e:
        out["google"] = {"error": str(e)[:200]}

    # HERE
    try:
        params = {"q": address, "lang": lang, "apiKey": _require_key("HERE_API_KEY")}
        d = _http_get("https://geocode.search.hereapi.com/v1/geocode?" + urllib.parse.urlencode(params))
        items = d.get("items") or []
        if items:
            it = items[0]
            pos = it.get("position", {})
            out["here"] = {"lat": pos.get("lat"), "lon": pos.get("lng"), "address": it.get("address", {}).get("label")}
    except Exception as e:
        out["here"] = {"error": str(e)[:200]}

    # Mapbox
    try:
        params = {"q": address, "language": lang, "limit": 1, "access_token": _require_key("MAPBOX_TOKEN")}
        d = _http_get("https://api.mapbox.com/search/geocode/v6/forward?" + urllib.parse.urlencode(params))
        fs = d.get("features") or []
        if fs:
            p = fs[0].get("properties", {})
            c = p.get("coordinates") or {}
            out["mapbox"] = {"lat": c.get("latitude"), "lon": c.get("longitude"), "address": p.get("full_address")}
    except Exception as e:
        out["mapbox"] = {"error": str(e)[:200]}

    # OpenCage
    try:
        params = {"q": address, "key": _require_key("OPENCAGE_API_KEY"), "language": lang, "limit": 1, "no_annotations": 1}
        d = _http_get("https://api.opencagedata.com/geocode/v1/json?" + urllib.parse.urlencode(params))
        rs = d.get("results") or []
        if rs:
            r = rs[0]
            g = r.get("geometry", {})
            out["opencage"] = {"lat": g.get("lat"), "lon": g.get("lng"), "address": r.get("formatted"), "confidence": r.get("confidence")}
    except Exception as e:
        out["opencage"] = {"error": str(e)[:200]}

    # Nominatim (free fallback)
    try:
        nm = nominatim_search(address, limit=1, lang=lang)
        if nm:
            out["nominatim"] = {"lat": nm[0]["lat"], "lon": nm[0]["lon"], "address": nm[0]["address"]}
    except Exception as e:
        out["nominatim"] = {"error": str(e)[:200]}

    return out


def reverse_geocode(lat, lon, lang="ru"):
    """Reverse: coordinates → address."""
    out = {}
    # 2GIS
    try:
        params = {"lat": lat, "lon": lon, "fields": "items.point,items.address,items.adm_div,items.full_name", "locale": "ru_RU", "key": _require_key("DGIS_API_KEY")}
        d = _http_get("https://catalog.api.2gis.com/3.0/items/geocode?" + urllib.parse.urlencode(params))
        items = (d.get("result") or {}).get("items", [])
        if items:
            it = items[0]
            out["2gis"] = {"address": it.get("full_name") or it.get("name"), "lat": (it.get("point") or {}).get("lat"), "lon": (it.get("point") or {}).get("lon")}
    except Exception as e:
        out["2gis"] = {"error": str(e)[:200]}

    # Yandex
    try:
        params = {"apikey": _require_key("YANDEX_GEOSEARCH_API_KEY"), "geocode": f"{lon},{lat}", "sco": "longlat", "format": "json", "lang": "ru_RU", "results": 1}
        d = _http_get("https://geocode-maps.yandex.ru/1.x/?" + urllib.parse.urlencode(params))
        fm = (d.get("response") or {}).get("GeoObjectCollection", {}).get("featureMember", [])
        if fm:
            go = fm[0]["GeoObject"]
            addr = ((go.get("metaDataProperty") or {}).get("GeocoderMetaData") or {}).get("Address", {})
            out["yandex"] = {"address": addr.get("formatted") or go.get("description")}
    except Exception as e:
        out["yandex"] = {"error": str(e)[:200]}

    # Google
    try:
        params = {"latlng": f"{lat},{lon}", "language": lang, "key": _require_key("GOOGLE_MAPS_API_KEY")}
        d = _http_get("https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(params))
        if d.get("results"):
            out["google"] = {"address": d["results"][0]["formatted_address"]}
    except Exception as e:
        out["google"] = {"error": str(e)[:200]}

    # HERE
    try:
        params = {"at": f"{lat},{lon}", "lang": lang, "apiKey": _require_key("HERE_API_KEY")}
        d = _http_get("https://revgeocode.search.hereapi.com/v1/revgeocode?" + urllib.parse.urlencode(params))
        items = d.get("items") or []
        if items:
            out["here"] = {"address": items[0].get("address", {}).get("label")}
    except Exception as e:
        out["here"] = {"error": str(e)[:200]}

    # Mapbox
    try:
        params = {"longitude": lon, "latitude": lat, "language": lang, "access_token": _require_key("MAPBOX_TOKEN")}
        d = _http_get("https://api.mapbox.com/search/geocode/v6/reverse?" + urllib.parse.urlencode(params))
        fs = d.get("features") or []
        if fs:
            out["mapbox"] = {"address": fs[0].get("properties", {}).get("full_address")}
    except Exception as e:
        out["mapbox"] = {"error": str(e)[:200]}

    # OpenCage
    try:
        params = {"q": f"{lat},{lon}", "key": _require_key("OPENCAGE_API_KEY"), "language": lang, "limit": 1, "no_annotations": 1}
        d = _http_get("https://api.opencagedata.com/geocode/v1/json?" + urllib.parse.urlencode(params))
        rs = d.get("results") or []
        if rs:
            out["opencage"] = {"address": rs[0].get("formatted")}
    except Exception as e:
        out["opencage"] = {"error": str(e)[:200]}

    # Nominatim
    try:
        params = {"lat": lat, "lon": lon, "format": "json", "accept-language": lang, "addressdetails": 1}
        req = urllib.request.Request("https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode(params), headers={"User-Agent": _user_agent()})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        if d:
            out["nominatim"] = {"address": d.get("display_name")}
    except Exception as e:
        out["nominatim"] = {"error": str(e)[:200]}

    return out


# ---------- Merge ----------

def merge(results_list, tolerance=0.0005):
    """Merge by proximity. results_list: list of provider result lists, in priority order."""
    if not results_list:
        return []
    base = list(results_list[0])  # mutable copy

    def near(a, b):
        if None in (a.get("lat"), a.get("lon"), b.get("lat"), b.get("lon")):
            return False
        return abs(a["lat"] - b["lat"]) < tolerance and abs(a["lon"] - b["lon"]) < tolerance

    for next_list in results_list[1:]:
        for nx in next_list:
            matched = False
            for b in base:
                if near(b, nx):
                    # Merge fields: prefer existing non-null
                    for k, v in nx.items():
                        if v in (None, "", [], {}):
                            continue
                        if b.get(k) in (None, "", [], {}):
                            b[k] = v
                    # Track all sources
                    srcs = b.get("sources") or [b.get("source")]
                    if nx.get("source") not in srcs:
                        srcs.append(nx.get("source"))
                    b["sources"] = srcs
                    matched = True
                    break
            if not matched:
                base.append(nx)
    return base


# ---------- Output ----------

def print_results(items):
    for i, p in enumerate(items, 1):
        name = p.get("name", "?")
        rating = p.get("rating")
        reviews = p.get("reviews")
        srcs = p.get("sources") or [p.get("source")]
        srcs_str = "/".join(s for s in srcs if s)
        rating_str = f"  star {rating} ({reviews})" if rating else ""
        print(f"{i:2}. [{srcs_str}] {name}{rating_str}")
        if p.get("address"):
            print(f"    {p['address']}")
        cats = p.get("categories", [])
        if cats:
            print(f"    [{', '.join(cats[:4])}]")
        phones = p.get("phones") or ([p["phone"]] if p.get("phone") else [])
        if phones:
            print(f"    tel: {', '.join(phones)}")
        if p.get("hours_text"):
            print(f"    hrs: {p['hours_text']}")
        elif p.get("hours_24x7"):
            print("    hrs: 24/7")
        elif p.get("working_status"):
            print(f"    hrs: {p['working_status']}")
        if p.get("website"):
            print(f"    web: {p['website']}")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command")  # google / yandex / 2gis / serpapi / both / all / geocode / reverse_geocode
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--radius", type=int, default=5000, help="meters")
    ap.add_argument("--span", type=float, default=0.3, help="degrees, Yandex bbox")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--lang", default="ru")
    ap.add_argument("--check-in", default=None, help="YYYY-MM-DD (airbnb)")
    ap.add_argument("--check-out", default=None, help="YYYY-MM-DD (airbnb)")
    ap.add_argument("--guests", type=int, default=2, help="airbnb")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cmd = args.command

    if cmd == "geocode":
        if not args.query:
            ap.error("geocode requires an address")
        out = geocode(args.query, lang=args.lang)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    if cmd == "reverse_geocode":
        if args.lat is None or args.lon is None:
            ap.error("reverse_geocode requires --lat and --lon")
        out = reverse_geocode(args.lat, args.lon, lang=args.lang)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    valid = ("google", "yandex", "2gis", "serpapi", "nominatim", "overpass",
             "mapbox", "here", "foursquare", "opencage", "ocm", "airbnb",
             "both", "all", "all+")
    if cmd not in valid:
        ap.error(f"unknown command: {cmd}. Valid: {', '.join(valid)}")
    if not args.query and cmd != "ocm":
        ap.error(f"{cmd} requires a query")

    providers = {
        "google": lambda: google_text_search(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "yandex": lambda: yandex_geosearch(args.query, args.lat, args.lon, (args.span, args.span), args.limit, lang="ru_RU"),
        "2gis":   lambda: dgis_search(args.query, args.lat, args.lon, args.radius, args.limit, lang="ru_RU"),
        "serpapi": lambda: serpapi_maps(args.query, args.lat, args.lon, 14, args.limit, hl=args.lang, gl="ru" if args.lang == "ru" else "us"),
        "nominatim": lambda: nominatim_search(args.query, args.lat, args.lon, args.limit, lang=args.lang + ",en"),
        "overpass": lambda: overpass_search(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "mapbox": lambda: mapbox_search(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "here":   lambda: here_discover(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "foursquare": lambda: foursquare_search(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "opencage": lambda: opencage_search(args.query, args.lat, args.lon, args.radius, args.limit, lang=args.lang),
        "ocm":    lambda: ocm_search(args.query or "ev", args.lat, args.lon, args.radius or 20000, args.limit, lang=args.lang),
        "airbnb": lambda: airbnb_search(args.query, args.lat, args.lon, args.limit, lang=args.lang,
                                         check_in=args.check_in, check_out=args.check_out, guests=args.guests),
    }

    if cmd in providers:
        try:
            results = providers[cmd]()
        except Exception as e:
            print(f"{cmd} error: {e}", file=sys.stderr)
            sys.exit(1)
    else:  # both / all / all+
        if cmd == "both":
            names = ["yandex", "google"]
        elif cmd == "all":
            names = ["yandex", "2gis", "google"]
        else:  # all+
            names = ["yandex", "2gis", "google", "here", "foursquare", "mapbox"]
        lists = []
        for n in names:
            try:
                lists.append(providers[n]())
            except Exception as e:
                print(f"{n} error: {e}", file=sys.stderr)
        results = merge(lists)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
