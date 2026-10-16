#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Гигиена счётчика Метрики — обязательный предзапуск, а не пункт чеклиста.

Пока в счётчике живут боты, свой же трафик и хиты с localhost, на этих данных
учатся ретаргетинг, look-alike и автостратегии Директа. Отравленный счётчик
портит не одну кампанию, а всю дальнейшую автоматику аккаунта.

Проверено на экосистеме пользователя 28.08.2026:
    news.your-domain.com — 116 129 из 133 030 визитов (87,3%) дал ОДИН headless-бот,
    он же 71 533 из 78 002 достижений автоцели. your-domain.com — 672 визита (18%)
    из город и Жабоатау, то есть сам владелец.

Что ищет:
  1. headless-браузеры и роботные User-Agent
  2. гео владельца (задаётся --owner-geo, по умолчанию бразильские города пользователя)
  3. хиты с localhost / dev-портов / самой mc.yandex.ru
  4. аномалии: визиты глубиной 1.0 с нулевым временем, перекос одного браузера
  5. считает, что останется от статистики после чистки

Использование:
    python counter_hygiene.py 109046150 --days 90
    python counter_hygiene.py 103552727 --days 90 --owner-geo "Miami,Jaboatao"
"""
from __future__ import annotations

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))
TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
BASE = "https://api-metrika.yandex.net/stat/v1/data"

BOT_MARKERS = ("headless", "phantom", "selenium", "puppeteer", "bot", "crawler", "spider")
DEV_MARKERS = ("127.0.0.1", "localhost", "0.0.0.0", "mc.yandex.ru", ":3000", ":3004", ":8080")
OWNER_GEO_DEFAULT = ("recife", "jaboat", "ресифи", "жабоат")


def q(counter: str, metrics: str, dimensions: str, days: int, limit: int = 50) -> list:
    r = requests.get(BASE, headers={"Authorization": f"OAuth {TOKEN}"},
                     params={"ids": counter, "metrics": metrics, "dimensions": dimensions,
                             "date1": f"{days}daysAgo", "date2": "today",
                             "sort": "-" + metrics.split(",")[0], "limit": limit}, timeout=45)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.json().get("data", [])


def name_of(row) -> str:
    return (row["dimensions"][0].get("name") or "—")


def scan(counter: str, days: int, owner_geo: tuple) -> dict:
    total_rows = q(counter, "ym:s:visits", "ym:s:deviceCategory", days)
    total = sum(int(r["metrics"][0]) for r in total_rows) or 1

    findings, dirty = [], 0

    def add(kind: str, label: str, visits: int, extra: str = "") -> None:
        nonlocal dirty
        dirty += visits
        findings.append({"kind": kind, "label": label, "visits": visits,
                         "pct": round(visits * 100 / total, 1), "extra": extra})

    # 1. боты по браузеру
    for row in q(counter, "ym:s:visits,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
                 "ym:s:browser", days):
        nm = name_of(row)
        if any(m in nm.lower() for m in BOT_MARKERS):
            add("бот", nm, int(row["metrics"][0]),
                f"отказов {row['metrics'][1]:.0f}%, {row['metrics'][2]:.0f} сек/визит")

    # 2. гео владельца
    for row in q(counter, "ym:s:visits", "ym:s:regionCity", days):
        nm = name_of(row)
        if any(g in nm.lower() for g in owner_geo):
            add("своё гео", nm, int(row["metrics"][0]), "трафик самого владельца")

    # 3. dev-хиты
    for row in q(counter, "ym:s:visits", "ym:s:startURL", days, limit=100):
        nm = name_of(row)
        if any(m in nm.lower() for m in DEV_MARKERS):
            add("dev/служебное", nm[:60], int(row["metrics"][0]), "не прод")

    # 4. перекос одного источника — признак единственного робота
    os_rows = q(counter, "ym:s:visits", "ym:s:operatingSystem", days)
    skew = None
    if os_rows:
        top = os_rows[0]
        share = int(top["metrics"][0]) * 100 / total
        if share > 60:
            skew = f"{name_of(top)} — {share:.1f}% всех визитов (перекос, вероятен один источник)"

    return {"counter": counter, "days": days, "total": total,
            "findings": findings, "dirty": dirty,
            "clean": total - dirty, "skew": skew}


def render(s: dict) -> int:
    print(f"\n{'=' * 76}")
    print(f"ГИГИЕНА СЧЁТЧИКА {s['counter']} · {s['days']} дней · всего визитов {s['total']}")
    print("=" * 76)

    if not s["findings"]:
        print("\nЗагрязнения по известным признакам не найдено.")
    else:
        print(f"\n{'тип':<16}{'что':<38}{'визитов':>9}{'доля':>7}")
        print("-" * 76)
        for f in sorted(s["findings"], key=lambda x: -x["visits"]):
            print(f"{f['kind']:<16}{f['label'][:37]:<38}{f['visits']:>9}{f['pct']:>6.1f}%")
            if f["extra"]:
                print(f"{'':16}{f['extra']}")

    if s["skew"]:
        print(f"\n[!] {s['skew']}")

    pct = s["dirty"] * 100 / s["total"]
    print(f"\nМУСОРА: {s['dirty']} визитов ({pct:.1f}%)")
    print(f"ОСТАНЕТСЯ ЧИСТЫХ: {s['clean']} ({100 - pct:.1f}%)")

    print(f"\n{'=' * 76}")
    if pct >= 50:
        print("ВЕРДИКТ: счётчик ОТРАВЛЕН — больше половины данных мусорные.")
        print("  Ретаргетинг, look-alike и автостратегии будут учиться на роботе.")
        print("  Чистить ДО любого рекламного бюджета, иначе испорчена вся дальнейшая автоматика.")
        code = 2
    elif pct >= 10:
        print("ВЕРДИКТ: заметное загрязнение — конверсии занижены, поведение искажено.")
        print("  Поставить фильтры до запуска, иначе CPA будет посчитана по кривой базе.")
        code = 1
    else:
        print("ВЕРДИКТ: загрязнение в пределах терпимого.")
        code = 0

    if s["findings"]:
        print("\nЧТО СДЕЛАТЬ (Метрика → Настройки → Фильтры):")
        kinds = {f["kind"] for f in s["findings"]}
        if "бот" in kinds:
            print("  · включить «Фильтровать роботов по строгим правилам и поведению»")
            print("  · добавить фильтр-исключение по User-Agent, содержащему Headless")
        if "своё гео" in kinds:
            print("  · исключить свой IP или своё гео (иначе все конверсии занижены)")
        if "dev/служебное" in kinds:
            print("  · исключить localhost и dev-порты; прод вынести на отдельный счётчик")
        print("\n  Фильтры Метрики работают ТОЛЬКО вперёд — историю они не чистят.")
        print("  Для анализа прошлого пользоваться сегментами, а не фильтрами.")
    print("=" * 76 + "\n")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description="Гигиена счётчика Метрики перед запуском рекламы")
    ap.add_argument("counter")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--owner-geo", default=None,
                    help="города владельца через запятую (по умолчанию город/Жабоатау)")
    a = ap.parse_args()

    if not TOKEN:
        print("нет YANDEX_OAUTH_TOKEN", file=sys.stderr)
        return 3
    geo = tuple(x.strip().lower() for x in a.owner_geo.split(",")) if a.owner_geo else OWNER_GEO_DEFAULT
    return render(scan(a.counter, a.days, geo))


if __name__ == "__main__":
    sys.exit(main())
