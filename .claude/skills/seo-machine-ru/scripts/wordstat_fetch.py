#!/usr/bin/env python3
"""Headless-съём частот Wordstat через internal API getTable (без Direct API).

Требует cookie залогиненной сессии wordstat.yandex.ru (важны Session_id / yandexuid).
Получить cookie один раз из залогиненного браузера:
    browser_evaluate:  () => document.cookie        # с любой страницы *.yandex.ru
или из DevTools → Application → Cookies → wordstat.yandex.ru.

Если cookie доставать неудобно — используй браузерный путь напрямую:
    scripts/wordstat_browser_snippet.js  (paste в browser_evaluate)
Полный рецепт и грабли: references/wordstat-real-recipe.md

CLI:
    python wordstat_fetch.py phrases.txt --cookie "Session_id=...; yandexuid=..." [--region 225] [--json]
    python wordstat_fetch.py --kw "агрегатор нейросетей" "нейросети для бизнеса" --cookie "..."
phrases.txt — по фразе на строку.
"""
import argparse
import json
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "https://wordstat.yandex.ru/wordstat/api/getTable"


def fetch_one(phrase, cookie, region="225", start="01.06.2024", end="31.05.2026"):
    body = {
        "currentDevice": "desktop,phone,tablet", "dbname": "rus",
        "filters": {"region": str(region), "tableType": "popular"},
        "searchValue": phrase, "startDate": start, "endDate": end,
    }
    headers = {
        "content-type": "application/json",
        "cookie": cookie,
        "referer": "https://wordstat.yandex.ru/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    # Direct API v4 / Wordstat требует UTF-8 body bytes
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    r = requests.post(API, data=data, headers=headers, timeout=30)
    if r.status_code != 200:
        return {"total": None, "status": r.status_code}
    j = r.json()
    td = (j.get("table") or {}).get("tableData") or {}
    top = [{"text": x.get("text"), "value": int(x.get("value", 0))}
           for x in (td.get("popular") or [])[:8]]
    return {"total": j.get("totalValue"), "status": 200, "top": top}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="файл с фразами (по строке)")
    ap.add_argument("--kw", nargs="+", help="фразы прямо в аргументах")
    ap.add_argument("--cookie", required=True, help="cookie залогиненной сессии wordstat.yandex.ru")
    ap.add_argument("--region", default="225")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    phrases = list(args.kw or [])
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            phrases += [ln.strip() for ln in f if ln.strip()]
    if not phrases:
        ap.error("дай фразы: файл или --kw")

    out = {}
    for p in phrases:
        try:
            out[p] = fetch_one(p, args.cookie, args.region)
        except Exception as e:  # noqa: BLE001
            out[p] = {"total": None, "err": str(e)[:60]}
        time.sleep(0.25)

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for p, v in sorted(out.items(), key=lambda kv: -(kv[1].get("total") or 0)):
            print(f"  {str(v.get('total')):>7}  {p}")


if __name__ == "__main__":
    main()
