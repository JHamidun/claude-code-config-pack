---
name: seo-machine-ru
description: "SEO/GEO/AEO контент-машина RU: исследование → написание → оптимизация → публикация лонгридов под Яндекс-стек (Метрика/Вебмастер/Wordstat) и Tilda; семантическое ядро, цитируемость в AI-поиске. Триггеры: «операторы вордстат», «кластер статей». НЕ: посты→tg-post."
metadata:
  version: 1.1.0
  updated: 2026-06-03
  ported_from: TheCraigHewitt/seomachine (+ marketingskills ai-seo/seo-audit/programmatic-seo/competitors)
  reuses: yandex, tilda, yourname-marketing-context, competitive-analysis
---

# SEO / GEO / AEO машина (RU)

Полный конвейер производства SEO-контента под российский поиск и AI-выдачу. Портирован с `seomachine`, но все внешние интеграции заменены на твой стек: данные тянутся скиллом `yandex` (Метрика/Вебмастер/Wordstat), публикация — скиллом `tilda`. Аналитические модули переписаны под русский (морфология, читаемость, anti-AI на русском).

**Перед любой задачей** прочитай контекст продукта: вызови `yourname-marketing-context` → `skills/yourname-marketing-context/references/business.md` (или `personal-brand.md` для блога пользователя) и `skills/yourname-marketing-context/references/ru-localization.md`.

## Когда использовать

- Семантическое ядро / кластеры под Яндекс (`research`, `cluster`).
- Написание и оптимизация лонгрида (`write`, `optimize`, `rewrite`).
- Аудит существующей страницы («почему не в топе»).
- GEO/AEO: попасть в ответы Яндекс Нейро / Alice / (regional LLM B) / ChatGPT / Perplexity.
- Лендинг под конверсию + CRO-аудит (связка с кластером `*-cro-ru`).
- Размещение в каталогах для ссылок и цитируемости (RU-каталоги).

## Архитектура: фазы → чеклисты-роли → Python

Команда (фаза) запускает аналитические **роли** (`references/agents-checklists.md`) и **Python-скрипты** (`scripts/`). Это та же модель command→agent→python из seomachine, но без отдельного репозитория — всё внутри скилла.

### Фазы (workflow)

| Фаза | Что делает | Чем | Выход |
|------|-----------|-----|-------|
| **research** | семантика + топ-10 Яндекса + гэпы + бриф | `yandex` (Wordstat/Вебмастер) → `scripts/opportunity_scorer.py`; роль keyword-mapper | бриф `research/brief-<slug>.md` |
| **cluster** | пиллар + 8-12 спутников + карта перелинковки | роль cluster-strategist + opportunity_scorer | `research/cluster-<slug>.md` |
| **write** | статья 1500-3000 слов, AEO-ready | роли + после: `scrub` → `content_scorer.py` (порог 70) | `drafts/<slug>.md` |
| **optimize** | финальный SEO-проход, 0-100 | `seo_quality_rater_ru.py` + роли seo-optimizer/meta-creator/internal-linker | отчёт + правки |
| **rewrite** | обновление старого материала | те же + диф изменений | `rewrites/<slug>.md` |
| **audit** | разбор URL/файла, почему не ранжируется | `seo_quality_rater_ru.py` + Вебмастер позиции | `audits/<slug>.md` |
| **aeo** | оптимизация под AI-цитирование | `references/aeo-geo.md` | план цитируемости |
| **publish** | публикация на сайт | скилл `tilda` (Feeds/page) | пост/страница в Tilda |

Подробный сценарий каждой фазы: `references/workflow.md`.

## Python-пайплайн (`scripts/`)

Все скрипты — чистый stdlib (pymorphy2 опционально, есть fallback). Запуск из папки `scripts/`.

