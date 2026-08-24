# Аналитический SQL: SQLite / PostgreSQL / MongoDB

Справочник по **запросам к данным** (в отличие от SKILL.md, который про схемы, миграции и индексы).
Три движка нашего стека. Всё в SQLite-разделе проверено запусками на `~/.claude/chats.db`
(560 545 сообщений, 75 532 сессии) и `~/.claude/memory-graph/graph.db`, SQLite 3.49.1.

---

## SQLite

Основной аналитический движок локально: `chats.db` (FTS5-поиск по всей истории),
`graph.db` (граф памяти), `brain.db`, `workflows.db`.

### FTS5: полнотекстовый поиск

Виртуальная таблица поверх обычной (external content — данные не дублируются):

```sql
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    session_id UNINDEXED,          -- хранится, но не индексируется: для фильтров
    role UNINDEXED,
    content='messages',            -- external content: тело лежит в messages
    content_rowid='id',
    tokenize='unicode61'           -- Unicode-совместимая нарезка (см. ниже, важно для русского)
);
```

Синтаксис MATCH-запроса (всё проверено):

```sql
-- простой терм
WHERE messages_fts MATCH 'pgvector'
-- фраза (кавычки внутри строки)
WHERE messages_fts MATCH '"claude code"'
-- префикс
WHERE messages_fts MATCH 'embed*'
-- булево
WHERE messages_fts MATCH 'pgvector NOT qdrant'
WHERE messages_fts MATCH 'pgvector OR hnsw'
-- близость: термы в пределах 20 токенов
WHERE messages_fts MATCH 'NEAR(pgvector hnsw, 20)'
-- ограничить конкретной колонкой
WHERE messages_fts MATCH 'content: pgvector'
```

### BM25-ранжирование

`bm25()` возвращает **отрицательное** число: чем меньше (левее по числовой оси), тем релевантнее.
Поэтому `ORDER BY bm25(...)` без DESC — это «сначала самое релевантное».

```sql
-- канон: сортировка по релевантности
SELECT rowid, bm25(messages_fts) AS r
FROM messages_fts
WHERE messages_fts MATCH ?
ORDER BY r
LIMIT 20;

-- то же короче: rank — встроенный алиас bm25() с весами по умолчанию
SELECT rowid, rank FROM messages_fts WHERE messages_fts MATCH ? ORDER BY rank LIMIT 20;

-- веса по колонкам: первая колонка (content) в 10 раз важнее второй
SELECT rowid, bm25(messages_fts, 10.0, 1.0) AS r FROM messages_fts
WHERE messages_fts MATCH ? ORDER BY r LIMIT 20;

-- если наружу нужен «чем больше тем лучше» (для UI, для смешивания с косинусной близостью)
SELECT rowid, -bm25(messages_fts) AS score FROM messages_fts
WHERE messages_fts MATCH ? ORDER BY score DESC LIMIT 20;
```

Сниппеты и подсветка вместо возврата всего тела (у нас сообщения бывают по 10 КБ):

```sql
-- snippet(table, colIdx, open, close, ellipsis, tokens) — вырезает окно вокруг совпадения
SELECT snippet(messages_fts, 0, '[', ']', '...', 8)
FROM messages_fts WHERE messages_fts MATCH ? LIMIT 10;

-- highlight() возвращает ВЕСЬ документ с обёрнутыми совпадениями — на длинных телах это дорого
SELECT highlight(messages_fts, 0, '>', '<') FROM messages_fts WHERE messages_fts MATCH ? LIMIT 1;
```

### 🚨 Грабля №1: FTS5-таблицу нельзя алиасить

Псевдоним ломает и `MATCH`, и `bm25()` — SQLite перестаёт видеть таблицу как FTS:

```sql
-- ❌ OperationalError: no such column: f   (все три варианта падают)
SELECT rowid FROM messages_fts f WHERE f MATCH 'pgvector';
SELECT bm25(f) FROM messages_fts f WHERE f MATCH 'pgvector';

-- ✅ пиши полное имя таблицы; алиасить можно только обычные таблицы в JOIN
SELECT m.session_id, bm25(messages_fts) AS r
FROM messages_fts
JOIN messages m ON m.id = messages_fts.rowid
WHERE messages_fts MATCH ?
ORDER BY r LIMIT 20;
```

### 🚨 Грабля №2: LIKE и lower() в SQLite — только ASCII

