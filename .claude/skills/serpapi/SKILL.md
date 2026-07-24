---
name: serpapi
description: "Real-time Google Search API через SerpAPI (SERPAPI_API_KEY): scraping выдачи Google Search / Maps / Shopping / News / Images / YouTube. Триггеры: serpapi, «google search API», «спарси выдачу гугла», «google maps данные», «цены google shopping»."
---

# SerpAPI Skill

## Overview

Expert skill for using SerpAPI - real-time Google Search API for scraping search results, maps, shopping, news, images, YouTube, and more.

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: SERPAPI_API_KEY
SERPAPI_API_KEY=os.getenv('SERPAPI_API_KEY')
```

## Локальная бесплатная альтернатива

Для простого парсинга живой выдачи (без carousels/Maps/Shopping/Trends — за структурой оставайся на SerpAPI) — self-hosted `karust/openserp` в Docker, `127.0.0.1:7000`, 0 кредитов. Поддерживает Google/Yandex/Bing/DuckDuckGo. DuckDuckGo/Bing работают из коробки; Google и особенно **Yandex** (которого SerpAPI не отдаёт вообще) из коробки капчатся/ратлимитятся без прокси — нужен `--proxy`/`--2captcha_key` на старте контейнера. Полные детали, эндпоинты, гочи → `~/.claude/skills/seo-machine-ru/SKILL.md`, секция «Яндекс/Google SERP локально (openserp)».

## When to Use SerpAPI

**Best for:**
- Google Search results scraping
- Google Maps/Places data
- Google Shopping prices
- News articles search
- Image search
- YouTube video search
- Local business info
- Reviews and ratings
- Knowledge Graph data

**Advantages:**
- Real-time search results
- Structured JSON output
- Multiple search engines
- No browser needed
- Handles CAPTCHAs
- Proxies included

## Dependencies

```bash
pip install google-search-results
```

## Supported Engines

| Engine | Description |
|--------|-------------|
| google | Web search |
| google_maps | Maps & Places |
| google_shopping | Product prices |
| google_news | News articles |
| google_images | Image search |
| google_videos | Video search |
| youtube | YouTube search |
| google_local | Local businesses |
| google_scholar | Academic papers |
| google_patents | Patents |
| google_jobs | Job listings |
| google_trends | Search trends |

## Basic Usage

### Setup Client

```python
from serpapi import GoogleSearch
import os

API_KEY = os.getenv('SERPAPI_API_KEY')
```

### Google Search

```python
def google_search(query: str, num_results: int = 10, location: str = None):
    """
    Search Google and get structured results.

    Args:
        query: Search query
        num_results: Number of results (10-100)
        location: Location for local results
    """
    params = {
        "api_key": API_KEY,
        "engine": "google",
        "q": query,
        "num": num_results,
        "hl": "en",
        "gl": "us"
    }

    if location:
        params["location"] = location

    search = GoogleSearch(params)
    results = search.get_dict()

    # Extract organic results
    organic = []
    for r in results.get("organic_results", []):
        organic.append({
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet"),
            "position": r.get("position")
        })

    return {
        "organic_results": organic,
        "knowledge_graph": results.get("knowledge_graph"),
        "answer_box": results.get("answer_box"),
        "related_questions": results.get("related_questions"),
        "related_searches": results.get("related_searches")
    }

