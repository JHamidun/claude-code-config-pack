# -*- coding: utf-8 -*-
"""
YouTube коннектор для book-mentions-monitor.
Два метода:
  1. YouTube Data API v3 (официальный, бесплатно) — search.list + videos.list
  2. ScrapeCreators /v1/youtube/search (резервный)
Дедуп по videoId. Каналы-омонимы фильтруются по регулярному выражению и через
список exclude из book.yaml.
"""
import sys
import pathlib
import urllib.parse
import urllib.request
import json
import re
import time
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

def _norm_title_yt(t: str) -> str:
    """Нормализация заголовка для дедупа (аналог norm_title из lib)."""
    return re.sub(r"[^а-яёa-z0-9 ]", "", (t or "").lower()).strip()


# Каналы-омонимы для исключения — задаётся динамически через book["exclude"].
# Эти константы можно переопределить или расширить в конфиге книги.
_EXCLUDE_CHANNEL_IDS: set = set()
_EXCLUDE_CHANNEL_HANDLES: set = set()
_EXCLUDE_CHANNEL_TITLE_RE = re.compile(r"(?!x)x")  # никогда не матчит по умолчанию


def _http_get(url: str, headers: dict = None, timeout: int = 15) -> dict | None:
    """Простой GET → JSON. Возвращает None при ошибке."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[youtube] HTTP error {url[:80]}: {e}", file=sys.stderr)
        return None


def _parse_iso_date(s: str) -> str:
    """2024-03-15T10:30:00Z → 2024-03-15"""
    if not s:
        return ""
    return s[:10]


def _is_excluded_channel(channel_id: str, channel_title: str, channel_handle: str) -> bool:
    """Проверяет, является ли канал нежелательным омонимом."""
    if channel_handle and channel_handle.lstrip("@").lower() in {h.lstrip("@").lower() for h in _EXCLUDE_CHANNEL_HANDLES}:
        return True
    if channel_title and _EXCLUDE_CHANNEL_TITLE_RE.search(channel_title):
        return True
    return False


def _build_queries(book: dict) -> list[str]:
    """Строит список поисковых запросов из поля queries или из title/anchors."""
    queries = list(book.get("queries") or [])
    if not queries:
        title = book.get("title", "")
        if title:
            queries.append(f'"{title}"')
        for anchor in (book.get("anchors") or [])[:2]:
            queries.append(anchor)
    return queries[:6]  # не более 6 запросов


def _is_relevant(item_title: str, item_desc: str, book: dict, strict: bool = True) -> bool:
    """
    Проверка релевантности. В strict-режиме требует anchor-хит.
    В non-strict (для ScrapeCreators без описания) — только проверяет excludes.
    """
    text = (item_title + " " + item_desc).lower()
    anchors = [a.lower() for a in (book.get("anchors") or [])]
    excludes = [e.lower() for e in (book.get("exclude") or [])]

    # Ни одного exclude-слова
    for ex in excludes:
        if ex in text:
            return False

    if not strict:
        return True

    # Хотя бы один anchor (или фрагмент title) присутствует
    title_words = book.get("title", "").lower().split()
    anchor_hit = any(a in text for a in anchors) or (
        len(title_words) >= 2 and all(w in text for w in title_words[:3])
    )
    return anchor_hit


# ──────────────────────────────────────────────
# Метод 1: YouTube Data API v3
# ──────────────────────────────────────────────

def _yt_search_api(query: str, api_key: str, max_results: int = 25) -> list[dict]:
    """Возвращает список items из search.list."""
    params = urllib.parse.urlencode({
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max_results, 50),
        "relevanceLanguage": "ru",
        "key": api_key,
    })
    url = f"https://www.googleapis.com/youtube/v3/search?{params}"
    data = _http_get(url)
    if not data:
        return []
    return data.get("items") or []


def _yt_videos_stats(video_ids: list[str], api_key: str) -> dict[str, dict]:
    """Возвращает {videoId: statistics} для списка id."""
    if not video_ids:
        return {}
    params = urllib.parse.urlencode({
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": api_key,
    })
    url = f"https://www.googleapis.com/youtube/v3/videos?{params}"
    data = _http_get(url)
    if not data:
        return {}
    return {item["id"]: item.get("statistics", {}) for item in (data.get("items") or [])}


def _collect_via_youtube_api(book: dict, api_key: str, limit: int) -> list[dict]:
    """Собирает упоминания через официальный YouTube Data API v3."""
    queries = _build_queries(book)
    per_query = max(10, limit // max(len(queries), 1))
    raw_items: dict[str, dict] = {}  # videoId → item

    for q in queries:
        items = _yt_search_api(q, api_key, max_results=min(per_query, 50))
        for item in items:
            vid_id = (item.get("id") or {}).get("videoId")
            if vid_id and vid_id not in raw_items:
                raw_items[vid_id] = item
        time.sleep(0.2)  # не бить API слишком часто

    # Получаем статистику батчами по 50
    all_ids = list(raw_items.keys())
    stats_map: dict[str, dict] = {}
    for i in range(0, len(all_ids), 50):
        batch = all_ids[i:i + 50]
        stats_map.update(_yt_videos_stats(batch, api_key))
        time.sleep(0.1)

    mentions = []
    for vid_id, item in raw_items.items():
        snippet = item.get("snippet") or {}
        ch_id = snippet.get("channelId", "")
        ch_title = snippet.get("channelTitle", "")
        # У API нет handle — проверяем по title
        if _is_excluded_channel(ch_id, ch_title, ""):
            continue

        vid_title = snippet.get("title", "")
        vid_desc = snippet.get("description", "")

        if not _is_relevant(vid_title, vid_desc, book):
            continue

        stats = stats_map.get(vid_id, {})
        views = int(stats.get("viewCount") or 0) or None
        likes = int(stats.get("likeCount") or 0) or None
        comments = int(stats.get("commentCount") or 0) or None

        pub_date = _parse_iso_date(snippet.get("publishedAt", ""))
        url = f"https://www.youtube.com/watch?v={vid_id}"

        mentions.append(make_mention(
            channel="youtube",
            type="Видео",
            source="YouTube",
            url=url,
            title=vid_title,
            snippet=vid_desc[:400],
            date=pub_date,
            author=ch_title,
            lang="ru",
            views=views,
            likes=likes,
            comments=comments,
            raw={
                "videoId": vid_id,
                "channelId": ch_id,
                "channelTitle": ch_title,
                "publishedAt": snippet.get("publishedAt", ""),
                "statistics": stats,
                "_source": "youtube_api_v3",
            },
        ))

    return mentions


# ──────────────────────────────────────────────
# Метод 2: ScrapeCreators /v1/youtube/search
# ──────────────────────────────────────────────

def _collect_via_scrapecreators(book: dict, api_key: str, limit: int) -> list[dict]:
    """
    Резервный метод через ScrapeCreators YouTube Search.

    Формат ответа (проверено эмпирически):
      {videos: [{id, url, title, channel: {title, id?, handle?},
                 viewCountInt, publishedTime (ISO), publishedTimeText, ...}]}
    Описания в search-ответе нет — релевантность по заголовку (strict=False + excludes).
    """
    queries = _build_queries(book)
    per_query = max(10, limit // max(len(queries), 1))
    results: dict[str, dict] = {}  # videoId → item

    for q in queries:
        url = (
            "https://api.scrapecreators.com/v1/youtube/search?query="
            + urllib.parse.quote(q, safe="")
        )
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json",
        }
        data = _http_get(url, headers=headers)
        if not data:
            continue

        # Ответ: {videos: [...], shorts: [...], channels: [...], ...}
        items = data.get("videos") or []

        count = 0
        for item in items:
            if count >= per_query:
                break

            vid_id = item.get("id") or ""
            if not vid_id or vid_id in results:
                continue

            # channel — dict {"title": ..., "id": ..., "handle": ...}
            ch_info = item.get("channel") or {}
            ch_title = ch_info.get("title") or item.get("channelTitle") or ""
            ch_handle = ch_info.get("handle") or item.get("channelHandle") or ""

            if _is_excluded_channel("", ch_title, ch_handle):
                continue

            vid_title = item.get("title") or ""
            vid_desc = ""  # search API не возвращает description

            # Поиск через queries уже целевой; дополнительно проверяем только excludes
            if not _is_relevant(vid_title, vid_desc, book, strict=False):
                continue

            results[vid_id] = item
            count += 1

        time.sleep(0.3)

    mentions = []
    for vid_id, item in results.items():
        ch_info = item.get("channel") or {}
        ch_title = ch_info.get("title") or item.get("channelTitle") or ""
        vid_title = item.get("title") or ""

        # publishedTime — ISO8601 строка
        pub_raw = item.get("publishedTime") or item.get("publishedAt") or ""
        pub_date = _parse_iso_date(pub_raw)

        # viewCountInt — готовое целое число от ScrapeCreators
        views = None
        raw_views = item.get("viewCountInt")
        if raw_views is not None:
            try:
                views = int(raw_views)
            except (ValueError, TypeError):
                pass

        url = item.get("url") or f"https://www.youtube.com/watch?v={vid_id}"
        mentions.append(make_mention(
            channel="youtube",
            type="Видео",
            source="YouTube",
            url=url,
            title=vid_title,
            snippet="",  # не возвращается в search
            date=pub_date,
            author=ch_title,
            lang="ru",
            views=views,
            likes=None,    # нет в search-ответе SC
            comments=None,
            raw={**item, "videoId": vid_id, "_source": "scrapecreators"},
        ))

    return mentions


# ──────────────────────────────────────────────
# Публичная функция collect()
# ──────────────────────────────────────────────

def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Собирает YouTube-упоминания книги.

    Args:
        book: словарь с полями title, authors, publisher, anchors, exclude, queries
        creds: распарсенный словарь из .env
        limit: максимум упоминаний на выходе

    Returns:
        list[dict] упоминаний в формате make_mention()
    """
    google_api_key = creds.get("GOOGLE_API_KEY") or creds.get("GEMINI_API_KEY") or ""
    scrapecreators_key = creds.get("SCRAPECREATORS_API_KEY") or ""

    all_mentions: list[dict] = []

    # Метод 1: YouTube Data API v3
    if google_api_key:
        try:
            api_mentions = _collect_via_youtube_api(book, google_api_key, limit)
            print(f"[youtube] API v3: {len(api_mentions)} hits", file=sys.stderr)
            all_mentions.extend(api_mentions)
        except Exception as e:
            print(f"[youtube] API v3 error: {e}", file=sys.stderr)
    else:
        print("[youtube] GOOGLE_API_KEY not found, skipping API v3", file=sys.stderr)

    # Метод 2: ScrapeCreators (резерв + дополнение)
    if scrapecreators_key:
        try:
            sc_mentions = _collect_via_scrapecreators(book, scrapecreators_key, limit)
            print(f"[youtube] ScrapeCreators: {len(sc_mentions)} hits", file=sys.stderr)
            all_mentions.extend(sc_mentions)
        except Exception as e:
            print(f"[youtube] ScrapeCreators error: {e}", file=sys.stderr)
    else:
        print("[youtube] SCRAPECREATORS_API_KEY not found, skipping ScrapeCreators", file=sys.stderr)

    # NOTE: lib.dedupe() нельзя использовать для YouTube напрямую —
    # norm_url() обрезает ?v=… и все watch-URL схлопываются в один ключ youtube.com/watch.
    # Делаем дедуп сами: сначала по videoId, затем по нормализованному заголовку.
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    result: list[dict] = []

    for m in all_mentions:
        raw = m.get("raw") or {}
        vid_id = (
            raw.get("videoId")
            or raw.get("id")
            or m.get("url", "").split("v=")[-1].split("&")[0]
        )
        # Нормализованный заголовок (дополнительный ключ дедупа)
        nt = _norm_title_yt(m.get("title", ""))

        if vid_id and vid_id in seen_ids:
            continue
        if nt and len(nt) > 12 and nt in seen_titles:
            continue

        if vid_id:
            seen_ids.add(vid_id)
        if nt:
            seen_titles.add(nt)
        result.append(m)

    result = result[:limit]
    print(f"[youtube] total after dedup: {len(result)}", file=sys.stderr)
    return result


# ──────────────────────────────────────────────
# Smoke-тест
# ──────────────────────────────────────────────


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
