# -*- coding: utf-8 -*-
"""
Коннектор: книжные магазины (Ozon, Wildberries, Читай-город, Лабиринт).

Метод: SerpAPI engine=google с site: фильтром (прямой HTTP к этим
магазинам блокируется). Где доступна страница товара — делаем
дополнительный fetch для рейтинга/цены.

Контракт: collect(book, creds, limit) -> list[dict]
"""

import sys
import pathlib
import time
import re
import json
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

# ──────────────────────────────────────────────
# Список магазинов для поиска
# ──────────────────────────────────────────────
STORES = [
    {"site": "chitai-gorod.ru",  "channel": "marketplace", "source": "Читай-город"},
    {"site": "ozon.ru",          "channel": "marketplace", "source": "Ozon"},
    {"site": "wildberries.ru",   "channel": "marketplace", "source": "Wildberries"},
    {"site": "biblio-globus.ru",    "channel": "marketplace", "source": "Библио-Глобус"},
    {"site": "labirint.ru",      "channel": "marketplace", "source": "Лабиринт"},
    {"site": "book24.ru",        "channel": "marketplace", "source": "Book24"},
    {"site": "biblio-globus.ru", "channel": "marketplace", "source": "Библио-Глобус"},
    {"site": "litres.ru",        "channel": "marketplace", "source": "ЛитРес"},
    {"site": "bookvoed.ru",      "channel": "marketplace", "source": "Буквоед"},
]

_SERPAPI_BASE = "https://serpapi.com/search.json"


def _serpapi_google(query: str, api_key: str, num: int = 10) -> list[dict]:
    """Запрос к SerpAPI Google Search, возвращает список organic_results."""
    params = urllib.parse.urlencode({
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": min(num, 10),
        "hl": "ru",
        "gl": "ru",
        "safe": "off",
    })
    url = f"{_SERPAPI_BASE}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("organic_results", [])
    except Exception as exc:
        print(f"[marketplace_stores] SerpAPI error for {query!r}: {exc}")
        return []


def _fetch_chitai_gorod(url: str) -> dict:
    """Пробуем вытащить рейтинг и цену со страницы Читай-города."""
    result = {"rating": None, "rating_count": None, "price": None}
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Рейтинг: ищем JSON-LD или мета-данные
        # Вариант 1: JSON-LD aggregateRating
        ld_match = re.search(
            r'"aggregateRating"\s*:\s*\{[^}]*?"ratingValue"\s*:\s*([\d.]+)'
            r'[^}]*?"ratingCount"\s*:\s*(\d+)',
            html,
        )
        if ld_match:
            result["rating"] = float(ld_match.group(1))
            result["rating_count"] = int(ld_match.group(2))
        else:
            # Вариант 2: ratingValue перед ratingCount
            rv = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
            rc = re.search(r'"ratingCount"\s*:\s*"?(\d+)"?', html)
            if rv:
                result["rating"] = float(rv.group(1))
            if rc:
                result["rating_count"] = int(rc.group(1))

        # Цена (для snippet)
        price_m = re.search(
            r'(?:itemprop="price"|"price"\s*:)\s*"?([\d\s]+)"?', html
        )
        if price_m:
            result["price"] = price_m.group(1).strip()

    except Exception as exc:
        print(f"[marketplace_stores] fetch chitai-gorod failed ({url}): {exc}")
    return result


def _is_excluded(text: str, exclude: list[str]) -> bool:
    """Фильтрует результаты по стоп-словам."""
    text_lo = text.lower()
    return any(ex.lower() in text_lo for ex in exclude if ex)


def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Ищет упоминания книги в книжных магазинах через SerpAPI Google site:.
    """
    api_key = creds.get("SERPAPI_API_KEY", "")
    if not api_key:
        print("[marketplace_stores] SERPAPI_API_KEY not found in creds")
        return []

    queries: list[str] = book.get("queries", [])
    if not queries:
        # Формируем базовый запрос из названия и авторов
        title = book.get("title", "")
        authors = book.get("authors", [])
        author_str = authors[0] if authors else ""
        queries = [f'"{title}"']
        if author_str:
            queries.append(f"{author_str} {title}")

    exclude = book.get("exclude", [])
    mentions: list[dict] = []
    seen_urls: set[str] = set()

    per_store = max(1, limit // len(STORES))

    for store in STORES:
        site = store["site"]
        source = store["source"]

        for q in queries:
            if len(mentions) >= limit:
                break

            search_query = f'{q} site:{site}'
            results = _serpapi_google(search_query, api_key, num=per_store)
            time.sleep(0.3)  # вежливая пауза

            for r in results:
                if len(mentions) >= limit:
                    break

                url = r.get("link", "")
                if not url or url in seen_urls:
                    continue

                title_r = r.get("title", "")
                snippet = r.get("snippet", "")

                # Фильтр по стоп-словам
                combined = f"{title_r} {snippet}".lower()
                if _is_excluded(combined, exclude):
                    continue

                seen_urls.add(url)

                # Дополнительный fetch для Читай-города
                rating = None
                rating_count = None
                price_str = ""
                if "chitai-gorod.ru" in url and "/product/" in url:
                    extra = _fetch_chitai_gorod(url)
                    rating = extra["rating"]
                    rating_count = extra["rating_count"]
                    if extra["price"]:
                        price_str = f" | Цена: {extra['price']} руб."

                # Дата из serpapi
                date_str = ""
                date_raw = r.get("date", "") or ""
                if date_raw:
                    date_str = date_raw

                snippet_final = snippet + price_str if snippet else price_str.strip()

                mention = make_mention(
                    channel="marketplace",
                    type="Магазин",
                    source=source,
                    url=url,
                    title=title_r,
                    snippet=snippet_final,
                    date=date_str,
                    author="",
                    lang="ru",
                    views=None,
                    likes=None,
                    reposts=None,
                    comments=None,
                    rating=rating,
                    rating_count=rating_count,
                    raw=r,
                )
                mentions.append(mention)

        if len(mentions) >= limit:
            break

    return mentions


# ──────────────────────────────────────────────
# Smoke-тест
# ──────────────────────────────────────────────


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
