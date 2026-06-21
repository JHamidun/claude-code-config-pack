# -*- coding: utf-8 -*-
"""
SerpAPI коннектор: Google News, Google Web News, Yandex News.
Контракт: collect(book, creds, limit) -> list[dict] (make_mention-формат).
"""
import sys
import pathlib
import time
import urllib.parse
import urllib.request
import json

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention, dedupe

_SERPAPI_BASE = "https://serpapi.com/search.json"


def _get(params: dict, timeout: int = 15) -> dict:
    """Минимальный HTTP GET к SerpAPI без зависимостей."""
    qs = urllib.parse.urlencode(params)
    url = f"{_SERPAPI_BASE}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "book-mentions-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _source_from_url(url: str) -> str:
    """Извлечь домен как название источника."""
    try:
        parsed = urllib.parse.urlparse(url if "//" in url else "//" + url)
        d = parsed.netloc.replace("www.", "").lower()
        return d
    except Exception:
        return ""


def _collect_google_news(query: str, api_key: str) -> list[dict]:
    """engine=google_news → news_results."""
    mentions = []
    try:
        data = _get({
            "engine": "google_news",
            "q": query,
            "hl": "ru",
            "gl": "ru",
            "api_key": api_key,
        })
        for item in data.get("news_results", []):
            # Каждый элемент может содержать stories (вложенный список)
            items_flat = []
            if "stories" in item:
                items_flat.extend(item["stories"])
            else:
                items_flat.append(item)

            for it in items_flat:
                url = it.get("link") or it.get("url") or ""
                title = it.get("title") or ""
                snippet = it.get("snippet") or it.get("description") or ""
                date = it.get("date") or it.get("published_date") or ""
                source_name = ""
                src = it.get("source")
                if isinstance(src, dict):
                    source_name = src.get("name") or src.get("title") or _source_from_url(url)
                elif isinstance(src, str):
                    source_name = src
                else:
                    source_name = _source_from_url(url)
                author = it.get("author") or ""

                mentions.append(make_mention(
                    channel="serpapi_news",
                    type="СМИ",
                    source=source_name,
                    url=url,
                    title=title,
                    snippet=snippet,
                    date=date,
                    author=author,
                    lang="ru",
                    raw=it,
                ))
    except Exception as e:
        print(f"[serpapi] google_news error for query={query!r}: {e}", file=sys.stderr)
    return mentions


def _collect_google_web_news(query: str, api_key: str) -> list[dict]:
    """engine=google + tbm=nws → news_results."""
    mentions = []
    try:
        data = _get({
            "engine": "google",
            "q": query,
            "tbm": "nws",
            "hl": "ru",
            "gl": "ru",
            "num": 20,
            "api_key": api_key,
        })
        for item in data.get("news_results", []):
            url = item.get("link") or ""
            title = item.get("title") or ""
            snippet = item.get("snippet") or item.get("description") or ""
            date = item.get("date") or ""
            source_name = item.get("source") or _source_from_url(url)

            mentions.append(make_mention(
                channel="serpapi_news",
                type="СМИ",
                source=source_name,
                url=url,
                title=title,
                snippet=snippet,
                date=date,
                author="",
                lang="ru",
                raw=item,
            ))
    except Exception as e:
        print(f"[serpapi] google_web_news error for query={query!r}: {e}", file=sys.stderr)
    return mentions


def _collect_yandex(query: str, api_key: str) -> list[dict]:
    """engine=yandex → organic_results (текстовый поиск Яндекса)."""
    mentions = []
    try:
        data = _get({
            "engine": "yandex",
            "text": query,
            "lang": "ru",
            "api_key": api_key,
        })
        for item in data.get("organic_results", []):
            url = item.get("link") or item.get("url") or ""
            title = item.get("title") or ""
            snippet = item.get("snippet") or item.get("description") or ""
            date = item.get("date") or item.get("published_date") or ""
            source_name = _source_from_url(url)

            mentions.append(make_mention(
                channel="yandex",
                type="СМИ",
                source=source_name,
                url=url,
                title=title,
                snippet=snippet,
                date=date,
                author="",
                lang="ru",
                raw=item,
            ))
    except Exception as e:
        print(f"[serpapi] yandex error for query={query!r}: {e}", file=sys.stderr)
    return mentions


def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Основная точка входа.

    book = {
        "title": str,
        "authors": [str],
        "publisher": str,
        "anchors": [str],
        "exclude": [str],
        "queries": [str],
    }
    creds = словарь KEY=VALUE из .env (уже распарсенный)
    limit  = максимум упоминаний в итоге
    """
    api_key = creds.get("SERPAPI_API_KEY", "")
    if not api_key:
        print("[serpapi] SERPAPI_API_KEY не найден в creds", file=sys.stderr)
        return []

    queries = book.get("queries") or []
    if not queries:
        # Запасной вариант: строим простой запрос из заголовка
        queries = [f'"{book.get("title", "")}"']

    all_mentions: list[dict] = []

    for q in queries:
        # 1. Google News (engine=google_news)
        batch = _collect_google_news(q, api_key)
        all_mentions.extend(batch)
        time.sleep(0.3)

        # 2. Google Web News (engine=google&tbm=nws)
        batch = _collect_google_web_news(q, api_key)
        all_mentions.extend(batch)
        time.sleep(0.3)

        # 3. Yandex (engine=yandex)
        batch = _collect_yandex(q, api_key)
        all_mentions.extend(batch)
        time.sleep(0.3)

    # Дедупликация по url/заголовку
    deduped = dedupe(all_mentions)

    return deduped[:limit]


# ---------------------------------------------------------------------------
# Smoke-тест
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
