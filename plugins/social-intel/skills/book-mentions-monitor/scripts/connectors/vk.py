# -*- coding: utf-8 -*-
"""
Коннектор VK — ищет упоминания книги в VK через SerpAPI (engine=google, site:vk.com).
Опционально дополняет через VK API newsfeed.search (если есть VK_TOKEN / VK_ACCESS_TOKEN).

Экспортирует: collect(book, creds, limit=50) -> list[dict]
"""
import sys
import pathlib
import time
import re
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention, dedupe

# ---------- константы ----------
SERPAPI_BASE = "https://serpapi.com/search.json"
VK_API_BASE  = "https://api.vk.com/method"
VK_API_VER   = "5.199"
SERP_PAUSE   = 0.4   # пауза между запросами SerpAPI (сек)
VK_PAUSE     = 0.3   # пауза между VK API запросами


# ---------- helpers ----------
def _get(url: str, params: dict, timeout: int = 15) -> dict:
    """GET-запрос, возвращает распарсенный JSON или {} при ошибке."""
    import urllib.request
    import json

    qs = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{url}?{qs}"
    try:
        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": "Mozilla/5.0 (BookMentionsMonitor/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"[vk.py] HTTP error {url}: {e}", file=sys.stderr)
        return {}


def _parse_date(ts) -> str:
    """Unix-timestamp -> ISO строка 'YYYY-MM-DD'."""
    if not ts:
        return ""
    try:
        import datetime
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except Exception:
        return str(ts)


def _extract_owner_post(url: str):
    """Из 'https://vk.com/wall-12345_678' → (-12345, 678) или (None, None)."""
    m = re.search(r"/wall(-?\d+)_(\d+)", url or "")
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def _build_serpapi_queries(book: dict) -> list[str]:
    """Строим поисковые запросы для SerpAPI (site:vk.com)."""
    queries = list(book.get("queries") or [])
    if not queries:
        title = book.get("title", "")
        authors = book.get("authors") or []
        anchors = book.get("anchors") or []

        if title:
            queries.append(f'"{title}"')
        for a in (authors + anchors)[:3]:
            if title:
                queries.append(f'"{title}" {a}')
            else:
                queries.append(f'"{a}"')

    # добавляем site:vk.com к каждому запросу
    out = []
    for q in queries:
        if "site:vk.com" not in q:
            out.append(f"{q} site:vk.com")
        else:
            out.append(q)
    return out


def _is_excluded(text: str, exclude: list) -> bool:
    tl = (text or "").lower()
    for ex in (exclude or []):
        if ex.lower() in tl:
            return True
    return False