| Скрипт | Что считает | Запуск |
|--------|-------------|--------|
| `content_scorer.py` | композит 5 измерений (humanity/specificity/structure/seo/readability), порог 70, JSON для авто-ревайза | `python content_scorer.py draft.md --kw "ключ"` |
| `seo_quality_rater_ru.py` | on-page SEO 0-100 по RU-гайдлайнам (объём, H2, мета, ссылки, плотность, AEO-intro) | `python seo_quality_rater_ru.py draft.md --kw "ключ"` |
| `readability_ru.py` | Флеш-Оборнева + водность (Главред) + структура | `python readability_ru.py draft.md` |
| `keyword_analyzer_ru.py` | плотность с лемматизацией, распределение, переспам | `python keyword_analyzer_ru.py draft.md --kw "ключ1" "ключ2"` |
| `content_scrubber.py` | чистит невидимые Unicode + типографика RU (НЕ трогает `---`/таблицы — фикс v1.1) | `python content_scrubber.py draft.md --in-place` |
| `opportunity_scorer.py` | приоритет ключей (8 факторов, CTR-кривая Яндекса) | `python opportunity_scorer.py keywords.json` |
| `wordstat_fetch.py` | реальные частоты Wordstat через internal API (headless, на cookie) | `python wordstat_fetch.py kw.txt --cookie "..."` |
| `wordstat_browser_snippet.js` | тот же съём частот через `browser_evaluate` на залогиненной странице | paste в browser_evaluate |
| `build_report_docx.py` | упаковка brief/cluster/draft в один Word-файл для стейкхолдера | `python build_report_docx.py --title T --out r.docx --draft d.md` |

**Цикл `write`:** написать → `content_scrubber.py --in-place` → `content_scorer.py`. Если `composite < 70` — применить `priority_fixes`, переписать (до 2 итераций), затем `seo_quality_rater_ru.py` для финального скора.

## Данные и публикация (НЕ дублировать — звать существующее)

- **Wordstat / частотность / Вебмастер-позиции / Метрика-трафик** → скилл `yandex`. Как именно — `references/data-yandex-tilda.md`.
- **Публикация поста/лендинга** → скилл `tilda`.
- **Конкуренты** → `competitive-analysis` / `similarweb-analytics`.
- **Метрики YourProduct** (что докрутить) → `product-analytics`.

`opportunity_scorer.py` ест JSON-массив ключей с полями `{keyword, volume, position, intent, competition, cluster_size}` — собери его из вывода Wordstat/Вебмастера через скилл `yandex`.

## Яндекс/Google SERP локально (openserp)

Self-hosted SERP API (`karust/openserp`, Docker) — бесплатная замена SerpAPI для сырого парсинга топ-выдачи (без carousels/Maps/Shopping/Trends — за этим оставайся на `serpapi`). Поднимается **локально** на машине пользователя (Docker Desktop), НЕ на your-server (сервер перегружен — steal 65-76%, см. память).

**Когда брать вместо SerpAPI:**
- Нужна чужая топ-10 выдача (конкуренты) по десяткам ключей кластера без траты платных SerpAPI-кредитов.
- DuckDuckGo/Bing-выдача для быстрой сверки без API-ключа.
- Яндекс-выдача (SerpAPI её не отдаёт вообще) — **см. гочу ниже, из коробки НЕ работает**.

**Запуск:**
```bash
docker run -d --name openserp -p 127.0.0.1:7000:7000 --restart unless-stopped karust/openserp:latest serve -a 0.0.0.0 -p 7000
```
Bind только на `127.0.0.1` — не открывать наружу. Проверить: `docker ps --filter name=openserp`, логи — `docker logs openserp`.

**Эндпоинты (проверено curl, 2026-07-20):**
- `GET /duckduckgo/search?text=<query>&limit=10` — **работает из коробки**, полный JSON (organic + ads + related_searches + pagination).
- `GET /bing/search?text=<query>&limit=10` — отвечает 200 с JSON, но в тесте выдал гео-нерелевантные результаты (нужна проверка `region`/`lang` параметров под RU перед продовым использованием).
- `GET /yandex/search?text=<query>&lang=RU&limit=10` — ⚠️ **из коробки НЕ работает**: стабильно `{"error":"captcha_detected","code":429}` даже с одиночным запросом и после паузы 40с (не burst-rate, а IP-блок).
- `GET /google/search?text=<query>&limit=10` — ⚠️ то же самое: `{"error":"blocked","code":429,"error_detail":"rate_limited"}` стабильно.
- `GET /mega/search?engines=bing,duckduckgo&text=<query>` — мультидвижковый запрос.
- Swagger UI: `http://127.0.0.1:7000/docs`.
- Формат ответа: `{query, meta, results: [{rank, type, title, url, snippet, domain, position, engine, ...}], serp_features, pagination}`.

