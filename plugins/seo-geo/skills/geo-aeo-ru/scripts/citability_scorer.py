#!/usr/bin/env python
"""
Citability Scorer — механический скоринг пассажей страницы на AI-цитируемость (0-100).

Основано на research: оптимальные AI-цитируемые пассажи —
- 134-167 слов;
- self-contained (извлекаемы без контекста);
- насыщены фактами и конкретными цифрами;
- со структурой «прямой ответ в начале».

Источник: zubair-trabzada/geo-seo-claude (MIT), адаптация для skills/geo-aeo-ru:
- Windows: python (не python3), UTF-8 stdout (cp1251 fix), lxml опционален;
- RU-паттерны: определения («X — это»), «по данным/согласно», RU-местоимения,
  RU-переходы («во-первых», «кроме того») и счётные слова («пользователей», «компаний»).

Usage: python citability_scorer.py <url>
"""

import sys
import json
import re
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1251 fix

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: pip install requests beautifulsoup4")
    sys.exit(1)

try:
    import lxml  # noqa: F401
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def score_passage(text: str, heading: Optional[str] = None) -> dict:
    """Score a single passage for AI citability (0-100)."""
    words = text.split()
    word_count = len(words)

    scores = {
        "answer_block_quality": 0,
        "self_containment": 0,
        "structural_readability": 0,
        "statistical_density": 0,
        "uniqueness_signals": 0,
    }

    # === 1. Answer Block Quality (30%) ===
    abq_score = 0

    # Definition patterns (EN + RU)
    definition_patterns = [
        r"\b\w+\s+is\s+(?:a|an|the)\s",
        r"\b\w+\s+refers?\s+to\s",
        r"\b\w+\s+means?\s",
        r"\b\w+\s+(?:can be |are )?defined\s+as\s",
        r"\bin\s+(?:simple|other)\s+(?:terms|words)\s*,",
        r"[\w»)]\s+—\s+это\s",              # RU: «X — это ...»
        r"\bназывается\s",                   # RU
        r"\bпростыми\s+словами\s*[,:—]",     # RU
    ]
    for pattern in definition_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            abq_score += 15
            break

    # Answer appears early (first 60 words)
    first_60_words = " ".join(words[:60])
    if any(
        re.search(p, first_60_words, re.IGNORECASE)
        for p in [
            r"\b(?:is|are|was|were|means?|refers?)\b",
            r"—\s+это\b",
            r"\d+\s*%",
            r"[$€₽]\s?[\d,\s]+",
            r"\d+\s+(?:million|billion|thousand|млн|млрд|тыс)",
        ]
    ):
        abq_score += 15

    # Question-based heading bonus
    if heading and heading.endswith("?"):
        abq_score += 10

    # Clear, direct sentence structure
    sentences = re.split(r"[.!?]+", text)
    short_clear_sentences = sum(1 for s in sentences if 5 <= len(s.split()) <= 25)
    if sentences:
        clarity_ratio = short_clear_sentences / len(sentences)
        abq_score += int(clarity_ratio * 10)

    # Has specific, quotable claim (EN + RU)
    if re.search(
        r"(?:according to|research shows|studies? (?:show|indicate|suggest|found)|data (?:shows|indicates|suggests)"
        r"|по\s+данным|по\s+оценке|согласно\s+(?:исследованию|отчёту|отчету|данным)|исследовани[ея]\s+показал)",
        text,
        re.IGNORECASE,
    ):
        abq_score += 10

    scores["answer_block_quality"] = min(abq_score, 30)

    # === 2. Self-Containment (25%) ===
    sc_score = 0

    # Optimal word count (134-167 words)
    if 134 <= word_count <= 167:
        sc_score += 10
    elif 100 <= word_count <= 200:
        sc_score += 7
    elif 80 <= word_count <= 250:
        sc_score += 4
    elif word_count < 30 or word_count > 400:
        sc_score += 0
    else:
        sc_score += 2

    # Low pronoun density (EN + RU)
    pronoun_count = len(
        re.findall(
            r"\b(?:it|they|them|their|this|that|these|those|he|she|his|her"
            r"|он|она|оно|они|их|его|её|ее|это|этот|эта|эти|тот|та|те)\b",
            text,
            re.IGNORECASE,
        )
    )
    if word_count > 0:
        pronoun_ratio = pronoun_count / word_count
        if pronoun_ratio < 0.02:
            sc_score += 8
        elif pronoun_ratio < 0.04:
            sc_score += 5
        elif pronoun_ratio < 0.06:
            sc_score += 3

    # Contains named entities (латиница + кириллица proper nouns)
    proper_nouns = len(
        re.findall(r"\b[A-ZА-ЯЁ][a-zа-яё]+(?:\s+[A-ZА-ЯЁ][a-zа-яё]+)*\b", text)
    )
    if proper_nouns >= 3:
        sc_score += 7
    elif proper_nouns >= 1:
        sc_score += 4

    scores["self_containment"] = min(sc_score, 25)

    # === 3. Structural Readability (20%) ===
    sr_score = 0

    if sentences:
        avg_sentence_length = word_count / len(sentences)
        if 10 <= avg_sentence_length <= 20:
            sr_score += 8
        elif 8 <= avg_sentence_length <= 25:
            sr_score += 5
        else:
            sr_score += 2

    # List-like transitions (EN + RU)
    if re.search(
        r"(?:first|second|third|finally|additionally|moreover|furthermore"
        r"|во-первых|во-вторых|в-третьих|наконец|кроме\s+того|более\s+того|также)",
        text,
        re.IGNORECASE,
    ):
        sr_score += 4

    # Numbered items
    if re.search(r"(?:\d+[\.\)]\s|\b(?:step|tip|point|шаг|совет|пункт)\s+\d+)", text, re.IGNORECASE):
        sr_score += 4

    # Paragraph breaks
    if "\n" in text:
        sr_score += 4

    scores["structural_readability"] = min(sr_score, 20)

    # === 4. Statistical Density (15%) ===
    sd_score = 0

    pct_count = len(re.findall(r"\d+(?:[.,]\d+)?\s*%", text))
    sd_score += min(pct_count * 3, 6)

    money_count = len(
        re.findall(
            r"(?:[$€]\s?[\d,\s]+(?:\.\d+)?(?:\s*(?:million|billion|M|B|K))?"
            r"|\d[\d\s]*(?:[.,]\d+)?\s*(?:₽|руб|рублей|млн\s*руб|млрд\s*руб))",
            text,
        )
    )
    sd_score += min(money_count * 3, 5)

    # Numbers with context (EN + RU counters)
    number_count = len(
        re.findall(
            r"\b\d+(?:[,.\s]\d{3})*(?:[.,]\d+)?\s+"
            r"(?:users|customers|pages|sites|companies|businesses|people|percent|times|x\b"
            r"|пользовател\w+|клиент\w+|компани\w+|человек|стран\w*|раз[а]?\b)",
            text,
            re.IGNORECASE,
        )
    )
    sd_score += min(number_count * 2, 4)

    # Year references (recency)
    year_count = len(re.findall(r"\b20(?:2[0-9]|1\d)\b", text))
    if year_count > 0:
        sd_score += 2

    # Named sources (EN + RU)
    source_patterns = [
        r"(?:according to|per|from|by)\s+[A-Z]",
        r"(?:по\s+данным|по\s+оценке|согласно)\s+[A-ZА-ЯЁ]",
        r"(?:Gartner|Forrester|McKinsey|Harvard|Stanford|MIT|Google|Microsoft|OpenAI|Anthropic"
        r"|Сбер|Яндекс|ВШЭ|РАНХиГС|Росстат)",
        r"\([A-ZА-ЯЁ][a-zа-яё]+(?:\s+\d{4})?\)",
    ]
    for pattern in source_patterns:
        if re.search(pattern, text):
            sd_score += 2

    scores["statistical_density"] = min(sd_score, 15)

    # === 5. Uniqueness Signals (10%) ===
    us_score = 0

    # Original data indicators (EN + RU)
    if re.search(
        r"(?:our (?:research|study|data|analysis|survey|findings)|we (?:found|discovered|analyzed|surveyed|measured)"
        r"|наш[еи]?\s+(?:исследование|данные|анализ|опрос)|мы\s+(?:выяснили|обнаружили|проанализировали|опросили|замерили))",
        text,
        re.IGNORECASE,
    ):
        us_score += 5

    # Case study / example indicators (EN + RU)
    if re.search(
        r"(?:case study|for example|for instance|in practice|real-world|hands-on"
        r"|например|к\s+примеру|на\s+практике|кейс)",
        text,
        re.IGNORECASE,
    ):
        us_score += 3

    # Specific tool/product mentions
    if re.search(r"(?:using|with|via|through|через|с\s+помощью)\s+[A-ZА-ЯЁ][a-zа-яё]+", text):
        us_score += 2

    scores["uniqueness_signals"] = min(us_score, 10)

    # === Total ===
    total = sum(scores.values())

    if total >= 80:
        grade, label = "A", "Highly Citable"
    elif total >= 65:
        grade, label = "B", "Good Citability"
    elif total >= 50:
        grade, label = "C", "Moderate Citability"
    elif total >= 35:
        grade, label = "D", "Low Citability"
    else:
        grade, label = "F", "Poor Citability"

    return {
        "heading": heading,
        "word_count": word_count,
        "total_score": total,
        "grade": grade,
        "label": label,
        "breakdown": scores,
        "preview": " ".join(words[:30]) + ("..." if word_count > 30 else ""),
    }


