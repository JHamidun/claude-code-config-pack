---
name: pgvector-rag
description: "RAG на pgvector: чанкинг, эмбеддинги, ingest — контракты и грабли из продакшена. Триггеры: «сделай RAG», «чанкинг документов», «векторный поиск»."
---

# pgvector-rag

Не общая теория RAG, а контракты и грабли, пойманные на двух живых системах:
корпоративный RAG на TypeScript (OpenAI + pgvector, ~500K векторов) и обучающая
платформа на Python (локальный Qwen3 + pgvector). Числа в тексте — замеры оттуда,
а не оценки.

## Что понадобится

| Нужно | Платно? | Без этого |
|---|---|---|
| PostgreSQL ≥ 13 с расширением `vector` (pgvector ≥ 0.5.0 — иначе нет HNSW) | нет | навык неприменим: всё построено на pgvector |
| **Либо** GPU уровня RTX 4090 для локальных эмбеддингов (Qwen3-0.6B ~9 chunks/s) | нет | bulk-индексация на CPU идёт в 10-30× медленнее — см. таблицу в `references/ingest-operations.md` |
| **Либо** `OPENAI_API_KEY` (или ключ Google) для облачных эмбеддингов | да, за токены | нечем эмбедить; ориентир: полный ре-эмбед корпуса на 2-3M чанков через `3-large` ≈ $120 |
| `pip install psycopg[binary] tiktoken` + `sentence-transformers` (для локальных) или `openai` | нет | — |

## Почему pgvector, а не Qdrant

Корпоративный проект начинал с Qdrant и ушёл на pgvector: одна БД → бэкап/транзакции/миграции проще, нет отдельной инфраструктуры, multi-tenancy решается отдельными таблицами, атомарный «обновить атом + embeddings» в одной транзакции. HNSW в pgvector ≥0.5.0 сопоставим с Qdrant до ~10M векторов. Qdrant оправдан при >50M векторов, advanced payload filters или distributed-индексации.

## Chunking

Дефолты, на которых сошлись оба проекта: `chunkSize=512` **токенов** (tiktoken cl100k_base, не символов!), `chunkOverlap=64` (~12%). DoS-guard: `overlap < chunkSize`, иначе бесконечный цикл. Стратегия — fixed-size token-based скользящим окном (`start_next = start + size - overlap`), не semantic и не recursive: простая, предсказуемая, работает для техдоки, транскриптов, книг, кода.

**Frontmatter в начало каждого чанка перед embedding** — иначе LLM видит куски без контекста и галлюцинирует:

```
---
Документ: {source_filename}
Чанк: {chunk_index + 1} из {total_chunks}
---

{chunk_text}
```

**Таблицы/Q&A** — отдельный `chunkTable()`: 20 записей на чанк, не рвать посередине записи, в metadata `columns`, `rows_range`, `total_rows`.

**Metadata на чанк**: `document_id`, `source`, `chunk_index`, `total_chunks`, `token_count`, `embedding_model`, `chunk_size/overlap`, `text` (превью 500 символов для выдачи без второго round-trip). Плюс атрибуция: `source_org`, `license`, `attribution_required`, `canonical_source_url` — в UI показывать ссылку и лицензию.

**Токенайзер чанкинга ≠ токенайзер эмбеддинга.** Режем cl100k, эмбедим Qwen3 — для него (32K контекст) запас огромный. Но у `bge-m3`/`e5-large` жёсткий лимит 512 токенов их токенайзера: 512 cl100k ≈ 550-650 их токенов → молчаливая обрезка хвоста. Для 512-лимитной модели бери `chunk_size≈384` cl100k.

## Embeddings

```python
EMBEDDING_DIMENSIONS = {
    # Локальные (sentence-transformers, бесплатно)
    "Qwen/Qwen3-Embedding-0.6B": 1024,   # ⭐ дефолт: Apache 2.0, лучший на русском; ~9 chunks/s на 4090 Laptop
    "Qwen/Qwen3-Embedding-4B":   2560,
    "Qwen/Qwen3-Embedding-8B":   4096,
    "BAAI/bge-m3":               1024,   # быстрее Qwen3, чуть хуже на русском
    "intfloat/multilingual-e5-large": 1024,
    "jinaai/jina-embeddings-v3": 1024,
    # OpenAI
    "text-embedding-3-small":    1536,
    "text-embedding-3-large":    3072,   # ⚠ >2000 → halfvec (см. ниже)
    "text-embedding-ada-002":    1536,
    # Google
    "text-embedding-004":        768,
    "gemini-embedding-001":      768,
}
```