**Гоча — Яндекс/Google требуют прокси:**
- Прямое подключение (`proxy_used: "direct"`) с текущего IP стабильно ловит капчу/rate-limit на Yandex и Google — это не «частые запросы», блок был и на первом запросе, и через 40с. Скорее всего IP не РФ (ваш регион) — Яндекс агрессивно капчит нероссийские IP, Google банит по репутации подсети.
- **Фикс (не сделан, нужны кредды прокси):** `docker run ... karust/openserp:latest serve -a 0.0.0.0 -p 7000 --proxy http://user:pass@host:port` (флаг `-x/--proxy` форсит прокси на все движки) или `--2captcha_key <key>` для автоrешения капчи. Для Яндекса нужен именно **РФ-прокси** (резидентский/датацентровый в РФ-подсети).
- Пока прокси не настроен — **для Яндекс-выдачи продолжай использовать связку из скилла `yandex`** (internal API `getTable` с залогиненного браузера, см. `references/wordstat-real-recipe.md`) — это отдельный, уже рабочий механизм (не через openserp).
- DuckDuckGo/Bing прокси не требуют — бери их через openserp уже сейчас для конкурентного парсинга без кредитов.
- Если позже настроишь прокси и снимешь капчу — обнови эту секцию (`captcha_detected`/`blocked` должны уйти).

## Семантическое ядро под Яндекс (фаза `research`)

Методология сбора ядра (маски/базисы → подзапросы, операторы Wordstat, кластеризация) вынесена в три reference (источник — методология, Дейн):

- `references/wordstat-operators.md` — операторы `+` `!` `" "` `[ ]` и что Яндекс НЕ учитывает; как операторы меняют цифру частоты.
- `references/keyword-mapping.md` — маски (базисы) → подзапросы; простые vs сложные синонимы; кластеризация по готовности (холодные/тёплые/горячие) и частотности (ВЧ/СЧ/НЧ).
- `references/perf-vs-seo-semantics.md` — чем сбор семантики для SEO отличается от рекламы (для SEO холодные/информационные запросы БЕРЁМ, для рекламы — отсекаем).

Связанные скиллы (НЕ дублировать — границы):

- **`yandex-direct-pro-ru`** → `skills/yandex-direct-pro-ru/references/semantics-wordstat.md` — те же операторы и маски, но **семантика для платной рекламы** (Директ): минус-слова, структура аккаунта, объявления Поиск/РСЯ, UTM.
- **`ai-seo-agent-pipeline`** — программатическая массовая генерация сотен страниц по собранному ядру (n8n + Perplexity, метод эксперт). Это ядро питает его конвейер.
- **`geo-aeo-ru`** — видимость и измерение цитируемости бренда в LLM-ответах ((regional LLM B)/(regional LLM A)/ChatGPT/Perplexity); информационные запросы из ядра идут в AEO (см. `references/aeo-geo.md`).

## References (читать по необходимости)

