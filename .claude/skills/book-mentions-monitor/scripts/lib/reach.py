# -*- coding: utf-8 -*-
"""Охват источников: Tranco-ранг (без ключа) + Cloudflare Radar (Global API Key) + соц-подписчики.
Обкатано 2026-06-03: tranco-list.eu/api/ranks/domain/<d>, CF radar/ranking/domain/<d>."""
import json, urllib.request, ssl, re
from lib.mention import domain

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
_CACHE = {}

def _get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read()

def tranco_rank(d):
    if d in _CACHE: return _CACHE[d]
    try:
        data = json.loads(_get(f"https://tranco-list.eu/api/ranks/domain/{d}"))
        ranks = data.get("ranks", [])
        r = ranks[-1]["rank"] if ranks else None
    except Exception:
        r = None
    _CACHE[d] = r
    return r

def rank_to_reach(rank):
    """Грубый бакет охвата по рангу (когда нет абсолютных визитов)."""
    if not rank: return 0
    if rank <= 1000: return 5_000_000
    if rank <= 10000: return 2_000_000
    if rank <= 100000: return 500_000
    if rank <= 1000000: return 50_000
    return 5_000

def cf_rank(d, creds):
    key = creds.get("CLOUDFLARE_GLOBAL_API_KEY"); email = creds.get("CLOUDFLARE_EMAIL")
    if not (key and email): return None
    try:
        data = json.loads(_get(f"https://api.cloudflare.com/client/v4/radar/ranking/domain/{d}?limit=5",
                               headers={"X-Auth-Email": email, "X-Auth-Key": key}))
        det = (data.get("result") or {}).get("details_0") or {}
        return det.get("rank") or det.get("bucket")
    except Exception:
        return None

def reach_for(m, creds=None):
    """Проставляет _reach. Соцсети — по охватам поста; СМИ — по Tranco/CF рангу домена."""
    creds = creds or {}
    # соцсети/видео/читательское: охват = метрики поста (views), НЕ трафик всего домена
    if m.get("_type") in ("Соцсеть", "Видео", "Читательский", "Магазин"):
        m["_reach"] = m.get("views") or 0
        return m["_reach"]
    # СМИ/агрегатор — ранг домена
    d = domain(m)
    if d:
        rank = tranco_rank(d)
        reach = rank_to_reach(rank)
        if not reach and creds:
            cf = cf_rank(d, creds)  # запасной сигнал
            reach = 500_000 if isinstance(cf, int) and cf <= 50000 else (50_000 if cf else 0)
        m["_reach"] = reach or m.get("_reach", 0)
        m["_rank"] = rank
    return m.get("_reach", 0)

def enrich_reach(mentions, creds=None):
    for m in mentions:
        try: reach_for(m, creds)
        except Exception: m.setdefault("_reach", 0)
    return mentions
