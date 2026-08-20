# GEO / LLM SEO / AEO — глубокое исследование

> Референс-контекст для маркетинговой стратегии под видимость в генеративных AI-системах.
> Дата: май 2026. Источники — академические работы, индустриальные отчёты.
> Технические термины (GEO, LLM, citation, schema.org) — на английском.

---

## TL;DR (для тех у кого нет времени)

1. **Search фундаментально сломан**. 60% Google-запросов в 2024 — zero-click. С появлением AI Overviews показатель растёт до 80–83% на запросах где AIO присутствует. HubSpot потерял 70–80% органического трафика за 2024–2025.
2. **Появилась новая дисциплина** — GEO (Generative Engine Optimization) / AEO (Answer Engine Optimization) / LLM SEO. Цель — попадание в ответ ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews, а не в синюю ссылку №1.
3. **GEO ≠ SEO**. Только 12% URL, цитируемых AI, пересекаются с топ-10 Google. Только 62% совпадение между ранжированием Google и видимостью ChatGPT. Это два разных рынка.
4. **Что работает (по Princeton/IIT Delhi 2024)**: добавление цитат +30–40%, статистики +30–40%, ссылок на источники +30–40%. Что НЕ работает: keyword stuffing, технический жаргон, авторитетный тон без подтверждений.
5. **Где брать ссылки**: Reddit (40% всех LLM-цитат у Semrush), Wikipedia (26%), YouTube (24%). Reddit доминирует у Perplexity (46.7% top citations), Wikipedia — у ChatGPT (до 47.9% top-10).
6. **AI-трафик конвертит в 4–14× выше Google organic**. ChatGPT B2B-конверсия 14–16% vs 1.76% у Google organic. Объём пока маленький (1% от веба), но растёт +527% за 5 месяцев.
7. **Инструменты GEO-трекинга**: Profound ($499/мес), Peec AI (mid-market, $100M+ valuation 2025), Otterly ($29/мес — самый дешёвый), AthenaHQ (ex-Google/DeepMind), Mention, BrandIndex. Рынок GEO-услуг — $886M в 2024 → прогноз $7.3B к 2031 (CAGR 34%).
8. **Контент → инфраструктура для AI и discovery**, а не пост под клики. Классическая связка «статья → трафик» умирает; страница становится источником для AI-ответа.
9. **Двойная игра для любого продукта**: (а) попасть в ответы ChatGPT/Perplexity как рекомендация в своей категории, (б) при возможности сделать GEO-видимость продуктовой фичей (мониторинг для брендов), (в) публиковать original research, чтобы личный/командный бренд цитировался AI.
10. **Action items** (детально в разделе 9): запустить llms.txt, перенести экспертные статьи в чистый канонический формат, посеять Reddit + профильные UGC-площадки, опубликовать оригинальное исследование по своей нише, поставить Profound или Otterly на мониторинг, добавить schema.org Article+FAQ+Person на сайт.

---

## 1. Терминология: GEO / LLM SEO / AEO

### 1.1 Три названия — одна суть

Три термина в обращении, все три означают примерно одно: оптимизация контента под видимость в ответах генеративных AI-систем.

| Термин | Расшифровка | Кто ввёл | Фокус |
|---|---|---|---|
| **GEO** (Generative Engine Optimization) | Оптимизация под генеративные поисковики | Aggarwal et al., Princeton/IIT Delhi/Georgia Tech/AI2 (arXiv ноябрь 2023, KDD 2024) | Академическое определение, фокус на цитируемости в LLM-ответах |
| **AEO** (Answer Engine Optimization) | Оптимизация под «движки ответов» | Conductor и индустрия (2024–2025) | UX-ориентированный, фокус на формате ответа |
| **LLM SEO** / **AI SEO** / **AISO** | Народные варианты | Индустрия | Прагматичный обиходный термин |

Industry consensus: **GEO и AEO — синонимы на 90%**. Conductor в академии прямо пишет: «GEO and AEO are two terms for the same practice». Разница только в фокусе — GEO про модель, AEO про пользовательский UX (получение прямого ответа).

> «AEO emerged as a distinct discipline in 2024 and 2025, as generative AI assistants began handling the kind of research and discovery questions that used to belong to Google.» — Profound, *What is AEO*.

В этом документе используется GEO как зонтичный термин (он первым появился в академии), AEO — когда речь именно про UX-формат ответа.

### 1.2 Что значит «быть видимым в LLM» — три пути

Видимость в LLM устроена принципиально по-другому, чем в Google. Есть три фундаментально разных канала попадания в ответ:

1. **Training data inclusion** (обучающие данные). Модель «запомнила» бренд в момент тренировки. Касается Claude (cutoff Jan 2025) и базы GPT/Gemini. Зависит от того, насколько часто бренд упоминался в Common Crawl, Reddit (Google заплатил $60M/год), Wikipedia, лицензированных датасетах. **Долгоиграющая ставка**.
2. **RAG / live browsing / search tool**. Модель в момент ответа лезет в индекс. ChatGPT использует Bing index (alignment 87% с Bing top results). Perplexity непрерывно краулит. Google AI Overviews — поверх Google index. Claude добавил web search в 2025. Gemini — поверх Google. **Быстро растущая ставка**.
3. **Citation in the visible answer** — то самое «попасть в [1], [2], [3]». Это уже видимый пользователю результат. Только Perplexity и иногда ChatGPT/Gemini показывают inline-citations. Claude — через Citations API (June 2025).

Большинство тактик GEO целит в **#2 + #3** (быстро), но настоящий долгосрочный moat — это **#1** (попасть в обучающие данные следующего поколения моделей через массовые упоминания на цитируемых доменах).

### 1.3 Чем GEO отличается от классического SEO

| Параметр | Classic SEO | GEO |
|---|---|---|
| Метрика успеха | Позиция в SERP, CTR, sessions | Citation share, brand mention frequency, AI Overview presence |
| Главный сигнал | Backlinks, on-page keywords, Core Web Vitals | Brand mentions, entity clarity, content depth, recency |
| Контент-формат | Длинные SEO-статьи под keyword | Структурированные chunks по 150 слов с прямыми ответами BLUF (Bottom Line Up Front) |
| Что НЕ работает | (всё работает в разной степени) | Keyword stuffing — НЕ работает (даже мешает) |
| Что работает | EAT, links, schema | Quotation, statistics, citations from authoritative sources |
| Источники силы | Google PageRank | Reddit, Wikipedia, YouTube, нишевые UGC |
| Конкуренция | ~10 синих ссылок | Top 15 доменов = 68% всех AI-цитат (Yext) |
| Конверсия | 1.76–2.8% (Google organic baseline) | 5–16% (ChatGPT B2B), 10.5% (Perplexity) |

Ключевая инверсия: **Ahrefs research (75K брендов)** — brand mentions коррелируют с AI Overview presence в **3:1 над backlinks**. YouTube mentions — 0.737 корреляция, web mentions — 0.664, backlinks — всего 0.218. Бренд-упоминания обогнали ссылки.

---

## 2. Как LLM-поисковики выбирают источники

### 2.1 Citation Pipeline — четыре стадии

Современные ответные движки работают по схеме, описанной в Hashmeta AI Marketing Blog и Discovered Labs:

1. **Query fan-out** — оригинальный запрос разворачивается в 8–12 sub-queries. ChatGPT часто выдаёт 4–6 вариаций, Perplexity — до 12. Это уже NOT keyword search.
2. **Chunking & retrieval** — страницы разбиваются на фрагменты (chunks), извлекаются самые релевантные.
3. **Passage selection** — кандидаты сравниваются по claim density, entity clarity, recency, structural format.
4. **Attribution** — выбранный контент связывается с источником и попадает в видимую цитату.

Большинство SEO-контента валится на стадии #2 — потому что «зарывает ответ» в середине статьи. LLM не дочитает.

### 2.2 ChatGPT (с search и browse)

**Архитектура**: внешний configurable retrieval layer, использует Bing search index. Alignment с Bing top-10 — около 87%.

**Источники в top citations**:
- Wikipedia: 47.9% top-10 citations (Discovered Labs) — главный «consensus source»
- Reddit: 11.3% (Discovered Labs)
- В hospitality industry — оф. сайты брендов 38.08% (Yext)

**Что работает**:
- Encyclopedic content с чёткими определениями entities
- Внешние ссылки на авторитетные источники
- Если индустрия имеет сильный Bing-индекс — традиционный SEO даёт перенос
- Trust signals: Yelp, BBB.org, верифицированные бренды

**Свежесть**: 56% журналистских цитат — за последние 12 месяцев. ChatGPT любит recency больше Claude.

### 2.3 Perplexity

**Архитектура**: непрерывный crawl, search-engine-first, новый контент попадает в индекс за часы–дни. «Самая прозрачная» из платформ — inline citations с кликабельными ссылками для каждого утверждения.

**Источники**:
- **Reddit: 46.7% top-10 citations** — это в 3.5 раза больше, чем у второго (YouTube 13.9%)
- Wikipedia, новостные сайты, профильные нишевые блоги

**Что работает (Perplexity-специфика)**:
- **BLUF format** — прямой ответ в первых 100 словах. 90% выигравших цитат имеют определение/ответ в начале страницы.
- **Freshness** — контент за последние 2–3 дня получает буст. Контент обновлённый за 30 дней — 3.2× больше цитат.
- **Schema markup** — в одном кейсе (pet products) деплой schema на топ-30 страниц → за 6 недель цитат-доля выросла с ≈0 до 14%.
- **Domain authority** — DA 40+ значимо повышает citation rate.
- **Two-stage process**: source selection (попасть в shortlist) + answer absorption (попасть в финальный ответ). Большинство гайдов путают эти две стадии.

### 2.4 Claude (с web search)

**Архитектура**: знание из training data (cutoff Jan 2025) + web search опционально + Citations API (запущен June 2025). Самая «осторожная» платформа, web browse по умолчанию выключен.

**Источники**:
- The New York Times, The Atlantic, The New Yorker, The Economist — престижная журналистика
- **User-generated content в 2–4× выше других моделей**. В Food & Beverage — почти в 10× чаще, чем Gemini.
- Только 36% журналистских цитат — за последний год (vs 56% у ChatGPT). Claude любит «старые» авторитетные источники.

**Что работает**:
- Formal authoritative tone
- Technical accuracy + verifiable claims (снижают риск hallucination)
- Bullet-pointed pages цитируются на 30% чаще (Lantern study)
- **Strict citation rules** — Anthropic пишет, что Claude обучен не врать про источники

### 2.5 Gemini / Google AI Overviews

**Архитектура**: grounded в Google Search index. По сути — поверх Google rankings, но с дополнительными reranker-сигналами для AI.

**Источники**:
- Официальные сайты брендов
- Google Business Profiles
- Structured local pages
- Reddit: 21% AI Overview sources

**Что работает**:
- Traditional SEO strength
- Google Business Profile completeness
- Structured data (особенно local/business schema)
- Position-1 organic — выше шанс попасть в AI Overview

**Удар по трафику**: когда AI Overview показывается, position-1 CTR падает на 34.5%. AIO появляется в 13% queries.

### 2.6 Bing AI / You.com / (regional LLM B) / (regional LLM A)

**Bing AI (Copilot)**: повторяет ChatGPT-логику (та же Bing-инфра).

**You.com**: больше всего напоминает Perplexity, sources показываются inline.

**(regional LLM B)**: обучен на русскоязычных данных, бизнес-ориентирован, экосистема Сбера. **Те же бренды показывают 2–3× разную Share of Voice между (regional LLM B) и Alice/(regional LLM A)** — отдельный мониторинг обязателен.

**(regional LLM A)/Alice**: часть Яндекс-экосистемы, использует Яндекс-индекс. К февралю 2026 — новая модель Alice. 12% пользователей нейросетей в РФ выбирают (regional LLM A).

### 2.7 Концентрация авторитета: новая монополия

Самый важный факт из 5W Citation Source Index 2026: **top-15 доменов = 68% всех AI-цитат** консолидированно. Это сильнее, чем когда-либо производил Google PageRank. Если ты не в top-15 цитируемых доменов или не цитируешься через них — ты не существуешь для AI.

Top источники (Semrush 17M citations study):
1. Reddit — 40.1%
2. Wikipedia — 26.3%
3. YouTube — 23.5%
4. Дальше: G2, Quora, профильные publishers

### 2.8 Чем отличаются от Google PageRank / Core Web Vitals

- **PageRank** — глобальный авторитет через входящие ссылки. **GEO** — entity-level mentions, в т.ч. без ссылок.
- **Core Web Vitals** (LCP, CLS, INP) — у LLM-краулеров не учитываются. Большинство AI-crawlers НЕ рендерят JavaScript. Если твой контент — SPA через React-hydration, LLM его не увидит.
- **Backlinks** — в GEO остаются важными (предсказывают Google ranking, который предсказывает AIO), но **brand mentions без ссылок весят больше**.
- **Click-through rate** — у LLM нет такого сигнала. Есть только citation rate.

### 2.9 Роль training data vs live browsing

| Платформа | Training data weight | Live browsing weight |
|---|---|---|
| Claude | High | Low (default off) |
| ChatGPT | Medium | High (default on с GPT-4o+) |
| Perplexity | Low | Very High (real-time crawl) |
| Gemini | Medium | High (Google index) |
| (regional LLM B) | High | Medium |

Вывод: если ты хочешь попасть в Claude — нужно быть в training data (Reddit, Wikipedia, лицензированные источники). Если в Perplexity — нужно быть в его live-crawl (свежий контент, schema, BLUF). ChatGPT — посередине: и то, и то.

---

## 3. Конкретные тактики GEO

### 3.1 Princeton GEO Study — что работает (с числами)

Самое важное академическое исследование: **Aggarwal, Murahari, Rajpurohit, Kalyan, Narasimhan, Deshpande**, *GEO: Generative Engine Optimization*, arXiv:2311.09735, KDD 2024.

Они протестировали 9 тактик на бенчмарке **GEO-bench (10,000 queries в разных доменах, train 8K / val 1K / test 1K)**. Метрика: **Position-Adjusted Word Count** — сколько слов от твоего источника попало в финальный ответ генеративного движка, с учётом позиции (раньше = лучше).

**Что работает (+30–40% к visibility)**:

| Тактика | Эффект | Объяснение |
|---|---|---|
| **Quotation Addition** | +30–40% | Добавление релевантных цитат от других источников |
| **Statistics Addition** | +30–40% | Числа, проценты, конкретика |
| **Cite Sources** | +30–40% | Ссылки на авторитетные источники внутри контента |