| Файл | Когда |
|------|-------|
| `references/workflow.md` | пошаговый сценарий каждой фазы |
| `references/agents-checklists.md` | 11 аналитических ролей (seo-optimizer, meta-creator, internal-linker, keyword-mapper, editor, cro-analyst, headline-generator, cluster-strategist и др.) как RU-чеклисты |
| `references/aeo-geo.md` | оптимизация под AI-выдачу: Яндекс Нейро/Alice/(regional LLM B)/ChatGPT/Perplexity + аудит цитирований + RU-каталоги для размещения |
| `references/seo-guidelines-ru.md` | пороги: объём, плотность (с леммами), длины мета под Яндекс, читаемость |
| `references/data-yandex-tilda.md` | как тянуть данные через `yandex` и публиковать через `tilda` |
| `references/wordstat-real-recipe.md` | **рабочий** съём реальных частот Wordstat (internal API getTable, логин, анти-завис браузера, suggest); Direct API заблокирован (error 58) |
| `references/wordstat-operators.md` | 4 оператора Wordstat (`+` `!` `" "` `[ ]`) для SEO + что Яндекс НЕ учитывает (окончания, порядок, стоп-слова); как операторы меняют цифру частоты Дейн) |
| `references/keyword-mapping.md` | методология «маски (базисы) → подзапросы (вложенные)»: простые vs сложные синонимы, источники расширения, кластеризация по готовности (холодные/тёплые/горячие) и частотности (ВЧ/СЧ/НЧ) Дейн) |
| `references/perf-vs-seo-semantics.md` | различия сбора семантики для рекламы vs SEO (судьба холодных запросов, глубина хвоста, минус-слова); cross-link на `yandex-direct-pro-ru` |

## Context (заполнить под проект — `context/`)

- `context/target-keywords.md` — ядро по кластерам (пиллар/кластер/лонг-тейл + интент + текущие позиции).
- `context/internal-links-map.md` — карта страниц для перелинковки.
- `context/ai-citation-targets.md` — где хотим цитироваться (RU-поверхности).
- Бренд-голос и конкуренты — НЕ дублировать: брать из `yourname-marketing-context` и `competitive-analysis`.

## Примеры (`examples/`)

- `examples/your-product/` — полный реальный прогон (тема YourProduct, июнь 2026): `keywords.json` (с реальными объёмами Wordstat), `research/brief-*.md` + `research/cluster-*.md`, `drafts/*.md` (статья 96/100) + `*.schema.json` (FAQPage+Article), `build_docx.py` (богатый генератор Word с резюме/картой рынка) и готовый `*.docx`. Брать как образец структуры артефактов и как шаблон отчёта для маркетолога.

## Реальный опыт (changelog/уроки)

- **v1.2 (2026-07-20):** добавлена секция «Яндекс/Google SERP локально (openserp)» — self-hosted альтернатива SerpAPI (Docker, `127.0.0.1:7000`). DuckDuckGo/Bing работают из коробки; Yandex/Google требуют прокси (капча/rate-limit подтверждены curl-тестом, не решено — нет кредов прокси). До прокси Яндекс-выдачу продолжай брать через уже рабочий механизм скилла `yandex` (internal API `getTable`).
- **v1.1 (2026-06-03):** добавлен рабочий путь к реальному Wordstat (`references/wordstat-real-recipe.md`, `scripts/wordstat_fetch.py`, `scripts/wordstat_browser_snippet.js`), упаковщик в Word (`scripts/build_report_docx.py`), пример `examples/your-product/`.
- **Wordstat:** Direct API заблокирован (`error 58` — нужен одобренный доступ к Директ API). Реальный способ — internal API `POST /wordstat/api/getTable` с залогиненного браузера (куки сами, CSRF не нужен). Креды Яндекса в `.credentials.master.env` (`YANDEX_EMAIL/PASSWORD`), 2FA проходит владелец, сессия в профиле playwright/chrome-devtools сохраняется.
- **Объёмы:** оценочные тиры (из ширины suggest) завышают в 5–10× — всегда снимать реальный Wordstat перед приоритизацией. Точные коммерческие лонг-тейлы часто = 0–3 показа: страницы под конверсию/AEO, не под трафик.
- **Фикс `content_scrubber.py`:** дефис-нормализация `--`→`—` ломала `---` (frontmatter) и `|---|` (таблицы) → мета не парсилась, таблицы исчезали. Теперь структурные строки пропускаются (`_is_structural`).
- **Фикс `yandex_api.py wordstat`:** Direct API v4 требует UTF-8-body (`json.dumps(...ensure_ascii=False).encode()`), иначе `error 501`.
