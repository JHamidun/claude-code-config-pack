---
name: geo-aeo-ru
description: "GEO/AEO/LLM SEO — видимость бренда в ответах ChatGPT, Perplexity, (regional LLM A); Citation Share, llms.txt. Триггеры: «попасть в ответы AI»."
metadata:
  version: 1.1.0
  updated: 2026-07-18
  source: "geo_llm_seo_research.md + Princeton GEO study (arXiv 2311.09735) + скрипты: zubair-trabzada/geo-seo-claude (MIT)"
  reuses: seo-machine-ru, ai-seo-agent-pipeline, schema-markup-ru, perplexity, multi-model-gateway, yandex
---

# GEO / AEO / LLM SEO — видимость бренда в AI-ответах (RU)

Playbook по **Generative Engine Optimization**: как сделать так, чтобы твой бренд/продукт
появлялся в ответах ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews, а в российском
контуре — (regional LLM B), (regional LLM A), Яндекс Нейро.

Это **не редакционный** и **не программатический** скилл про создание контента. Это
**стратегия видимости**: измерить, где ты сейчас в AI-ответах, понять как LLM выбирают источники,
применить тактики попадания, замерить рост Citation Share.

> **Источник истины:** `references/geo-llm-seo-research.md` (локальная копия research'а, все цифры
> со ссылками на Princeton/Ahrefs/Semrush/Conductor). Цифры в этом скилле — оттуда.
> **Не выдумывай новых бенчмарков** — если числа нет в research, говори «нет данных».

---

## Границы со смежными скиллами (читай перед стартом)

| Задача | Скилл | Почему не сюда |
|--------|-------|----------------|
| Написать SEO-статью под Яндекс, семантическое ядро, кластер | `seo-machine-ru` | там Python-пайплайн качества + Wordstat/Tilda стек |
| Массовая генерация сотен страниц (1 ключ = 1 страница, n8n) | `ai-seo-agent-pipeline` | там программатическая фабрика страниц |
| Базовая нота «что любит цитировать каждый движок» | `seo-machine-ru/references/aeo-geo.md` | там краткий чеклист; **здесь** — полная стратегия с измерением |
| Сама JSON-LD разметка (Article/FAQPage/Person) | `schema-markup-ru` | там шаблоны; здесь — какая schema нужна для GEO и почему |
| Прогон промптов через несколько моделей | `perplexity` / `multi-model-gateway` | инструменты; здесь — методология аудита |

**Этот скилл отвечает на:** «мой бренд вообще видят в AI?», «как измерить?», «как попасть?»,
«чем (regional LLM B) отличается?». Стратегия и измерение, не текст.

---

## Что такое GEO / AEO / LLM SEO

**Три названия — одна суть:** оптимизация контента под видимость в ответах генеративных AI.

| Термин | Расшифровка | Кто ввёл |
|--------|-------------|----------|
| **GEO** (Generative Engine Optimization) | под генеративные движки | Aggarwal et al., Princeton/IIT Delhi, arXiv 2311.09735, KDD 2024 |
| **AEO** (Answer Engine Optimization) | под «движки ответов» | Conductor, индустрия 2024-2025 |
| **LLM SEO / AI SEO / AISO** | народные варианты | индустрия |

GEO и AEO — синонимы на ~90%. GEO про модель, AEO про UX-формат ответа. Используем GEO как
зонтик (первым появился в академии).

### Почему это новый рынок, а не extension SEO

- **GEO ≠ SEO.** Только **12% URL**, цитируемых AI, пересекаются с топ-10 Google. Только **62%**
  совпадение между ранжированием Google и видимостью ChatGPT. Это два разных рынка.
- **Brand mentions обогнали backlinks.** Ahrefs (75K брендов): brand mentions коррелируют с
  AI Overview presence в **3:1 над backlinks**. YouTube mentions — 0.737 корреляция, web mentions
  0.664, классический Domain Rating — всего 0.218.
- **Что НЕ работает:** keyword stuffing (Princeton: «no improvement»), технический жаргон,
  авторитетный тон без подтверждений. Часть классических SEO-приёмов в GEO бесполезна.

### Кризис, который это породил (аргумент перед клиентом/руководством)

- **Zero-click: 60%** запросов в 2024 → **80-83%** на запросах с AI Overviews в 2026.
- **HubSpot потерял 70-80%** органики (13.5M → 6-7M → <1M) за 2024-2025. Канонический кейс.
- **Но AI-трафик конвертит в 4-14× выше** Google organic (ChatGPT B2B 14-16% vs 1.76%). Объём
  пока ~1% веба, но рост **+527% за 5 месяцев**. Маленький, но качественный и быстрорастущий канал.

