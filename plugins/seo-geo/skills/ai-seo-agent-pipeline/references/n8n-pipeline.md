# n8n Pipeline — архитектура AI SEO агента (эксперт

Детальная архитектура low-code workflow на n8n. Источник — урок «AI SEO агент» + операционные
выжимки курса методология. Структура `AI SEO Writer.json` реконструирована по описанию узлов из
урока (оригинальный файл 20.5 KiB прикреплён к в Notion — если он есть, импортируй напрямую).

> Почему low-code, а не код: в продакшене агенты пишут на коде (гибче), но для урока/прототипа
> используется n8n. Этот формат подходит для тестирования, выдерживает небольшую нагрузку, удобен
> для прототипирования, **менее гибкий**, чем кодовая реализация. На больших объёмах (тысячи
> страниц) — переписывать на код.

---

## Полная схема узлов (Вариант B — полный конвейер)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. TRIGGER                                                                 │
│    n8n Form Trigger ИЛИ Webhook ИЛИ Manual                                 │
│    Вход: { "seed": "movers from san francisco to los angeles" }            │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 2. (опц.) ТЗ-ГЕНЕРАТОР / ПАРСЕР Google Doc                                  │
│    Если ТЗ заранее в Google Doc: Google Docs node (Get) → Code node        │
│    парсит → JSON { keyword, intent, title, meta_description, canonical,     │
│    robots, structure[], target_length }                                    │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 3. PERPLEXITY (research-агент)                                             │
│    HTTP Request node → Perplexity API (или LLM с браузингом)               │
│    Промпт: «проанализируй выдачу по {seed}, собери источники, дай summary» │
│    Выход: { summary, citations: [url...], key_points }                     │
│    ⚑ citations сохранить отдельно — пригодятся для AEO / citation-mining   │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 4. ИЗВЛЕЧЕНИЕ КОНТЕНТА ИЗ ССЫЛОК                                            │
│    Split In Batches (по citations) → HTTP Request (GET url) →              │
│    Code/HTML Extract node (strip HTML, оставить текст) →                   │
│    Merge → собранный материал (research_corpus)                            │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 5. КОПИРАЙТЕР-АГЕНТ (OpenAI / Claude)                                       │
│    AI Agent / OpenAI Chat node                                             │
│    System: роль · география · продукт · структура · ключи · форматирование │
│    User: research_corpus + ТЗ                                              │
│    Параметры: 1500-2000 слов, H2 с ключом, FAQ, Key Takeaways, ETR,        │
│               internal links, bold/italic/lists                            │
│    Output: строго JSON (см. ниже)                                          │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 6. ИЗОБРАЖЕНИЯ + HTML                                                       │
│    Image gen node (LLM) → alt-тексты → вставка в блоки                     │
│    Code node: собрать HTML по фиксированной структуре блоков               │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌─────────────────┐  ┌────────────────────────────────────────────────────┐
│ 7a. GOOGLE DOCS │  │ 7b. SUPABASE — поиск релевантных статей            │
│   + GMAIL       │  │   HTTP/Postgres node → SELECT по embeddings/ключам  │
│  (Вариант A:    │  │   → список internal-link кандидатов → вставить в    │
│   статья на     │  │   тело статьи (anchor-text по ключам)               │
│   email)        │  └───────────────┬────────────────────────────────────┘
└─────────────────┘                  │
                ┌────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 8. JSON → CMS                                                              │
│    Code node: финальный JSON (смысл НЕ меняется, текст НЕ дополняется)     │
│    HTTP Request node → CMS API:                                           │
│      • WordPress: POST /wp-json/wp/v2/posts                                │
│      • Webflow:   POST /collections/{id}/items                            │
│      • Tilda:     Feeds API (см. скилл tilda)                             │
│    → автосоздание поста в нужной категории                                 │
└───────────────┬──────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 9. SUPABASE — INSERT опубликованной статьи                                 │
│    запись { url, title, keyword, cluster, embedding, published_at }        │
│    → пополняет БД для будущей автоперелинковки + ускоряет индексацию       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Последовательность (текстом, для чтения без диаграммы)

1. **Trigger** принимает seed-фразу (ключевой запрос). Один запуск = одна страница.
2. (Опц.) **ТЗ из Google Doc** парсится в JSON (intent, keywords, meta, структура, длина).
3. **Perplexity** анализирует выдачу, собирает ссылки (citations), парсит контент, даёт summary.
   Perplexity заменяема любой LLM с браузингом.
4. Из citation-ссылок **извлекаются тексты** → собирается research-материал.
5. **Копирайтер-агент** генерирует SEO-статью по строгому промпту и параметрам. Output — JSON.
6. **Изображения** (LLM) + alt-тексты, оформление в **HTML** по фиксированной структуре блоков.
7a. **Вариант A:** статья → Google Docs → Gmail (на email). Конец.
7b. **Вариант B:** Supabase ищет релевантные опубликованные статьи → вставляются internal links.
8. Финальный **JSON** (смысл не меняется) → **CMS API** → автопубликация в нужной категории.
9. **Supabase** записывает новую статью → растёт база для перелинковки, ускоряется индексация.

---

## Структура `AI SEO Writer.json` (реконструкция для импорта в n8n)

> Это **реконструкция** структуры по описанию узлов из урока, а не дамп оригинального файла.
> Оригинальный `AI SEO Writer.json` (20.5 KiB) прикреплён к в Notion. Если он у тебя есть —
> импортируй его напрямую (n8n → workflow menu → Import from File) вместо ручной сборки.
> Реконструкция нужна, чтобы собрать эквивалент с нуля.

Минимальный набор нод (Вариант A), которые надо создать в n8n и связать по порядку:

