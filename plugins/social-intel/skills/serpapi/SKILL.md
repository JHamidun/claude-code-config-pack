---
name: serpapi
description: "Google Search API через SerpAPI (SERPAPI_API_KEY): выдача, Maps, Shopping, News, YouTube. Триггеры: «спарси выдачу гугла», «цены google shopping»."
---

# SerpAPI

Живая выдача Google в структурированном JSON: web, Maps, Shopping, News, Images,
YouTube, Scholar, Jobs, Trends. Один эндпоинт, движок выбирается параметром
`engine`. Капчи и прокси на стороне сервиса — браузер не нужен.

## Ключ

`SERPAPI_API_KEY` из `~/.claude/.credentials.master.env`, читать через
`os.getenv`. Каждый вызов списывает единицу квоты плана — при отладке не гоняй
цикл по страницам вслепую. Тарифы и лимиты → `references/pricing-and-limits.md`.

## Вызов

```python
import os, requests

def serp(engine: str, **params) -> dict:
    r = requests.get("https://serpapi.com/search", params={
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": engine, "output": "json",
        "hl": "en", "gl": "us", **params,
    })
    r.raise_for_status()
    return r.json()
```

Есть официальная обёртка, но ставится она под неочевидным именем:
`pip install google-search-results`, а импорт при этом `from serpapi import
GoogleSearch`. Возможностей она не добавляет — тот же GET с теми же параметрами.

## Локальная бесплатная альтернатива

Для простого парсинга живой выдачи (без carousels/Maps/Shopping/Trends — за
структурой оставайся на SerpAPI) — self-hosted `karust/openserp` в Docker,
`127.0.0.1:7000`, 0 кредитов. Поддерживает Google/Yandex/Bing/DuckDuckGo.
DuckDuckGo/Bing работают из коробки; Google и особенно **Yandex** (которого
SerpAPI не отдаёт вообще) из коробки капчатся/ратлимитятся без прокси — нужен
`--proxy`/`--2captcha_key` на старте контейнера. Полные детали, эндпоинты, гочи
→ `~/.claude/skills/seo-machine-ru/SKILL.md`, секция «Яндекс/Google SERP локально
(openserp)».

## Движки: параметр запроса и ключ результатов

Ключ, под которым лежат результаты, из имени движка не выводится — угадаешь
неверно, получишь пустой список и решишь, что выдача пустая.

| engine | запрос кладётся в | результаты в |
|---|---|---|
| `google` | `q` | `organic_results` + `knowledge_graph`, `answer_box`, `related_questions`, `related_searches` |
| `google_maps` | `q` | `local_results` |
| `google_shopping` | `q` | `shopping_results` |
| `google_news` | `q` | `news_results` |
| `google_images` | `q` | `images_results` (не `image_`) |
| `youtube` | **`search_query`** (не `q`) | `video_results` |
| `google_scholar` | `q` | `organic_results` |
| `google_jobs` | `q` | `jobs_results` |
| `google_trends` | `q` | `interest_over_time`, `related_queries`, `related_topics` |
| `google_videos`, `google_local`, `google_patents` | `q` | распечатай `results.keys()` — здесь не зафиксировано |

## Параметры, которые не угадываются

| Задача | Параметр |
|---|---|
| Язык / страна выдачи | `hl=en`, `gl=us` |
| Вторая страница | `start=10` (третья — 20) |
| Свежесть: день/неделя/месяц/год | `tbs=qdr:d` / `qdr:w` / `qdr:m` / `qdr:y` |
| Вилка цен в Shopping | `tbs=mr:1,price:1,ppr_min:50` (и/или `ppr_max:200`) |
| Размер картинки | `tbs=isz:l` (`m` средние, `i` иконки) |
| Тип картинки | `tbs=itp:photo` (`clipart`, `lineart`) |
| Публикации от года (Scholar) | `as_ylo=2023` |
| Точка на карте | `ll=@55.75,37.61,15z` — с `@` и `z`-зумом; либо `location=Moscow` |
| Окно Trends | `date="today 12-m"` (`now 1-H`, `now 7-d`, `today 1-m`) + `data_type=TIMESERIES` |

`tbs` — одна строка: несколько фильтров склеиваются через запятую, второе
присваивание затирает первое.

## Вложенные поля ответа

Часть значений лежит глубже, чем кажется по названию:

- News: `source.name` (не `source`)
- YouTube: `channel.name`, `thumbnail.static`
- Scholar: `publication_info.summary`, `inline_links.cited_by.total`,
  PDF — `resources[0].link` (списка `resources` может не быть вовсе)
- Jobs: `detected_extensions.posted_at`, `detected_extensions.salary`
- Shopping: `price` — строка с валютой, число для сравнения — `extracted_price`
- Maps: `gps_coordinates`, `hours`

## Гочи

- Результаты кэшируются ~30 секунд: повтор идентичного запроса вернёт тот же
  снимок. Если нужна свежесть после правки — меняй параметры, а не жми повтор.
- Локаль решает состав выдачи: `gl`/`hl` меняют не только язык подписей, но и
  набор блоков (`answer_box`, «People also ask» появляются не везде).