# Usage
results = google_search("best python libraries 2025")
```

### Google Maps / Places

```python
def search_places(query: str, location: str = None, type: str = None):
    """
    Search Google Maps for places.

    Args:
        query: Place name or type
        location: "lat,lng" or city name
        type: restaurant, hotel, cafe, etc.
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_maps",
        "q": query,
        "type": type or "search"
    }

    if location:
        if "," in location:
            params["ll"] = f"@{location},15z"  # lat,lng
        else:
            params["location"] = location

    search = GoogleSearch(params)
    results = search.get_dict()

    places = []
    for place in results.get("local_results", []):
        places.append({
            "title": place.get("title"),
            "address": place.get("address"),
            "rating": place.get("rating"),
            "reviews": place.get("reviews"),
            "phone": place.get("phone"),
            "website": place.get("website"),
            "hours": place.get("hours"),
            "gps_coordinates": place.get("gps_coordinates")
        })

    return places

# Usage
restaurants = search_places("sushi restaurants", "New York")
```

### Google Shopping

```python
def search_shopping(query: str, min_price: int = None, max_price: int = None):
    """
    Search Google Shopping for products.

    Returns prices, sellers, and product info.
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_shopping",
        "q": query,
        "hl": "en",
        "gl": "us"
    }

    if min_price:
        params["tbs"] = f"mr:1,price:1,ppr_min:{min_price}"
    if max_price:
        params["tbs"] = f"mr:1,price:1,ppr_max:{max_price}"

    search = GoogleSearch(params)
    results = search.get_dict()

    products = []
    for item in results.get("shopping_results", []):
        products.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "extracted_price": item.get("extracted_price"),
            "source": item.get("source"),
            "link": item.get("link"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews"),
            "thumbnail": item.get("thumbnail")
        })

    return products

# Usage
products = search_shopping("mechanical keyboard", min_price=50, max_price=200)
```

### Google News

```python
def search_news(query: str, when: str = None):
    """
    Search Google News.

    Args:
        query: News topic
        when: Time filter - "d" (day), "w" (week), "m" (month), "y" (year)
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_news",
        "q": query,
        "hl": "en",
        "gl": "us"
    }

    if when:
        params["tbs"] = f"qdr:{when}"

    search = GoogleSearch(params)
    results = search.get_dict()

    articles = []
    for news in results.get("news_results", []):
        articles.append({
            "title": news.get("title"),
            "link": news.get("link"),
            "source": news.get("source", {}).get("name"),
            "date": news.get("date"),
            "snippet": news.get("snippet"),
            "thumbnail": news.get("thumbnail")
        })

    return articles

# Usage
news = search_news("AI technology", when="w")  # Last week
```

### Google Images

```python
def search_images(query: str, size: str = None, type: str = None):
    """
    Search Google Images.

    Args:
        query: Image search query
        size: "large", "medium", "icon"
        type: "photo", "clipart", "lineart", "animated"
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_images",
        "q": query,
        "hl": "en"
    }

    tbs_parts = []
    if size:
        size_map = {"large": "l", "medium": "m", "icon": "i"}
        tbs_parts.append(f"isz:{size_map.get(size, 'l')}")
    if type:
        type_map = {"photo": "photo", "clipart": "clipart", "lineart": "lineart"}
        tbs_parts.append(f"itp:{type_map.get(type, 'photo')}")

    if tbs_parts:
        params["tbs"] = ",".join(tbs_parts)

    search = GoogleSearch(params)
    results = search.get_dict()

    images = []
    for img in results.get("images_results", []):
        images.append({
            "title": img.get("title"),
            "original": img.get("original"),
            "thumbnail": img.get("thumbnail"),
            "source": img.get("source"),
            "link": img.get("link")
        })

    return images

