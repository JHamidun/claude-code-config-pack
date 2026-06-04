# Cookbook — рецепты использования

> Конкретные сценарии с командами. Предполагается, что `pip install pyyaml openpyxl pymorphy3 pymorphy3-dicts-ru requests` выполнен.

---

## Рецепт А: Разовый отчёт по книге

**Когда:** нужно посмотреть «что пишут о книге» один раз, структурированный XLSX как у Медиалогии.

```bash
# 1. Создать конфиг книги
cd ~/.claude/skills/book-mentions-monitor
cp config/book.example.yaml config/mybook.yaml
# Заполнить: title, authors, anchors, exclude, isbn, channels

# 2. Собрать упоминания
python scripts/monitor.py collect config/mybook.yaml
# → out/mentions.json (все) + out/to_classify.json (батч для LLM)

# 3. В этой же Claude-сессии — LLM-классификация (opus + haiku по подписке):
#    a. Read out/to_classify.json
#    b. Task(model="opus") → disambiguate_prompt.md → {id, is_target_book, role, genre, cite}
#    c. Task(model="haiku") на is_target=true → tone_prompt.md → {id, tone}
#    d. Слить результаты → записать out/classified.json

# 4. Построить XLSX + дайджест
python scripts/monitor.py finalize config/mybook.yaml
# → out/<Название_книги>.xlsx (21 лист) + out/digest.md
```

**Быстрый baseline без LLM** (только правила, ниже точность):
```bash
python scripts/monitor.py run config/mybook.yaml --llm none
```

---

## Рецепт Б: Регулярный мониторинг через `/loop`

**Когда:** нужно отслеживать новые упоминания каждую неделю/день, инкрементально.

```yaml
# В config/mybook.yaml добавить:
period:
  mode: incremental      # только новое с прошлого прогона (сохраняется last_run.txt)
  lookback_days: 7       # запас на случай задержки индексации

digest:
  telegram_chat: "-100XXXXXXXXX"   # chat_id канала/группы
  alert_on_negative: true
```

В интерактивной Claude Code сессии:
```
/loop 7d python scripts/monitor.py collect config/mybook.yaml && [LLM-шаг] && python scripts/monitor.py finalize config/mybook.yaml
```

Или через `/schedule` (remote agent по cron):
```
/schedule "0 9 * * 1" "book-mentions-monitor mybook.yaml weekly"
```

**❗ Важно:** LLM-шаг (Task opus+haiku) должен быть в интерактивной сессии, не в cron headless.  
Для headless cron — только `--llm none` (правила-fallback, без расходов).

---

## Рецепт В: Репутационный алерт на негатив

**Когда:** нужно немедленно узнать, если появился негативный отзыв/публикация.

```yaml
# В config/mybook.yaml:
digest:
  telegram_chat: "-100XXXXXXXXX"
  alert_on_negative: true
  negative_threshold: 1   # алерт при первом же негативном упоминании
```

`monitor.py finalize` автоматически вызывает `report_digest.alert_negative(rel, book, chat)`:
- Собирает все `_tone == "Негатив"` с `_is_target == true`.
- Отправляет в Telegram отдельное сообщение: источник + заголовок + сниппет + ссылка.

Для немедленного алерта (мониторинг в реальном времени) — `/loop 1d` или RSSHub-подписка на профильные каналы с немедленным уведомлением.

---

## Рецепт Г: Мониторинг автора и издательства как отдельных объектов

**Когда:** нужно отследить упоминания не только книги, но и автора/издательства — как папка «АВТОРЫ» у Медиалогии.

Создать отдельный конфиг для каждого объекта:

```yaml
# config/author_monitor.yaml
title: "<ФАМИЛИЯ АВТОРА>"
object_type: person     # тип объекта (для листа «Объекты»)
anchors:
  - "детская книга"
  - "<ИЗДАТЕЛЬСТВО>"
  - "иллюстратор"
exclude:
  - "торговая марка"
channels:
  - googlenews
  - serpapi_connector
  - vk
  - telegram
```

Запустить параллельно или последовательно:
```bash
python scripts/monitor.py run config/mybook.yaml --llm none
python scripts/monitor.py run config/author_monitor.yaml --llm none
```

Объединить в сводный дайджест:
```bash
# Объект «<Издательство>» — отдельный конфиг для издательства
python scripts/monitor.py run config/publisher.yaml --llm none
```

В листе «Объекты» итогового XLSX появятся строки для каждого объекта с 9 метриками — точно как в Медиалогии.

---

## Рецепт Д: Добавить новый коннектор

**Когда:** нужен источник, которого нет в стандартных 11 (например, Habr, Pikabu, профильный RSS).

### Контракт коннектора (`scripts/lib/mention.py`)

```python
def collect(book: dict, creds: dict, limit: int = 50) -> list[dict]:
    """
    book   — конфиг книги из YAML (title, authors, anchors, exclude, isbn, …)
    creds  — словарь переменных из .env
    limit  — максимум упоминаний за прогон

    Возвращает список dicts с полями:
      url       str    — уникальный URL публикации (обязательно)
      title     str    — заголовок
      snippet   str    — краткое содержание / лид (≤ 500 симв)
      source    str    — домен или название источника
      date      str    — дата публикации ISO 8601 (YYYY-MM-DD или YYYY-MM-DDThh:mm)
      channel   str    — имя коннектора (= __file__.stem)

    Опционально (если доступно):
      author    str    — автор публикации
      views     int    — просмотры
      likes     int    — лайки
      reposts   int    — репосты
      comments  int    — комментарии
      text      str    — полный текст статьи
    """
    mentions = []
    # ... ваша логика ...
    return mentions
```

### Создать файл

```bash
cp scripts/connectors/googlenews.py scripts/connectors/habr.py
# Отредактировать: URL запроса, парсинг ответа, поля mention
```

### Подключить в book.yaml

```yaml
channels:
  - googlenews
  - habr          # имя файла без .py
  - serpapi_connector
```

### Проверить

```bash
python scripts/monitor.py collect config/mybook.yaml
# В выводе должна появиться строка: "habr: N"
```

**Правила хорошего коннектора:**
- Уважать `limit` — не тянуть больше, чем запрошено.
- `content_scrubber.scrub(text)` на snippet перед возвратом.
- Пауза 1–3 с между запросами к одному хосту (не получить бан).
- Не падать с исключением — логировать ошибку и возвращать пустой список.
- Точная фраза в кавычках + якори из `book["anchors"]` — обязательно.
