---
name: perplexity
description: "Perplexity AI API Skill"
---

# Perplexity AI API Skill

## Overview

Expert skill for Perplexity AI — specialized in web search and research with real-time information.

## ⭐ ПРЕДПОЧТИТЕЛЬНЫЙ СПОСОБ: pplx-max.py через подписку Max

**Используй pplx-max.py wrapper по умолчанию** — это даёт доступ к Claude Opus 4.7 Thinking + reasoning mode через подписку Perplexity Max (без API quota, без лимитов биллинга).

### Quick start

```bash
# Reasoning mode + Claude Opus 4.7 Thinking (default)
python ~/.claude/skills/perplexity/pplx-max.py "your deep question"

# Pro mode (broader search, default model claude-4.7-opus)
python ~/.claude/skills/perplexity/pplx-max.py --mode pro "broad search"

# Deep research mode (slow, comprehensive)
python ~/.claude/skills/perplexity/pplx-max.py --mode "deep research" "research topic"

# Override model explicitly
python ~/.claude/skills/perplexity/pplx-max.py --model gpt-5.5 "query"
```

Output: answer text + numbered sources with URLs.

### Доступные модели

**reasoning mode** (для глубокого анализа):
- `claude-4.7-opus-thinking` (default — лучший reasoning)
- `gpt-5.5-thinking`
- `kimi-k2.6-thinking`

**pro mode** (для поиска):
- `claude-4.7-opus` (default)
- `claude-4.6-sonnet`
- `gpt-5.5` / `gpt-5.4`
- `gemini-3.1-pro`
- `sonar-2`

### Конфигурация (уже настроена)

```bash
# В ~/.claude/.credentials.master.env
PERPLEXITY_COOKIES='{"__Secure-next-auth.session-token":"...","__cf_bm":"..."}'
```

Cookies нужны от залогиненного аккаунта Perplexity Max. Срок жизни ~30 дней — обновлять при истечении через DevTools → Application → Cookies → Export.

### Когда использовать pplx-max vs API

| Сценарий | Инструмент |
|----------|-----------|
| Глубокий research с reasoning | `pplx-max.py --mode reasoning` (Opus 4.7 thinking) |
| Быстрый факт-чек | `pplx-max.py --mode pro` |
| Comprehensive multi-source | `pplx-max.py --mode "deep research"` |
| CI/CD автоматизация | API key (sonar-pro) — нет cookies |

### Параллельные запросы

Несколько pplx-max в фоне ускоряют research × 3-4 раза:

```bash
nohup python ~/.claude/skills/perplexity/pplx-max.py "query 1" > /tmp/q1.log 2>&1 &
nohup python ~/.claude/skills/perplexity/pplx-max.py "query 2" > /tmp/q2.log 2>&1 &
nohup python ~/.claude/skills/perplexity/pplx-max.py "query 3" > /tmp/q3.log 2>&1 &
wait
```

### Гочеты

- **UTF-8 на Windows**: pplx-max.py содержит `sys.stdout.reconfigure(encoding='utf-8')` — без этого падает на cp1251 при кириллице.
- **Ответ — это generator/dict**: используется `stream=False` для возврата dict с ключом `answer`. Если `stream=True` — генератор chunks (последний chunk содержит финальный ответ).
- **Pip пакет**: `perplexity` (helallao/perplexity-ai). Класс `Client` (не `Perplexity`!).
- **Cookies формат**: JSON-объект. **Обязателен только `__Secure-next-auth.session-token`** — `__cf_bm` опционален и быстро устаревает.
- **Производительность**: reasoning mode ~30-90s, pro mode ~10-30s, deep research ~60-180s.
- **chunks structure**: `result['chunks']` — список из словарей (с `url`, `title`) ИЛИ из строк. Wrapper парсит оба варианта.

---

## ⭐ Workflow: фактчекинг non-fiction статей и книг

Реальный сценарий из работы над книгой User: после internal fact-check пайплайна получаешь FACT-REPORT.md с флагами FABRICATION / DRIFT / NOT_FOUND. Перед тем как удалять — проверь через Perplexity Max.

### Пять типов ошибок, которые ловит Perplexity Max

