# Deep Research - Perplexity AI powered research with citations

Используй Perplexity AI для глубокого исследования тем с real-time веб поиском и цитированием источников.

## 🎯 Когда использовать

### ✅ Идеально для:

1. **Актуальная информация**
   - Последние новости и тренды
   - Текущее состояние рынка
   - Недавние изменения в технологиях
   - Real-time данные

2. **Исследования с источниками**
   - Нужны цитаты и ссылки
   - Важна точность информации
   - Требуется проверка фактов
   - Академические исследования

3. **Сравнительный анализ**
   - Сравнение технологий
   - Анализ конкурентов
   - Обзор рынка
   - Pros & cons различных решений

4. **Проверка фактов**
   - Верификация утверждений
   - Поиск противоречий
   - Оценка достоверности
   - Определение актуальности информации

### ❌ НЕ подходит для:

- Вопросы о внутреннем коде проекта (используй обычный Claude)
- Персональные данные или confidential info
- Задачи не требующие внешних источников
- Когда нужен мгновенный ответ без исследования

---

## 🚀 Использование

### Инструкции для Claude:

Когда пользователь просит провести исследование, используй Python helper:

```python
import sys
sys.path.append('${WORKSPACE}/tools')
from perplexity_helper import PerplexityClient

client = PerplexityClient()

# Основное исследование
result = client.research(
    query="Твой исследовательский вопрос",
    temperature=0.2  # Низкая для точности
)

print(result['content'])  # Результаты исследования

# Источники
for citation in result['citations']:
    print(f"Источник: {citation}")
```

### Типы исследований:

#### 1. Общее исследование
```python
result = client.research(
    query="What are the latest developments in AI agents for 2025?",
    return_citations=True
)
```

#### 2. Маркетинговое исследование
```python
result = client.market_research(
    topic="AI automation tools",
    aspects=[
        "market size and growth",
        "key players",
        "trends",
        "pricing models"
    ]
)
```

#### 3. Проверка фактов
```python
result = client.fact_check(
    claim="Claude 4 supports 1M token context window"
)
```

#### 4. Технический анализ
```python
result = client.tech_analysis(
    technology="FastAPI framework",
    depth="comprehensive"  # quick | standard | comprehensive
)
```

#### 5. Сравнение источников
```python
result = client.compare_sources(
    topic="Model Context Protocol (MCP)",
    sources=["anthropic.com", "github.com", "modelcontextprotocol.io"]
)
```

---

## 📋 Примеры использования

### Пример 1: Исследование технологии

**Пользователь:**
> "Изучи последние новости про Model Context Protocol и расскажи что нового"

**Claude:**
```python
result = client.research(
    query="Latest news and updates about Model Context Protocol (MCP) in 2025",
    return_citations=True
)

# Анализирует результаты
print("Последние обновления MCP:")
print(result['content'])

print("\nИсточники:")
for i, citation in enumerate(result['citations'], 1):
    print(f"{i}. {citation}")
```

### Пример 2: Маркетинговое исследование

**Пользователь:**
> "Проведи market research по AI coding assistants"

**Claude:**
```python
result = client.market_research(
    topic="AI coding assistants and IDEs",
    aspects=[
        "market size and growth rate",
        "major players (GitHub Copilot, Cursor, Claude Code)",
        "pricing models",
        "user adoption trends",
        "future outlook"
    ]
)

# Форматирует в структурированный отчёт
print("Market Research: AI Coding Assistants")
print("=" * 50)
print(result['content'])
```

### Пример 3: Fact-checking

**Пользователь:**
> "Проверь правда ли что Claude Sonnet 4.5 лучше GPT-4 в coding benchmarks"

**Claude:**
```python
result = client.fact_check(
    claim="Claude Sonnet 4.5 outperforms GPT-4 on coding benchmarks"
)

print("Fact Check Results:")
print(result['content'])
print("\nSources:")
for citation in result['citations']:
    print(f"- {citation}")
```

### Пример 4: Технический анализ

**Пользователь:**
> "Сделай deep dive в Anthropic's MCP protocol"

**Claude:**
```python
result = client.tech_analysis(
    technology="Anthropic Model Context Protocol (MCP)",
    depth="comprehensive"
)

print("Technical Deep Dive: MCP")
print("=" * 50)
print(result['content'])

print("\nKey Sources:")
for citation in result['citations']:
    print(f"- {citation}")
```

### Пример 5: Сравнительный анализ

**Пользователь:**
> "Сравни информацию о Cursor IDE из разных источников"

**Claude:**
```python
result = client.compare_sources(
    topic="Cursor AI IDE features and capabilities",
    sources=[
        "cursor.sh",
        "github.com",
        "producthunt.com",
        "techcrunch.com"
    ]
)

print("Source Comparison: Cursor IDE")
print("=" * 50)
print(result['content'])
```

