# -*- coding: utf-8 -*-
"""
Коннектор ScrapeCreators: Instagram + TikTok + Reddit.
Документация: https://docs.scrapecreators.com
Контракт: collect(book, creds, limit) -> list[dict make_mention()]
Кредиты: 1 кредит / запрос. Экономный режим: 1-2 запроса на платформу.
"""

import sys
import pathlib
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

_BASE = "https://api.scrapecreators.com"
_TIMEOUT = 20


# ─────────────────────── низкоуровневый HTTP ─────────────────────────────────

def _get(path: str, params: dict, api_key: str) -> dict:
    """GET запрос к ScrapeCreators API. Возвращает dict или {} при ошибке."""
    url = f"{_BASE}{path}?" + urllib.parse.urlencode(params, safe="")
    req = urllib.request.Request(url, headers={"x-api-key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        print(f"[scrapecreators] HTTP {e.code} {path}: {body}", file=sys.stderr)
        return {}
    except Exception as ex:
        print(f"[scrapecreators] {path} failed: {ex}", file=sys.stderr)
        return {}


# ─────────────────────── построение запросов ─────────────────────────────────

def _build_queries(book: dict) -> list[str]:
    """Составляем 2-3 запроса из title/authors/anchors. Дедуп."""
    queries = list(book.get("queries") or [])
    title = (book.get("title") or "").strip()
    authors = book.get("authors") or []

    # основной запрос по заголовку
    if title and title not in queries:
        queries.insert(0, title)

    # запрос «первый автор + ключевое слово из названия»
    if authors:
        first_author = authors[0].split()[-1]  # фамилия
        short = title.split()[:3]
        combo = f"{first_author} {' '.join(short)}".strip()
        if combo not in queries:
            queries.append(combo)

    return queries[:3]  # не более 3 запросов


def _relevant(text: str, book: dict) -> bool:
    """Минимальный фильтр релевантности по anchors/exclude."""
    if not text:
        return False
    tl = text.lower()
    exclude = [x.lower() for x in (book.get("exclude") or [])]
    for ex in exclude:
        if ex in tl:
            return False
    anchors = [a.lower() for a in (book.get("anchors") or [])]
    title_words = [w.lower() for w in (book.get("title") or "").split() if len(w) > 3]
    check_words = anchors + title_words
    if not check_words:
        return True
    return any(w in tl for w in check_words)


def _ts_to_iso(ts) -> str:
    """Unix timestamp → ISO 8601 строка. Безопасно."""
    if not ts:
        return ""
    try:
        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return str(ts)


# ─────────────────────── Reddit ──────────────────────────────────────────────

def collect_reddit(book: dict, api_key: str, limit: int) -> list[dict]:
    """GET /v1/reddit/search — глобальный поиск постов Reddit."""
    results: list[dict] = []
    queries = _build_queries(book)

    for query in queries[:2]:  # max 2 запроса, экономим кредиты
        data = _get("/v1/reddit/search", {"query": query, "limit": min(limit, 25)}, api_key)
        posts = data.get("posts", [])
        for p in posts:
            title = p.get("title", "")
            snippet = title  # Reddit search не возвращает selftext в списке
            full_text = f"{title} {p.get('selftext', '')}"
            if not _relevant(full_text, book):
                continue
            url = p.get("url") or f"https://www.reddit.com{p.get('permalink', '')}"
            date = p.get("created_at_iso") or _ts_to_iso(p.get("created_utc"))
            results.append(make_mention(
                channel="reddit",
                type="Соцсеть",
                source=f"reddit.com/r/{p.get('subreddit', '')}",
                url=url,
                title=title,
                snippet=snippet,
                date=date,
                author=p.get("author") or "",
                lang="ru",
                views=None,
                likes=p.get("ups") or p.get("score"),
                reposts=None,
                comments=p.get("num_comments"),
                raw=p,
            ))
        if len(results) >= limit:
            break
        time.sleep(0.5)  # мягкий rate-limit

    return results[:limit]


# ─────────────────────── Instagram ───────────────────────────────────────────

def _ig_post_to_mention(p: dict, book: dict, source_label: str) -> dict | None:
    """Конвертирует пост Instagram в make_mention dict. None если нерелевантен."""
    caption = p.get("caption") or ""
    acc_cap = p.get("accessibility_caption") or ""
    full_text = f"{caption} {acc_cap}"
    if not _relevant(full_text, book):
        return None
    url = p.get("url") or (
        f"https://www.instagram.com/reel/{p.get('shortcode', '')}"
        if p.get("shortcode") else ""
    )
    owner = p.get("owner") or {}
    author = owner.get("username") or owner.get("full_name") or ""
    date = p.get("taken_at") or ""
    views = p.get("video_view_count") or p.get("video_play_count") or None
    likes = p.get("like_count") if (p.get("like_count") or 0) >= 0 else None
    return make_mention(
        channel="instagram",
        type="Соцсеть",
        source=source_label,
        url=url,
        title=caption[:120] if caption else (acc_cap[:120] or ""),
        snippet=caption[:300] if caption else acc_cap[:300],
        date=date,
        author=author,
        lang="ru",
        views=views,
        likes=likes,
        reposts=None,
        comments=p.get("comment_count"),
        raw=p,
    )


def collect_instagram(book: dict, api_key: str, limit: int) -> list[dict]:
    """
    1 запрос /v2/instagram/reels/search (keyword из title).
    1 запрос /v1/instagram/search/hashtag (первый anchor без пробелов).
    """
    results: list[dict] = []
    title = (book.get("title") or "").strip()
    anchors = book.get("anchors") or []

    # ── Reels search по title ──────────────────────────────────────────────
    if title:
        data = _get("/v2/instagram/reels/search", {"query": title}, api_key)
        for p in data.get("reels", []):
            m = _ig_post_to_mention(p, book, "instagram.com (reels)")
            if m:
                results.append(m)
        time.sleep(0.5)

    # ── Hashtag search по первому anchor ──────────────────────────────────
    # Берём первый anchor из 4–8 букв латиницы/кириллицы без пробелов
    hashtag = ""
    for anchor in anchors:
        candidate = anchor.replace(" ", "").replace(".", "")
        if 4 <= len(candidate) <= 30:
            hashtag = candidate
            break
    # Если нет подходящего — строим из publisher или title
    if not hashtag:
        publisher = (book.get("publisher") or "").replace(" ", "").replace(".", "")
        hashtag = publisher[:20] if publisher else title.replace(" ", "")[:20]

    if hashtag and len(results) < limit:
        data = _get("/v1/instagram/search/hashtag", {"hashtag": hashtag}, api_key)
        for p in data.get("posts", []):
            m = _ig_post_to_mention(p, book, f"instagram.com #{hashtag}")
            if m:
                results.append(m)
                if len(results) >= limit:
                    break

    return results[:limit]


# ─────────────────────── TikTok ──────────────────────────────────────────────

def _tt_aweme_to_mention(aw: dict, book: dict) -> dict | None:
    """Конвертирует TikTok aweme_info в make_mention dict."""
    desc = aw.get("desc") or ""
    if not _relevant(desc, book):
        return None
    aweme_id = aw.get("aweme_id") or ""
    author = aw.get("author") or {}
    handle = author.get("uniqueId") or author.get("unique_id") or author.get("nickname") or ""
    url = ""
    share_info = aw.get("share_info") or {}
    share_url = share_info.get("share_url") or share_info.get("url") or ""
    if share_url:
        url = share_url.split("?")[0]  # убираем tracking params
    elif aweme_id and handle:
        url = f"https://www.tiktok.com/@{handle}/video/{aweme_id}"
    stats = aw.get("statistics") or aw.get("stats") or {}
    date = _ts_to_iso(aw.get("create_time"))
    return make_mention(
        channel="tiktok",
        type="Соцсеть",
        source="tiktok.com",
        url=url,
        title=desc[:120],
        snippet=desc[:300],
        date=date,
        author=handle,
        lang="ru",
        views=stats.get("play_count"),
        likes=stats.get("digg_count"),
        reposts=stats.get("share_count") or stats.get("repost_count"),
        comments=stats.get("comment_count"),
        raw=aw,
    )


def collect_tiktok(book: dict, api_key: str, limit: int) -> list[dict]:
    """GET /v1/tiktok/search/keyword — 1-2 запроса."""
    results: list[dict] = []
    queries = _build_queries(book)

    for query in queries[:2]:
        data = _get("/v1/tiktok/search/keyword", {"query": query}, api_key)
        for item in data.get("search_item_list", []):
            aw = item.get("aweme_info") or {}
            if not aw:
                continue
            m = _tt_aweme_to_mention(aw, book)
            if m:
                results.append(m)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
        time.sleep(0.5)

    return results[:limit]


# ─────────────────────── главная точка входа ─────────────────────────────────

def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Собирает упоминания книги в Instagram, TikTok, Reddit через ScrapeCreators.

    Args:
        book: описание книги (title, authors, publisher, anchors, exclude, queries)
        creds: распарсенный словарь из .env
        limit: максимальное количество упоминаний на каждую платформу (суммарно limit * 3)

    Returns:
        list[dict] в формате make_mention()
    """
    api_key = creds.get("SCRAPECREATORS_API_KEY", "")
    if not api_key:
        print("[scrapecreators] SCRAPECREATORS_API_KEY не найден в creds", file=sys.stderr)
        return []

    per_platform = max(5, limit // 3)
    mentions: list[dict] = []

    # Reddit
    try:
        reddit_results = collect_reddit(book, api_key, per_platform)
        mentions.extend(reddit_results)
        print(f"[scrapecreators] Reddit: {len(reddit_results)} упоминаний", file=sys.stderr)
    except Exception as e:
        print(f"[scrapecreators] Reddit error: {e}", file=sys.stderr)

    # Instagram
    try:
        ig_results = collect_instagram(book, api_key, per_platform)
        mentions.extend(ig_results)
        print(f"[scrapecreators] Instagram: {len(ig_results)} упоминаний", file=sys.stderr)
    except Exception as e:
        print(f"[scrapecreators] Instagram error: {e}", file=sys.stderr)

    # TikTok
    try:
        tt_results = collect_tiktok(book, api_key, per_platform)
        mentions.extend(tt_results)
        print(f"[scrapecreators] TikTok: {len(tt_results)} упоминаний", file=sys.stderr)
    except Exception as e:
        print(f"[scrapecreators] TikTok error: {e}", file=sys.stderr)

    return mentions


# ─────────────────────── smoke-тест ──────────────────────────────────────────


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
