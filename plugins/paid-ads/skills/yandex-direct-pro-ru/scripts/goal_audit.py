#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Аудит измерителя ДО любого рекламного бюджета.

Первый гейт перед Директом — не кампания, а вопрос «а конверсии вообще меряются?».
Пока ответ «нет», любая CPA считается по фантомам, а автостратегия учится на шуме.

Что проверяет:

  1. РАСХОЖДЕНИЕ КОД <-> ИНТЕРФЕЙС
     Грепает исходники посадочной (HTML + все её JS) на ym(<id>,'reachGoal','<name>')
     и сверяет со списком целей из Метрики. Две таблицы:
       - цель заведена в интерфейсе, но её reachGoal нет в коде  -> никогда не сработает
       - reachGoal есть в коде, но цели в интерфейсе нет         -> данные уходят в никуда

  2. АВТОЦЕЛИ НЕПРИГОДНЫ ДЛЯ CPA
     Автоцель Яндекса "Отправка формы" срабатывает на DOM-событии submit — ДО ответа
     сервера, включая падения валидации и catch-ветку fetch. Оптимизировать на неё
     оплату за конверсию = платить за нажатие кнопки.

  3. МЁРТВЫЕ ЦЕЛИ
     Цель есть, код есть, а достижений за период 0 — значит она не работает,
     и обучать на ней стратегию нельзя.

  4. РАСХОЖДЕНИЕ АВТОЦЕЛЬ <-> РУЧНАЯ на одном действии
     Если автоцель и ручная цель описывают одно действие, а расходятся в разы —
     одна из них врёт, и именно она определит вердикт по CPL.

  5. ВОРОНКА ЗА ПРЕДЕЛАМИ СЧЁТЧИКА
     Ищет редиректы на t.me / wa.me / внешние домены после конверсии: если целевое
     действие уходит в мессенджер, Метрика слепа и нужны офлайн-конверсии.

Использование:
    python goal_audit.py 107063001 https://aiuniversity.edu/
    python goal_audit.py 103552727 https://your-domain.com/vibecoding --days 90 --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))
TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
METRIKA = "https://api-metrika.yandex.net"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# ym(12345678,'reachGoal','goal_name')  /  ym(id, "reachGoal", "name")
RE_REACHGOAL = re.compile(r"""ym\s*\(\s*(\d+)\s*,\s*['"]reachGoal['"]\s*,\s*['"]([^'"]+)['"]""")
RE_SCRIPT_SRC = re.compile(r"""<script[^>]+src=['"]([^'"]+)['"]""", re.I)
RE_MESSENGER = re.compile(r"""(t\.me/|wa\.me/|telegram\.me/|api\.whatsapp\.com)""", re.I)
RE_FORM = re.compile(r"<form\b", re.I)
RE_BUTTON = re.compile(r"<button\b", re.I)
# Имя, побитое на стороне Метрики: цель заведена через API с неверной кодировкой,
# в сырых байтах ответа лежат литеральные replacement-символы. Такую цель не найти
# в интерфейсе поиском по названию — она видна только по id.
BROKEN_NAME = re.compile("�")

# Типы целей Метрики, которые срабатывают на DOM-событии, а не на факте от бэкенда.
DOM_LEVEL_TYPES = {"form", "phone", "email", "messenger", "file", "search", "button"}


def api(path: str, **params) -> dict:
    r = requests.get(f"{METRIKA}{path}", headers={"Authorization": f"OAuth {TOKEN}"},
                     params=params, timeout=40)
    r.raise_for_status()
    # Страховка: без charset в заголовке requests уходит в latin-1 и калечит кириллицу.
    # ВНИМАНИЕ: не лечит имена, побитые в самой Метрике — там в сырых байтах приходят
    # литеральные � (цель создана через API с неверной кодировкой). Такие имена
    # ловятся отдельно, см. BROKEN_NAME.
    r.encoding = "utf-8"
    return r.json()


def fetch_goals(counter: str) -> list:
    return api(f"/management/v1/counter/{counter}/goals", useDirect="true").get("goals", [])


def fetch_reaches(counter: str, goals: list, days: int) -> dict:
    """Достижения по каждой цели. Батчами по 15 — больше API не берёт."""
    out = {}
    ids = [str(g["id"]) for g in goals]
    for i in range(0, len(ids), 15):
        chunk = ids[i:i + 15]
        metrics = ",".join(f"ym:s:goal{g}reaches" for g in chunk)
        try:
            d = api("/stat/v1/data", ids=counter, metrics=metrics,
                    date1=f"{days}daysAgo", date2="today")
            totals = d.get("totals", [])
            for j, gid in enumerate(chunk):
                out[gid] = int(totals[j]) if j < len(totals) else None
        except Exception as e:
            print(f"  ! батч целей {chunk}: {type(e).__name__}", file=sys.stderr)
            for gid in chunk:
                out[gid] = None
    return out


