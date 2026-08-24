---
name: database-design
description: "Схема БД, миграции, оптимизация запросов: PostgreSQL, MongoDB, Redis; нормализация, индексы. Триггеры: «дизайн базы», «оптимизируй запрос»."
keywords: database, schema, migration, postgres, mongodb, redis, normalization, indexing, query-optimization
---

# Database Design & Optimization

Проектирование схем, планирование миграций, оптимизация запросов — SQL и NoSQL.
Синтаксис DDL, нормальные формы и устройство индексов не пересказываются: ниже —
только решения, которые легко пропустить, и то, что проверено на наших проектах.

## Решения, которые забывают

| Решение | Почему |
|---|---|
| Индекс на КАЖДЫЙ foreign key | Postgres не создаёт его сам; без индекса `DELETE` родителя сканирует всю дочернюю таблицу |
| Наружу отдавать UUID, а не `SERIAL` | Автоинкремент в URL раскрывает объём базы и позволяет перебор чужих записей |
| Soft delete (`deleted_at`) + частичный индекс `WHERE deleted_at IS NULL` | Полный индекс по удалённым строкам растёт вечно и портит планы |
| В `order_items` хранить `unit_price` снимком | Цена товара меняется; без снимка старые заказы задним числом переписывают историю |
| Курсорная пагинация вместо `OFFSET` | `OFFSET 100000` физически пролистывает 100k строк на каждой странице |
| Составной индекс работает только слева направо | `(user_id, status)` не поможет запросу по одному `status` — порядок колонок это не украшение |
| Транзакция на любое изменение нескольких таблиц | Иначе частичная запись остаётся навсегда, и найдут её через месяц |

## Безопасная миграция на живой базе

Порядок нарушать нельзя — каждый шаг отдельным деплоем:

1. добавить колонку **nullable** (мгновенно, без блокировки таблицы);
2. заполнить данные батчами (`UPDATE ... WHERE ... LIMIT`);
3. только теперь `SET NOT NULL` / добавить constraint.

Одношаговое «добавить NOT NULL с DEFAULT» на большой таблице берёт `ACCESS
EXCLUSIVE` и кладёт запись на время переписывания. Индексы в проде создавать
`CREATE INDEX CONCURRENTLY` — обычный `CREATE INDEX` блокирует запись целиком.
Каждая миграция обязана иметь рабочий `downgrade`: откат в 3 часа ночи пишут не с
нуля.

## Диагностика медленного запроса

`EXPLAIN (ANALYZE, BUFFERS)` — и смотреть на расхождение `rows=` оценки и
`actual rows`: расхождение в разы означает устаревшую статистику (`ANALYZE`), а не
недостающий индекс. `Seq Scan` на большой таблице с фильтром — кандидат на индекс;
`Seq Scan` на маленькой — норма, планировщик прав.

N+1 ловится не глазами, а логом запросов: одинаковый запрос с разным параметром
подряд = отсутствует eager loading (`joinedload` / `prefetch_related` /
`include`).

## Аналитический SQL (запросы к данным)

Всё про **чтение** данных — в `references/analytics-sql-playbook.md`. Открывай его,
когда пишешь отчёт, воронку, когорту или разбираешь упавший аналитический запрос:
SQLite (FTS5 + BM25-ранжирование, оконные функции, `json_extract`, ATTACH
нескольких баз, PRAGMA для скорости, отличия от Postgres и три грабли — алиас
ломает FTS5, `LIKE`/`lower()` не знают кириллицы, `SUM(CASE)` без ELSE даёт NULL),
аналитический диалект PostgreSQL, агрегации MongoDB с картой SQL→pipeline,
паттерны (CTE-шаги, когортное удержание, воронка, дедупликация). SQLite-раздел
проверен запусками на `chats.db` и `graph.db`.

## ER-диаграммы из схемы (liam)

`@liam-hq/cli` — интерактивные ER-диаграммы (React Flow, HTML) из
Prisma/PostgreSQL/drizzle-схем. Работает через `npx`, ставить ничего не нужно.
Проверено 2026-07-19 на ClientProjectA (61 модель).

**Prisma (одиночный файл):**
```bash
npx -y @liam-hq/cli@latest erd build --input schema.prisma --format prisma --output-dir liam-erd
```

**Postgres по URL (любая live-БД):**
```bash
npx -y @liam-hq/cli@latest erd build --input "postgresql://user:pass@host:5432/db" --format postgres --output-dir liam-erd
```
Форматы: `prisma | postgres | drizzle | schemarb | tbls | liam`. Для схемы на
drizzle/psql — либо `--format drizzle` на schema-файлы, либо `pg_dump
--schema-only > dump.sql` и `--format postgres`.

**Вывод:** `--output-dir` (дефолт `dist/`) — index.html + schema.json + assets.
Открывать ТОЛЬКО через HTTP (file:// не работает):
```bash
npx http-server -c-1 liam-erd/
```

**Гочи (Windows / Prisma 7 multi-file — ClientProjectA):**
- Абсолютный Windows-путь с глобом (`C:/...*.prisma`) → `ERROR: fetch failed`. Запускай из директории схемы с относительным путём.
- Bundled Prisma 6.8.2 не понимает multi-file schema и generator `provider = "prisma-client"` (Prisma 7): конкатенируй файлы в один temp `merged.prisma`, замени generator на `prisma-client-js` и добавь `url = env("DATABASE_URL")` в datasource — затем build проходит.
- Гоча из практики: в монорепо Prisma-схема часто лежит НЕ в `<repo>/prisma/`, а глубже —
  например `packages/tools/prisma/schema/{core,crm,pms}.prisma`. Перед правкой найди её
  фактическое место (`generator`/`datasource` блоки), а не полагайся на соглашение.

**Когда полезно:** ревью схемы перед миграцией (ClientProjectD LMS/CRM,
ClientProjectB, ClientProjectC, ClientProjectA), онбординг в чужую БД, проверка
связей после новых моделей, скриншот диаграммы в доку/КП.
