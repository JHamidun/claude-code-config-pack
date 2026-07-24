#!/usr/bin/env python
"""
Brand Mention Scanner — присутствие бренда на платформах, которые цитируют LLM.

Brand mentions коррелируют с AI-видимостью в 3× сильнее беклинков
(Ahrefs, декабрь 2025, 75K брендов). Веса платформ:
1. YouTube (~0.737 корреляция — сильнейшая)
2. Reddit (high)
3. Wikipedia/Wikidata (high)
4. LinkedIn (moderate)
5. Domain Rating/backlinks (~0.266 — слабая)

Источник: zubair-trabzada/geo-seo-claude (MIT), адаптация для skills/geo-aeo-ru:
- Windows: python (не python3), UTF-8 stdout;
- RU-контур: проверка ru.wikipedia в дополнение к en (training-сигнал для
  (regional LLM B)/(regional LLM A)), в «other platforms» добавлены Habr и vc.ru (главные
  RU-домены цитирования, см. references/russian-llm.md).

Механические проверки — только Wikipedia/Wikidata API (без ключей). Остальные
платформы возвращают search_url + чек-лист для ручной/агентной проверки
(WebFetch/dev-browser).

Usage: python brand_scanner.py "<brand_name>" [domain]
"""

import sys
import json
from urllib.parse import quote_plus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1251 fix

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def check_youtube_presence(brand_name: str) -> dict:
    """Check brand presence on YouTube (checklist framework)."""
    return {
        "platform": "YouTube",
        "correlation": 0.737,
        "weight": "25%",
        "search_url": f"https://www.youtube.com/results?search_query={quote_plus(brand_name)}",
        "check_instructions": [
            f"Search YouTube for '{brand_name}' and check:",
            "1. Официальный канал бренда есть?",
            "2. Видео ОТ бренда (туториалы, демо, thought leadership)?",
            "3. Видео О бренде от сторонних авторов?",
            "4. Просмотры на видео по бренду?",
            "5. Позитивные обзоры/демонстрации?",
        ],
        "recommendations": [
            "Создать канал, если нет",
            "Публиковать обучающий контент по нише",
            "Стимулировать обзоры/демо от клиентов",
            "Имя бренда в заголовках и описаниях видео",
            "Таймкоды и главы — улучшают AI-парсинг",
            "Проверять авто-транскрипты на точность",
        ],
    }


def check_reddit_presence(brand_name: str) -> dict:
    """Check brand presence on Reddit (checklist framework)."""
    return {
        "platform": "Reddit",
        "correlation": "High",
        "weight": "25%",
        "search_url": f"https://www.reddit.com/search/?q={quote_plus(brand_name)}",
        "check_instructions": [
            f"Search Reddit for '{brand_name}' and check:",
            "1. Свой сабреддит (r/brandname)?",
            "2. Обсуждают ли в отраслевых сабреддитах?",
            "3. Сентимент (позитив/негатив/нейтрал)?",
            "4. Есть ли в recommendation-тредах?",
            "5. Официальное присутствие бренда?",
            "6. Свежие ли упоминания (последние 6 мес)?",
        ],
        "recommendations": [
            "Мониторить релевантные сабреддиты",
            "Участвовать аутентично (не спамить) — с brand-аккаунта про себя постить нельзя, банят",
            "Официальный аккаунт для поддержки",
            "Ценный контент, не самопиар",
            "Отвечать на вопросы по категории продукта",
        ],
    }


def _wiki_api_check(brand_name: str, lang: str) -> dict:
    """Query Wikipedia search API for brand presence in a given language wiki."""
    out = {"has_page": False, "search_results": 0}
    try:
        api_url = (
            f"https://{lang}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={quote_plus(brand_name)}&format=json"
        )
        response = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            search_results = response.json().get("query", {}).get("search", [])
            out["search_results"] = len(search_results)
            if search_results:
                top_title = search_results[0].get("title", "").lower()
                if brand_name.lower() in top_title:
                    out["has_page"] = True
    except Exception:
        pass
    return out


def check_wikipedia_presence(brand_name: str) -> dict:
    """Check brand/entity presence on Wikipedia (en + ru) and Wikidata."""
    result = {
        "platform": "Wikipedia",
        "correlation": "High",
        "weight": "20%",
        "has_wikipedia_page_en": False,
        "has_wikipedia_page_ru": False,
        "has_wikidata_entry": False,
        "search_url": f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(brand_name)}",
        "search_url_ru": f"https://ru.wikipedia.org/wiki/Служебная:Поиск?search={quote_plus(brand_name)}",
        "wikidata_url": f"https://www.wikidata.org/w/index.php?search={quote_plus(brand_name)}",
        "recommendations": [],
    }

    en = _wiki_api_check(brand_name, "en")
    result["has_wikipedia_page_en"] = en["has_page"]
    result["wikipedia_search_results_en"] = en["search_results"]

    # RU-wiki: training-сигнал для (regional LLM B)/(regional LLM A) + источник ChatGPT на RU-запросах
    ru = _wiki_api_check(brand_name, "ru")
    result["has_wikipedia_page_ru"] = ru["has_page"]
    result["wikipedia_search_results_ru"] = ru["search_results"]

    try:
        wikidata_url = (
            f"https://www.wikidata.org/w/api.php"
            f"?action=wbsearchentities&search={quote_plus(brand_name)}&language=en&format=json"
        )
        response = requests.get(wikidata_url, headers=DEFAULT_HEADERS, timeout=15)
        if response.status_code == 200:
            entities = response.json().get("search", [])
            if entities:
                result["has_wikidata_entry"] = True
                result["wikidata_id"] = entities[0].get("id", "")
                result["wikidata_description"] = entities[0].get("description", "")
    except Exception:
        pass

    result["recommendations"] = [
        "Если проходит по notability — создать статью (для RU-бренда начинать с ru-wiki)",
        "Wikidata-запись с полными структурными данными",
        "sameAs в schema-разметке → ссылки на Wikipedia/Wikidata",
        "Попасть источником в существующие статьи",
        "Notability строится через прессу и независимые обзоры",
    ]

    return result