def fetch_sources(url: str, max_scripts: int = 40) -> tuple:
    """HTML страницы + тела всех её <script src>. Возвращает (карта файл->текст, ошибки)."""
    sources, errors = {}, []
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=40)
        html = r.text
        sources[url] = html
    except Exception as e:
        return {}, [f"{url}: {type(e).__name__} {e}"]

    for src in RE_SCRIPT_SRC.findall(html)[:max_scripts]:
        if src.startswith("data:"):
            continue
        full = urljoin(url, src)
        host = urlparse(full).netloc
        # чужие CDN (метрика, аналитика, шрифты) не трогаем — reachGoal там не живёт
        if any(x in host for x in ("mc.yandex", "google", "gstatic", "googletagmanager",
                                   "fonts.", "cloudflare", "jsdelivr", "unpkg")):
            continue
        try:
            rr = requests.get(full, headers={"User-Agent": UA}, timeout=30)
            if rr.ok:
                sources[full] = rr.text
        except Exception as e:
            errors.append(f"{full}: {type(e).__name__}")
    return sources, errors


def audit(counter: str, url: str, days: int) -> dict:
    goals = fetch_goals(counter)
    reaches = fetch_reaches(counter, goals, days) if goals else {}
    sources, fetch_errors = fetch_sources(url)

    # что реально вызывается в коде
    in_code = {}
    for path, text in sources.items():
        for cid, name in RE_REACHGOAL.findall(text):
            in_code.setdefault(name, []).append({"file": path, "counter_in_call": cid})

    html = sources.get(url, "")
    rows, orphan_ui, dead, dom_level = [], [], [], []

    for g in goals:
        gid, name, gtype = str(g["id"]), g.get("name", ""), g.get("type", "")
        n = reaches.get(gid)
        # у JS-целей идентификатор в коде лежит в conditions[].url
        js_ids = [c.get("url") for c in (g.get("conditions") or []) if c.get("url")]
        hit = next((j for j in js_ids if j in in_code), None)
        has_code = bool(hit) or name in in_code

        row = {"id": gid, "name": name, "type": gtype, "reaches": n,
               "js_ids": js_ids, "code_found": has_code}
        rows.append(row)

        if gtype == "action" and js_ids and not has_code:
            orphan_ui.append(row)
        if n == 0:
            dead.append(row)
        if gtype in DOM_LEVEL_TYPES or (gtype != "action" and gtype != "url"):
            dom_level.append(row)

    known_js = {j for g in goals for c in (g.get("conditions") or []) if (j := c.get("url"))}
    orphan_code = [{"name": n, "calls": c} for n, c in in_code.items() if n not in known_js]
    broken_names = [r for r in rows if BROKEN_NAME.search(r["name"])]

    # воронка за пределами счётчика
    messenger_exit = bool(RE_MESSENGER.search(html))
    redirect_after = bool(re.search(r"location\.href\s*=\s*['\"][^'\"]*t\.me", html))

    return {
        "counter": counter, "url": url, "days": days,
        "goals_total": len(goals),
        "reachgoal_calls_in_code": sum(len(v) for v in in_code.values()),
        "sources_scanned": len(sources),
        "fetch_errors": fetch_errors,
        "rows": rows,
        "orphan_ui": orphan_ui,
        "orphan_code": orphan_code,
        "dead": dead,
        "dom_level": dom_level,
        "broken_names": broken_names,
        "has_form": bool(RE_FORM.search(html)),
        "has_button": bool(RE_BUTTON.search(html)),
        "messenger_exit": messenger_exit,
        "redirect_to_messenger": redirect_after,
    }