→ детали и все источники: `references/tactics.md` (раздел «Кризис и цифры»).

---

## Как LLM выбирают источники (3 канала + citation pipeline)

**Три фундаментально разных пути попасть в ответ:**

1. **Training data** — модель «запомнила» бренд при обучении (Common Crawl, Reddit, Wikipedia,
   лицензированные датасеты). Долгая ставка. Главный сигнал для Claude.
2. **RAG / live browsing** — модель лезет в индекс в момент ответа (ChatGPT→Bing, Perplexity→свой
   краул, Gemini→Google, Яндекс Нейро→Яндекс). Быстрорастущая ставка.
3. **Citation в видимом ответе** — то самое «попасть в [1], [2], [3]». Perplexity, иногда
   ChatGPT/Gemini, Claude через Citations API.

Большинство тактик целят в **#2 + #3** (быстро), но настоящий moat — **#1** (массовые упоминания
на цитируемых доменах → попасть в обучающие данные следующего поколения моделей).

**Citation pipeline (4 стадии):** query fan-out (запрос → 8-12 sub-queries) → chunking & retrieval
→ passage selection (claim density, entity clarity, recency) → attribution. Большинство SEO-контента
валится на retrieval, потому что «зарывает ответ» в середину статьи — LLM не дочитает.

### Кто что любит цитировать (краткая матрица)

| Движок | Главный источник | Что любит | Training vs Live |
|--------|------------------|-----------|------------------|
| **ChatGPT** | Wikipedia (47.9% top-10) | энциклопедичность, entity clarity, recency, Bing-индекс | Medium / High |
| **Perplexity** | **Reddit (46.7%)** | BLUF в первых 100 словах, свежесть (×3.2 за 30 дн), schema, inline-citations | Low / Very High |
| **Claude** | UGC (2-4× выше других), NYT/Atlantic | формальный тон, verifiable claims, престижная журналистика, bullet-points (+30%) | High / Low (off по умолчанию) |
| **Gemini / AI Overviews** | Google index + Reddit (21%) | традиционный SEO, Google Business Profile, structured data | Medium / High |
| **(regional LLM B)** | RU-веб, новости | присутствие в RU-инфополе (vc/Habr), бизнес-фокус | High / Medium |
| **(regional LLM A) / Нейро** | Яндекс-индекс | топ Яндекса + структурированные ответы + FAQ | — |

**Концентрация авторитета:** top-15 доменов = **68% всех AI-цитат** (5W Index 2026). Source
dominance (Semrush, 17M citations): Reddit 40.1%, Wikipedia 26.3%, YouTube 23.5%.

→ полный разбор каждого движка: `references/tactics.md` (раздел «Как движки выбирают источники»).

---

## Тактики попадания (что реально работает)

**Princeton GEO study** (9 тактик на GEO-bench, 10K queries). Что даёт **+30-40%** к visibility:

| Тактика | Эффект | Как |
|---------|--------|-----|
| **Quotation Addition** | +30-40% | релевантные цитаты от других источников |
| **Statistics Addition** | +30-40% | числа, проценты, конкретика |
| **Cite Sources** | +30-40% | ссылки на авторитетные источники внутри контента |
| Fluency / Easy-to-Understand | +15-30% | читабельность, упрощение |
| ~~Keyword Stuffing~~ | ~0% | **НЕ работает** |
| ~~Authoritative tone~~ | ~0% | **НЕ работает** без подтверждений |

**Контент-принципы:** BLUF (главный ответ в первых 100 словах — 90% выигравших Perplexity-цитат),
chunk-friendly структура (блоки по 150 слов), density of claims (один параграф = одно проверяемое
утверждение с числом), original research (корреляция 0.79 с visibility), recency stamps,
FAQ-секции, comparison-контент («vs», «best», «top»).

**Distribution (где публиковать, Tier 1):** Reddit (40% цитат), Wikipedia (26%), YouTube (0.737
корреляция), Quora, Substack/Medium. **Нельзя постить про себя с brand-аккаунта** — модерация банит.

**Технические артефакты:** schema (Article + FAQPage + Person + Organization — hygiene, не magic),
llms.txt (только 3.2% сайтов, downside нулевой, upside спекулятивный — делать «на всякий случай»),
robots.txt **allow** для GPTBot/ClaudeBot/PerplexityBot/Google-Extended/CCBot (блокировка =
самоубийство в долгую). **SSR обязателен** — AI-краулеры не рендерят JavaScript.

