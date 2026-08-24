# gbrain: типизированные рёбра без LLM + gap-анализ (паттерн-референс)

> Дистилляция из [garrytan/gbrain](https://github.com/garrytan/gbrain) (Garry Tan, MIT).
> Цель — усилить локальный граф памяти `~/.claude/scripts/memory_graph.py` (`~/.claude/memory-graph/graph.db`).
> Это референс-паттерн, НЕ инструмент к установке: gbrain = TS/Bun + Postgres/PGLite + pgvector, наш стек = Python+SQLite. Берём идеи, не код.

---

## 1. Что в gbrain ценно именно для нас

| Приём gbrain | Наш эквивалент | Дельта |
|---|---|---|
| Типизированные рёбра из pattern-matching **на каждом write, 0 LLM** | `link`/`supersedes`/`about`/`involves`/`uses`/`for_company`/`in_project` — тоже без LLM | у нас все `[[link]]` рёбра **безтиповые** — можно типизировать по namespace цели |
| **Gap-анализ**: чего мозг НЕ знает (stale / uncited / contradictions / holes) | частично: `orphans` + `dangling` | нет staleness, нет контра-детекта, нет единой команды → **внедрено: `gaps`** |
| Граф-сигнал даёт **+31.4pp P@5** vs vector-only/BM25 | у нас ретрив живёт отдельно от memory_graph | обоснование, зачем граф-слой в гибридном ретриве (не код-правка тут) |
| Git как system-of-record + soft-delete при удалении файла | bi-temporal supersedes (иммутабельность, не удаляем) | уже покрыто `rules/auto-learning.md` |
| Schema packs — канон-словарь типов узлов (15 канонич.) | 5 типов заметок + 5 namespace сущностей | наш словарь достаточен, расширять не нужно |

**Вывод: чистый дубль по 3 пунктам (soft-delete, schema packs, git-as-record). Реально ценно 2: gap-анализ (внедрён) + типизация link-рёбер по цели (предложение).**

---

## 2. Типизированные рёбра БЕЗ LLM — как это делает gbrain

gbrain на КАЖДОМ сохранении страницы прогоняет **чистый pattern-matching** по markdown/wikilinks и создаёт типизированные рёбра. Никаких LLM-вызовов.

- Источник типа ребра — **namespace/путь цели ссылки**: `[[wiki/people/bob]]` → узел `person`, `[[wiki/companies/acme]]` → узел `company`.
- Новая сущность в ссылке → автоматически создаётся stub-страница → граф растёт органически.
- Декларированные типы рёбер (gbrain-base-v2): `attended`, `works_at`, `invested_in`, `founded`, `advises`, `mentions`.
- 15 канонич. типов узлов: `person, company, media, tweet, social-digest, analysis, atom, concept, source, deal, email, slack, writing, project, note`.

**Ключевая идея для нас:** тип ребра выводится из ТИПА ЦЕЛИ, а не из содержимого — а у нас типы целей уже есть в namespace (`person:`, `company:`, `tool:`, `proj:`, `case:`). Значит link-рёбра к ним можно типизировать механически (см. §4, предложение P2).

---

## 3. Gap-анализ — таксономия (сердце паттерна)

gbrain при ответе на запрос отдельным блоком выдаёт «чего мозг пока НЕ знает». Механизмы детекта (все дёшевы, без тяжёлого LLM в базовом варианте):

| Тип дыры | Как детектит gbrain | Наш дешёвый аналог (SQLite) |
|---|---|---|
| **Stale** (устаревшее) | age-check страниц: «про Alice ничего не добавлено с 22 апреля, 6 недель» | `mtime` узла-заметки старше порога + высокая степень = вероятный дрейф |
| **Uncited** (бездоказательное) | claim без ссылки на источник | заметка без `[[link]]` наружу и без входящих ссылок = не вплетена |
| **Contradiction** (противоречие) | LLM-судья сэмплит пары страниц | bi-temporal: узел — цель `supersedes`-ребра, но `status` не `superseded` |
| **Holes** (пробелы) | query-conditioned reasoning: чего не хватает под вопрос | `dangling` — ссылаются на заметку, которой нет (кандидат создать); `orphans` — заметка без связей |

**Мораль:** три из четырёх типов дыр детектятся чистым SQL по нашим же данным (mtime, status, рёбра). LLM-судья для противоречий — опционально, но у нас уже есть дешёвый bi-temporal сигнал (supersedes), который его частично заменяет.

---

## 4. Конкретные предложения по `memory_graph.py`

### P1 — команда `gaps` — ВНЕДРЕНО (2026-07-17)
Добавлена функция `gaps([stale_days=45])` + запись в dispatch и docstring. Выдаёт 4 секции gbrain-таксономии одним прогоном:
- **ORPHANS** — заметки (`mtime>0`) без единого ребра → кандидаты на `[[link]]`.
- **DANGLING** — `rel='link'` на несуществующий узел, топ по частоте → кандидаты создать заметку.
- **STALE HUBS** — узлы с высокой степенью и `mtime` старше порога → проверить на дрейф/противоречие с кодом.
- **SUPERSEDED-UNMARKED** — узел является целью `supersedes`-ребра, но его `status` не помечен superseded → bi-temporal противоречие (эвристика).

Вызов:
```bash
python ~/.claude/scripts/memory_graph.py gaps         # порог устаревания 45 дней
python ~/.claude/scripts/memory_graph.py gaps 30      # свой порог
```
Куда встроить в поток: навык `dream` — `gaps` даёт готовый to-do список консолидации (что вплести,
что пометить superseded, что проверить на дрейф).

### P2 — типизировать `link`-рёбра по namespace цели (предложение, НЕ внедрено)
Сейчас `edges.append((name, l, "link"))` — все безтиповые. Если цель ссылки имеет namespace (`person:X`, `tool:Y`, `proj:Z`), присвоить ребру тип `mentions_person` / `mentions_tool` / `mentions_project` (по образцу gbrain `mentions`). Это даёт типизированные фильтры соседей без LLM.
Скетч (в `build()`, где формируются link-рёбра):
```python
NS_REL = {"person": "mentions_person", "company": "mentions_company",
          "tool": "mentions_tool", "proj": "mentions_project"}
for l in links:
    rel = "link"
    if ":" in l:
        rel = NS_REL.get(l.split(":", 1)[0], "link")
    edges.append((name, l, rel))
```
Риск: большинство наших `[[link]]` целят в имена заметок (без namespace) → эффект малый, пока заметки не начнут ссылаться на сущности через namespace. Отложено как low-ROI.

### P3 — граф-сигнал в гибридный ретрив (обоснование, вне scope этого файла)
gbrain +31.4pp P@5 получен добавлением graph adjacency boost к vector+BM25. Если у тебя есть
отдельный векторный ретрив с реранкингом — adjacency из `graph.db` (сосед-хабы искомого) можно
подмешивать туда как boost. Тяжёлая задача, здесь только заметка о направлении.

---

## 5. Вердикт
- **Внедрено:** `gaps`-команда в `memory_graph.py` (gbrain gap-таксономия на нашем SQLite, 0 LLM).
- **Паттерн-референс:** этот файл — типизация рёбер без LLM + gap-таксономия.
- **Дубль (не внедряю):** soft-delete (=наш supersedes), schema packs (наш словарь достаточен), git-as-record.
- **Не тянем:** gbrain целиком (TS/Bun/Postgres/pgvector/ZeroEntropy reranker) — другой стек, платный reranker, наш локальный SQLite-граф закрывает нишу «офлайн-память».
