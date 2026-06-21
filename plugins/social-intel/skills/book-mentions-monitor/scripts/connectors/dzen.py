# -*- coding: utf-8 -*-
"""Коннектор Яндекс.Дзен (dzen.ru).

Метод: SerpAPI engine=google + engine=yandex с site:dzen.ru.
Дзен требует SSO (302-редиректы), поэтому полный текст статей не тянем —
используем сниппеты из поисковой выдачи.
type="Соцсеть", channel="dzen".
"""

import sys
import pathlib
import time
import re
import urllib.parse
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention, dedupe

SERPAPI_BASE = "https://serpapi.com/search"
DZEN_DOMAINS = ("dzen.ru", "zen.yandex.ru", "zen.yandex.com")


def _is_dzen_url(url: str) -> bool:
    url_lower = (url or "").lower()
    return any(d in url_lower for d in DZEN_DOMAINS)


def _parse_date(raw: str) -> str:
    """Возвращает строку даты как есть, нормализуем лишь пробелы."""
    return (raw or "").strip()


def _extract_author(result: dict) -> str:
    """Пробуем достать автора/название канала из разных полей SerpAPI."""
    # Rich snippet может содержать detected_extensions.price_range или displayed_link
    displayed = result.get("displayed_link", "")
    # dzen.ru › channel_name › article
    parts = re.split(r"[›»>]", displayed)
    if len(parts) >= 2:
        candidate = parts[1].strip()
        if candidate and candidate.lower() not in ("dzen.ru", "zen.yandex.ru"):
            return candidate
    # source внутри inline_sitelinks
    source = result.get("source", {})
    if isinstance(source, dict):
        return source.get("name", "")
    return ""


def _result_to_mention(result: dict, engine: str) -> Optional[dict]:
    """Конвертирует один результат SerpAPI → mention или None."""
    url = result.get("link", "") or result.get("url", "")
    if not _is_dzen_url(url):
        return None

    title = result.get("title", "")
    snippet = result.get("snippet", "") or result.get("description", "")
    date_raw = (
        result.get("date", "")
        or result.get("published_date", "")
        or (result.get("rich_snippet", {}) or {}).get("top", {}).get("detected_extensions", {}).get("date", "")
    )
    author = _extract_author(result)

    # Метрики из rich_snippet если есть
    views = None
    likes = None
    comments_count = None
    rich = result.get("rich_snippet", {}) or {}
    top = rich.get("top", {}) or {}
    de = top.get("detected_extensions", {}) or {}
    if "views" in de:
        try:
            views = int(str(de["views"]).replace(" ", "").replace(",", ""))
        except Exception:
            pass
    if "likes" in de:
        try:
            likes = int(str(de["likes"]).replace(" ", "").replace(",", ""))
        except Exception:
            pass
    if "comments" in de:
        try:
            comments_count = int(str(de["comments"]).replace(" ", "").replace(",", ""))
        except Exception:
            pass

    return make_mention(
        channel="dzen",
        type="Соцсеть",
        source="dzen.ru",
        url=url,
        title=title,
        snippet=snippet,
        date=_parse_date(date_raw),
        author=author,
        lang="ru",
        views=views,
        likes=likes,
        reposts=None,
        comments=comments_count,
        rating=None,
        rating_count=None,
        raw={"engine": engine, "serpapi_result": result},
    )


def _search_google(query: str, api_key: str, num: int = 10) -> list[dict]:
    """Один запрос через SerpAPI engine=google, возвращает raw-результаты."""
    import urllib.request
    import json

    params = urllib.parse.urlencode({
        "engine": "google",
        "q": query,
        "num": min(num, 100),
        "hl": "ru",
        "gl": "ru",
        "api_key": api_key,
    })
    url = f"{SERPAPI_BASE}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("organic_results", [])
    except Exception as e:
        print(f"[dzen] google search error for '{query}': {e}", file=sys.stderr)
        return []


def _search_yandex(query: str, api_key: str, num: int = 10) -> list[dict]:
    """Один запрос через SerpAPI engine=yandex, возвращает raw-результаты."""
    import urllib.request
    import json

    params = urllib.parse.urlencode({
        "engine": "yandex",
        "text": query,
        "num": min(num, 50),
        "lang": "ru",
        "api_key": api_key,
    })
    url = f"{SERPAPI_BASE}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("organic_results", [])
    except Exception as e:
        print(f"[dzen] yandex search error for '{query}': {e}", file=sys.stderr)
        return []


def _build_queries(book: dict) -> list[str]:
    """Строим список поисковых запросов с site:dzen.ru для обоих движков."""
    base_queries: list[str] = list(book.get("queries", []))

    title = book.get("title", "")
    authors = book.get("authors", [])
    anchors = book.get("anchors", [])

    # Если пользователь не передал queries — генерируем базовые
    if not base_queries:
        if title:
            base_queries.append(f'"{title}"')
        for anchor in anchors[:3]:
            if anchor and anchor not in title:
                base_queries.append(anchor)

    # Для каждого anchor добавляем запрос anchor + первый автор
    extra = []
    if authors:
        first_author_last = authors[0].split()[0] if authors else ""
        for anchor in anchors[:2]:
            if first_author_last and anchor != first_author_last:
                extra.append(f"{anchor} {first_author_last}")

    all_queries = base_queries + extra

    # Навешиваем site:dzen.ru
    dzen_queries = []
    for q in all_queries:
        if "site:" not in q:
            dzen_queries.append(f"{q} site:dzen.ru")
        else:
            dzen_queries.append(q)

    return dzen_queries


def _passes_filters(mention: dict, book: dict) -> bool:
    """Фильтруем по exclude-терминам книги."""
    exclude = [e.lower() for e in book.get("exclude", [])]
    if not exclude:
        return True
    haystack = (mention.get("title", "") + " " + mention.get("snippet", "")).lower()
    for term in exclude:
        if term in haystack:
            return False
    return True


def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Собирает упоминания книги на Яндекс.Дзен.

    Args:
        book: метаданные книги (title, authors, anchors, exclude, queries…)
        creds: распарсенный .env
        limit: максимальное число упоминаний на выходе

    Returns:
        list[dict] — упоминания в формате make_mention()
    """
    api_key = creds.get("SERPAPI_API_KEY", "")
    if not api_key:
        print("[dzen] SERPAPI_API_KEY не найден в creds", file=sys.stderr)
        return []

    queries = _build_queries(book)
    mentions: list[dict] = []
    per_query = max(5, min(20, limit // max(len(queries), 1)))

    for i, q in enumerate(queries):
        if len(mentions) >= limit:
            break

        # Google
        try:
            g_results = _search_google(q, api_key, num=per_query)
            for r in g_results:
                m = _result_to_mention(r, engine="google")
                if m and _passes_filters(m, book):
                    mentions.append(m)
        except Exception as e:
            print(f"[dzen] google batch error: {e}", file=sys.stderr)

        # Небольшая пауза между движками чтобы не спамить SerpAPI
        time.sleep(0.3)

        # Yandex
        try:
            y_results = _search_yandex(q, api_key, num=per_query)
            for r in y_results:
                m = _result_to_mention(r, engine="yandex")
                if m and _passes_filters(m, book):
                    mentions.append(m)
        except Exception as e:
            print(f"[dzen] yandex batch error: {e}", file=sys.stderr)

        if i < len(queries) - 1:
            time.sleep(0.5)

    # Дедуп и обрезка
    mentions = dedupe(mentions)[:limit]
    return mentions


# ---------------------------------------------------------------------------
# Smoke-тест
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