# ---------- SerpAPI fetch ----------
def _collect_serpapi(book: dict, api_key: str, limit: int) -> list[dict]:
    """Основной источник — Google site:vk.com через SerpAPI."""
    results: list[dict] = []
    queries = _build_serpapi_queries(book)
    exclude = book.get("exclude") or []
    per_query = max(10, limit // max(1, len(queries)))

    for q in queries:
        fetched = 0
        page_start = 0
        while fetched < per_query:
            batch = min(10, per_query - fetched)
            params = {
                "engine": "google",
                "q": q,
                "hl": "ru",
                "gl": "ru",
                "num": batch,
                "start": page_start,
                "api_key": api_key,
            }
            data = _get(SERPAPI_BASE, params)
            organics = data.get("organic_results") or []
            if not organics:
                break  # нет результатов — идём к следующему запросу

            for item in organics:
                url   = item.get("link") or item.get("url") or ""
                title = item.get("title") or ""
                snip  = item.get("snippet") or ""
                # фильтр: только vk.com
                if "vk.com" not in url.lower():
                    continue
                combined = f"{title} {snip}"
                if _is_excluded(combined, exclude):
                    continue

                # извлекаем source (domain path)
                source = "vk.com"
                m_src = re.search(r"vk\.com/([^?#/]+)", url)
                if m_src:
                    source = f"vk.com/{m_src.group(1)}"

                results.append(make_mention(
                    channel="vk",
                    type="Соцсеть",
                    source=source,
                    url=url,
                    title=title,
                    snippet=snip,
                    date=item.get("date") or "",
                    author="",
                    lang="ru",
                    views=None,
                    likes=None,
                    reposts=None,
                    comments=None,
                    rating=None,
                    rating_count=None,
                    raw=item,
                ))

            fetched += len(organics)
            page_start += batch
            if len(organics) < batch:
                break  # кончились результаты
            if len(results) >= limit:
                break
            time.sleep(SERP_PAUSE)

        if len(results) >= limit:
            break

    return results


# ---------- VK API newsfeed.search ----------
def _collect_vk_api(book: dict, vk_token: str, serp_results: list[dict], limit: int) -> list[dict]:
    """
    Обогащение через VK API newsfeed.search.
    Добавляет посты, которых нет в SerpAPI-результатах, и дополняет метрики.
    """
    results: list[dict] = []
    exclude = book.get("exclude") or []

    # Сокращённый список запросов (без site:vk.com)
    raw_queries: list[str] = list(book.get("queries") or [])
    if not raw_queries:
        title   = book.get("title", "")
        authors = book.get("authors") or []
        if title:
            raw_queries.append(f'"{title}"')
        if title and authors:
            raw_queries.append(f'"{title}" {authors[0]}')

    seen_urls = {r["url"] for r in serp_results}
    fetched_total = 0

    for q in raw_queries[:3]:  # ограничим 3 запроса
        params = {
            "access_token": vk_token,
            "q": q,
            "count": 50,
            "extended": 1,
            "lang": 0,
            "v": VK_API_VER,
        }
        data = _get(f"{VK_API_BASE}/newsfeed.search", params)
        response = data.get("response") or {}
        items = response.get("items") or []

        for item in items:
            post_id   = item.get("id") or ""
            owner_id  = item.get("owner_id") or item.get("from_id") or ""
            url       = f"https://vk.com/wall{owner_id}_{post_id}" if owner_id and post_id else ""
            text      = item.get("text") or ""
            date_ts   = item.get("date")
            likes_obj = item.get("likes") or {}
            rep_obj   = item.get("reposts") or {}
            views_obj = item.get("views") or {}
            comm_obj  = item.get("comments") or {}

            combined = text[:300]
            if _is_excluded(combined, exclude):
                continue
            if url and url in seen_urls:
                continue

            if url:
                seen_urls.add(url)

            results.append(make_mention(
                channel="vk",
                type="Соцсеть",
                source=f"vk.com/wall{owner_id}" if owner_id else "vk.com",
                url=url,
                title="",
                snippet=text[:500],
                date=_parse_date(date_ts),
                author=str(owner_id) if owner_id else "",
                lang="ru",
                views=views_obj.get("count"),
                likes=likes_obj.get("count"),
                reposts=rep_obj.get("count"),
                comments=comm_obj.get("count"),
                rating=None,
                rating_count=None,
                raw=item,
            ))
            fetched_total += 1
            if fetched_total >= limit:
                break

        if fetched_total >= limit:
            break
        time.sleep(VK_PAUSE)

    return results


# ---------- главный коллектор ----------
def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    book  — описание книги (title, authors, publisher, anchors, exclude, queries)
    creds — словарь из .env
    limit — максимум упоминаний (мягкий лимит)
    """
    serpapi_key = creds.get("SERPAPI_API_KEY") or creds.get("SERPAPI_KEY") or ""
    vk_token    = (
        creds.get("VK_TOKEN")
        or creds.get("VK_ACCESS_TOKEN")
        or ""
    )

    results: list[dict] = []

    # 1. SerpAPI (основной источник)
    if serpapi_key:
        try:
            serp = _collect_serpapi(book, serpapi_key, limit)
            results.extend(serp)
        except Exception as e:
            print(f"[vk.py] SerpAPI error: {e}", file=sys.stderr)
            serp = []
    else:
        print("[vk.py] SERPAPI_API_KEY не задан — SerpAPI пропущен", file=sys.stderr)
        serp = []

    # 2. VK API newsfeed.search (опционально, если есть токен)
    if vk_token:
        try:
            vk = _collect_vk_api(book, vk_token, serp, limit - len(results))
            results.extend(vk)
        except Exception as e:
            print(f"[vk.py] VK API error: {e}", file=sys.stderr)

    # 3. Дедупликация
    results = dedupe(results)

    return results[:limit]


# ---------- smoke-тест ----------


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
