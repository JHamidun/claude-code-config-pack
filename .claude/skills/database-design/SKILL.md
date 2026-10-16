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
| Курсорная пагинация вместо `OFFSET` | `OFFSET 100000` физически пролистывает 100k строк на каждой странице; глубже пары тысяч строк берут `WHERE (created_at, id) < (…, …)` с `ORDER BY` по тем же колонкам |
| Составной индекс работает только слева направо | `(user_id, status)` не поможет запросу по одному `status` — порядок колонок это не украшение; первым ставят самый селективный столбец |
| Транзакция на любое изменение нескольких таблиц | Иначе частичная запись остаётся навсегда, и найдут её через месяц |
| `created_at` / `updated_at` в каждой таблице, `updated_at` — триггером БД | Если поле обновляет приложение, ручной `UPDATE`, второй сервис или миграция оставят «время последнего изменения» устаревшим |
| MongoDB: embed — для «один-к-немногим» и редко меняющегося, reference — для «один-ко-многим» и часто меняющегося | Неограниченно растущий вложенный массив раздувает документ (лимит BSON — 16 МБ) и переписывается вместе с ним |
| Кеш дорогих запросов в Redis — только с явной инвалидацией при записи | Без инвалидации кеш отдаёт старое до конца TTL, и баг выглядит как «иногда не обновляется» |
| Бэкап: ежедневный + WAL archiving; регулярный `VACUUM` | Дамп вернёт базу на момент бэкапа, WAL archiving — на нужную минуту; без `VACUUM` (autovacuum включён и успевает) таблицы пухнут мёртвыми строками |

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
`include`). Какие запросы в сумме съедают больше всего времени, показывает
`pg_stat_statements`.

## Framework-интеграция БД (boilerplate, /setup-db)

Готовые шаблоны подключения БД к фреймворкам — `references/framework-db-boilerplate.md`:
PostgreSQL (FastAPI+SQLAlchemy sync/async, Django ORM, Express+TypeORM,
Express+Prisma, NestJS+TypeORM, Go+GORM), MongoDB (Mongoose, Motor), Redis-кэш,
docker-compose для всех БД, `.env.example`, seed-скрипты, миграции под каждый
фреймворк, best practices. Команда `/setup-db <db> <framework>` берёт те же шаблоны.

⚠️ **MySQL и SQLite в референсе покрыты НЕ полностью.** `/setup-db` принимает их
аргументом (и даже приводит примерами `/setup-db mysql django`, `/setup-db sqlite
fastapi`), но per-framework секций у них в референсе нет — есть только сервис в
`docker-compose.yml` и переменные в `.env.example`. Секции «Setup» написаны для
PostgreSQL, MongoDB и Redis. Для MySQL/SQLite бери ближайшую по фреймворку
PostgreSQL-секцию и меняй драйвер и DSN, а не ищи готовую.

## Аналитический SQL (запросы к данным)

Всё про **чтение** данных — в `references/analytics-sql-playbook.md`. Открывай его,
когда пишешь отчёт, воронку, когорту или разбираешь упавший аналитический запрос:
SQLite (FTS5 + BM25-ранжирование, оконные функции, `json_extract`, ATTACH
нескольких баз, PRAGMA для скорости, отличия от Postgres и три грабли — алиас
ломает FTS5, `LIKE`/`lower()` не знают кириллицы, `SUM(CASE)` без ELSE даёт NULL),
аналитический диалект PostgreSQL, агрегации MongoDB с картой SQL→pipeline,
паттерны (CTE-шаги, когортное удержание, воронка, дедупликация, оконные функции).
SQLite-раздел проверен запусками на `chats.db` и `graph.db`.

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