def analyze_page_citability(url: str) -> dict:
    """Analyze all content blocks on a page for citability."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch page: {str(e)}"}

    soup = BeautifulSoup(response.text, PARSER)

    for element in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "form"]):
        element.decompose()

    # Extract content blocks (heading → paragraphs until next heading)
    blocks = []
    current_heading = "Introduction"
    current_paragraphs = []

    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table"]):
        if element.name.startswith("h"):
            if current_paragraphs:
                combined = " ".join(current_paragraphs)
                if len(combined.split()) >= 20:
                    blocks.append({"heading": current_heading, "content": combined})
            current_heading = element.get_text(strip=True)
            current_paragraphs = []
        else:
            text = element.get_text(strip=True)
            if text and len(text.split()) >= 5:
                current_paragraphs.append(text)

    if current_paragraphs:
        combined = " ".join(current_paragraphs)
        if len(combined.split()) >= 20:
            blocks.append({"heading": current_heading, "content": combined})

    scored_blocks = [score_passage(b["content"], b["heading"]) for b in blocks]

    if scored_blocks:
        avg_score = sum(b["total_score"] for b in scored_blocks) / len(scored_blocks)
        top_blocks = sorted(scored_blocks, key=lambda x: x["total_score"], reverse=True)[:5]
        bottom_blocks = sorted(scored_blocks, key=lambda x: x["total_score"])[:5]
        optimal_count = sum(1 for b in scored_blocks if 134 <= b["word_count"] <= 167)
    else:
        avg_score, top_blocks, bottom_blocks, optimal_count = 0, [], [], 0

    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for block in scored_blocks:
        grade_dist[block["grade"]] += 1

    return {
        "url": url,
        "total_blocks_analyzed": len(scored_blocks),
        "average_citability_score": round(avg_score, 1),
        "optimal_length_passages": optimal_count,
        "grade_distribution": grade_dist,
        "top_5_citable": top_blocks,
        "bottom_5_citable": bottom_blocks,
        "all_blocks": scored_blocks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python citability_scorer.py <url>")
        print("Returns JSON with citability analysis for all content blocks.")
        sys.exit(1)

    print(json.dumps(analyze_page_citability(sys.argv[1]), indent=2, ensure_ascii=False, default=str))
