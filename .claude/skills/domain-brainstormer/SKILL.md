---
name: domain-brainstormer
description: "Domain name ideas + availability checks. Triggers: «domain name», «is the domain free», «what to name the site»."
---

# Domain Name Brainstormer Skill

## Overview

Генерация креативных доменных имен и проверка доступности.

## When to Use

- Запуск нового продукта/стартапа
- Ребрендинг
- Поиск доменного имени
- Brainstorm naming

## Domain Generation Strategies

### 1. Word Combinations

```python
def combine_words(word1: str, word2: str) -> list:
    """Generate combinations of two words"""
    return [
        f"{word1}{word2}",           # taskflow
        f"{word2}{word1}",           # flowtask
        f"{word1}-{word2}",          # task-flow
        f"{word1}.{word2}",          # task.flow
        f"get{word1}",               # gettask
        f"{word1}app",               # taskapp
        f"{word1}io",                # taskio
        f"{word1}hq",                # taskhq
        f"{word1}lab",               # tasklab
        f"my{word1}",                # mytask
        f"{word1}ly",                # taskly
        f"{word1}ify",               # taskify
        f"use{word1}",               # usetask
        f"try{word1}",               # trytask
    ]
```

### 2. Prefix/Suffix Patterns

```python
PREFIXES = [
    "get", "go", "my", "our", "use", "try", "the", "hey",
    "super", "mega", "ultra", "pro", "smart", "easy", "quick",
    "one", "open", "all", "any", "ever", "on", "up", "in"
]

SUFFIXES = [
    "app", "io", "ly", "ify", "hub", "hq", "lab", "base",
    "flow", "kit", "pad", "box", "spot", "zone", "way", "zen",
    "fy", "er", "co", "ai", "x", "up", "me", "now"
]

def generate_with_affixes(word: str) -> list:
    """Generate domain ideas with prefixes/suffixes"""
    ideas = []
    for prefix in PREFIXES:
        ideas.append(f"{prefix}{word}")
    for suffix in SUFFIXES:
        ideas.append(f"{word}{suffix}")
    return ideas
```

### 3. Phonetic Patterns

```python
def generate_phonetic(concept: str) -> list:
    """Generate phonetic variations"""
    variations = []

    # Remove vowels
    consonants = ''.join([c for c in concept if c.lower() not in 'aeiou'])
    variations.append(consonants)

    # Double letters
    variations.append(concept.replace('t', 'tt').replace('s', 'ss'))

    # K instead of C
    variations.append(concept.replace('c', 'k'))

    # I instead of Y
    variations.append(concept.replace('y', 'i'))

    # Abbreviation
    words = concept.split()
    if len(words) > 1:
        abbrev = ''.join([w[0] for w in words])
        variations.append(abbrev)

    return variations
```

### 4. AI-Powered Generation

```python
def generate_with_ai(concept: str, style: str = "tech") -> list:
    """Generate creative names using LLM"""
    prompt = f"""Generate 20 creative, memorable domain name ideas for a {concept}.

Style: {style}
Requirements:
- Short (ideally under 12 characters)
- Easy to spell and pronounce
- Memorable and brandable
- Available TLDs: .com, .io, .co, .app

Output format: just the domain names, one per line, without TLD.
"""
    return call_llm(prompt).split('\n')
```

## Domain Availability Check

### Using WHOIS

```python
import whois

def check_domain(domain: str) -> dict:
    """Check domain availability"""
    try:
        w = whois.whois(domain)
        return {
            "domain": domain,
            "available": False,
            "registrar": w.registrar,
            "expiration": str(w.expiration_date),
        }
    except whois.parser.PywhoisError:
        return {
            "domain": domain,
            "available": True,
        }
```

### Using API Services

```python
import requests

def check_domains_bulk(domains: list, api_key: str) -> list:
    """Check multiple domains via API"""
    results = []

    for domain in domains:
        response = requests.get(
            f"https://api.domainr.com/v2/status",
            params={
                "domain": domain,
                "client_id": api_key
            }
        )
        data = response.json()

        results.append({
            "domain": domain,
            "available": "inactive" in data.get("status", []),
            "status": data.get("status")
        })

    return results
```

### Check Multiple TLDs

```python
TLDS = ['.com', '.io', '.co', '.app', '.dev', '.ai', '.so', '.to']

def check_all_tlds(name: str) -> list:
    """Check name across popular TLDs"""
    results = []

    for tld in TLDS:
        domain = f"{name}{tld}"
        result = check_domain(domain)
        results.append(result)

    return results
```

## Complete Workflow

```python
def brainstorm_domains(concept: str, keywords: list) -> dict:
    """Complete domain brainstorming workflow"""

    # 1. Generate ideas
    ideas = set()

    # Word combinations
    for i, word1 in enumerate(keywords):
        for word2 in keywords[i+1:]:
            ideas.update(combine_words(word1, word2))

    # Affixes
    for keyword in keywords:
        ideas.update(generate_with_affixes(keyword))

    # Phonetic variations
    for keyword in keywords:
        ideas.update(generate_phonetic(keyword))

    # AI generated
    ai_ideas = generate_with_ai(concept)
    ideas.update(ai_ideas)

    # 2. Filter
    # Remove too long
    ideas = {name for name in ideas if len(name) <= 15}
    # Remove numbers and special chars (except -)
    ideas = {name for name in ideas if name.isalnum() or '-' in name}

    # 3. Check availability
    available = []
    taken = []

    for name in ideas:
        result = check_domain(f"{name}.com")
        if result['available']:
            available.append(name)
        else:
            taken.append(name)

    # 4. Score available domains
    scored = []
    for name in available:
        score = score_domain(name)
        scored.append({"name": name, "score": score})

    scored.sort(key=lambda x: x['score'], reverse=True)

    return {
        "total_generated": len(ideas),
        "available": scored[:20],
        "taken": taken[:10],
    }
```

## Domain Scoring

```python
def score_domain(name: str) -> int:
    """Score domain name quality (0-100)"""
    score = 100

    # Length penalty
    if len(name) > 10:
        score -= (len(name) - 10) * 5

    # Hyphens penalty
    score -= name.count('-') * 10

    # Numbers penalty
    if any(c.isdigit() for c in name):
        score -= 15

    # Hard to spell penalty (double letters, unusual combinations)
    if any(name.count(c) > 2 for c in name):
        score -= 10

    # Bonus for .com memorable patterns
    if name.endswith(('io', 'ly', 'fy', 'er')):
        score += 5

    return max(0, min(100, score))
```

## Output Template

```markdown
# Domain Name Ideas for: [Concept]

## Top Available Domains

| Domain | Score | TLDs Available |
|--------|-------|----------------|
| taskflow | 95 | .io, .co, .app |
| flowtask | 90 | .com, .io |
| gettask | 85 | .io, .co |

## Premium Domains (Taken but valuable)
These might be available for purchase:
- taskflow.com (check aftermarket)
- flowhq.com (check aftermarket)

## Alternative TLDs
If .com taken, consider:
- .io - Tech/startups
- .co - Startups
- .app - Apps
- .dev - Developer tools
- .ai - AI products

## Recommendations
1. **Best overall:** `taskflow.io`
2. **Most brandable:** `flowhq.com`
3. **Best available:** `gettask.co`
```

## Tips

1. **Shorter is better** - aim for 6-10 chars
2. **.com first** - всё ещё самый ценный TLD
3. **Easy to spell** - избегай сложных слов
4. **No hyphens** - if possible
5. **Check trademarks** - перед покупкой
6. **Social handles** - проверь доступность в соцсетях
7. **Buy early** - домены дорожают
