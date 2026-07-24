# Тактики попадания в AI-ответы (полный список с приоритетами)

> Все цифры — из `[local-source]` (разделы 2, 3, 5). Не выдумывай.

## Princeton GEO study — что работает (с числами)

**Aggarwal et al.**, *GEO: Generative Engine Optimization*, arXiv:2311.09735, KDD 2024.
9 тактик протестированы на **GEO-bench (10K queries, 8K/1K/1K сплит)**. Метрика —
**Position-Adjusted Word Count** (сколько слов источника попало в финальный ответ, с учётом позиции).

**Работает (+30-40%):**

| Тактика | Эффект | Объяснение |
|---------|--------|------------|
| **Quotation Addition** | +30-40% | релевантные цитаты от других источников |
| **Statistics Addition** | +30-40% | числа, проценты, конкретика |
| **Cite Sources** | +30-40% | ссылки на авторитетные источники внутри контента |

**Работает умеренно (+15-30%):** Fluency Optimization, Easy-to-Understand (упрощение языка).

**НЕ работает или слабо:**
- **Keyword Stuffing** — «offer little to no improvement» (**противоречит classic SEO!**)
- Authoritative tone без подтверждений — «no significant improvement»
- Unique Words — минимально · Technical Terms — ограниченно

**Real-world:** проверено на Perplexity.ai, улучшения до **37%**. Эффективность тактик
**варьируется по доменам** (HEALTH ≠ FACTUAL) — domain-specific optimization обязателен.

## Контент-стратегия: как писать

1. **BLUF (Bottom Line Up Front)** — главный ответ в первых 100 словах. **90%** выигравших
   Perplexity-цитат соблюдают это.
2. **Chunk-friendly структура** — блоки по 150 слов, semantically coherent, понятны независимо.
   Heading-driven separation, одна идея на параграф, списки как natural split points.
   Открывающее предложение блока сильно влияет на embedding similarity при retrieval.
3. **Density of claims** — один параграф = одно проверяемое утверждение с числом или цитатой.
4. **Original research** — корреляция **0.79** с LLM visibility (Organic Labs). Свои данные/опросы —
   самый мощный citation-магнит (никто другой не может процитировать первоисточник кроме тебя).
5. **Recency stamps** — публикуй даты, обновляй явно («Updated May 2026» в заголовке). Perplexity:
   контент за 30 дней → **×3.2** больше цитат; за 3 месяца — 6 cites/page vs 3.6 у устаревшего.
6. **FAQ-секции** — преоптимизированы под Q&A retrieval (готовая пара question→answer для chunking).
7. **Comparison-контент** («vs», «best», «top») — LLM-friendly.

### Структура страницы (шаблон)

```
<H1> — главный entity / question
<TLDR/Summary> — BLUF, 50-100 слов, прямой ответ
<H2> — раздел
   <Paragraph> — semantic chunk 150 слов
   <H3> — подраздел
     <List> — bulleted/numbered
     <Stats> — числа, проценты
     <Quote> — цитата с атрибуцией
<H2> FAQ
   <H3> Q1 / A1 ...
<Schema> — JSON-LD: Article + FAQPage + Person/Author + Organization
```

## Distribution — где публиковать

**Tier 1 (высокая цитируемость, проверено Semrush/Ahrefs):**
- **Reddit** — 40% всех LLM-цитат. Тематические сабреддиты. **Только настоящими аккаунтами, не спамом.**
- **Wikipedia** — если бренд достоин (есть пресса). **Нельзя писать о себе напрямую** (нарушает правила) — работать через notable mentions в смежных статьях.
- **YouTube** — упоминания/обзоры. Корреляция **0.737** с AI visibility (топ-фактор Ahrefs).
- **Quora** (особенно B2B), **Substack/Medium** (часто попадают в training data), личные блоги экспертов.

**Tier 2 (отраслевые):** G2, Capterra (SaaS), Stack Overflow (dev-tool), Indie Hackers, ProductHunt.

**Tier 3 (PR):** mainstream press. Для Claude особенно — NYT, Atlantic, Economist. Для РФ — РБК, Newspaper1.

**Русскоязычная специфика:** Habr (техническая, хорошо цитируется в русских LLM), VC.ru (бизнес-кейсы),
РБК (авторитет), Roem.ru. → публикация: `habr-post`, `vc-post`, `rbc-post`.

### Off-page «семени» в training data (долгая игра)

1. **Co-mentions** — упоминания бренда рядом с конкурентами/категорией. AI учится через контекст:
   если «YourProduct» появляется рядом с «ChatGPT, Claude, Gemini» в десятках источников — ассоциирует.
2. **Reddit seeding** — органические треды «Какой AI работает с рублёвой картой?». Не самопостинг.
3. **Wikipedia notability** — сложнейший сигнал, но раз попал → модели «знают» навсегда.
4. **YouTube creator outreach** — транскрипты видео в training data всех топ-LLM.
5. **Open dataset / API** под CC/MIT — Common Crawl индексирует.
6. **GitHub repos** (для tech-брендов) — README попадают в training data.

## Технические артефакты

### schema.org