Выбор: свой GPU + русский контент → Qwen3-0.6B; нет GPU → 3-large (halfvec) или 3-small; скорость важнее → bge-m3. Для локальных обязателен `normalize_embeddings=True`. Провайдер определяется по префиксу имени: `text-embedding-*` → OpenAI, `gemini-*` → Google, иначе local.

**Гоча №1 (поймана в проде): OpenAI игнорирует размерность индекса.** Индекс создан dim=1536, а API вернул дефолтные 3072 → silent fail, поиск отдаёт 0 результатов. **Всегда** явно `dimensions: N` в `embeddings.create`, совпадающий с индексом.

**Гоча №2 (локальные модели): query/document асимметрия.** Qwen3/e5/bge ждут instruct-префикс на **запросе** и пустой на документах; `default_prompt_name: null` в конфиге модели означает «без prompt_name префикс не применяется вовсе». Эмбедишь запрос как документ → тихо -1-5% recall:

```python
doc_vecs  = model.encode(chunks, normalize_embeddings=True)                       # ингест: без префикса
query_vec = model.encode([query], prompt_name="query", normalize_embeddings=True)[0]  # поиск: с префиксом
```

Схема у каждой модели своя (`e5`: `query:`/`passage:`) — проверяй `config_sentence_transformers.json`.

**Batch policy** — два лимита одновременно: `BATCH_SIZE=100` текстов И `MAX_TOKENS_PER_BATCH=250_000` (лимит OpenAI 300k, берём запас). Флашить батч, когда следующий текст пробивает любой из двух. Один гигантский текст = собственный батч.

## Vector store (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE idx_{name} (
  id       TEXT PRIMARY KEY,              -- "{document_id}_{chunk_index}"
  text     TEXT NOT NULL DEFAULT '',      -- ПОЛНОЕ тело чанка: превью 500 символов режет 70% контекста для LLM
  vector   VECTOR(1024) NOT NULL,         -- размерность = модель (Qwen3 = 1024)
  metadata JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_{name}_vector ON idx_{name}