**Что работает умеренно (+15–30%)**:
- Fluency Optimization — улучшение читабельности текста
- Easy-to-Understand — упрощение языка

**Что НЕ работает или работает слабо**:
- Authoritative tone (без подтверждений) — «no significant improvement»
- **Keyword Stuffing** — «offer little to no improvement» (противоречит classic SEO)
- Unique Words — минимально
- Technical Terms — ограниченный эффект

**Real-world validation**: тестировали на Perplexity.ai, получили улучшения до 37%. Эффективность тактик **варьируется по доменам** — для HEALTH-домена работает одно, для FACTUAL — другое. Domain-specific optimization обязателен.

### 3.2 Контент-стратегия: что писать и как

**Основные принципы GEO-контента**:

1. **BLUF (Bottom Line Up Front)** — главный ответ в первых 100 словах. 90% выигравших Perplexity-цитат соблюдают это правило.

2. **Chunk-friendly structure** — каждый блок 150 слов, semantically coherent, понятен independently:
   - Heading-driven separation
   - One idea per paragraph
   - Numerical lists и bulleted lists как natural split points
   - Открывающее предложение блока — сильно влияет на embedding similarity при retrieval

3. **Density of claims** — LLM ищет «фактологическую плотность». Один параграф = одно проверяемое утверждение с числом или цитатой.

4. **Original research** — Princeton данные. Sara Vaughan, Organic Labs: «comprehensive, authoritative pages показывают корреляцию 0.79 с LLM visibility». Оригинальные данные/опросы — самый мощный citation magnet.

5. **Recency stamps** — публикуй даты, обновляй контент явно (`Updated May 2026` в заголовке). Perplexity-контент за 30 дней → 3.2× больше цитат. Свежий контент за 3 месяца — 6 cites/page vs 3.6 у устаревшего.

6. **FAQ-секции** — преоптимизированы под Q&A retrieval pattern. ChatGPT/Claude любят FAQ потому что это уже готовая пара question→answer для chunking.

7. **«vs», «best», «top»** content — LLM-friendly comparison content. Ahrefs прямо рекомендует.

### 3.3 Структура страницы

```
<H1> — главный entity / question
<TLDR/Summary> — BLUF, 50–100 слов, прямой ответ
<H2> — основной раздел
   <Paragraph> — semantic chunk 150 слов
   <H3> — подраздел
     <List> — bulleted/numbered
     <Stats> — числа, проценты
     <Quote> — цитата с атрибуцией
<H2> FAQ
   <H3> Q1: ... <H3> A1: ...
<Schema> — JSON-LD: Article + FAQPage + Person/Author + Organization
```

### 3.4 Технические артефакты

#### schema.org / Structured data

Ключевые типы для GEO:
- **Article** / **BlogPosting** / **NewsArticle** — обязательно для editorial
- **FAQPage** — критично для AI Q&A extraction
- **HowTo** — для step-by-step контента
- **Person** — для авторства (E-E-A-T signal)
- **Organization** — для бренда
- **Product** + **Offer** — для e-commerce
- **BreadcrumbList** — для навигации
- **Dataset** — для оригинальных данных/исследований

E-E-A-T триада в structured data: **Organization + Person + Article**, связанные через `@id` references и `sameAs` links → формируют entity graph, который AI использует для верификации.

**Важная оговорка**: декабрьское 2024 исследование Quoleady + Search Atlas не нашло прямой корреляции между объёмом schema и частотой AI-цитат. Predictors — content authority и relevance, а не JSON-LD payload. Но **schema всё равно нужна для парсинга** — она снижает риск misinterpretation и hallucination, и платформенные кейсы (включая HubSpot) показывают +60% citation share после деплоя структурированных данных. Industry consensus: «schema — это hygiene, а не magic».

#### llms.txt

Файл `/llms.txt` — community-предложение от Jeremy Howard (Answer.AI, 2024). По спеке — это plain-text карта сайта для LLM с метаданными.

**Реальное состояние на май 2026**:
- **Только 3.2% сайтов имеют llms.txt** (State of llms.txt 2026, Presenc AI)
- **Ни OpenAI, ни Google, ни Anthropic, ни Meta, ни Mistral официально не подтвердили использование llms.txt в production**
- Это community convention, **не стандарт IETF/W3C**
- AEO Engine: «AI Bots Ignore It (2026)» — данных о существенном эффекте нет

**Вердикт**: ставить llms.txt — дёшево, downside нулевой, upside спекулятивный. Сделать стоит «на всякий случай», особенно для документации/dev-product сайтов. Mintlify уже автогенерирует. **Не приоритет** — приоритет content & mentions.

#### robots.txt и AI bots

Отдельный вопрос — пускать или нет:
- `GPTBot` — OpenAI
- `ClaudeBot` / `anthropic-ai` — Anthropic
- `PerplexityBot` — Perplexity
- `Google-Extended` — Google Gemini training
- `CCBot` — Common Crawl (база для всех)

**По умолчанию: пускать всех**. Если блокируешь — твой контент не попадёт ни в training data, ни в live retrieval, ни в RAG. Блокировка целесообразна только для платного контента или эксклюзивных исследований.

### 3.5 Authority signals

1. **Автор страницы**:
   - Person schema с `sameAs` на LinkedIn, личный сайт, Wikipedia (если есть), научный профиль
   - Реальное лицо (фото), bio, credentials
   - Кросс-цитирование автора на других платформах
2. **Организация**: Wikipedia-страница (если уровень позволяет), Crunchbase, LinkedIn Company, отраслевые директории
3. **Даты**: `datePublished`, `dateModified`, явное «Updated YYYY-MM-DD» в тексте
4. **Внешние ссылки на исследования**: чем больше outbound цитат на peer-reviewed и авторитетные источники, тем выше credibility score

### 3.6 Distribution — где публиковать

**Tier 1 (высокая цитируемость в LLM, проверено Semrush/Ahrefs)**:
- **Reddit** — 40% всех LLM-цитат. Тематические сабреддиты в твоей нише. Участвуй настоящими аккаунтами, не спамом.
- **Wikipedia** — если бренд достоин (есть пресса). Не пиши о себе напрямую — это правила нарушит, но можно работать через notable mentions в смежных статьях.
- **YouTube** — упоминания/обзоры твоего бренда. YouTube mentions correlate 0.737 с AI visibility (Ahrefs).
- **Quora** — особенно для B2B, в нишах где Reddit слаб
- **Substack / Medium** — независимые публикации, часто попадают в training data
- **Личные блоги экспертов** — LLM любит «expert opinion»

**Tier 2 (отраслевые)**:
- G2, Capterra (если SaaS) — review platforms
- Stack Overflow (если dev-tool)
- Indie Hackers, ProductHunt
- Профильные отраслевые медиа

**Tier 3 (PR)**:
- Mainstream press (NYT, Bloomberg, TechCrunch — для США, РБК, Newspaper1 — для РФ)
- Authority-press — особенно для Claude (NYT, Atlantic, Economist)

**Русскоязычная специфика**:
- Habr — техническая аудитория, хорошо цитируется в русскоязычных моделях
- VC.ru — бизнес-кейсы
- РБК — авторитет
- ICANN/Roem.ru — нишевые медиа

### 3.7 Off-page тактика «семени» в обучающие данные