| Тип | Пример из практики | Как ловится |
|-----|--------------------|-------------|
| **Фабрикация** | ConsultingFirm1 «3x успешность с change management» — цифра не существует | Запрос «confirm ConsultingFirm1 finding X» → «I could not verify» + список реальных цифр (12% vs 5%, ~2.4×) |
| **Source mix-up** | «ConsultingFirm2 обзор 2026, 5%/60%» — реально это «Widening AI Value Gap» сентябрь 2025 | Запрос с цифрами → правильное название отчёта + URL |
| **Name correction** | "Person A" → real author name; misspelled name → corrected | Запрос про человека → реальное имя в источниках |
| **Factual error** | IBM PC «1985» → реально 1981 (запуск 12 августа 1981) | Запрос «when was IBM PC launched» → точная дата |
| **False fabrication flag** | Cambridge «Feedback of Flattery» — fact-checker пометил как fabrication, но исследование РЕАЛЬНОЕ | Запрос «does X study exist» → URL + полная цитата |

### Pattern: триаж FABRICATION-флагов

```bash
# Для каждой главы с BLOCK вердиктом:
# 1. Прочитать FACT-REPORT.md, выделить FABRICATION items
# 2. Запустить параллельные pplx-max queries:

for claim in "$@"; do
  nohup python ~/.claude/skills/perplexity/pplx-max.py \
    "Verify: $claim. Provide URL if real, or confirm fabrication." \
    > "/tmp/pplx-$$-$RANDOM.log" 2>&1 &
done
wait

# 3. Применить фиксы:
#    - Если REAL → добавить в SOURCES.md, оставить текст
#    - Если FABRICATION → удалить или заменить на верифицированную цифру
#    - Если NAME WRONG → исправить
```

### Промпт-формулы для фактчекинга

| Цель | Формула |
|------|---------|
| Подтверждение существования | `"Does X study/report by Y exist? URL if yes, no if fabrication."` |
| Точные цифры | `"Confirm exact figures from X report: A%, B%. Provide URL."` |
| Имя автора | `"Who is the lead author of X publication? Full name and affiliation."` |
| Дата события | `"When exactly was X launched/published? Exact date with source."` |
| Real quote | `"Did Y publicly say Z? Provide direct quote and source link."` |

### Source-добавление в SOURCES.md после верификации

Если Perplexity подтвердил спорный факт — добавь источник в SOURCES.md по шаблону:

```markdown
- **«Точное название отчёта»** — Org, Date.
  https://exact-url
  **Что важно:** конкретная цитата/цифра из отчёта (по чему его вспоминать).
  **Какой тезис главы поддерживает:** один-два предложения о том, что именно подтверждается.
```

После этого fact-checker при следующем прогоне найдёт источник в SOURCES.md и снимет FABRICATION-флаг.

### Когда НЕ доверять Perplexity Max

1. **Контркстно близкие, но разные исследования** — Perplexity иногда подтверждает «похожий» факт, не указывая что это другой отчёт. Всегда проверяй точное название.
2. **Regional sources** — for non-English content, indexing quality varies; for verification of regional companies/figures, add an explicit "Regional sources OK" hint to the prompt.
3. **Закрытые отчёты** — Gartner / Forrester / IDC paywalled. Perplexity видит только пресс-релизы — детали могут отличаться.
4. **Статистика < 6 месяцев старая** — для совсем свежих данных лучше `--mode "deep research"` или прямой первоисточник.

---

## Старый способ: API ключ (если нет подписки Max)

## API Key

```bash
# API ключи: ~/.claude/.credentials.master.env
# Переменная: PERPLEXITY_API_KEY
PERPLEXITY_API_KEY=os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL=sonar
```

## When to Use Perplexity

**Best for:**
- Real-time web search
- Current events and news
- Research with citations
- Fact-checking
- Market research
- Competitive analysis
- Technical documentation lookup

**Advantages:**
- Always up-to-date information
- Source citations included
- No hallucinations on facts
- Multiple search modes
- Fast responses

## Dependencies

```bash
pip install openai  # Uses OpenAI-compatible API
```

## Models