→ полный список тактик с приоритетами и числами: `references/tactics.md`.

---

## Workflow: аудит видимости бренда в AI

Базовая последовательность (применима к любому бренду):

1. **Собрать prompt-set (50 промптов, 5 типов):**
   - *Brand direct:* «Расскажи про [Бренд]» — проверка training data inclusion
   - *Category:* «Лучшие [категория] для [задача]» — в шортлисте ли ты
   - *Comparison:* «[Бренд] vs [Конкурент]» — наличие и тон
   - *Problem-aware:* «Как решить [проблему, которую решает бренд]?» — самый сильный сигнал фита
   - *Niche / long-tail:* специфические запросы из реальных юз-кейсов клиентов

2. **Прогнать через 6 платформ:** ChatGPT, Claude, Perplexity, Gemini, (regional LLM B), (regional LLM A)
   (+ Яндекс Нейро для РФ). Инструмент — `multi-model-gateway`, `perplexity` или любой
   агрегатор моделей в одном окне. 50 промптов × 6 платформ = базовый аудит.

3. **Зафиксировать baseline по чеклисту** (для каждого ответа):
   - [ ] Бренд упомянут напрямую? Со ссылкой на оф. сайт?
   - [ ] Из какого источника LLM взял бренд (Wikipedia/Reddit/личный сайт)?
   - [ ] Тон (позитив/нейтрал/негатив)? Корректна ли категория/USP?
   - [ ] Не путается ли с конкурентом? Какие конкуренты рядом? В какой позиции?

4. **Посчитать метрики:** Citation Share (% ответов с упоминанием), Share of Voice (доля vs
   конкуренты), Sentiment, Top sources. → методология: `references/measurement-tools.md`.

5. **Найти гэпы → план:** где конкуренты есть, а тебя нет = что создать/где засеяться.

6. **Поставить трекинг:** Otterly ($29/мес), Profound ($499), или свой prompt-runner на API.
   Перемерить через квартал, сравнить с baseline.

→ метрики, инструменты с ценами, методология промпт-аудита: `references/measurement-tools.md`.

---

## Скрипты (исполняемая механика, scripts/)

Методология выше — «что проверять»; скрипты — реально проверяют. Все выводят JSON в stdout,
зависимости: `requests` + `beautifulsoup4` (уже стоят). Портировано из geo-seo-claude (MIT)
с RU-адаптацией (кириллица-паттерны, YandexBot, ru-wiki, Habr/vc.ru).

```bash
cd ~/.claude/skills/geo-aeo-ru/scripts

# 1. Citability: скоринг пассажей страницы 0-100 (134-167 слов, BLUF, цифры, self-containment)
python citability_scorer.py https://site.ru/article

# 2. llms.txt: проверить наличие/формат ИЛИ сгенерировать по главной
python llmstxt_generator.py https://site.ru            # validate
python llmstxt_generator.py https://site.ru generate   # → generated_llmstxt в JSON

# 3. Технический фетч: страница/robots (доступ 16 AI-краулеров, вкл. YandexBot)/llms/sitemap/всё
python fetch_page.py https://site.ru robots
python fetch_page.py https://site.ru full

# 4. Brand mentions: Wikipedia en+ru / Wikidata (API-проверка) + чек-листы YouTube/Reddit/LinkedIn/Habr
python brand_scanner.py "YourBrand" yourbrand.ru
```

Куда смотреть в выводе: `average_citability_score` + `bottom_5_citable` (что переписать),
`ai_crawler_status` (BLOCKED = невидимость), `has_ssr_content: false` = AI-краулеры видят пустоту,
`has_wikipedia_page_ru/en` + `has_wikidata_entry` (training-data блокер).

Скрипты НЕ заменяют промпт-аудит (workflow выше) — они проверяют сайт, а не ответы LLM.

---

## Российская специфика (главное отличие этого скилла)

**Западные GEO-тулы (Profound, Otterly, Peec AI, AthenaHQ) НЕ мониторят (regional LLM B) / (regional LLM A) /
Яндекс Нейро.** Это слепая зона — и одновременно возможность.

- **(regional LLM B) vs (regional LLM A)/Alice:** одни и те же бренды показывают **2-3× разную Share of Voice**
  между ними (GeoScout). → отдельный мониторинг каждой русской платформы обязателен.
- **(regional LLM B) (ClientCorp3):** обучен на русскоязычных данных, бизнес-фокус, экосистема Сбера. Любит
  присутствие в RU-инфополе (vc.ru, Habr, новости). Training-weight высокий.