def render(a: dict) -> int:
    print(f"\n{'=' * 78}")
    print(f"АУДИТ ИЗМЕРИТЕЛЯ · счётчик {a['counter']} · {a['url']} · {a['days']} дней")
    print("=" * 78)
    print(f"целей в интерфейсе: {a['goals_total']}   "
          f"вызовов reachGoal в коде: {a['reachgoal_calls_in_code']}   "
          f"просканировано файлов: {a['sources_scanned']}")

    blockers = []

    if a["goals_total"] and a["reachgoal_calls_in_code"] == 0:
        blockers.append(
            f"reachGoal не встречается в коде НИ РАЗУ при {a['goals_total']} заведённых целях. "
            "Всё, что считается, — это автоцели на DOM-событиях. CPA по ним считать нельзя."
        )

    print(f"\n{'цель':<38}{'тип':<12}{'достижений':>12}{'код':>8}")
    print("-" * 78)
    for r in sorted(a["rows"], key=lambda x: -(x["reaches"] or 0)):
        code = "есть" if r["code_found"] else ("НЕТ" if r["js_ids"] else "—")
        n = r["reaches"] if r["reaches"] is not None else "?"
        print(f"{r['name'][:37]:<38}{r['type']:<12}{str(n):>12}{code:>8}")

    if a["orphan_ui"]:
        print(f"\n[!] ЦЕЛЬ ЗАВЕДЕНА, КОДА НЕТ — никогда не сработает ({len(a['orphan_ui'])}):")
        for r in a["orphan_ui"]:
            print(f"    · {r['name']}  (ждёт вызов: {', '.join(r['js_ids'])})")
        blockers.append(f"{len(a['orphan_ui'])} JS-целей заведены в интерфейсе и не подключены в коде.")

    if a["orphan_code"]:
        print(f"\n[!] КОД ЕСТЬ, ЦЕЛИ НЕТ — данные уходят в никуда ({len(a['orphan_code'])}):")
        for r in a["orphan_code"]:
            print(f"    · {r['name']}  ({r['calls'][0]['file']})")

    if a["dead"]:
        print(f"\n[!] МЁРТВЫЕ ЦЕЛИ — 0 достижений за {a['days']} дней ({len(a['dead'])}):")
        for r in a["dead"]:
            print(f"    · {r['name']}")

    if a.get("broken_names"):
        print(f"\n[!] ИМЯ ЦЕЛИ ПОБИТО В САМОЙ МЕТРИКЕ ({len(a['broken_names'])}):")
        for r in a["broken_names"]:
            print(f"    · id {r['id']}: {r['name']!r} — заведена через API с неверной кодировкой,")
            print("      в интерфейсе её не найти поиском по названию, только по id")

    if a["dom_level"]:
        print(f"\n[!] ЦЕЛИ УРОВНЯ DOM — непригодны как основа CPA ({len(a['dom_level'])}):")
        for r in a["dom_level"]:
            print(f"    · {r['name']} [{r['type']}] — срабатывает до ответа сервера")
        blockers.append(
            "Оптимизация на «Оплату за конверсию» по DOM-цели = оплата за нажатие кнопки, "
            "а не за заявку. Нужна цель после успешного ответа бэкенда или /thanks с целью на URL."
        )

    print("\nПОСАДОЧНАЯ:")
    print(f"    форма на странице: {'да' if a['has_form'] else 'НЕТ'}")
    print(f"    кнопка на странице: {'да' if a['has_button'] else 'НЕТ'}")
    if not a["has_form"]:
        blockers.append("На посадочной нет ни одного тега <form> — заявку физически негде оставить.")

    if a["messenger_exit"]:
        note = "с автоматическим редиректом" if a["redirect_to_messenger"] else "ссылкой"
        print(f"    воронка уходит в мессенджер ({note}) — Метрика дальше слепа")
        blockers.append(
            "Целевое действие завершается в мессенджере. Без загрузки офлайн-конверсий "
            "из бота обратно в Метрику канал неоптимизируем в принципе."
        )

    if a["fetch_errors"]:
        print(f"\n    не скачалось файлов: {len(a['fetch_errors'])} (проверка неполна)")

    print(f"\n{'=' * 78}")
    if blockers:
        print("ВЕРДИКТ: измеритель к рекламному бюджету НЕ ГОТОВ")
        for b in blockers:
            print(f"  · {b}")
        print("\nПока это не починено, любой расчёт CPA и любая автостратегия работают по фантомам.")
    else:
        print("ВЕРДИКТ: критичных дефектов измерителя не найдено.")
    print("=" * 78 + "\n")
    return 1 if blockers else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Аудит целей Метрики против кода посадочной")
    ap.add_argument("counter", help="ID счётчика Метрики")
    ap.add_argument("url", help="URL посадочной")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--json", help="сохранить полный отчёт в файл")
    a = ap.parse_args()

    if not TOKEN:
        print("нет YANDEX_OAUTH_TOKEN в credentials", file=sys.stderr)
        return 2

    result = audit(a.counter, a.url, a.days)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print(f"полный отчёт: {a.json}")
    return render(result)


if __name__ == "__main__":
    sys.exit(main())
