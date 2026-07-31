# Данные и публикация: адаптеры к `yandex` и `tilda`

> Машина НЕ имеет своих API-клиентов к Яндексу/Tilda — она переиспользует существующие скиллы. Это сознательный выбор: один источник правды по OAuth/токенам. Здесь — как именно дёргать.

## Семантика и частотность — Wordstat (скилл `yandex`)

Wordstat = Direct API v4 (legacy), service 13. Через скилл `yandex`:
```bash
# Создать отчёт Wordstat по фразам
python ~/.claude/skills/yandex/scripts/yandex_api.py  # см. SKILL.md §12 Wordstat
# Метод CreateNewWordstatReport {"Phrases": ["нейросети для бизнеса", ...]}
# затем GetWordstatReportList / GetWordstatReport <id>
```
Берёт частотность фраз и связанные запросы. Из результата собрать JSON для `opportunity_scorer.py`:
```json
[{"keyword":"нейросети для бизнеса","volume":12000,"position":14,"intent":"commercial","competition":0.6,"cluster_size":8}]
```
`position` — из Вебмастера (ниже), `competition` — оценка по топу выдачи, `intent` — классификация по запросу.

## Позиции, запросы, индексация — Вебмастер (скилл `yandex`)

Webmaster API v4, service 5:
```bash
python ~/.claude/skills/yandex/scripts/yandex_api.py webmaster sites
# далее по SKILL.md §5: search queries, indexing, backlinks для host_id
```
Даёт: текущие позиции и показы (для quick-win поз. 11-20), CTR, проиндексированность, ошибки, бэклинки. После публикации — отправить URL на переобход.

## Трафик и конверсии — Метрика (скилл `yandex` / `product-analytics`)

```bash
python ~/.claude/skills/yandex/scripts/yandex_api.py metrika report \
  --metrics "ym:s:visits,ym:s:pageviews,ym:s:bounceRate" --date1 "30daysAgo" --date2 "today"
```
Для YourProduct — лучше `product-analytics` (уже умеет сегменты corporate/individual, воронки buy, UTM). Используется в фазе `performance` и для CRO-приоритизации.

## Конкуренты / объёмы рынка

- Гэп-анализ контента, трафик конкурентов → `similarweb-analytics`, `competitive-analysis`.
- Топ выдачи Яндекса для оценки конкуренции — WebFetch/WebSearch или `dev-browser`.

## Публикация — Tilda (скилл `tilda`)

```bash
# Пост в фид блога / медиа — Feeds API
python ~/.claude/skills/tilda/scripts/...   # см. tilda/SKILL.md: posts_Add/Edit/Active
# Лендинг / страница — page editor, T123 custom HTML, page publish
```
Мета (title/description/og) ставятся в SEO-полях страницы/поста Tilda (НЕ Yoast). После публикации обязательно `posts_Active` (Edit сбрасывает active — известная грабля, см. tilda skill memory).

Новостной материал в блог your-domain.com → готовый конвейер `ai-news-bot` (build_tilda_blocks + JSON-LD + push).

## Принцип

Машина считает (Python-скрипты) и пишет (роли), но **данные берёт и публикует через `yandex`/`tilda`/`product-analytics`**. Не воспроизводить их OAuth/HTTP-клиенты здесь.