USING hnsw (vector vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_{name}_meta ON idx_{name} USING GIN (metadata);
```

**HNSW не индексирует >2000 dim.** Для 3072 (`3-large`) — `HALFVEC(3072)` + `halfvec_cosine_ops` + каст в поиске `$1::halfvec` (recall практически не падает). 1024/1536 влезают в обычный `vector`.

**Multi-tenancy — отдельная таблица на тенанта/категорию** (`idx_<проект>_<категория>`: `idx_kb_articles`, `idx_kb_lessons`, …), НЕ `WHERE metadata->>'tenant_id'` — медленно и небезопасно. Имена таблиц подставляются в SQL строкой, поэтому валидация обязательна: `/^[a-z0-9][a-z0-9_-]*$/i`, max 63 символа (лимит PostgreSQL).

**Санитизация payload:** PostgreSQL JSONB не держит null-байты — `text.replace(/[\x00-\x1F]/g, '')` перед upsert.

**DELETE только по whitelist ключей** (`ALLOWED_FILTER_KEYS = ['document_id']`), значение — параметром: произвольный metadata-ключ в шаблоне строки = SQL injection.

## Search

```sql
SET LOCAL hnsw.ef_search = 200;   -- высокий recall
SELECT id, text, metadata, 1 - (vector <=> $1) AS similarity
FROM "idx_name"
WHERE 1 - (vector <=> $1) >= $2
ORDER BY vector <=> $1
LIMIT $3;                          -- topK*2..3, если дальше rerank
```

- Query эмбедится **той же моделью**, что индекс (+ prompt_name для локальных).
- Дефолты: `topK=5`, `minScore=0.3`, `ef_search=200`. Но **min_score относителен к модели**: у Qwen3 хорошие матчи 0.6-0.74, мусор <0.4; у OpenAI распределение другое. Откалибруй 5-10 реальными запросами (score на заведомо релевантном vs заведомо нерелевантном, порог между).
- Rerank малой LLM (`claude-haiku-4-5-20251001`): retrieve topK×3 → rerank до topK. Без rerank в большом корпусе на topK=5 лезет мусор.
- **Boost душит источники.** Merge по `boosted_score` даёт priority, но при `boost=2.0` у книги внешние курсы не всплыли ни разу. Нужна diversity → квота на индекс: гарантированный минимум N результатов из каждого, потом добить лучшими.

## LLM-интеграция и health-check

Tool через function-calling (`RagToolFactory.create({index_name, embedding_model, top_k, min_score, rerank})`); LLM сам решает, вызывать ли.

Диагностика при создании tool: индекс существует (fail loud) → не пустой (warn) → **dim(модель) == dim(индекса)** → min_score ∈ [0,1]. И honest-check в рантайме: реально эмбедь dummy и сверь длину вектора с индексом — ловит и dim mismatch, и мёртвый ключ (`insufficient_quota` поймали за секунды вместо тихих пустых результатов).

Graceful degradation: БД упала / API timeout → tool возвращает пустой результат + лог, LLM продолжает без контекста, не падаем.

**Верификация после ingest** — не верь «N чанков загружено», прогони известный семантический запрос: «свобода и личность» → должны всплыть Рэнд и Оруэлл. Мусор в топе (всё <0.4) = не та модель на query vs index / битый frontmatter / пустой индекс.

## Миграции и ingest

- **Смена модели ИЛИ чанкинга = полный re-index.** Размерность и стратегия резки — контракт, фиксируется на старте; досыпать Qwen3-вектора в OpenAI-индекс нельзя.
- **Идемпотентный ingest**: `delete_by_document_id(doc_id)` ПЕРЕД upsert; `document_id = sha256(path)[:16]` стабилен между запусками → прерывание/повтор безопасны.
- **Blue-green re-index**: in-place DROP+rebuild кладёт поиск на часы (полный ре-индекс обучающего корпуса — ~3.5 ч на 4090). Лей в `idx_{name}_v2`, по готовности атомарный `ALTER TABLE ... RENAME` в одной транзакции, старую дропни.

Bulk-прогоны на часы-сутки (супервайзер schtasks, sentinel-resumability, GPU/CPU-планирование, embedder-микросервис, ASR-пайплайн, SSH-туннели) → `references/ingest-operations.md`. Тюнинг качества → `references/rag-optimization.md`; on-prem деплой → `references/onprem-rag-deploy.md`.

## Раскладка кода, которая себя оправдала

Реализации, из которых собран этот навык, приватные, поэтому вместо «скопируй файл» —
карта модулей: шесть файлов, каждый с одной ответственностью. Разложишь так же — куски
навыка лягут по местам без переделки.

| Модуль | Что внутри | Ключевое из навыка |
|---|---|---|
| `chunking.py` / `chunking.service.ts` | token splitter, `chunkTable()`, sanitize, `document_id` | 512/64 на cl100k, frontmatter, DoS-guard `overlap < size` |
| `embeddings.py` / `EmbeddingService.ts` | выбор провайдера по префиксу имени модели, локальный + облачный fallback | явный `dimensions`, `prompt_name="query"` только на поиске |
| `vector_store.py` / `VectorStoreService.ts` | схема, HNSW, GIN, upsert, `search_across` | полная TEXT-колонка, halfvec >2000 dim, whitelist DELETE-ключей |
| `ingest.py` | YAML-driven идемпотентный ingest | `delete_by_document_id` перед upsert, `document_id = sha256(path)[:16]` |
| `search.py` | multi-index, per-source boost, квоты | boost душит источники — нужна квота на индекс |
| `rag_tool.py` / `rag-tool.factory.ts` | function-calling обёртка + health-check | dummy-embed на старте ловит dim mismatch и мёртвый ключ |

Начинать с `chunking` + `vector_store`: пока не устаканены размер чанка и схема таблицы,
остальное переписывать придётся всё равно.

## Checklist для нового RAG

- [ ] `CREATE EXTENSION vector`; один индекс = одна таблица, имя через SAFE_IDENTIFIER
- [ ] HNSW на `vector` (halfvec если >2000 dim), GIN на `metadata`, полная TEXT-колонка
- [ ] Chunking 512/64 token-based + frontmatter; таблицы через chunkTable
- [ ] Embeddings: **всегда `dimensions`** (OpenAI), **prompt_name="query"** только на поиске (локальные)
- [ ] Batch: 100 items OR 250k tokens
- [ ] Search: topK=5, ef_search=200, min_score откалиброван под модель, rerank
- [ ] Security: whitelist DELETE-ключей, unicode sanitize, валидация имён индексов
- [ ] Health-check с dummy-embed; graceful degradation; sanity query после ingest
- [ ] Идемпотентный ingest; re-index только blue-green

## Перфоманс (замеры на проде)

pgvector HNSW ~50ms p50 top-5 из 500K векторов (1536-dim) · OpenAI batch 100 текстов ~200ms · rerank ~300ms · итого retrieve ~600-700ms p50. Ускорение: кэш эмбеддингов запросов в Redis, `pg_prewarm('idx_name_vector')`, batch queries через `UNNEST`.