Ключевые типы: **Article/BlogPosting/NewsArticle** (editorial), **FAQPage** (критично для Q&A),
**HowTo**, **Person** (E-E-A-T авторство), **Organization** (бренд), **Product+Offer** (e-commerce),
**BreadcrumbList**, **Dataset** (для оригинальных данных). E-E-A-T триада: Organization + Person +
Article, связанные через `@id` и `sameAs` → entity graph для верификации.

**Оговорка:** Quoleady + Search Atlas (дек 2024) — **NO корреляции** между объёмом schema и частотой
AI-цитат. Predictors — content authority и relevance, не JSON-LD payload. **Но schema нужна** для
парсинга (снижает misinterpretation/hallucination), кейсы дают +60% citation share. Консенсус:
**«schema — это hygiene, а не magic».** → шаблоны: `schema-markup-ru`.

### llms.txt

`/llms.txt` — community-предложение (Jeremy Howard, Answer.AI, 2024). Plain-text карта сайта для LLM.
**Реальность на 2026:** только **3.2% сайтов** имеют; **ни OpenAI/Google/Anthropic/Meta/Mistral
официально не подтвердили** использование в production; это convention, не стандарт.
**Вердикт:** дёшево, downside нулевой, upside спекулятивный. Сделать «на всякий случай» (особенно
docs/dev-сайтам). **Не приоритет** — приоритет content & mentions.

### robots.txt и AI-боты

**По умолчанию — пускать всех.** Блокировка = твой контент не попадёт ни в training data, ни в
retrieval, ни в RAG. Явно allow:
- `GPTBot` (OpenAI) · `ClaudeBot` / `anthropic-ai` (Anthropic) · `PerplexityBot` (Perplexity)
- `Google-Extended` (Gemini training) · `CCBot` (Common Crawl — база для всех)

Блокировать целесообразно только платный/эксклюзивный контент.

### SSR (обязательно)

**Большинство AI-краулеров НЕ рендерят JavaScript.** SPA через React-hydration без SSR → контент
LLM не видит. Проверка через Mobile Friendly Test + Schema Markup Validator.

## Authority signals

- **Автор:** Person schema с `sameAs` на LinkedIn/личный сайт/Wikipedia/научный профиль, реальное
  фото, bio, credentials, кросс-цитирование на других платформах.
- **Организация:** Wikipedia (если уровень позволяет), Crunchbase, LinkedIn Company, директории.
- **Даты:** `datePublished`, `dateModified`, явное «Updated YYYY-MM-DD» в тексте.
- **Outbound-цитаты** на peer-reviewed/авторитетные источники → выше credibility score.

## Кризис и цифры (аргумент перед клиентом)

- **Zero-click:** 58.5% US / 59.7% EU в 2024 (SparkToro) → **80-83%** на queries с AIO в 2026.
- **HubSpot:** 13.5M (ноя 2024) → 8.6M (дек 2024) → 6-7M (нач 2025) = **−70…−80%**. CNN −27/−38%,
  Business Insider −55%.
- **Position-1 CTR** падает на **34.5%** когда показывается AI Overview. AIO в ~13% queries.
- **Конверсия AI-трафика:** ChatGPT B2B 14-16%, Perplexity 10.5%, Claude 5%, Gemini 3% (vs Google 1.76%).
- **GEO ≠ SEO:** 12% URL-overlap, 62% rank-correlation.
- **Brand mentions vs backlinks:** 3:1 для AIO. YouTube 0.737, web 0.664, DR 0.218.
- **Source dominance:** Reddit 40.1%, Wikipedia 26.3%, YouTube 23.5%. Top-15 доменов = 68% цитат.

## Как движки выбирают источники (детальный разбор)

**ChatGPT (с search):** внешний retrieval поверх Bing (alignment 87%). Wikipedia 47.9% top-10,
Reddit 11.3%. Любит энциклопедичность, entity clarity, recency (56% цитат за 12 мес), trust signals
(Yelp, BBB).

**Perplexity:** непрерывный краул, новый контент в индексе за часы-дни. Самая прозрачная
(inline-citations). **Reddit 46.7%** (×3.5 над YouTube 13.9%). Любит BLUF, freshness (×3.2 за 30 дн),
schema (кейс: 0→14% citation за 6 нед на топ-30 страницах), DA 40+. Two-stage: source selection +
answer absorption.

**Claude (с web):** training data (cutoff Jan 2025) + web search (off по умолчанию) + Citations API.
Самая осторожная. NYT/Atlantic/Economist, **UGC в 2-4× выше** (F&B почти ×10 vs Gemini). Только 36%
цитат за год (любит старые авторитетные). Bullet-points цитируются **+30%**. Strict citation rules.

**Gemini / AI Overviews:** grounded в Google index + reranker. Оф. сайты, Google Business Profiles,
structured local pages, Reddit 21%. Любит традиционный SEO, GBP completeness, structured data,
position-1 organic.

**(regional LLM B) / (regional LLM A)** → отдельный файл `russian-llm.md`.

## Источники

Полный список со ссылками — `geo_llm_seo_research.md` раздел Sources (академические, платформенные,
tactical guides, Reddit, schema/llms.txt, traffic loss, tools, conversion, Russian context).
