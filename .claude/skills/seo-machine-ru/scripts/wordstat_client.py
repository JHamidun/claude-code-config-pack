#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wordstat client — прямые запросы к внутреннему API вместо парсинга DOM.

Официальный Wordstat API (через Директ) требует одобренной заявки на доступ
и отдаёт `error_code: 58 / No access` без неё. Этот клиент ходит в тот же
эндпоинт, что и веб-интерфейс, под сессией пользователя.

Контракт вскрыт реверсом 2026-08-11 (перехват XHR в залогиненном профиле):

    POST https://wordstat.yandex.ru/wordstat/api/getTable
    content-type: application/json
    referer:      https://wordstat.yandex.ru/?region=all&view=table&words=<urlencoded>
    {
      "currentDevice": "desktop,phone,tablet",
      "dbname": "rus",
      "filters": {"region": "all", "tableType": "popular"},
      "searchValue": "<фраза>",
      "startDate": "01.08.2024",
      "endDate": "31.07.2026"
    }

    -> {"table": {"tableData": {"associations": [{"text": "...", "value": "13914"}, ...],
                                "including":    [...] }}}

`associations` — что ещё ищут рядом (расширение семантики),
`including`    — вхождения самой фразы (кластер под страницу).

Авторизация: куки берутся из persistent-профиля Playwright (~/.wordstat/profile),
который пользователь логинит РУКАМИ один раз — Яндекс требует QR/телефон.
Куки кэшируются в ~/.wordstat/cookies.json и переиспользуются, пока живы.

Использование:
    python wordstat_client.py refresh                     # обновить куки из профиля
    python wordstat_client.py freq "курс вайбкодинга"     # частотности одной фразы
    python wordstat_client.py batch seeds.txt --out o.json  # пачкой из файла
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

WS_HOME = Path.home() / ".wordstat"
PROFILE = WS_HOME / "profile"
COOKIE_CACHE = WS_HOME / "cookies.json"
API = "https://wordstat.yandex.ru/wordstat/api/getTable"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


# ---------------------------------------------------------------- cookies ---
def refresh_cookies(headed: bool = False) -> bool:
    """Вытащить свежие куки из залогиненного профиля Playwright."""
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright не установлен", file=sys.stderr)
        return False

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE), headless=not headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://wordstat.yandex.ru/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        url = page.url
        cookies = ctx.cookies()
        ctx.close()

    if "passport" in url or "auth" in url.lower():
        print("NEEDS_LOGIN — профиль разлогинен, войди в браузере", file=sys.stderr)
        return False

    WS_HOME.mkdir(parents=True, exist_ok=True)
    COOKIE_CACHE.write_text(json.dumps(cookies, ensure_ascii=False), encoding="utf-8")
    print(f"куки обновлены: {len(cookies)} шт -> {COOKIE_CACHE}")
    return True


def cookie_header() -> str:
    if not COOKIE_CACHE.exists():
        raise RuntimeError("нет кэша кук — сначала `refresh`")
    cookies = json.loads(COOKIE_CACHE.read_text(encoding="utf-8"))
    keep = [c for c in cookies if "yandex" in (c.get("domain") or "")]
    return "; ".join(f"{c['name']}={c['value']}" for c in keep)


# ------------------------------------------------------------------- api ----
def default_period() -> tuple:
    """Последние 24 месяца — так же, как ставит веб-интерфейс по умолчанию."""
    end = date.today().replace(day=1) - timedelta(days=1)
    start = (end.replace(day=1) - timedelta(days=730)).replace(day=1)
    return start.strftime("%d.%m.%Y"), end.strftime("%d.%m.%Y")


def fetch(phrase: str, region: str = "all", timeout: int = 45) -> dict:
    start, end = default_period()
    payload = {
        "currentDevice": "desktop,phone,tablet",
        "dbname": "rus",
        "filters": {"region": region, "tableType": "popular"},
        "searchValue": phrase,
        "startDate": start,
        "endDate": end,
    }
    ref = ("https://wordstat.yandex.ru/?region=" + region + "&view=table&words="
           + urllib.parse.quote(phrase))
    req = urllib.request.Request(
        API, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": UA,
            "Referer": ref,
            "Origin": "https://wordstat.yandex.ru",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Cookie": cookie_header(),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def parse(raw: dict) -> dict:
    """Достать обе таблицы. value приходит строкой — приводим к int."""
    td = (raw.get("table") or {}).get("tableData") or {}

    def rows(key):
        out = []
        for x in td.get(key) or []:
            try:
                out.append({"phrase": x.get("text", ""), "freq": int(str(x.get("value", "0")).replace(" ", ""))})
            except ValueError:
                continue
        return sorted(out, key=lambda r: -r["freq"])

    # Ключи ответа: `popular` — вхождения самой фразы (ядро под страницу),
    # `associations` — что ищут рядом. Второй список шумный: к «курс вайбкодинга»
    # он подмешивает «урок субботней школы» и «тренинг инвокера», так что для
    # семантики опираться надо на popular, а associations смотреть глазами.
    return {
        "invalid": bool((raw.get("table") or {}).get("isQueryInvalid")),
        "no_data": bool((raw.get("table") or {}).get("noData")),
        "including": rows("popular"),
        "associations": rows("associations"),
    }


# ------------------------------------------------------------------- cli ----
def cmd_freq(args) -> int:
    data = parse(fetch(args.phrase, region=args.region))
    if data["invalid"]:
        print("Wordstat считает запрос невалидным")
        return 1
    print(f"=== «{args.phrase}» ===")
    print(f"-- вхождения ({len(data['including'])}) --")
    for r in data["including"][:args.limit]:
        print(f"  {r['freq']:>8}  {r['phrase']}")
    print(f"-- рядом ищут ({len(data['associations'])}) --")
    for r in data["associations"][:args.limit]:
        print(f"  {r['freq']:>8}  {r['phrase']}")
    return 0


def cmd_batch(args) -> int:
    seeds = [s.strip() for s in Path(args.file).read_text(encoding="utf-8").splitlines()
             if s.strip() and not s.startswith("#")]
    out = {}
    for i, s in enumerate(seeds, 1):
        try:
            out[s] = parse(fetch(s, region=args.region))
            top = out[s]["including"][:1]
            head = f"{top[0]['freq']} ({top[0]['phrase']})" if top else "нет данных"
            print(f"[{i}/{len(seeds)}] {s:44} -> {head}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(seeds)}] {s:44} -> ОШИБКА {type(e).__name__}: {str(e)[:80]}", flush=True)
            out[s] = {"error": str(e)[:200]}
        time.sleep(args.delay)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nсохранено: {args.out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Wordstat через внутренний API")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_r = sub.add_parser("refresh", help="обновить куки из профиля браузера")
    p_r.add_argument("--headed", action="store_true", help="показать окно (для входа)")

    p_f = sub.add_parser("freq", help="частотности одной фразы")
    p_f.add_argument("phrase")
    p_f.add_argument("--region", default="all")
    p_f.add_argument("--limit", type=int, default=15)

    p_b = sub.add_parser("batch", help="пачка фраз из файла")
    p_b.add_argument("file")
    p_b.add_argument("--out", default="wordstat_batch.json")
    p_b.add_argument("--region", default="all")
    p_b.add_argument("--delay", type=float, default=1.5)

    args = ap.parse_args()
    if args.cmd == "refresh":
        return 0 if refresh_cookies(args.headed) else 2
    if args.cmd == "freq":
        return cmd_freq(args)
    if args.cmd == "batch":
        return cmd_batch(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