Если хочешь попасть в следующую версию модели через training data:

1. **Co-mentions**: упоминания твоего бренда рядом с конкурентами/категорией. AI учится через context — если «YourProduct» появляется рядом с «ChatGPT, Claude, Gemini» (или с ключевыми игроками твоей ниши) в десятках источников, модель ассоциирует.
2. **Reddit seeding** — натуральные треды «What's the best [category] tool?», где органически фигурирует бренд. **Нельзя постить с brand account про себя** — модерация банит.
3. **Wikipedia notability** — попасть в Wikipedia hardest signal, но раз попал → модели тебя «знают» навсегда.
4. **YouTube creator outreach** — заплатить/подружиться с креаторами в нише, чтобы бренд естественно упоминался в видео. Транскрипты YouTube — в training data всех топ-LLM.
5. **Open dataset / API** — публикация открытых данных под лицензией CC/MIT. Common Crawl индексирует.
6. **GitHub repositories** — для tech-брендов. README попадают в training data.

---

## 4. Метрики и инструменты

### 4.1 Что мерить

| Метрика | Что показывает | Как считать |
|---|---|---|
| **Citation Share** | % ответов на тестовый prompt-set, где упомянут твой бренд | Запустить 100–500 prompts через API, считать частоту |
| **Share of Voice (SoV)** | Доля твоего бренда vs конкурентов в LLM-ответах | Сравнительный анализ по prompt-set |
| **Sentiment in LLM** | Тон упоминаний — позитив/нейтрал/негатив | Manual / LLM-classifier |
| **AI Overview Presence** | % твоих ключей где появляется AIO + ты в ней | Google Search Console + ручной check |
| **LLM Referral Traffic** | Сессии из ChatGPT/Perplexity/Claude/Gemini | GA4 referrer matching |
| **Brand Mention Velocity** | Темп роста brand mentions на цитируемых доменах | Mention/Ahrefs/Semrush |
| **Hallucinated URLs** | LLM генерирует «фейковые» URL под твой бренд | Server logs 404 monitoring |

### 4.2 Инструменты GEO-tracking

| Инструмент | Цена (Lite) | Что умеет | Кому подходит |
|---|---|---|---|
| **Profound** | $499/мес | Полный enterprise GEO suite, prompt monitoring, competitor benchmarks | Enterprise, агентства |
| **Peec AI** | Mid-market | Закрыл Series A $21M в ноябре 2025, $100M+ valuation. Сильный sweet spot для SMB+ | Mid-market |
| **Otterly** | $29/мес | Самый дешёвый. Gartner Cool Vendor 2025. Базовый prompt tracking | Solo / startups |
| **AthenaHQ** | Enterprise | Основатели ex-Google Search/DeepMind | Серьёзные команды |
| **Mention** | $49+/мес | Brand monitoring, не специализирован под LLM, но мониторит mentions | Brand tracking |
| **BrandIndex (YouGov)** | Enterprise | Consumer perception tracking | Big brands |
| **Lantern, xSeek, GenRankEngine, ZipTie** | Various | Нишевые GEO-трекеры | Эксперименты |
| **Manual (ChatGPT API + prompt-set + sheet)** | $0–50 | Свой собственный prompt audit | Solopreneurs, технари |

Рынок: $886M в 2024 → $7.3B к 2031 (CAGR 34%). Сейчас **92% брендов невидимы в ChatGPT** — большой headroom.

### 4.3 Promo audit — какие prompts тестировать

Базовый аудит для любого бренда — 5 типов промптов:

1. **Brand direct**: «Tell me about [Brand]» / «What is [Brand]?» — проверка training data inclusion
2. **Category**: «Best [category] tools for [use case]» / «Top alternatives to [Competitor]» — проверка где твой бренд в шортлисте
3. **Comparison**: «[Brand] vs [Competitor]» — проверяет наличие и тон
4. **Problem-aware**: «How do I solve [problem brand solves]?» — самый сильный сигнал товарного фита
5. **Niche/long-tail**: специфические запросы из реальных юз-кейсов клиентов

Запускать на каждой платформе отдельно (ChatGPT/Claude/Perplexity/Gemini/(regional LLM B)/(regional LLM A) для РФ). 50–100 prompts × 6 платформ = базовый audit.

### 4.4 Чек-лист «мой бренд попал в ответ?»

- [ ] Бренд упоминается напрямую (текстом)
- [ ] Бренд упоминается со ссылкой на оф. сайт
- [ ] В каком источнике LLM нашёл бренд (Wikipedia, Reddit, личный сайт?)
- [ ] Тон описания (позитив/нейтрал/негатив)
- [ ] Корректна ли информация (категория, USP)
- [ ] Не путается ли LLM с конкурентом
- [ ] Какие конкуренты упомянуты рядом
- [ ] В какой позиции (первый/middle/последний)

---

## 5. Что говорят исследования

### 5.1 Princeton GEO Study (Aggarwal et al., KDD 2024)

См. раздел 3.1. Главное:
- +30–40% к visibility за счёт Quotations / Statistics / Cite Sources
- Keyword stuffing — НЕ работает
- Domain-specific optimization обязателен
- GEO-bench: 10K queries в 8K/1K/1K сплите

### 5.2 Ahrefs LLM Visibility Study (75K брендов, 2025)

- Brand mentions vs backlinks для AI Overview presence — **3:1 в пользу mentions**
- YouTube mentions: correlation 0.737 (топ-фактор)
- Web mentions: 0.664
- Branded anchor text: 0.527
- Branded search volume: 0.334
- Domain Rating (классический Ahrefs DR): 0.218 — слабее всего

Источник: ahrefs.com/blog/llm-visibility/, 17M citations analysed.

### 5.3 Semrush LLM Citation Source Study

- Reddit: 40.1% всех LLM citations
- Wikipedia: 26.3%
- YouTube: 23.5%
- (Reddit > Wikipedia + YouTube вместе)

### 5.4 Conductor 2026 AEO/GEO Benchmarks

3.3B sessions, >13K enterprise доменов. Главное:
- В среднем organic traffic у enterprise упал двузначными цифрами в 2024–2025
- AEO citation lift приходит ДО traffic lift (на недели/месяцы)

### 5.5 SparkToro Zero-Click Study (Rand Fishkin, 2024)

- US: 58.5% queries — zero-click (на 1000 Google searches только 360 кликов на open web)
- EU: 59.7% — zero-click (374 кликов/1000)
- AI Overviews — только 12.7% SERPs (в июне 2024)
- Fishkin sceptical: «fear of AI Overviews — sound and fury, signifying nothing»

В 2026 цифры ухудшились:
- **80–83% zero-click на queries с AIO** (Pikaseo, Superprompt data)
- Median publisher: -10% YoY в H1 2025
- News publishers: -7%, non-news content: -14%

### 5.6 HubSpot Case (canonical zero-click victim)

- Organic traffic: 13.5M (ноябрь 2024) → 8.6M (декабрь 2024) → 6–7M (начало 2025)
- Total drop: **-70 до -80%**
- Реакция HubSpot: запустили собственный AEO tool, переписали content strategy
- HubSpot AEO самоотчёт: citation share +60%, brand visibility awareness +35pp

CNN: -27 до -38%. Business Insider: -55% organic между апр 2022 и апр 2025.

### 5.7 AI Search Conversion Studies (2025–2026)

