# -*- coding: utf-8 -*-
"""
Wordstat коннектор — сигнал спроса (показы/мес) + Яндекс Suggest (расширения якорей).

Не является коннектором упоминаний в обычном смысле: возвращает type="СМИ", channel="yandex"
с title="Спрос Wordstat: <фраза> = N показов/мес" (1 запись на якорь/запрос).

Источники:
  1. wordstat.yandex.ru/wordstat/api/getTable  — требует Session_id cookie залогиненной сессии
  2. suggest.yandex.ru/suggest-ya.cgi          — публичный, без авторизации

Cookie берётся из:
  1. creds["YANDEX_WORDSTAT_COOKIE"]   — явно заданная строка cookie в .env
  2. creds["YANDEX_SESSION_ID"]        — только Session_id (подставляется в заголовок)
  3. локальный профиль браузера (Playwright/Chrome)     — автоматическое извлечение Session_id/yandexuid
  4. Нет cookie → режим partial (только Suggest, без частот)

Как добавить cookie вручную (один раз):
  - Открой wordstat.yandex.ru в браузере, залогинься
  - DevTools → Application → Cookies → скопируй Session_id и yandexuid
  - Добавь в .env:
      YANDEX_WORDSTAT_COOKIE=Session_id=3:xxxx; yandexuid=xxxx

Контракт:
  collect(book, creds, limit) -> list[dict]  (make_mention-формат)
"""

import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

# Добавляем lib в путь
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention
from lib.wordstat_fetch import fetch_one

# ────────────────────────────────────────────────────────────
# Константы
# ────────────────────────────────────────────────────────────
SUGGEST_URL = "https://suggest.yandex.ru/suggest-ya.cgi"
SUGGEST_TIMEOUT = 10
WORDSTAT_DELAY = 0.4   # задержка между запросами к Wordstat (сек)
SUGGEST_DELAY = 0.15   # задержка между запросами к Suggest (сек)

# Источник куки Wordstat. Приоритет: переменная YANDEX_WORDSTAT_COOKIE (готовая строка
# вида "Session_id=...; yandexuid=..."), иначе попытка достать из локального профиля Chrome.
# Путь к собственному браузерному cookie-SQLite можно задать через WORDSTAT_COOKIE_DB в .env.
CHROME_LOCAL_STATE = pathlib.Path(
    os.path.expanduser(r"~/AppData/Local/Google/Chrome/User Data/Local State")
)
CHROME_COOKIE_DB = pathlib.Path(
    os.path.expanduser(r"~/AppData/Local/Google/Chrome/User Data/Default/Network/Cookies")
)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Safari/537.36")


# ────────────────────────────────────────────────────────────
# Cookie helpers
# ────────────────────────────────────────────────────────────

def _extract_cookie_from_sqlite(db_path: pathlib.Path) -> str:
    """Пробуем достать Session_id + yandexuid из SQLite Chromium Cookies (незашифрованные).
    Возвращает строку cookie или пустую строку."""
    import sqlite3, shutil, tempfile, os
    if not db_path.exists():
        return ""
    tmp = tempfile.mktemp(suffix=".db")
    try:
        shutil.copy2(db_path, tmp)
        conn = sqlite3.connect(tmp)
        cur = conn.execute(
            "SELECT name, value FROM cookies "
            "WHERE host_key LIKE '%yandex%' AND value != ''"
        )
        rows = cur.fetchall()
        conn.close()
        parts = {name: val for name, val in rows if val}
        if not parts:
            return ""
        # Собираем строку cookie только из нужных ключей
        useful = {k: v for k, v in parts.items()
                  if k in ("Session_id", "yandexuid", "i", "ymex", "yuidss", "bh")}
        return "; ".join(f"{k}={v}" for k, v in useful.items())
    except Exception:
        return ""
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _resolve_cookie(creds: dict) -> str:
    """Ищет cookie для Wordstat в порядке приоритета. Возвращает строку или ''."""
    # 1. Явный полный cookie
    c = creds.get("YANDEX_WORDSTAT_COOKIE", "").strip()
    if c:
        return c

    # 2. Только Session_id
    sid = creds.get("YANDEX_SESSION_ID", "").strip()
    if sid:
        return f"Session_id={sid}"

    # 3. Свой браузерный cookie-SQLite, если путь задан в .env (WORDSTAT_COOKIE_DB)
    custom_db = creds.get("WORDSTAT_COOKIE_DB", "").strip()
    if custom_db:
        c = _extract_cookie_from_sqlite(pathlib.Path(os.path.expanduser(custom_db)))
        if c and "Session_id" in c:
            return c

    # 4. Chrome (старый формат без app-bound encryption — не поддерживается в Chrome 127+)
    c = _extract_cookie_from_sqlite(CHROME_COOKIE_DB)
    if c and "Session_id" in c:
        return c

    return ""