- **(regional LLM A) / Alice / Нейро:** поверх Яндекс-индекса. Оптимизация = классический SEO под Яндекс
  (см. `seo-machine-ru` + `yandex`) + структурированные ответы + FAQ + recency. 12% пользователей
  нейросетей в РФ выбирают (regional LLM A).

→ полный разбор русских LLM + почему западные тулы их не видят + стратегия под русские платформы:
`references/russian-llm.md`.

---

## Как применить это к своему продукту (двойная игра)

GEO обычно даёт две параллельные выгоды — используй обе:

**(1) Попасть в ответы как рекомендуемый вариант в своей категории.** Цель: на категорийный или
problem-aware запрос («какие есть [категория] для [задача]?», «чем решить [проблема]?») твой бренд
оказывается в ответе ChatGPT/Perplexity/Claude рядом с конкурентами, желательно в выгодной
формулировке категории. Типовые блокеры: нет Wikipedia-страницы (критично для Claude/ChatGPT
training data), нет sustained Reddit/Habr presence, нет оригинального исследования как
citation-магнита. Прогони workflow-аудит выше, найди свой блокер и закрой его.

**(2) GEO-видимость как продуктовая фича или платная услуга.** Тот же движок — «AI Visibility
Dashboard»: клиент вводит бренд + 20 промптов → прогон по 6 платформам (включая (regional LLM B)/(regional LLM A),
которых нет у западных тулов) → Citation Share + PDF-отчёт. Уникальная позиция на RU-рынке —
мониторинг ВСЕХ платформ сразу, а не только западных. Упакуй как SaaS-подписку или как разовый
аудит-пакет (пример вилки: 5–15K RUB/мес за мониторинг). Продажную обвязку и структуру
proposal см. в `references/geo-audit-service.md`.

→ шаблон action-plan P0/P1/P2 с KPI, бюджетом и дедлайнами: `references/action-plan.md`.

---

## References (читать по необходимости)

| Файл | Когда |
|------|-------|
| `references/measurement-tools.md` | метрики SoV/Citation Share, инструменты трекинга с ценами, методология промпт-аудита |
| `references/tactics.md` | полный список тактик попадания (Princeton +30-40%, distribution, schema, llms.txt, кризис и цифры, разбор каждого движка) |
| `references/russian-llm.md` | (regional LLM B)/(regional LLM A)/Нейро специфика, почему западные тулы их не видят, стратегия под русские LLM |
| `references/action-plan.md` | шаблон P0/P1/P2 action plan под свой бренд с KPI и бюджетом |
| `references/geo-audit-service.md` | GEO-аудит как платная услуга: пакеты, proposal-структура, white-label |

## Связки (не дублировать — звать существующее)

- Написание контента под цитируемость → `seo-machine-ru` (роли + Python-пайплайн).
- Массовая генерация страниц под long-tail → `ai-seo-agent-pipeline`.
- JSON-LD разметка (Article/FAQPage/Person/Organization) → `schema-markup-ru`.
- Прогон промптов через модели → `multi-model-gateway` / `perplexity`.
- Публикация на площадки (Habr/VC/RBC/LinkedIn) для distribution → скиллы публикации постов, `tilda`.

## Реальный опыт (changelog/уроки)

- **v1.1 (2026-07-18):** добавлена исполняемая механика `scripts/` (citability_scorer /
  llmstxt_generator / fetch_page / brand_scanner) — порт из zubair-trabzada/geo-seo-claude (MIT,
  9K★) с RU-адаптацией: кириллица-паттерны в скоринге, YandexBot в robots-чеке, ru-wiki +
  Habr/vc.ru в brand-скане, UTF-8 stdout под Windows, lxml опционален. Смок пройден
  (py_compile + usage). Плюс `references/geo-audit-service.md` — продажная обвязка «GEO-аудит как услуга».
- **v1.0 (2026-06-22):** создан из research'а по GEO/LLM SEO. Все бенчмарки — из research.
  Отделён от `seo-machine-ru` (контент под Яндекс) и `ai-seo-agent-pipeline` (программатическая
  фабрика): этот скилл — про ИЗМЕРЕНИЕ видимости и СТРАТЕГИЮ попадания в LLM-ответы + российскую специфику.
- **Главный инсайт для РФ:** западные GEO-тулы не видят (regional LLM B)/(regional LLM A)/Нейро → у любого
  RU-бренда есть уникальная возможность для GEO-мониторинга этих платформ.
