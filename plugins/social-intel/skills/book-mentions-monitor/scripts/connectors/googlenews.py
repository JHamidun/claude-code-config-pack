# -*- coding: utf-8 -*-
"""
Коннектор Google News RSS.
Гоняет каждый book["queries"] через:
  GET https://news.google.com/rss/search?q=<URL-enc>&hl=ru&gl=RU&ceid=RU:ru
Парсит RSS (xml.etree), строит упоминания через make_mention().
Ключей API не требует.
"""

import sys
import pathlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import time
import re

# --- путь к lib ---
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention, dedupe

# Имена доменов, которые считаем агрегаторами (не СМИ)
_AGGREGATOR_DOMAINS = {
    "news.google.com", "google.com", "yandex.ru", "mail.ru",
    "rambler.ru", "bing.com", "yahoo.com", "msn.com",
    "flipboard.com", "feedly.com", "anews.com", "news.ru",
}

_RSS_BASE = "https://news.google.com/rss/search"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


def _build_url(query: str) -> str:
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "ru",
        "gl": "RU",
        "ceid": "RU:ru",
    })
    return f"{_RSS_BASE}?{params}"


def _fetch_rss(url: str, retries: int = 2) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as exc:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
    return b""


def _parse_date(raw: str) -> str:
    """RFC-2822 → ISO-8601 YYYY-MM-DD, или вернуть как есть."""
    if not raw:
        return ""
    # Пример: "Mon, 02 Jun 2025 10:30:00 GMT"
    m = re.search(r"(\d{1,2})\s+(\w{3})\s+(\d{4})", raw)
    if not m:
        return raw.strip()
    months = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    day, mon, year = m.group(1).zfill(2), months.get(m.group(2), "00"), m.group(3)
    return f"{year}-{mon}-{day}"


def _source_name(item_elem, channel_elem) -> str:
    """Извлекаем имя источника из <source> или из <title> канала RSS."""
    src = item_elem.find("source")
    if src is not None and src.text:
        return src.text.strip()
    # Иногда у Google News в <title> канала пишется название издания
    if channel_elem is not None:
        t = channel_elem.findtext("title", "")
        if t and t.lower() not in ("google news", ""):
            return t.strip()
    return ""


def _source_url(item_elem) -> str:
    src = item_elem.find("source")
    if src is not None:
        return src.get("url", "") or ""
    return ""


def _mention_type(url: str, source_url_str: str) -> str:
    """СМИ или Агрегатор."""
    for u in (url, source_url_str):
        try:
            domain = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
        except Exception:
            continue
        if domain in _AGGREGATOR_DOMAINS:
            return "Агрегатор"
    return "СМИ"


def _is_excluded(text: str, exclude: list) -> bool:
    tl = text.lower()
    for ex in (exclude or []):
        if ex.lower() in tl:
            return True
    return False


def _parse_feed(xml_bytes: bytes, query: str, book: dict) -> list[dict]:
    mentions = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return mentions

    channel_elem = root.find("channel")
    if channel_elem is None:
        return mentions

    for item in channel_elem.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = _parse_date(item.findtext("pubDate") or "")
        description = (item.findtext("description") or "").strip()
        # Google News иногда пихает HTML в description — стрипим теги
        snippet = re.sub(r"<[^>]+>", "", description).strip()

        src_name = _source_name(item, channel_elem)
        src_url = _source_url(item)

        combined = f"{title} {snippet}"
        if _is_excluded(combined, book.get("exclude", [])):
            continue

        mtype = _mention_type(link, src_url)

        m = make_mention(
            channel="googlenews",
            type=mtype,
            source=src_name,
            url=link,
            title=title,
            snippet=snippet,
            date=pub_date,
            author="",
            lang="ru",
            views=None,
            likes=None,
            reposts=None,
            comments=None,
            rating=None,
            rating_count=None,
            raw={
                "query": query,
                "pubDate": item.findtext("pubDate") or "",
                "source_url": src_url,
                "guid": item.findtext("guid") or "",
            },
        )
        mentions.append(m)
    return mentions


def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Основная функция коннектора.
    book["queries"] — список поисковых фраз.
    Возвращает дедуплицированный список упоминаний, не более limit.
    """
    queries = book.get("queries") or []
    if not queries:
        # Fallback: строим запрос из title
        title = book.get("title", "")
        if title:
            queries = [f'"{title}"']

    all_mentions: list[dict] = []

    for query in queries:
        url = _build_url(query)
        try:
            xml_bytes = _fetch_rss(url)
        except Exception as exc:
            # Не падаем — логируем и продолжаем
            print(f"[googlenews] fetch error for query={query!r}: {exc}", file=sys.stderr)
            continue

        if not xml_bytes:
            continue

        parsed = _parse_feed(xml_bytes, query, book)
        all_mentions.extend(parsed)

        # Вежливая пауза между запросами
        if len(queries) > 1:
            time.sleep(1.2)

    deduped = dedupe(all_mentions)
    return deduped[:limit]


# ---------------------------------------------------------------------------
# Smoke-test: запускай напрямую
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