- ChatGPT B2B conversion: 14.2–15.9% (vs Google organic 1.76–2.8%)
- Perplexity: 10.5%
- Claude: 5%
- Gemini: 3%
- Industry consensus: AI-referred traffic конвертит **в 4–14× выше organic**
- AI traffic share: ~1% от веба, но рост +527% за 5 месяцев (Jan→May 2025)

### 5.8 ChatGPT vs Google SEO Overlap Study (Chatoptic)

- **Только 62% overlap** между Google ranking и ChatGPT visibility
- Только 12% URLs цитируемых AI пересекаются с Google top-10 (Discovered Labs)
- GEO ≠ SEO — это два разных рынка

### 5.9 Quoleady + Search Atlas Schema Study (декабрь 2024)

- **NO correlation между объёмом schema на сайте и частотой AI citations**
- Predictors: content authority + relevance
- Вывод: schema нужна как hygiene, не как лекарство

---

## 6. Кейсы

### 6.1 HubSpot — выжить после потери 70% трафика

**До**: 13.5M monthly organic visits, лидер content marketing.
**После AI Overviews**: 6–7M.
**Реакция**:
1. Запустили HubSpot AEO tool (для клиентов)
2. Переписали глоссарий с учётом AEO-форматов
3. Замерили: citation share related prompts +60%, brand visibility awareness-stage prompts +35pp
4. Через NexTiny Marketing + Human-to-Answer framework — одному клиенту подняли AI visibility с near-zero до 35%+ за недели

**Урок**: даже когда теряешь трафик, citation share в AI можно восстанавливать.

### 6.2 Reddit — невольный победитель

**Реакция**:
- $60M/год от Google за лицензию на training data
- Отдельный deal с OpenAI
- Perplexity вручную бустит Reddit
- Результат: 40% всех LLM-цитат идут через Reddit

**Урок для брендов**: Reddit — твой главный distribution channel в эпоху GEO. Не игнорировать, не спамить, но участвовать.

### 6.3 Notion — entity-driven success

Notion — пример бренда который хорошо «знают» все LLM. Тактики (industry consensus):
- Огромный community-driven контент (templates, guides)
- Сильный Wikipedia entity
- Бренд-amalgam на YouTube (Thomas Frank, Marie Poulin)
- Reddit r/Notion активный
- Documentation site — высокое качество, цитируется

### 6.4 Stripe — developer-first authority

- Документация — индустриальный эталон
- GitHub репозитории с кодом
- Stripe Blog — long-form thought leadership
- Stripe Press — собственное издательство, книги
- Patrick Collison как public intellectual

LLM ассоциирует Stripe не только с платежами, но и с «developer infrastructure», «fintech leadership», «founder thinking» — это широкий entity graph.

### 6.5 Anthropic Blog — собственный пример

Anthropic интересен как кейс самопродвижения LLM-компании:
- Регулярные research papers (Claude, Constitutional AI, mech interp)
- Сильный academic citation flow
- Каждый блог-пост → research paper → arXiv → следующее поколение моделей знает
- Self-reinforcing loop: LLM компания, чьи статьи учат LLM

**Урок**: публикация собственных research/data — самоподкрепляющаяся тактика.

### 6.6 Apify — long-tail dominance

Apify — пример long-tail GEO для нишевого SaaS. Их Actors каталог = тысячи страниц под специфические запросы («scrape X», «extract Y»). Каждая страница — отдельный entity. Доминируют в Perplexity по nichevym scraping queries.

Урок: programmatic SEO + GEO. Тысячи страниц под конкретные intent-based queries.

### 6.7 Что НЕ работает (provalnye кейсы)

- **Pure SEO без brand mentions**: сайты с DA 70+ но без Reddit/YouTube/Wikipedia упоминаний — невидимы в AI
- **Keyword stuffing** в AI-эпоху: ноль эффекта (Princeton)
- **JavaScript-heavy SPAs без SSR** — LLM-краулеры не рендерят JS, content invisible
- **Блокировка GPTBot/ClaudeBot/PerplexityBot** в robots.txt — самоубийство в долгую
- **Anonymous content без авторства** — слабый E-E-A-T signal
- **Контент 2018 года без обновлений** — recency penalty

---

## 7. GEO в маркетинговом обучении: чему учат курсы

Современные маркетинговые курсы всё чаще вводят GEO как отдельную дисциплину. Типовая структура блока — три опоры, применимые к любому продукту.

### 7.1 Базовый SEO-цикл — фундамент под GEO

Классическая инфраструктура: семантика, кластеризация, on-page, аналитика. Это **фундамент** под GEO — без классической SEO-гигиены LLM тебя тоже не найдёт.
- Подготовка: similarweb, Screaming Frog SEO Spider, Ahrefs
- Структура: главная, меню, html-карта
- Текстовая оптимизация — LLM (Claude/GPT) для генерации и редактуры контента
- Аналитика — Rush Analytics или аналог для позиций
- Под Запад: site.com/country/language/ — мультирегион

### 7.2 GEO-манифест: «контент как инфраструктура для AI»

Самый GEO-релевантный тезис таких курсов — контент перестаёт быть постом под клики и становится источником для AI-ответа. Ключевые формулировки (industry consensus):

> «Органический трафик падает у всех. Пример: HubSpot — с 10 млн до <1 млн визитов. Причина: AI-ответы в Google, ChatGPT / Gemini / Perplexity. Пользователь получает ответ, не переходя на сайт.»

> «Google = канал импрессий, а не кликов. Классическое SEO "статья → клики" умирает. Контент больше не пост. Контент = инфраструктура для AI и discovery.»

> «Веб превратился в огромную базу знаний для LLM, источник данных, который сканируют боты. 70%+ контента в интернете: AI-generated или Human + AI.»

> «Цель: быть источником для AI-ответов. Генерируем ультраперсонализированные страницы. Не просто меняем заголовки — меняется весь контент страницы.»

> «Страницы плохо читаются людьми, отлично читаются ботами, стабильно попадают в LLM-выдачу.»

Типовые примеры programmatic-подхода:
- Movers from San Francisco → Los Angeles
- Transfer Geneva → Méribel
- Каждая страница: локалка + стоимость + маршруты + FAQ + related queries

Эффект: −30% маркетингового бюджета, ×2–3 рост производительности, сотни тысяч органического трафика, независимость от алгоритмов одного канала.

### 7.3 «AI SEO агент»: практический workflow

Практическая реализация — workflow для генерации SEO-статей через AI-агента. Типовой стек:
- Perplexity (анализ выдачи, citations, summary) или любая LLM с браузингом
- OpenAI (генерация)
- Google Docs (промежуточное хранилище ТЗ)
- CMS публикация через API (WordPress/Webflow + JSON)

Принцип: **1 ключевой запрос = 1 статья = 1 страница**. Целить в low-volume (100–300/mo) ключи с низкой конкуренцией. Подключение БД (Supabase) → автоматическая перелинковка → ускорение индексации.

Структура каждой статьи (промт): 1500–2000 слов, H2 с ключём, FAQ, Key Takeaways, Estimated Reading Time, internal links, bold/italic/lists.

**Ограничения**:
> «Полная автоматизация невозможна, потому что исследование ключей требует экспертизы, кластеризация не полностью автоматизируется, выбор стратегии зависит от рынка. AI — инструмент, но стратегию формирует эксперт.»