Проверено: `'ПРИВЕТ' LIKE 'привет'` → **0**, `lower('ПРИВЕТ')` → **'ПРИВЕТ'** (без изменений).
Регистронезависимый поиск по русскому через LIKE **молча не работает** — вернёт 0 строк
и это выглядит как «ничего не нашлось», а не как ошибка.

FTS5 с `tokenize='unicode61'` регистр складывает правильно: `память`, `ПАМЯТЬ`, `ПаМяТь`
дают одинаковые 4074 совпадения. **Русский текст ищем только через FTS5, не через LIKE.**

### Оконные функции (есть с SQLite 3.25, работают как в Postgres)

```sql
-- дедупликация: последнее сообщение в каждой сессии
WITH ranked AS (
  SELECT session_id, id, content,
         ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY id DESC) AS rn
  FROM messages
)
SELECT * FROM ranked WHERE rn = 1;

-- LAG/LEAD + рамка окна
SELECT id,
       LAG(id) OVER (ORDER BY id) AS prev_id,
       COUNT(*) OVER (ORDER BY id ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3
FROM messages;

-- накопительный итог по месяцам
SELECT strftime('%Y-%m', created) AS m,
       COUNT(*) AS c,
       SUM(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', created)) AS running_total
FROM sessions WHERE created IS NOT NULL GROUP BY m ORDER BY m;
```

`FILTER (WHERE ...)` поддерживается — читается лучше, чем `SUM(CASE WHEN ...)`:

```sql
SELECT COUNT(*) AS total,
       COUNT(*) FILTER (WHERE role = 'user') AS from_user
FROM messages;                       -- → 560545 / 301628
```

Перцентилей (`percentile_cont`) в SQLite нет. Дешёвая замена — `NTILE`:

```sql
WITH x AS (SELECT message_count AS v, NTILE(100) OVER (ORDER BY message_count) AS p FROM sessions)
SELECT p, MIN(v) FROM x WHERE p IN (50, 90, 95, 99) GROUP BY p;
```

### JSON

```sql
SELECT json_extract(extra, '$.tags')          FROM knowledge;   -- скаляр/подобъект
SELECT extra ->> '$.tags'                     FROM knowledge;   -- ->> = как text (3.38+)
SELECT COUNT(*) FROM knowledge k, json_each(k.extra) WHERE json_valid(k.extra);  -- развернуть массив/объект
```

`json_valid()` перед `json_each()` обязателен: невалидный JSON в колонке роняет весь запрос,
а не отдельную строку.

### ATTACH: несколько баз в одном запросе

Путь в `ATTACH` SQLite берёт **буквально**: ни `~`, ни `$HOME`, ни `${HOME}` он не
разворачивает. Литерал `${HOME}/...` даёт `unable to open database file` — ошибку, которую
легко прочитать как «базы нет», хотя база на месте. Поэтому путь собирает Python (модуль
`sqlite3` из stdlib, отдельная программа для этого не нужна) — см. пример ниже.

```sql
-- ВПИШИ АБСОЛЮТНЫЙ ПУТЬ вместо <HOME>: /home/имя, /Users/имя, C:/Users/имя
ATTACH DATABASE 'file:<HOME>/.claude/chats.db?mode=ro'            AS chats;
ATTACH DATABASE 'file:<HOME>/.claude/memory-graph/graph.db?mode=ro' AS g;

SELECT COUNT(*) FROM chats.sessions;                    -- 75532
SELECT name FROM g.sqlite_master WHERE type='table';    -- nodes, edges
PRAGMA database_list;                                   -- что реально подключено
```

Из Python URI-путь в ATTACH работает **только** если соединение открыто с `uri=True` —
иначе `unable to open database: file:...?mode=ro` (проверено, легко принять за «файла нет»):

```python
import sqlite3
from pathlib import Path

home = Path.home().as_posix()                 # ← собираем путь, а не пишем ${HOME} в строке
con = sqlite3.connect(':memory:', uri=True)   # ← uri=True включает URI и для ATTACH
con.execute(f"ATTACH DATABASE 'file:{home}/.claude/chats.db?mode=ro' AS chats")
```

`mode=ro` — обязательная привычка при анализе чужой/рабочей БД: физически запрещает запись.
JOIN между приаттаченными базами работает без ограничений.

### PRAGMA для скорости чтения

