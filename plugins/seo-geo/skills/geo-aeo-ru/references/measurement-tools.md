# Метрики и инструменты GEO-трекинга

> Все цифры — из `[local-source]` (разделы 4, 5). Не выдумывай новых.

## 1. Что мерить (7 метрик)

| Метрика | Что показывает | Как считать |
|---------|----------------|-------------|
| **Citation Share** | % ответов на тестовый prompt-set, где упомянут твой бренд | прогнать 100-500 промптов через API, считать частоту упоминаний |
| **Share of Voice (SoV)** | доля твоего бренда vs конкурентов в LLM-ответах | сравнительный анализ по prompt-set: упоминания тебя / (тебя + конкурентов) |
| **Sentiment in LLM** | тон упоминаний (позитив/нейтрал/негатив) | manual или LLM-classifier |
| **AI Overview Presence** | % твоих ключей, где появляется AIO и ты в ней | Google Search Console + ручной check |
| **LLM Referral Traffic** | сессии из ChatGPT/Perplexity/Claude/Gemini | GA4 / Метрика — matching по referrer |
| **Brand Mention Velocity** | темп роста brand mentions на цитируемых доменах | Mention / Ahrefs / Semrush |
| **Hallucinated URLs** | LLM генерирует «фейковые» URL под твой бренд | мониторинг 404 в server logs |

**Главная пара для baseline:** Citation Share (есть/нет тебя) + Share of Voice (ты vs конкуренты).
Остальное — углубление.

## 2. Методология промпт-аудита

### Prompt-set: 5 типов промптов

Базовый аудит для любого бренда — 5 категорий, по 10 промптов = 50 на платформу:

1. **Brand direct** — «Расскажи про [Бренд]», «Что такое [Бренд]?»
   → проверяет **training data inclusion** (модель вообще знает бренд?).
2. **Category** — «Лучшие [категория] инструменты для [задача]», «Топ-альтернативы [Конкурент]»
   → проверяет, в **шортлисте** ли твой бренд.
3. **Comparison** — «[Бренд] vs [Конкурент]»
   → проверяет наличие и **тон**.
4. **Problem-aware** — «Как мне решить [проблему, которую решает бренд]?»
   → **самый сильный сигнал** товарного фита (бренд всплывает без упоминания имени).
5. **Niche / long-tail** — специфические запросы из реальных юз-кейсов клиентов.

### Прогон по 6 платформам

ChatGPT / Claude / Perplexity / Gemini / GigaChat / YandexGPT (+ Яндекс Нейро для РФ).
**Каждую платформу — отдельно** (логика выбора источников у всех разная).

**50-100 промптов × 6 платформ = базовый audit.**

Инструменты прогона:
- **Свой агрегатор LLM** (если есть) — прогон через несколько моделей разом.
- `multi-model-gateway` — кросс-модельный прогон.
- `perplexity` — для Perplexity-специфики (citations).
- Свой скрипт на API всех 6 платформ + crontab + Google Sheets/Метрика.

### Чек-лист «мой бренд попал в ответ?» (на каждый ответ)

- [ ] Бренд упоминается напрямую (текстом)?
- [ ] Бренд упоминается со ссылкой на оф. сайт?
- [ ] В каком источнике LLM нашёл бренд (Wikipedia / Reddit / личный сайт)?
- [ ] Тон описания (позитив / нейтрал / негатив)?
- [ ] Корректна ли информация (категория, USP)?
- [ ] Не путается ли LLM с конкурентом?
- [ ] Какие конкуренты упомянуты рядом?
- [ ] В какой позиции (первый / middle / последний)?

## 3. Инструменты GEO-tracking (с ценами)

| Инструмент | Цена (Lite) | Что умеет | Кому |
|------------|-------------|-----------|------|
| **Profound** | $499/мес | полный enterprise GEO suite, prompt monitoring, competitor benchmarks | enterprise, агентства |
| **Peec AI** | mid-market | Series A $21M (ноя 2025), $100M+ valuation, sweet spot SMB+ | mid-market |
| **Otterly** | **$29/мес** | самый дешёвый, Gartner Cool Vendor 2025, базовый prompt tracking | solo / стартапы |
| **AthenaHQ** | enterprise | основатели ex-Google Search / DeepMind | серьёзные команды |
| **Mention** | $49+/мес | brand monitoring (не специализирован под LLM, но мониторит mentions) | brand tracking |
| **BrandIndex (YouGov)** | enterprise | consumer perception tracking | big brands |
| **Lantern, xSeek, GenRankEngine, ZipTie** | разное | нишевые GEO-трекеры | эксперименты |
| **Manual (ChatGPT API + prompt-set + sheet)** | $0-50 | свой prompt audit | solopreneurs, технари |

> ⚠️ **Критично для РФ:** **ни один** западный инструмент (Profound, Otterly, Peec, AthenaHQ)
> **НЕ мониторит GigaChat / YandexGPT / Яндекс Нейро.** Это слепая зона. Для русского контура —
> только свой prompt-runner или свой агрегатор LLM. Подробно: `russian-llm.md`.

**Рынок GEO-услуг:** $886M в 2024 → прогноз $7.3B к 2031 (CAGR 34%). Сейчас **92% брендов
невидимы в ChatGPT** — большой headroom.

## 4. Бенчмарки по конверсии (зачем вообще GEO)

- ChatGPT B2B conversion: **14.2-15.9%** (vs Google organic 1.76-2.8%)
- Perplexity: 10.5% · Claude: 5% · Gemini: 3%
- Industry consensus: AI-трафик конвертит **в 4-14× выше** organic
- AI traffic share: ~1% от веба, но рост **+527% за 5 месяцев** (Jan→May 2025)

→ объём маленький, но качество и темп роста делают канал стратегически важным.

## 5. Источники

- Princeton GEO study: arXiv:2311.09735 (Aggarwal et al., KDD 2024) — GEO-bench 10K queries.
- Ahrefs LLM Visibility (75K брендов, 17M citations): ahrefs.com/blog/llm-visibility/
- Semrush LLM Citation Source Study — source dominance.
- Conductor 2026 AEO/GEO Benchmarks — 3.3B sessions, 13K+ доменов.
- Полный список со ссылками: `geo_llm_seo_research.md` раздел Sources.