| # | Node type (n8n) | Назначение | Ключевые поля |
|---|-----------------|------------|---------------|
| 1 | **Form Trigger** | приём seed | поле `seed` (text, required) |
| 2 | **HTTP Request** | Perplexity research | POST к Perplexity API, body с промптом research-агента, заголовок `Authorization: Bearer {{PERPLEXITY_API_KEY}}` |
| 3 | **Code** | вытащить citations из ответа Perplexity | парс `choices[].message` + `citations[]` |
| 4 | **Split In Batches** | итерировать по citation-ссылкам | batchSize 1 |
| 5 | **HTTP Request** | GET каждой ссылки | responseFormat: string |
| 6 | **HTML / Code** | strip HTML → чистый текст | оставить `body` текст |
| 7 | **Merge / Aggregate** | собрать research_corpus | конкатенация текстов |
| 8 | **OpenAI / AI Agent** | копирайтер | system-промпт копирайтера, user = corpus, `response_format: json_object` |
| 9 | **Code** | собрать HTML по блокам + ETR | подсчёт слов → reading time |
| 10 | **Google Docs** | создать документ | folder, title = keyword |
| 11 | **Gmail** | отправить на email | to, subject = keyword, body = ссылка на Doc |

Для **Варианта B** добавить после ноды 9:

| # | Node type | Назначение |
|---|-----------|------------|
| B1 | **Postgres / HTTP (Supabase)** | SELECT релевантных статей для internal links |
| B2 | **Code** | вставить internal links в тело (anchor-text по ключам) |
| B3 | **Code** | финальный JSON для CMS (строгая структура, без артефактов) |
| B4 | **HTTP Request** | POST в CMS API (WordPress `/wp-json/wp/v2/posts` / Webflow / Tilda Feeds) |
| B5 | **Postgres / HTTP (Supabase)** | INSERT записи опубликованной статьи |

> Сборка узлов, креды и дебаг — см. скилл **`n8n`**. Здесь — только специфика SEO-конвейера.

---

## JSON output копирайтера (контракт для CMS)

Строгий вывод — **только JSON**, без markdown-обёрток и артефактов. Текст в JSON смыслово не
меняется и не дополняется на этапе конвертации (правило урока).

```json
{
  "title": "Movers from San Francisco to Los Angeles: Costs, Routes & FAQ",
  "slug": "movers-san-francisco-to-los-angeles",
  "meta_description": "How much it costs to move from SF to LA, routes, timelines, and answers to the most common questions.",
  "canonical": "https://example.com/movers-san-francisco-to-los-angeles",
  "robots": "index,follow",
  "keyword": "movers from san francisco to los angeles",
  "estimated_reading_time_min": 8,
  "key_takeaways": ["...", "...", "..."],
  "html_body": "<h1>...</h1><h2>...keyword in one H2...</h2>...<section class='faq'>...</section>",
  "faq": [
    {"q": "How much does it cost to move from SF to LA?", "a": "..."},
    {"q": "How long does the move take?", "a": "..."}
  ],
  "internal_links": [
    {"anchor": "moving to Los Angeles", "url": "/moving-to-los-angeles"}
  ],
  "images": [
    {"alt": "Moving truck on I-5 between San Francisco and Los Angeles", "src": "..."}
  ],
  "category": "Route pages"
}
```

CMS-узел маппит эти поля на API целевой системы (WordPress/Webflow/Tilda).

---

## Supabase schema (БД статей + автоперелинковка)

Минимальная таблица для перелинковки в масштабе. Цель: при публикации новой страницы найти
релевантные уже опубликованные и вставить internal links → ускорить индексацию.

```sql
create table seo_articles (
  id            bigint generated always as identity primary key,
  url           text not null unique,
  slug          text not null,
  title         text not null,
  keyword       text not null,
  cluster       text,                      -- 'Resort' | 'Route' | 'Airport' | ...
  summary       text,
  embedding     vector(1536),              -- pgvector: для semantic relink (опц.)
  published_at  timestamptz default now()
);

-- индексы для поиска кандидатов на internal links
create index on seo_articles using gin (to_tsvector('simple', title || ' ' || keyword));
-- при использовании pgvector:
-- create index on seo_articles using ivfflat (embedding vector_cosine_ops);
```

Поиск кандидатов (вариант без embeddings — по ключам/кластеру):

```sql
select url, title, keyword
from seo_articles
where cluster = :current_cluster
  and id <> :current_id
  and to_tsvector('simple', title || ' ' || keyword) @@ plainto_tsquery('simple', :keyword)
order by published_at desc
limit 5;
```

Узел в n8n вызывает этот SELECT, получает кандидатов, нода-Code вставляет `<a>` в `html_body` по
anchor-text. См. `programmatic-strategy.md` → раздел про Supabase.

---

## Креды и подключения (минимум)

- **Perplexity API** — биллинг + ключ (`PERPLEXITY_API_KEY`). Скилл `perplexity`.
- **OpenAI API** (`OPENAI_API_KEY`) и/или Claude (`claude-api`).
- **Google Docs + Gmail** — OAuth credential в n8n (скиллы `gdocs`, `gmail`).
- **Supabase** — URL проекта + service/anon key (REST) или Postgres connection.
- **CMS** — WordPress App Password / Webflow API token / Tilda (скилл `tilda`).

Все ключи — из `~/.claude/.credentials.master.env` (см. правило security). В n8n — через
Credentials, не хардкодом в нодах.

---

## Эфемерный запуск за 5-10 минут (Вариант A)

При базовой настройке (Perplexity billing + OpenAI key + Google Docs creds + Gmail) агент
собирается и запускается за 5-10 минут, статьи приходят на email. Полная автопубликация в CMS
требует учёта структуры конкретной CMS и кастомной интеграции (Вариант B).