```sql
PRAGMA journal_mode;                 -- у chats.db: wal (читатели не блокируют писателя)
PRAGMA mmap_size = 268435456;        -- 256 МБ: чтение через mmap вместо read() — заметно на больших сканах
PRAGMA cache_size = -200000;         -- отрицательное = килобайты (здесь ~200 МБ), положительное = страницы
PRAGMA temp_store = MEMORY;          -- временные B-деревья сортировок в RAM
PRAGMA synchronous = NORMAL;         -- только для WAL и только для своих БД, не для чужого прода
PRAGMA optimize;                     -- перед закрытием долгоживущего соединения: обновляет статистику
ANALYZE;                             -- разово после массовой заливки, чтобы планировщик видел кардинальность
```

Диагностика плана: `EXPLAIN QUERY PLAN SELECT ...` → `SCAN messages` значит полный скан
(нужен индекс), `SEARCH messages USING INDEX ...` — индекс используется.

Интроспекция схемы (аналог information_schema):

```sql
SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','view','index');
SELECT name, type, "notnull", pk FROM pragma_table_info('messages');   -- pragma как table-valued function
SELECT * FROM pragma_index_list('messages');
```

### Отличия от PostgreSQL (что ломается при переносе запроса)

| Тема | PostgreSQL | SQLite |
|---|---|---|
| Типы колонок | строгие | динамические: в INTEGER-колонку ляжет текст (если не `STRICT`-таблица) |
| Сравнение типов | ошибка / приведение | `'10' > 9` → **истина**: TEXT всегда «больше» числа. Спасает `CAST(x AS INTEGER)` |
| Двойные кавычки | всегда идентификатор | идентификатор, а при отсутствии колонки **молча становится строкой** → `WHERE col = "typo"` не падает, а возвращает 0 строк. Строки — только в одинарных |
| Деление целых | `1/2` = 0 (так же) | `1/2` = 0. Процент считать как `100.0 * a / b` |
| Регистр/Unicode | `ILIKE`, полноценный `lower()` | `LIKE`/`lower()` только ASCII → русский только через FTS5 |
| Полнотекст | `tsvector` + GIN | FTS5 + bm25 |
| Перцентили | `percentile_cont` | нет, через NTILE |
| RIGHT/FULL JOIN | есть | FULL/RIGHT есть с 3.39, но в старых сборках нет — безопаснее переписать на LEFT |
| Дата/время | `NOW()`, `INTERVAL` | `date()`, `datetime()`, `strftime('%Y-%m', ts)`, `julianday(a)-julianday(b)` (в днях) |
| Тип даты | date/timestamp | **типа нет**: TEXT ISO-8601, сравнение строковое → формат обязан быть единым |
| Изменение схемы | богатый ALTER | `ALTER TABLE` умеет мало: DROP COLUMN только с 3.35, смена типа — через пересоздание таблицы |
| Конкурентность | MVCC | один писатель на базу; WAL спасает читателей, но не параллельные записи |

### 🚨 Грабля №3: `SUM(CASE WHEN ... THEN 1 END)` без ELSE

Если ни одна строка не совпала, SUM по одним NULL возвращает **NULL, а не 0** — и метрика
«доля пропусков» тихо становится пустой ячейкой в отчёте (поймано на профилировании `sessions`):

```sql
SELECT SUM(CASE WHEN project_path IS NULL THEN 1 END)          FROM sessions;  -- NULL ❌
SELECT SUM(CASE WHEN project_path IS NULL THEN 1 ELSE 0 END)   FROM sessions;  -- 0    ✅
SELECT COUNT(*) FILTER (WHERE project_path IS NULL)            FROM sessions;  -- 0    ✅ лучше
```

### Профилирование таблицы одним запросом

```sql
SELECT COUNT(*) AS rows,
       ROUND(100.0 * COUNT(*) FILTER (WHERE col IS NULL OR col = '') / COUNT(*), 2) AS null_pct,
       COUNT(DISTINCT col)                                       AS distinct_ct,
       ROUND(1.0 * COUNT(DISTINCT col) / COUNT(*), 4)            AS cardinality_ratio,
       MIN(col), MAX(col)
FROM my_table;
-- на sessions.project_path: 75532 строк, 0.0% пустых, 60 значений, ratio 0.0008 → это измерение, не ключ
```

Смешанные типы в колонке (болезнь динамической типизации) ловятся так:
`SELECT typeof(col), COUNT(*) FROM t GROUP BY 1;` — больше одной строки в выводе = данные грязные.