---

## ⚙️ Параметры

### Temperature:
- **0.0-0.2** - Максимальная точность (fact-checking, research)
- **0.2-0.5** - Баланс точности и креативности (market research)
- **0.5-1.0** - Более креативный подход (brainstorming)

### Models:
- `llama-3.1-sonar-small-128k-online` - Быстрый, экономичный
- `llama-3.1-sonar-large-128k-online` - Рекомендуется (по умолчанию)
- `llama-3.1-sonar-huge-128k-online` - Максимальное качество

### Max Tokens:
- **1000-2000** - Краткий ответ
- **2000-4000** - Стандартный (по умолчанию)
- **4000-8000** - Детальный анализ

---

## 🔧 CLI команды

Альтернативно можно использовать через CLI:

```bash
# Basic research
python tools/perplexity_helper.py research "What are AI agents?"

# Market research
python tools/perplexity_helper.py market "AI automation tools"

# Fact check
python tools/perplexity_helper.py fact-check "Claude 4 has 1M context"

# Tech analysis
python tools/perplexity_helper.py tech "FastAPI" --depth comprehensive

# Compare sources
python tools/perplexity_helper.py compare "MCP protocol" --sources "anthropic.com" "github.com"
```

---

## 📊 Best Practices

### 1. Формулирование запросов:

✅ **Хорошо:**
```
"Compare AI coding assistants released in 2024-2025:
features, pricing, and user satisfaction"
```

❌ **Плохо:**
```
"coding tools"
```

### 2. Использование system prompts:

```python
result = client.research(
    query="AI agent frameworks",
    system_prompt="""
    Focus on:
    1. Open source frameworks
    2. Production-ready solutions
    3. Active development and community
    4. Enterprise adoption

    Prioritize recent information (2024-2025).
    """
)
```

### 3. Обработка результатов:

```python
# Всегда проверяй citations
if result['citations']:
    print("\nВажно! Информация основана на источниках:")
    for citation in result['citations']:
        print(f"- {citation}")
else:
    print("\nОсторожно: Нет цитат для этого ответа")
```

### 4. Комбинирование с другими инструментами:

```python
# 1. Research с Perplexity
research_result = perplexity_client.research("AI agent frameworks 2025")

# 2. Дополнительный анализ с Claude
# Claude видит research_result и может добавить свой анализ

# 3. Создание задачи в Manus для долгосрочного мониторинга
manus_client.create_task(
    prompt=f"Monitor updates on: {research_result['content'][:200]}...",
    mode="speed"
)
```

---

## 🎯 Типичные сценарии

### Сценарий 1: Competitive Analysis

```python
# Исследуй конкурентов
competitor_analysis = client.market_research(
    topic="AI coding assistants competitors: GitHub Copilot, Cursor, Windsurf",
    aspects=[
        "features comparison",
        "pricing models",
        "market share",
        "user reviews",
        "unique selling points"
    ]
)
```

### Сценарий 2: Technology Decision

```python
# Помощь в выборе технологии
tech_comparison = client.compare_sources(
    topic="FastAPI vs Flask vs Django for microservices",
    sources=[
        "official documentation",
        "stackoverflow.com",
        "medium.com",
        "realpython.com"
    ]
)
```

### Сценарий 3: Trend Analysis

```python
# Анализ трендов
trends = client.research(
    query="AI development trends in 2025: agents, MCP, multimodal",
    system_prompt="""
    Focus on:
    - Adoption rates and statistics
    - Major players and investments
    - Technical breakthroughs
    - Industry predictions

    Provide data-driven insights with sources.
    """
)
```

---

## 📚 Документация

- **Perplexity API:** https://docs.perplexity.ai/
- **Helper код:** `tools/perplexity_helper.py`
- **API Reference:** https://docs.perplexity.ai/reference

---

## 💡 Tips

1. **Всегда включай return_citations=True** для важных исследований
2. **Используй низкую temperature (0.1-0.2)** для fact-checking
3. **Указывай временные рамки** в запросе ("in 2024-2025", "recent developments")
4. **Проверяй даты источников** - информация может быть устаревшей
5. **Комбинируй с Memory MCP** - сохраняй важные результаты исследований

---

## Примеры для быстрого старта

### Quick Research:
```
/deep-research "Latest AI agent frameworks 2025"
```

### Market Analysis:
```
/deep-research "Market analysis: AI automation tools for developers"
```

### Fact Check:
```
/deep-research "Verify: Does Claude 4 have vision capabilities?"
```

### Tech Comparison:
```
/deep-research "Compare: React vs Vue vs Svelte in 2025"
```

---

**Готово! Используй Perplexity для актуальных исследований с источниками!** 🔍