### 7.4 Full-funnel аналитика: AI-traffic как отдельный source

Релевант для GEO: измерение **LTV когорт по каналам, включая AI-traffic** как отдельный source. Если ChatGPT-трафик конвертит в 14× выше organic, full-funnel-аналитика обязана его выделить отдельным сегментом, иначе будешь масштабировать неправильные каналы. CRM-интеграция, когортная выручка, predict LTV — те же фреймворки применимы к AI-traffic.

### 7.5 Окно возможности

GEO — новая тема, которую курсы только вводят. Кто первым запустит реальный GEO-проект и принесёт кейс в профессиональное комьюнити — получает репутационное преимущество и раннюю видимость в AI-ответах по своей нише.

---

## 8. Как применить это к своему продукту

Ниже — обобщённый шаблон приложения GEO к конкретному продукту (SaaS / онлайн-сервис / медиа). Подставь свою нишу, категорию и конкурентов.

### 8.1 GEO как канал привлечения

**Сценарий «попасть в ответы»**:
- Запрос пользователя в ChatGPT/Perplexity/Claude: «Какие есть [аналоги / инструменты] в [категории]?» / «Сервис, который [делает ключевую задачу продукта]?»
- Цель: YourProduct в ответе вместе с ключевыми игроками категории, желательно в #1 позиции своего сегмента

**Что для этого нужно**:

1. **Wikipedia-страница продукта** (на нужных языках). Если её нет — это блокер для Claude/ChatGPT training data.
2. **Sustained Reddit/Habr presence** — органические треды по проблеме, которую решает продукт, где он упоминается комьюнити. Не самопостинг.
3. **Сравнительный контент**: «YourProduct vs [Конкурент A] vs [Конкурент B]» — таблица, бенчмарки, цены. Опубликовать на собственном блоге + профильных площадках (Habr / VC.ru / отраслевые медиа).
4. **Оригинальное исследование**: публичный бенчмарк/датасет по своей нише под open license + препринт. Это самый сильный GEO-магнит.
5. **YouTube creator outreach** — разбор продукта у профильных tech-блогеров. YouTube mentions = highest correlation с AI visibility (Ahrefs 0.737).
6. **Person schema для команды** — на сайте карточки авторов/founders с sameAs на LinkedIn, личные сайты, научные профили.
7. **llms.txt** + robots.txt allow для GPTBot/ClaudeBot/PerplexityBot/Google-Extended — обязательно.

### 8.2 GEO как продуктовая фича

Если продукт даёт доступ к нескольким LLM/API, GEO-мониторинг можно завернуть в отдельную фичу.

**Идея**: раздел «AI Visibility Monitor для брендов».

**Логика**:
- 92% брендов невидимы в ChatGPT (industry)
- Профессиональные tools (Profound $499/mo) — дороги/непригодны для локальных рынков
- Если у продукта уже есть API ко всем моделям → он может прогонять prompt-аудит для клиента дёшево
- Мониторить сразу все релевантные платформы (ChatGPT, Claude, Gemini + локальные модели вроде (regional LLM B)/(regional LLM A)) — сильное УТП на рынке, где западные трекеры не покрывают локальные движки

**Продуктовая фича**: «Brand Visibility Dashboard». Клиент вводит бренд + 20 prompts. Система прогоняет каждый prompt по 5–6 платформам, считает Citation Share, отдаёт PDF-отчёт. Цена: [example] 5–15K/мес. Аудитория: SMB-маркетологи, бренд-менеджеры enterprise.

**Почему это работает**:
- Enterprise начинает массово закладывать AI-маркетинг в бюджеты
- Западные трекеры не покрывают локальные модели — окно для нишевого решения
- Параллельный pitch: «продукт — это не только доступ к моделям, это AI-marketing stack»

### 8.3 Почему GEO релевантно на уровне продукта и founder-бренда

1. **Стратегически** — AI Overviews убивают classic SEO, продукту нужен новый канал привлечения. GEO = новый канал.
2. **Продуктово** — GEO можно монетизировать как фичу (раздел 8.2).
3. **Личный бренд** — founder/лидер продукта должен быть видим в AI-ответах. Его посты, статьи, выступления должны попадать в training data. Это даёт долгосрочный moat (модели «знают» founder = доверие к продукту).
4. **Конкурентно** — крупные игроки категории не будут продвигать твой продукт. Строй свою AI-видимость сам.
5. **Инвестиционно** — раунды 2026 будут смотреть на «AI-native marketing» как сигнал зрелости команды. Founder, который cite himself в Princeton GEO paper и Conductor reports, выглядит сильнее тех, кто «делает classic SEO».

---

## 9. Action Items на ближайший квартал

Обобщённый чек-лист из 10 шагов с приоритетами и KPI. Подставь свой продукт (YourProduct), конкурентов и площадки.

### P0 — критичные, делать в первый месяц

**1. Запустить базовый GEO-аудит (2 дня)**
- Составить prompt-set: 50 запросов (brand direct, category, comparison vs конкурентами, problem-aware, long-tail)
- Прогнать через ChatGPT, Claude, Perplexity, Gemini + локальные модели (вручную или через API)
- Зафиксировать baseline: Citation Share, Sentiment, Top sources
- **KPI**: baseline measured, спред по платформам понятен. Это база для следующих шагов.

**2. Wikipedia-страница продукта (3–4 недели, через подрядчика)**
- Нанять Wikipedia-редактора (notable contributor) для драфта
- Собрать notability evidence: пресса, инвестиции, упоминания в авторитетных медиа
- Опубликовать сначала на основном языке, потом английскую версию
- **KPI**: страница опубликована, не удалена в течение 14 дней.

**3. llms.txt + robots.txt allow + Person schema (1 день)**
- Опубликовать `/llms.txt` (минимальный, Mintlify-формат)
- Robots.txt: явно разрешить GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot
- На каждой ключевой странице сайта — JSON-LD: Organization + Person (для founder/автора) + Article
- **KPI**: технически готово, проверить через rich-results test.

### P1 — высокий приоритет, делать в первые 6 недель

**4. Опубликовать оригинальное исследование (3 недели)**
- Бенчмарк/датасет по своей нише — то, чего нет у конкурентов
- Открытый dataset (HuggingFace), методология, репликабельность
- Препринт на arXiv (при релевантности) + статья на профильных площадках + пост в LinkedIn
- **KPI**: 500+ просмотров на arXiv, 10K+ просмотров на статье, 3+ цитаты в течение квартала.

**5. Reddit + профильная distribution campaign (ongoing, 2–3 поста/нед)**
- 3 профильных сабреддита в нише (для en-видимости)
- Еженедельная экспертная публикация на отраслевой площадке (Habr/VC.ru/индустриальный блог), не промо
- Кейсы клиентов — на бизнес-площадках
- Тема постов: 70% общая экспертиза, 30% product-specific
- **KPI**: 4 публикации до конца квартала, 10+ комментариев в neutral-positive tone.

**6. YouTube-кампания с профильными блогерами (4–6 недель)**
- Список топ-10 релевантных блогеров в нише
- 3 спонсорских разбора + 3 независимых обзора
- Транскрипты обязательно (попадают в training data всех LLM)
- **KPI**: 6 видео опубликованы, суммарно 100K+ просмотров.

### P2 — средний приоритет, квартал