| Model | Context | Best For |
|-------|---------|----------|
| `sonar` | 128K | General search, balanced |
| `sonar-pro` | 200K | Deep research, complex queries |
| `sonar-reasoning` | 128K | Multi-step analysis |

## Basic Usage

### Setup Client

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv('PERPLEXITY_API_KEY'),
    base_url="https://api.perplexity.ai"
)

MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')
```

### Simple Search

```python
def perplexity_search(query: str):
    """
    Search web with Perplexity.

    Returns answer with citations.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": query}
        ]
    )

    return response.choices[0].message.content

# Usage
result = perplexity_search("What are the latest AI developments in 2025?")
```

### Deep Research

```python
def deep_research(topic: str, focus: str = "comprehensive"):
    """
    Comprehensive research on a topic.

    Args:
        topic: Research topic
        focus: "comprehensive", "technical", "business", "academic"
    """
    system_prompts = {
        "comprehensive": "Provide a thorough analysis with multiple perspectives.",
        "technical": "Focus on technical details, implementations, and specifications.",
        "business": "Focus on market trends, competitors, and business implications.",
        "academic": "Focus on academic sources, research papers, and scientific evidence."
    }

    response = client.chat.completions.create(
        model="sonar-pro",  # Use pro for deep research
        messages=[
            {"role": "system", "content": system_prompts.get(focus, system_prompts["comprehensive"])},
            {"role": "user", "content": f"Research this topic thoroughly: {topic}"}
        ]
    )

    return response.choices[0].message.content
```

### Search with Citations

```python
def search_with_sources(query: str):
    """Search and extract sources."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Always cite your sources with URLs. Format: [Source Title](URL)"
            },
            {"role": "user", "content": query}
        ]
    )

    content = response.choices[0].message.content

    # Extract citations if available in response metadata
    citations = []
    if hasattr(response.choices[0].message, 'citations'):
        citations = response.choices[0].message.citations

    return {
        "answer": content,
        "citations": citations
    }
```

### Fact Check

```python
def fact_check(claim: str):
    """Verify a claim with sources."""

    prompt = f"""Fact-check this claim:

"{claim}"

Provide:
1. Verdict: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIABLE
2. Evidence for and against
3. Sources with URLs
4. Context and nuance"""

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

### Compare Options

```python
def compare_options(options: list, criteria: list = None):
    """Compare multiple options (products, tools, frameworks)."""

    criteria_str = ", ".join(criteria) if criteria else "features, pricing, pros/cons"

    prompt = f"""Compare these options:
{', '.join(options)}

Criteria: {criteria_str}

Create a comparison table and provide recommendations."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# Usage
result = compare_options(
    ["React", "Vue", "Svelte"],
    ["performance", "learning curve", "ecosystem", "job market"]
)
```

### Market Research

```python
def market_research(industry: str, aspects: list = None):
    """Research market/industry trends."""

    aspects_str = ", ".join(aspects) if aspects else "trends, key players, opportunities, challenges"

    prompt = f"""Market research for: {industry}

Analyze:
{aspects_str}

Include recent data, statistics, and sources."""

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

### Technical Documentation

```python
def find_docs(technology: str, topic: str):
    """Find documentation and examples."""

    prompt = f"""Find documentation for {technology} about: {topic}

Provide:
1. Official documentation links
2. Key concepts explained
3. Code examples
4. Common patterns/best practices"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

## Slash Commands Integration

```bash
# Quick search
/ai-search "query"

# Deep research
/deep-research "topic"
```

## Use Cases

| Scenario | Function |
|----------|----------|
| Quick question | `perplexity_search()` |
| Deep dive | `deep_research()` with sonar-pro |
| Verify facts | `fact_check()` |
| Compare tools | `compare_options()` |
| Industry analysis | `market_research()` |
| API docs lookup | `find_docs()` |

## Tips

1. **sonar-pro** - для глубокого исследования
2. **sonar** - для быстрых запросов
3. **Специфичные вопросы** - лучше чем общие
4. **Просите источники** - всегда включай в промпт
5. **Текущие события** - Perplexity лучше чем LLMs
6. **Технические темы** - отлично для документации
