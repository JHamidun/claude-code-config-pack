# -*- coding: utf-8 -*-
"""
Коннектор LiveLib — читательские рейтинги и рецензии.
Уникальная ценность: читательский сигнал (рейтинг + рецензии), которого нет у Медиалогии.

Метод:
  1. Ищем страницу книги через SerpAPI site:livelib.ru + запрос из book["queries"]
     ИЛИ через прямой поиск https://www.livelib.ru/find/<enc>
  2. На странице книги: JSON-LD schema.org Book/AggregateRating (cp1251 decode)
  3. Собираем рецензии (заголовок / фрагмент / оценка / автор / дата)
  4. Каждая рецензия + сама книга — отдельное упоминание type="Читательский"
"""

import sys
import pathlib
import re
import json
import time
import urllib.parse

# --- путь к lib ---
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

import requests

# --------------------------------------------------------------------------- #
# Константы
# --------------------------------------------------------------------------- #
SERPAPI_BASE = "https://serpapi.com/search"
LIVELIB_SEARCH = "https://www.livelib.ru/find/{query}"
LIVELIB_BASE = "https://www.livelib.ru"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# --------------------------------------------------------------------------- #
# Вспомогательные функции
# --------------------------------------------------------------------------- #

def _fetch(url: str, encoding: str = "utf-8", timeout: int = 15) -> str:
    """GET с таймаутом, возвращает текст (пустую строку при ошибке)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.encoding = encoding
        return r.text
    except Exception:
        return ""


def _fetch_bytes(url: str, timeout: int = 15) -> bytes:
    """GET, возвращает сырые байты."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r.content
    except Exception:
        return b""