# ────────────────────────────────────────────────────────────
# Suggest helper
# ────────────────────────────────────────────────────────────

def _fetch_suggest(phrase: str) -> list[str]:
    """GET suggest.yandex.ru — возвращает список подсказок (или пустой список)."""
    params = urllib.parse.urlencode({
        "v": "4",
        "uil": "ru",
        "part": phrase,
        "n": "10",
        "lr": "225",
    })
    url = f"{SUGGEST_URL}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=SUGGEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # Формат: ["фраза", ["подсказка1", ...], ...]
            if isinstance(data, list) and len(data) >= 2:
                suggestions = data[1]
                if isinstance(suggestions, list):
                    return [s for s in suggestions if isinstance(s, str)]
    except Exception as e:
        print(f"[wordstat] suggest error for {phrase!r}: {e}", file=sys.stderr)
    return []


# ────────────────────────────────────────────────────────────
# collect()
# ────────────────────────────────────────────────────────────

def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Возвращает список упоминаний-сигналов спроса:
      - По каждому якорю/запросу — 1 запись type="СМИ" channel="yandex"
        с title="Спрос Wordstat: <фраза> = N показов/мес"
      - В raw — suggest-подсказки и топ связанных слов из Wordstat

    partial-режим: если нет cookie → только Suggest (snippet содержит подсказки,
    views=None, title указывает что данные из Suggest).
    """
    mentions: list[dict] = []

    cookie = _resolve_cookie(creds)
    has_cookie = bool(cookie)

    if not has_cookie:
        print("[wordstat] YANDEX_WORDSTAT_COOKIE не найден — режим partial (только Suggest)",
              file=sys.stderr)

    # Собираем фразы: queries + anchors (дедуп)
    queries: list[str] = list(book.get("queries") or [])
    anchors: list[str] = list(book.get("anchors") or [])

    # Добавляем якоря (без дублей с queries)
    seen = {q.lower() for q in queries}
    for anchor in anchors:
        if anchor.lower() not in seen:
            queries.append(anchor)
            seen.add(anchor.lower())

    # Ограничиваем число фраз разумным числом
    phrases = queries[:20]

    for phrase in phrases:
        # ── Suggest (всегда) ──────────────────────────────
        suggest_list = _fetch_suggest(phrase)
        time.sleep(SUGGEST_DELAY)

        raw_suggest = {
            "suggest_query": phrase,
            "suggestions": suggest_list,
        }

        # ── Wordstat API ───────────────────────────────────
        if has_cookie:
            try:
                result = fetch_one(phrase, cookie)
                total = result.get("total")
                status = result.get("status")
                top = result.get("top") or []
                raw_suggest["wordstat_total"] = total
                raw_suggest["wordstat_top"] = top
                raw_suggest["wordstat_status"] = status

                if status == 200 and total is not None:
                    title = f"Спрос Wordstat: {phrase} = {total:,} показов/мес".replace(",", " ")
                    snippet_parts = []
                    if top:
                        snippet_parts.append("Топ фраз: " + ", ".join(
                            f"{t['text']} ({t['value']})" for t in top[:4]
                        ))
                    if suggest_list:
                        snippet_parts.append("Suggest: " + "; ".join(suggest_list[:5]))
                    snippet = " | ".join(snippet_parts)
                    views = int(total) if total is not None else None
                else:
                    # Wordstat вернул ошибку (не залогинен, лимит и т.д.)
                    title = f"Спрос Wordstat: {phrase} — нет данных (status={status})"
                    snippet = "Suggest: " + "; ".join(suggest_list[:5]) if suggest_list else ""
                    views = None
            except Exception as e:
                print(f"[wordstat] fetch_one error for {phrase!r}: {e}", file=sys.stderr)
                title = f"Спрос Wordstat: {phrase} — ошибка API"
                snippet = "Suggest: " + "; ".join(suggest_list[:5]) if suggest_list else ""
                views = None
            time.sleep(WORDSTAT_DELAY)
        else:
            # Нет cookie — только Suggest
            if suggest_list:
                title = f"Suggest Яндекс: {phrase} ({len(suggest_list)} подсказок)"
                snippet = "; ".join(suggest_list[:8])
            else:
                title = f"Suggest Яндекс: {phrase} — нет подсказок"
                snippet = ""
            views = None

        url = (
            "https://wordstat.yandex.ru/#?"
            + urllib.parse.urlencode({"words": phrase, "region": "225", "type": "words"})
        )

        mentions.append(make_mention(
            channel="yandex",
            type="СМИ",
            source="wordstat.yandex.ru",
            url=url,
            title=title,
            snippet=snippet,
            date="",
            author="",
            lang="ru",
            views=views,
            raw=raw_suggest,
        ))

        if len(mentions) >= limit:
            break

    return mentions


# ────────────────────────────────────────────────────────────
# Smoke-тест
# ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