---

## PostgreSQL: аналитический диалект

```sql
-- дата/время
CURRENT_DATE, NOW()
created_at + INTERVAL '7 days'
DATE_TRUNC('month', created_at)
EXTRACT(DOW FROM created_at)             -- 0 = воскресенье
TO_CHAR(created_at, 'YYYY-MM-DD')

-- строки
first_name || ' ' || last_name
col ILIKE '%паттерн%'                    -- регистронезависимо, Unicode работает (в отличие от SQLite)
col ~ '^regex$'
SPLIT_PART(str, ',', 2)
REGEXP_REPLACE(str, pattern, repl)

-- JSON / массивы
data->>'key'                             -- как text
data->'nested'->'key'                    -- как json
data#>>'{path,to,key}'
ARRAY_AGG(col), array_col @> ARRAY['v']

-- перцентили (в SQLite аналога нет)
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value)
```

Производительность: `EXPLAIN ANALYZE` (реальное время, не только план), частичные индексы
под частый фильтр, `EXISTS` вместо `IN` для коррелированных подзапросов, `NULLIF(x, 0)`
в знаменателе. Схема, индексы и партиционирование — в SKILL.md.

---

## MongoDB: агрегации

Pipeline — эквивалент SQL-запроса; стадии выполняются по порядку, поэтому `$match` и `$project`
двигают как можно ближе к началу (это и есть «фильтруй рано»).

```javascript
db.orders.aggregate([
  { $match: { created_at: { $gte: ISODate("2026-01-01") }, status: { $ne: "test" } } },  // WHERE, до всего
  { $group: {                                                                            // GROUP BY
      _id: { month: { $dateToString: { format: "%Y-%m", date: "$created_at" } },
             user: "$user_id" },
      total:  { $sum: "$amount" },
      orders: { $sum: 1 },
      avg:    { $avg: "$amount" },
      // условный счётчик = SQL COUNT(*) FILTER (WHERE ...)
      paid:   { $sum: { $cond: [{ $eq: ["$status", "paid"] }, 1, 0] } }
  }},
  { $sort:  { total: -1 } },
  { $limit: 100 }
]);
```

Соответствия SQL → aggregation:

| SQL | MongoDB |
|---|---|
| `WHERE` | `$match` |
| `GROUP BY` | `$group` (`_id` = ключ группировки; `_id: null` = агрегат по всей коллекции) |
| `HAVING` | `$match` **после** `$group` |
| `SELECT a, b` | `$project` |
| `JOIN` | `$lookup` (+ `$unwind`, если нужен один документ на совпадение) |
| `ROW_NUMBER() OVER (PARTITION BY)` | `$setWindowFields` (4.4+) |
| `DISTINCT` | `$group: { _id: "$field" }` |
| `UNION ALL` | `$unionWith` |

```javascript
// JOIN + дедупликация «последняя запись на ключ»
db.users.aggregate([
  { $lookup: { from: "orders", localField: "_id", foreignField: "user_id", as: "orders" } },
  { $addFields: { order_count: { $size: "$orders" } } },
  { $match: { order_count: { $gt: 0 } } }
]);

db.events.aggregate([
  { $setWindowFields: {
      partitionBy: "$entity_id",
      sortBy: { updated_at: -1 },
      output: { rn: { $documentNumber: {} } }
  }},
  { $match: { rn: 1 } }
]);
```

Гочи: `$lookup` не использует индекс целевой коллекции, если поле не проиндексировано —
проверяй `.explain("executionStats")`; `$unwind` без `preserveNullAndEmptyArrays: true`
молча выкидывает документы без совпадений (тот же эффект, что INNER вместо LEFT JOIN);
стадия `$group` держит результат в памяти (лимит 100 МБ) — на больших объёмах нужен
`{ allowDiskUse: true }`. Индексы и модель документов — в SKILL.md.

---

## Универсальные аналитические паттерны

Синтаксис ниже — Postgres; для SQLite замены: `DATE_TRUNC('month', x)` → `strftime('%Y-%m', x)`,
`INTERVAL '1 month'` → `date(x, '+1 month')`.

### CTE как шаги рассуждения

Один CTE = одна логическая операция, имя описывает результат, а не источник.
Это единственный способ сделать 200-строчный запрос ревьюабельным:

```sql
WITH base_users AS (            -- 1. определили популяцию
    SELECT user_id, created_at, plan_type FROM users
    WHERE created_at >= DATE '2026-01-01' AND status = 'active'
),
user_metrics AS (               -- 2. метрики на пользователя
    SELECT u.user_id, u.plan_type,
           COUNT(DISTINCT e.session_id) AS sessions,
           SUM(e.revenue)                AS revenue
    FROM base_users u LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY u.user_id, u.plan_type
)
SELECT plan_type, COUNT(*) AS users, AVG(sessions) AS avg_sessions, SUM(revenue) AS revenue
FROM user_metrics GROUP BY plan_type ORDER BY revenue DESC;
```

### Когортное удержание

```sql
WITH cohorts AS (
    SELECT user_id, DATE_TRUNC('month', first_activity_date) AS cohort_month FROM users
),
activity AS (
    SELECT user_id, DATE_TRUNC('month', activity_date) AS activity_month FROM user_activity
)
SELECT c.cohort_month,
       COUNT(DISTINCT c.user_id) AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month THEN a.user_id END) AS m0,
       COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '1 month' THEN a.user_id END) AS m1,
       COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '3 months' THEN a.user_id END) AS m3
FROM cohorts c LEFT JOIN activity a ON c.user_id = a.user_id
GROUP BY c.cohort_month ORDER BY c.cohort_month;
```

`COUNT(DISTINCT ...)` здесь не для красоты: без него LEFT JOIN с несколькими активностями
на пользователя раздувает когорту.

### Воронка

Схлопываем события в одну строку на пользователя, потом считаем переходы:

```sql
WITH funnel AS (
    SELECT user_id,
           MAX(CASE WHEN event = 'page_view'       THEN 1 ELSE 0 END) AS s1,
           MAX(CASE WHEN event = 'signup_start'    THEN 1 ELSE 0 END) AS s2,
           MAX(CASE WHEN event = 'signup_complete' THEN 1 ELSE 0 END) AS s3
    FROM events WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT SUM(s1) AS viewed, SUM(s2) AS started, SUM(s3) AS completed,
       ROUND(100.0 * SUM(s2) / NULLIF(SUM(s1), 0), 1) AS view_to_start_pct,
       ROUND(100.0 * SUM(s3) / NULLIF(SUM(s2), 0), 1) AS start_to_complete_pct
FROM funnel;
```

`NULLIF(x, 0)` в знаменателе — не паранойя: пустой сегмент роняет весь отчёт делением на ноль.

### Дедупликация «последняя запись на ключ»

```sql
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY updated_at DESC) AS rn
    FROM source_table
)
SELECT * FROM ranked WHERE rn = 1;
```

### Оконные функции — шпаргалка

```sql
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)   -- строгая нумерация
RANK() / DENSE_RANK() OVER (ORDER BY score DESC)                    -- с/без пропуска мест при равенстве
SUM(x)  OVER (ORDER BY d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)  -- накопительный итог
AVG(x)  OVER (ORDER BY d ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)          -- скользящее среднее 7 точек
LAG(x, 1)  OVER (PARTITION BY e ORDER BY d)                         -- предыдущее значение
x / SUM(x) OVER ()                                                  -- доля от общего
x / SUM(x) OVER (PARTITION BY category)                             -- доля внутри категории
```

`LAST_VALUE` без явной рамки `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`
возвращает текущую строку, а не последнюю — классическая тихая ошибка.

### Отладка упавшего запроса

1. **Синтаксис** — сверь диалект по таблице отличий выше (частая: `ILIKE`/`percentile_cont` в SQLite).
2. **Нет колонки** — опечатка либо кавычки: в SQLite `"typo"` не падает, а превращается в строку.
3. **Несовпадение типов** — приводи явно (`CAST(x AS INTEGER)`, `x::date`), особенно в SQLite,
   где сравнение TEXT с числом всегда даёт «TEXT больше».
4. **Деление на ноль / NULL** — `NULLIF(denom, 0)`; `SUM(CASE ...)` без `ELSE 0` даёт NULL.
5. **Неоднозначная колонка** — квалифицируй алиасом таблицы во всех JOIN.
6. **GROUP BY** — все неагрегированные колонки должны быть в GROUP BY.
7. **Результат «странный, но без ошибки»** — сверь `COUNT(*)` до и после JOIN;
   рост числа строк = размножение many-to-many, а не «нашлось больше данных».