# Usage
images = search_images("sunset photography", size="large")
```

### YouTube Search

```python
def search_youtube(query: str, sort_by: str = "relevance"):
    """
    Search YouTube videos.

    Args:
        query: Video search query
        sort_by: "relevance", "date", "views", "rating"
    """
    params = {
        "api_key": API_KEY,
        "engine": "youtube",
        "search_query": query
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    videos = []
    for video in results.get("video_results", []):
        videos.append({
            "title": video.get("title"),
            "link": video.get("link"),
            "channel": video.get("channel", {}).get("name"),
            "views": video.get("views"),
            "published_date": video.get("published_date"),
            "length": video.get("length"),
            "description": video.get("description"),
            "thumbnail": video.get("thumbnail", {}).get("static")
        })

    return videos

# Usage
videos = search_youtube("python tutorial 2025")
```

### Google Scholar

```python
def search_scholar(query: str, year_from: int = None):
    """
    Search academic papers on Google Scholar.

    Args:
        query: Research topic
        year_from: Start year for publications
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_scholar",
        "q": query,
        "hl": "en"
    }

    if year_from:
        params["as_ylo"] = year_from

    search = GoogleSearch(params)
    results = search.get_dict()

    papers = []
    for paper in results.get("organic_results", []):
        papers.append({
            "title": paper.get("title"),
            "link": paper.get("link"),
            "snippet": paper.get("snippet"),
            "publication_info": paper.get("publication_info", {}).get("summary"),
            "cited_by": paper.get("inline_links", {}).get("cited_by", {}).get("total"),
            "pdf_link": paper.get("resources", [{}])[0].get("link") if paper.get("resources") else None
        })

    return papers

# Usage
papers = search_scholar("machine learning healthcare", year_from=2023)
```

### Google Jobs

```python
def search_jobs(query: str, location: str = None):
    """Search job listings."""

    params = {
        "api_key": API_KEY,
        "engine": "google_jobs",
        "q": query,
        "hl": "en"
    }

    if location:
        params["location"] = location

    search = GoogleSearch(params)
    results = search.get_dict()

    jobs = []
    for job in results.get("jobs_results", []):
        jobs.append({
            "title": job.get("title"),
            "company_name": job.get("company_name"),
            "location": job.get("location"),
            "description": job.get("description"),
            "posted_at": job.get("detected_extensions", {}).get("posted_at"),
            "salary": job.get("detected_extensions", {}).get("salary"),
            "apply_link": job.get("apply_link")
        })

    return jobs

# Usage
jobs = search_jobs("python developer", location="San Francisco")
```

### Google Trends

```python
def get_trends(query: str, geo: str = "US", timeframe: str = "today 12-m"):
    """
    Get Google Trends data.

    Args:
        query: Search term
        geo: Country code (US, GB, DE, etc.)
        timeframe: "now 1-H", "now 4-H", "now 1-d", "now 7-d", "today 1-m", "today 12-m"
    """
    params = {
        "api_key": API_KEY,
        "engine": "google_trends",
        "q": query,
        "geo": geo,
        "date": timeframe,
        "data_type": "TIMESERIES"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return {
        "interest_over_time": results.get("interest_over_time"),
        "related_queries": results.get("related_queries"),
        "related_topics": results.get("related_topics")
    }

# Usage
trends = get_trends("artificial intelligence", geo="US")
```

### Direct API Call (без библиотеки)

```python
import requests

def serpapi_search(engine: str, params: dict):
    """Direct API call to SerpAPI."""

    base_params = {
        "api_key": API_KEY,
        "engine": engine,
        "output": "json"
    }

    all_params = {**base_params, **params}

    response = requests.get(
        "https://serpapi.com/search",
        params=all_params
    )

    return response.json()

# Usage
results = serpapi_search("google", {"q": "python tutorials"})
```

## API Pricing

| Plan | Searches/month | Price |
|------|----------------|-------|
| Free | 100 | $0 |
| Developer | 5,000 | $75/mo |
| Small Business | 15,000 | $150/mo |
| Business | 30,000 | $250/mo |
| Corporate | 50,000 | $350/mo |
| Enterprise | Custom | Custom |

## Quick Reference

| Task | Engine | Code |
|------|--------|------|
| Web search | google | `GoogleSearch({"engine": "google", "q": query})` |
| Places | google_maps | `GoogleSearch({"engine": "google_maps", "q": query})` |
| Shopping | google_shopping | `GoogleSearch({"engine": "google_shopping", "q": query})` |
| News | google_news | `GoogleSearch({"engine": "google_news", "q": query})` |
| Images | google_images | `GoogleSearch({"engine": "google_images", "q": query})` |
| YouTube | youtube | `GoogleSearch({"engine": "youtube", "search_query": query})` |
| Scholar | google_scholar | `GoogleSearch({"engine": "google_scholar", "q": query})` |
| Jobs | google_jobs | `GoogleSearch({"engine": "google_jobs", "q": query})` |
| Trends | google_trends | `GoogleSearch({"engine": "google_trends", "q": query})` |

## Tips

1. **Локализация** - используй `gl` (country) и `hl` (language)
2. **Пагинация** - `start=10` для второй страницы
3. **Фильтры времени** - `tbs=qdr:d` (день), `qdr:w` (неделя)
4. **Knowledge Graph** - автоматически в результатах Google
5. **Related Questions** - секция "People also ask"
6. **Rate limits** - зависят от плана
7. **Кэширование** - результаты кэшируются ~30 секунд