def check_linkedin_presence(brand_name: str) -> dict:
    """Check brand presence on LinkedIn (checklist framework)."""
    return {
        "platform": "LinkedIn",
        "correlation": "Moderate",
        "weight": "15%",
        "search_url": f"https://www.linkedin.com/search/results/companies/?keywords={quote_plus(brand_name)}",
        "check_instructions": [
            f"Search LinkedIn for '{brand_name}' and check:",
            "1. Страница компании есть? Сколько фолловеров?",
            "2. Страница активна (свежие посты)?",
            "3. Thought leadership от сотрудников?",
            "4. Статьи о бренде? Вовлечение на постах?",
        ],
        "recommendations": [
            "Создать/оптимизировать страницу компании",
            "Регулярный thought-leadership контент",
            "Employee advocacy (шаринг сотрудниками)",
            "LinkedIn URL в schema sameAs",
        ],
    }


def check_other_platforms(brand_name: str) -> dict:
    """Check brand presence on additional platforms (incl. RU)."""
    platforms = {
        "Quora": f"https://www.quora.com/search?q={quote_plus(brand_name)}",
        "Stack Overflow": f"https://stackoverflow.com/search?q={quote_plus(brand_name)}",
        "GitHub": f"https://github.com/search?q={quote_plus(brand_name)}",
        "Crunchbase": f"https://www.crunchbase.com/textsearch?q={quote_plus(brand_name)}",
        "Product Hunt": f"https://www.producthunt.com/search?q={quote_plus(brand_name)}",
        "G2": f"https://www.g2.com/search?utf8=&query={quote_plus(brand_name)}",
        "Trustpilot": f"https://www.trustpilot.com/search?query={quote_plus(brand_name)}",
        # RU-контур: главные цитируемые RU-домены ((regional LLM B) любит RU-инфополе)
        "Habr": f"https://habr.com/ru/search/?q={quote_plus(brand_name)}",
        "vc.ru": f"https://vc.ru/search?query={quote_plus(brand_name)}",
        "Otzovik": f"https://otzovik.com/?search_text={quote_plus(brand_name)}",
    }

    return {
        "platform": "Other Platforms",
        "weight": "15%",
        "platforms_checked": {
            name: {
                "search_url": url,
                "check_instruction": f"Search for '{brand_name}' on {name}",
            }
            for name, url in platforms.items()
        },
        "recommendations": [
            "Профили на отраслевых платформах",
            "Отвечать на вопросы (Quora/Stack Overflow; RU — Habr Q&A, отраслевые ТГ-чаты)",
            "Отзывы на G2/Trustpilot; RU — Otzovik/Яндекс.Карты",
            "Crunchbase-профиль для B2B",
            "Open-source вклад на GitHub — авторитет у dev-аудитории",
            "RU: sustained-присутствие на Habr/vc.ru — training-сигнал для (regional LLM B)",
        ],
    }


def generate_brand_report(brand_name: str, domain: str = None) -> dict:
    """Generate a comprehensive brand mention report."""
    report = {
        "brand_name": brand_name,
        "domain": domain,
        "key_insight": "Brand mentions correlate 3x more strongly with AI visibility than backlinks (Ahrefs Dec 2025, 75K brands)",
        "platforms": {
            "youtube": check_youtube_presence(brand_name),
            "reddit": check_reddit_presence(brand_name),
            "wikipedia": check_wikipedia_presence(brand_name),
            "linkedin": check_linkedin_presence(brand_name),
            "other": check_other_platforms(brand_name),
        },
        "overall_recommendations": [
            "P1: YouTube — сильнейшая корреляция (0.737) с AI-цитатами. Обучающий контент.",
            "P2: Reddit — аутентичное присутствие в отраслевых сабреддитах; RU-аналог по весу — Habr/vc.ru.",
            "P3: Wikipedia (en+ru) — notability через прессу, затем статья + Wikidata.",
            "P4: LinkedIn — thought leadership основателей и сотрудников.",
            "P5: Review-платформы — G2/Trustpilot/Otzovik для social proof.",
            "Кросс-платформенно: единый NAP (Name, Address, Phone) везде.",
            "Schema: sameAs со ссылками на ВСЕ профили платформ.",
            "Мониторинг: алерты на упоминания бренда (RU-мониторинг LLM-ответов — workflow аудита в SKILL.md).",
        ],
    }
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python brand_scanner.py "<brand_name>" [domain]')
        print('Example: python brand_scanner.py "YourProduct" your-product.example')
        sys.exit(1)

    brand = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None

    print(json.dumps(generate_brand_report(brand, domain), indent=2, ensure_ascii=False, default=str))