**7. Запустить GEO-tracking — Otterly или собственный prompt-runner (1 неделя)**
- Если бюджет ограничен: Otterly $29/мес для базового мониторинга
- Если сразу серьёзно — Profound $499/мес
- Альтернатива: написать собственный скрипт на API всех 6 платформ, запускать по расписанию еженедельно, выгружать в Google Sheets
- **KPI**: еженедельный отчёт Citation Share, тренд за квартал.

**8. Продуктовая инициатива: AI Visibility Dashboard как feature (6–8 недель)**
- Спецификация: MVP — клиент вводит бренд + 20 prompts → отчёт за 24 часа
- Эксплуатация: использовать существующую модельную карусель/API продукта
- Pricing: [example] базовый / enterprise-тариф с конкурентами
- Pilot с 3–5 брендами бесплатно для кейсов
- **KPI**: MVP запущен, 3 paying customer'а до конца квартала, кейс публично опубликован.

### P3 — поддерживающие, продолжающиеся

**9. Личный бренд founder/автора: автор-схема + ежемесячная статья**
- Person schema на личном сайте с sameAs на LinkedIn, профильные площадки, продукт
- 1 экспертная статья в месяц (не промо, а размышления по индустрии)
- LinkedIn — еженедельный пост (английский, для international LLM training data)
- Подкаст-апы: попасть гостем на 2–3 профильных подкаста
- **KPI**: brand mentions founder'а появляются в LLM-ответах на запрос «[niche] experts» или «[YourProduct] founder».

**10. Schema audit и SSR check (1–2 дня)**
- Убедиться что весь публичный контент отдаётся в HTML без обязательного JS-рендеринга (LLM-краулеры не рендерят JS)
- На блог, документацию, лендинги добавить Article + FAQPage + BreadcrumbList schema
- Проверить через Mobile Friendly Test + Schema Markup Validator
- **KPI**: 100% ключевых страниц с валидным schema, SSR работает.

### Priority табличка

| # | Action | Effort | Impact | Priority | Deadline |
|---|---|---|---|---|---|
| 1 | Baseline GEO-audit | 2 дня | High | P0 | Неделя 1 |
| 2 | Wikipedia-страница | 3–4 нед, $$ | Very High | P0 | Неделя 4 |
| 3 | llms.txt + schema + robots | 1 день | Medium | P0 | Неделя 1 |
| 4 | Оригинальное исследование | 3 нед | Very High | P1 | Неделя 6 |
| 5 | Reddit+профильная distribution | Ongoing | High | P1 | Continuous |
| 6 | YouTube outreach | 4–6 нед, $$ | High | P1 | Неделя 8 |
| 7 | Tracking-tool (Otterly/Profound) | 1 нед, $ | Medium | P2 | Неделя 3 |
| 8 | AI Visibility Dashboard продукт | 6–8 нед | Very High (product) | P2 | Неделя 10 |
| 9 | Личный бренд founder | Ongoing | Medium-High (longterm) | P3 | Continuous |
| 10 | Schema audit + SSR | 1–2 дня | Medium (hygiene) | P3 | Неделя 2 |

### Бюджетный sketch (пример)

- Wikipedia-редактор подрядчик: ~[example] $500
- YouTube outreach (3 спонсорских ролика): ~[example] $3–6K
- Otterly tracking: ~$29/мес
- Profound tracking (если нужно enterprise): ~$499/мес
- Original research (методология+publishing): ~[example] $500
- **Total Q1**: [example] $4–8K на GEO. Окупаемость через рост platform reach.

### Главные KPI на квартал

1. **YourProduct в top-3 ответе** на ключевой категорийный запрос во всех 6 платформах
2. **Wikipedia-страница опубликована** и не удалена в течение 30 дней
3. **1 оригинальное исследование** опубликовано на arXiv + профильной площадке с 10K+ просмотров
4. **AI Visibility Dashboard MVP** — 3 платящих клиента
5. **Citation Share по prompt-set** вырос в 3× от baseline

---

## Sources

### Академические и исследовательские