def _decode_cp1251(raw: bytes) -> str:
    """Декодируем тело как cp1251 (LiveLib отдаёт в windows-1251)."""
    try:
        return raw.decode("cp1251", errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")


def _extract_json_ld(html: str) -> list[dict]:
    """Извлекаем все <script type='application/ld+json'> из страницы."""
    results = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            results.append(json.loads(m.group(1)))
        except Exception:
            pass
    return results


def _find_book_url_via_serpapi(queries: list[str], api_key: str) -> str | None:
    """Ищем страницу книги на livelib.ru через SerpAPI."""
    for q in queries:
        search_q = f'site:livelib.ru {q}'
        params = {
            "engine": "google",
            "q": search_q,
            "api_key": api_key,
            "num": 5,
            "hl": "ru",
            "gl": "ru",
        }
        try:
            r = requests.get(SERPAPI_BASE, params=params, timeout=20)
            data = r.json()
            for res in data.get("organic_results", []):
                link = res.get("link", "")
                # Страница книги: /book/<id>-<slug> или /book/<slug>
                if re.search(r"livelib\.ru/book/", link):
                    return link
        except Exception:
            pass
        time.sleep(0.5)
    return None


def _find_book_url_via_direct(queries: list[str], book: dict) -> str | None:
    """Резервный поиск через livelib.ru/find/."""
    search_terms = []
    if book.get("title"):
        search_terms.append(book["title"])
    for a in book.get("authors", [])[:1]:
        search_terms.append(a)

    for term in search_terms[:2]:
        enc = urllib.parse.quote(term)
        url = LIVELIB_SEARCH.format(query=enc)
        raw = _fetch_bytes(url)
        if not raw:
            continue
        html = _decode_cp1251(raw)
        # Ищем ссылку на книгу
        m = re.search(r'href="(/book/[^"]+)"', html)
        if m:
            return LIVELIB_BASE + m.group(1)
        time.sleep(0.5)
    return None


def _parse_book_page(url: str) -> dict:
    """
    Парсит страницу книги livelib.ru.
    Возвращает dict с ключами:
      title, authors, rating, rating_count, reviews, cover_url
    """
    result = {
        "title": "",
        "authors": [],
        "rating": None,
        "rating_count": None,
        "reviews": [],
        "cover_url": "",
    }

    raw = _fetch_bytes(url)
    if not raw:
        return result

    html = _decode_cp1251(raw)

    # --- JSON-LD: Book / AggregateRating ---
    for obj in _extract_json_ld(html):
        schema_type = obj.get("@type", "")
        # Иногда это список
        if isinstance(schema_type, list):
            schema_type = " ".join(schema_type)

        if "Book" in schema_type:
            result["title"] = result["title"] or obj.get("name", "")
            # author может быть dict или list
            author_raw = obj.get("author", [])
            if isinstance(author_raw, dict):
                author_raw = [author_raw]
            result["authors"] = [
                a.get("name", "") for a in author_raw if isinstance(a, dict)
            ] or result["authors"]

            agg = obj.get("aggregateRating", {})
            if agg:
                try:
                    result["rating"] = float(agg.get("ratingValue", 0)) or None
                except (ValueError, TypeError):
                    pass
                try:
                    result["rating_count"] = int(agg.get("ratingCount", 0)) or None
                except (ValueError, TypeError):
                    pass
            break

    # --- Fallback: парсим рейтинг из HTML, если JSON-LD пустой ---
    if result["rating"] is None:
        m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', html)
        if m:
            try:
                result["rating"] = float(m.group(1))
            except ValueError:
                pass
        m = re.search(r'"ratingCount"\s*:\s*"?(\d+)"?', html)
        if m:
            try:
                result["rating_count"] = int(m.group(1))
            except ValueError:
                pass

    # --- Парсим рецензии ---
    # LiveLib: div.review-item или article с классами review
    # Используем regex для извлечения блоков рецензий
    reviews = []

    # Паттерн 1: data-review-id — современный HTML
    for rev_block in re.finditer(
        r'data-review-id="(\d+)".*?</article>',
        html,
        re.DOTALL,
    ):
        block = rev_block.group(0)

        # Автор рецензии
        author_m = re.search(r'class="[^"]*user-name[^"]*"[^>]*>([^<]+)<', block)
        author = author_m.group(1).strip() if author_m else ""

        # Дата
        date_m = re.search(r'datetime="([^"]+)"', block)
        date = date_m.group(1)[:10] if date_m else ""

        # Оценка
        rating_m = re.search(r'class="[^"]*rating[^"]*"[^>]*>.*?(\d[\d,\.]*)\s*/?\s*5', block, re.DOTALL)
        rev_rating = None
        if rating_m:
            try:
                rev_rating = float(rating_m.group(1).replace(",", "."))
            except ValueError:
                pass

        # Текст рецензии
        # Убираем теги, берём первые 400 символов
        text_m = re.search(r'class="[^"]*review-text[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
        snippet = ""
        if text_m:
            raw_text = text_m.group(1)
            snippet = re.sub(r"<[^>]+>", " ", raw_text)
            snippet = re.sub(r"\s+", " ", snippet).strip()[:400]

        # URL рецензии
        rev_id = rev_block.group(1)
        review_url = f"{url}#review-{rev_id}" if rev_id else url

        if snippet or author:
            reviews.append({
                "url": review_url,
                "author": author,
                "date": date,
                "rating": rev_rating,
                "snippet": snippet,
            })

    # Паттерн 2: более широкий поиск если паттерн 1 не дал результатов
    if not reviews:
        for rev_block in re.finditer(
            r'class="[^"]*review[^"]*"[^>]*>(.*?)(?=class="[^"]*review[^"]*"|</section>|$)',
            html,
            re.DOTALL,
        ):
            block = rev_block.group(1)
            if len(block) < 50:
                continue

            snippet_raw = re.sub(r"<[^>]+>", " ", block)
            snippet = re.sub(r"\s+", " ", snippet_raw).strip()[:400]

            if len(snippet) > 30:
                reviews.append({
                    "url": url,
                    "author": "",
                    "date": "",
                    "rating": None,
                    "snippet": snippet,
                })

    result["reviews"] = reviews[:20]  # берём до 20 рецензий
    return result


# --------------------------------------------------------------------------- #
# Основная функция коннектора
# --------------------------------------------------------------------------- #

def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    Собирает упоминания книги на LiveLib.

    Возвращает list[dict] формата make_mention():
    - 1 упоминание с рейтингом (общая карточка книги)
    - N упоминаний — отдельные рецензии (до limit)
    """
    api_key = creds.get("SERPAPI_API_KEY", "")
    mentions = []

    # 1. Ищем URL страницы книги
    queries = book.get("queries", [])
    if not queries:
        # Строим запрос из заголовка + автора
        parts = [book.get("title", "")]
        parts += book.get("authors", [])[:1]
        queries = [" ".join(p for p in parts if p)]

    book_url = None

    # Сначала через SerpAPI (точнее)
    if api_key:
        book_url = _find_book_url_via_serpapi(queries, api_key)

    # Резерв: прямой поиск на livelib
    if not book_url:
        book_url = _find_book_url_via_direct(queries, book)

    if not book_url:
        # Ничего не нашли
        return []

    # 2. Парсим страницу книги
    try:
        parsed = _parse_book_page(book_url)
    except Exception:
        return []

    book_title = parsed.get("title") or book.get("title", "")
    authors = parsed.get("authors") or book.get("authors", [])
    author_str = ", ".join(authors) if authors else ""
    rating = parsed.get("rating")
    rating_count = parsed.get("rating_count")

    # 3. Главная карточка книги (с рейтингом)
    mentions.append(
        make_mention(
            channel="livelib",
            type="Читательский",
            source="livelib.ru",
            url=book_url,
            title=book_title,
            snippet=(
                f"Рейтинг: {rating}/5 ({rating_count} оценок)"
                if rating and rating_count
                else f"Страница книги на LiveLib"
            ),
            date="",
            author=author_str,
            lang="ru",
            rating=rating,
            rating_count=rating_count,
            raw={
                "type": "book_card",
                "url": book_url,
                "title": book_title,
                "authors": authors,
            },
        )
    )

    # 4. Рецензии
    for rev in parsed.get("reviews", [])[: limit - 1]:
        rev_snippet = rev.get("snippet", "")
        rev_author = rev.get("author", "")
        rev_date = rev.get("date", "")
        rev_rating = rev.get("rating")
        rev_url = rev.get("url", book_url)

        # Пропускаем слишком короткие фрагменты
        if len(rev_snippet) < 20:
            continue

        mentions.append(
            make_mention(
                channel="livelib",
                type="Читательский",
                source="livelib.ru",
                url=rev_url,
                title=f"Рецензия: {book_title}",
                snippet=rev_snippet,
                date=rev_date,
                author=rev_author,
                lang="ru",
                rating=rev_rating,
                rating_count=None,
                raw={
                    "type": "review",
                    "book_url": book_url,
                    "book_title": book_title,
                },
            )
        )

    return mentions[:limit]


# --------------------------------------------------------------------------- #
# Smoke-тест
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