- [GEO: Generative Engine Optimization (arXiv 2311.09735)](https://arxiv.org/abs/2311.09735) — Aggarwal et al., Princeton/IIT Delhi/Georgia Tech/AI2. KDD 2024. Базовая академическая работа, 9 тактик, GEO-bench 10K queries.
- [Princeton Collaborate page](https://collaborate.princeton.edu/en/publications/geo-generative-engine-optimization/) — institutional reference на paper.
- [arXiv HTML version](https://arxiv.org/html/2311.09735v3) — текстовая версия paper.

### Платформенный citation logic

- [Yext: How AI Engines Decide What to Cite](https://www.yext.com/blog/how-chatgpt-perplexity-gemini-claude-decide-what-to-cite) — sectoral breakdown ChatGPT/Claude/Perplexity/Gemini.
- [Discovered Labs: AI Citation Patterns](https://discoveredlabs.com/blog/ai-citation-patterns-how-chatgpt-claude-and-perplexity-choose-sources) — Wikipedia 47.9% у ChatGPT, Reddit 46.7% у Perplexity, Claude UGC 2-4× выше.
- [Discovered Labs: ChatGPT vs Claude vs Perplexity Citations](https://discoveredlabs.com/blog/chatgpt-claude-perplexity-and-google-ai-overviews-how-each-platform-cites-sources-differently) — углубление по платформам.
- [Lantern: 10 most cited domains](https://www.asklantern.com/blogs/10-most-cited-domains-across-chatgpt-perplexity-gemini-and-claudee-here-s-the-pattern) — кросс-платформенная статистика top-10 доменов.
- [5W Citation Source Index 2026](https://www.prnewswire.com/news-releases/5w-releases-ai-platform-citation-source-index-2026-the-50-websites-that-now-decide-what-brands-are-visible-inside-chatgpt-claude-perplexity-gemini-and-google-ai-overviews-302759804.html) — top 15 доменов = 68% всех AI-цитат.

### Tactical guides

- [Ahrefs: LLM Visibility](https://ahrefs.com/blog/llm-visibility/) — 75K брендов, brand mentions vs backlinks 3:1, YouTube 0.737 correlation.
- [Backlinko / SurferSEO: How to Get Cited by LLMs](https://surferseo.com/blog/llm-citations/) — 7 практических тактик.
- [Authoritytech: Perplexity Citations 2026](https://authoritytech.io/blog/how-to-get-cited-in-perplexity-ai-2026) — 9 source signals для Perplexity.
- [Hashmeta: Chunk-Level Optimization](https://www.hashmeta.ai/en/blog/chunk-level-optimization-how-to-structure-content-for-llm-retrieval) — citation pipeline 4-stage.
- [Discovered Labs: Content Clarity & Verifiability](https://discoveredlabs.com/blog/content-clarity-and-verifiability-the-technical-patterns-that-drive-llm-citations) — какие технические паттерны движут citation.

### Reddit / source dominance

- [Soar Agency: Reddit as Biggest LLM Source](https://www.soar.sh/blog/how-reddit-became-the-biggest-llm-citation-source) — 40.1% всех LLM citations, Google заплатил $60M.
- [Perrill: Why Reddit is Cited in LLMs](https://www.perrill.com/why-is-reddit-cited-in-llms/) — анализ почему.
- [ZipTie: Why Reddit Dominates AI Search 2026](https://ziptie.dev/blog/why-reddit-dominates-chatgpt-perplexity-and-google-ai-overviews/) — кросс-платформенная статистика Reddit citation share.

### Schema.org / llms.txt

- [Soar: Schema.org markup for AI citations 2026](https://www.soar.sh/blog/schema-markup-ai-citations-2026) — что matters в 2026.
- [Averi: Schema Markup Implementation Guide](https://www.averi.ai/blog/schema-markup-for-ai-citations-the-technical-implementation-guide) — техническая имплементация.
- [Presenc AI: State of llms.txt 2026](https://presenc.ai/research/state-of-llms-txt-2026) — 3.2% adoption, no major AI committed.
- [AEO Engine: llms.txt Zero Usage](https://aeoengine.ai/blog/llms-txt-zero-usage-ai-bots-ignore) — критический взгляд, «AI Bots Ignore It».
- [Codersera: llms.txt Honest Guide May 2026](https://codersera.com/blog/llms-txt-complete-guide-2026/) — текущая адопция.

### Traffic loss / zero-click

- [SparkToro: 2024 Zero-Click Study](https://sparktoro.com/blog/2024-zero-click-search-study-for-every-1000-us-google-searches-only-374-clicks-go-to-the-open-web-in-the-eu-its-360/) — Rand Fishkin, 58.5% US, 59.7% EU.
- [PPC Land: HubSpot AEO Tool + 27% Traffic Drop](https://ppc.land/hubspot-launches-aeo-tool-as-organic-traffic-drops-27-for-its-customers/) — HubSpot ответ на zero-click.
- [AthenaHQ: HubSpot Lost 70%](https://athenahq.ai/blog/hubspot-lost-70-of-its-seo-trafficbut-that-doesnt-mean-its-losing) — анализ потери траффика.
- [PikaSEO: Zero-Click Search 2026 AI Overviews](https://pikaseo.com/articles/zero-click-search-ai-overviews-2026) — 58% click cut.
- [Superprompt: Zero-Click Crisis Worsens](https://superprompt.com/blog/zero-click-search-worsens-58-percent-google-no-clicks-november-2025-recovery-strategies) — Nov 2025 update.
- [Digital Bloom: 2026 Organic Traffic Crisis Update](https://thedigitalbloom.com/learn/organic-traffic-crisis-report-2026-update/) — статистика по медиа.

### Tools

- [Surmado: Best AI Visibility Tools 2026](https://www.surmado.com/blog/best-ai-visibility-tools-2026) — Profound vs Peec vs Otterly comparison.
- [Promptwatch: Best GEO and AI Visibility Platforms 2026](https://promptwatch.com/best-geo-and-ai-visibility-platforms-compared-2026) — обзор tools.
- [Discovered Labs: Profound vs Peec vs Otterly](https://discoveredlabs.com/blog/profound-vs-peec-vs-otterly-which-ai-visibility-platform-should-you-buy) — direct comparison.
- [Profound: What is AEO](https://www.tryprofound.com/resources/articles/what-is-answer-engine-optimization) — определение AEO от категорного лидера.
- [Otterly: Perplexity SEO 2026](https://otterly.ai/blog/perplexity-seo/) — guide на их блоге.

### Conversion & traffic

- [ALM Corp: ChatGPT 31% Higher Conversion](https://almcorp.com/blog/chatgpt-vs-organic-search-conversion-rate/) — конкретные цифры conversion.
- [Stan Ventures: LLM vs Organic Conversion](https://www.stanventures.com/news/llm-vs-organic-search-conversion-study-4266/) — alternative data, no statistical significance.
- [Emarketed: AI Referral Converts 4.4x Higher](https://emarketed.com/aeo/ai-referral-traffic-conversion-value-2026/) — мета-анализ.
- [Lantern: ChatGPT 87% of AI Referral Traffic](https://www.asklantern.com/blogs/chatgpt-drives-87-of-ai-referral-traffic) — share AI traffic by platform.
- [The Stacc: 42 AI Search Referral Stats 2026](https://thestacc.com/blog/ai-search-referral-traffic-stats/) — комплексная статистика.

### Russian context

- [GeoScout: (regional LLM B) brand recommendations](https://geoscout.pro/en/blog/gigachat-how-it-recommends-brands) — Russian AI brand mentions, 2-3× difference (regional LLM B) vs Alice.
- [TADviser: AI Russia market](https://tadviser.com/index.php/Article:Artificial_Intelligence_(Russian_market)) — overview Russian AI market.
- [MySummit: (regional LLM A) Review 2026](https://mysummit.school/blog/en/yandexgpt-review-2026/) — Russian AI platform review.
- [MySummit: Best AI for Managers Russia 2026](https://mysummit.school/blog/en/best-ai-for-managers-russia-2026/) — 52 моделей, 3300+ оценок.

### Conductor / industry analysis

- [Conductor: AEO Academy](https://www.conductor.com/academy/answer-engine-optimization/) — enterprise guide.
- [Conductor: AEO/GEO Benchmarks 2026](https://almcorp.com/blog/aeo-geo-benchmarks-2025-conductor-analysis-complete-guide/) — 3.3B sessions analysed.
- [CMSWire: Conductor AgentStack Launch](https://www.cmswire.com/digital-experience/conductor-launches-agentstack-for-aeo/) — industry move.

### WordLift / entity SEO

- [WordLift: Future of SEO and LLMs (BrightonSEO)](https://wordlift.io/blog/en/the-future-of-seo-and-the-role-of-llms/) — Andrea Volpini keynote.
- [WordLift: Understanding LLM Optimization](https://wordlift.io/blog/en/understanding-llm-optimization/) — entity-driven подход.
- [WordLift: Knowledge Graph + LLM](https://wordlift.io/blog/en/knowledge-graph-and-llm/) — semantic web tactic.

### HubSpot AEO case studies

- [HubSpot Blog: How HubSpot Became #1 CRM in AI Search](https://blog.hubspot.com/marketing/hubspot-aeo-case-study) — самоотчёт HubSpot AEO.
- [HubSpot Blog: AEO Case Studies that Prove ROI](https://blog.hubspot.com/marketing/answer-engine-optimization-case-studies) — кросс-кейсы.
- [Nextiny: HubSpot AEO Case Study Human-to-Answer](https://blog.nextinymarketing.com/hubspot-aeo-case-study-how-we-increased-ai-brand-visibility-in-weeks-using-the-human-to-answer-framework) — 0% → 35% за недели.

### Other industry studies

- [Chatoptic: 62% Overlap Google vs ChatGPT](https://www.chatoptic.com/blog/google-chatgpt-visibility-study) — только 62% совпадение.
- [Virayo: LLM SEO B2B Guide](https://virayo.com/blog/llm-seo) — B2B-фокусированный гайд.
- [Position Digital: 150+ AI SEO Stats 2026](https://www.position.digital/blog/ai-seo-statistics/) — компиляция статистики.
- [Search Engine Land: Zero-Click Searches Up](https://searchengineland.com/zero-click-searches-up-organic-clicks-down-456660) — отраслевой апдейт.

### Reference (mentioned, not primary)

- arXiv: 2406.17526 (LumberChunker) — про chunking длинных нарративов.
- 5W AI Citation Source Index 2026 — индустриальный benchmark.
- Quoleady + Search Atlas (December 2024) — schema correlation study, без прямого URL.

---

*Референс подготовлен как контекст для маркетинговой стратегии под видимость в генеративных AI-системах. Май 2026.*
