---
name: seo-machine-ru
description: SEO/GEO/AEO контент-машина для русского рынка — исследование → написание → оптимизация → публикация лонгридов и лендингов под Яндекс-стек (Метрика/Вебмастер/Wordstat). Включает рабочий Python-пайплайн (скоринг качества, читаемость по Флешу-Оборневой, плотность ключей с лемматизацией, очистка от AI-следов) и оптимизацию под цитируемость в AI-поиске (Яндекс Нейро, Alice, GigaChat, ChatGPT, Perplexity), плюс рабочий рецепт реального Wordstat. Использовать когда пользователь говорит «напиши SEO-статью», «оптимизируй под Яндекс», «семантическое ядро», «кластер статей», «попасть в AI-ответы», «GEO/AEO», «контент под поиск», «лендинг под конверсию», «почему не ранжируюсь». НЕ для постов в соцсети/мессенджеры и не для копирайтинга под личный бренд.
metadata:
  version: 1.1.0
  license: MIT
  ported_from: TheCraigHewitt/seomachine (локализация под RU/Яндекс)
---

# SEO / GEO / AEO машина (RU)

Полный конвейер производства SEO-контента под российский поиск и AI-выдачу. Локализован под Яндекс-стек (Метрика/Вебмастер/Wordstat). Аналитические модули написаны под русский (морфология, читаемость, anti-AI на русском). Скилл **самодостаточен**: движок (скоринг/читаемость/плотность/чистка/упаковка) внутри, данные и публикацию подключаете своими (см. `.env.example`).

**Перед любой задачей** прочитай контекст продукта: `context/product.md` (заполняется под твой бренд/ICP/оффер). Это заменяет внешний marketing-context.

## Когда использовать

- Семантическое ядро / кластеры под Яндекс (`research`, `cluster`).
- Написание и оптимизация лонгрида (`write`, `optimize`, `rewrite`).
- Аудит существующей страницы («почему не в топе»).
- GEO/AEO: попасть в ответы Яндекс Нейро / Alice / GigaChat / ChatGPT / Perplexity.
- Лендинг под конверсию + CRO-аудит.
- Размещение в каталогах для ссылок и цитируемости (RU-каталоги).

## Архитектура: фазы → чеклисты-роли → Python

Команда (фаза) запускает аналитические **роли** (`references/agents-checklists.md`) и **Python-скрипты** (`scripts/`).

### Фазы (workflow)

| Фаза | Что делает | Чем | Выход |
|------|-----------|-----|-------|
| **research** | семантика + топ-10 Яндекса + гэпы + бриф | Wordstat (`references/wordstat-real-recipe.md`) → `scripts/opportunity_scorer.py`; роль keyword-mapper | бриф `research/brief-<slug>.md` |
| **cluster** | пиллар + 8-12 спутников + карта перелинковки | роль cluster-strategist + opportunity_scorer | `research/cluster-<slug>.md` |
| **write** | статья 1500-3000 слов, AEO-ready | роли + после: `scrub` → `content_scorer.py` (порог 70) | `drafts/<slug>.md` |
| **optimize** | финальный SEO-проход, 0-100 | `seo_quality_rater_ru.py` + роли seo-optimizer/meta-creator/internal-linker | отчёт + правки |
| **rewrite** | обновление старого материала | те же + диф изменений | `rewrites/<slug>.md` |
| **audit** | разбор URL/файла, почему не ранжируется | `seo_quality_rater_ru.py` + Вебмастер позиции | `audits/<slug>.md` |
| **aeo** | оптимизация под AI-цитирование | `references/aeo-geo.md` | план цитируемости |
| **publish** | публикация на сайт | ваш CMS (Tilda/WordPress/Headless) | пост/страница |

Подробный сценарий каждой фазы: `references/workflow.md`.

## Python-пайплайн (`scripts/`)

Все скрипты — чистый stdlib (pymorphy2 опционально, есть fallback; `requests`/`python-docx` нужны для wordstat_fetch/docx). Запуск из папки `scripts/`.

| Скрипт | Что считает | Запуск |
|--------|-------------|--------|
| `content_scorer.py` | композит 5 измерений (humanity/specificity/structure/seo/readability), порог 70, JSON для авто-ревайза | `python content_scorer.py draft.md --kw "ключ"` |
| `seo_quality_rater_ru.py` | on-page SEO 0-100 по RU-гайдлайнам (объём, H2, мета, ссылки, плотность, AEO-intro) | `python seo_quality_rater_ru.py draft.md --kw "ключ"` |
| `readability_ru.py` | Флеш-Оборнева + водность (Главред) + структура | `python readability_ru.py draft.md` |
| `keyword_analyzer_ru.py` | плотность с лемматизацией, распределение, переспам | `python keyword_analyzer_ru.py draft.md --kw "ключ1" "ключ2"` |
| `content_scrubber.py` | чистит невидимые Unicode + типографика RU (НЕ трогает `---`/таблицы) | `python content_scrubber.py draft.md --in-place` |
| `opportunity_scorer.py` | приоритет ключей (8 факторов, CTR-кривая Яндекса) | `python opportunity_scorer.py keywords.json` |
| `wordstat_fetch.py` | реальные частоты Wordstat через internal API (headless, на cookie) | `python wordstat_fetch.py kw.txt --cookie "..."` |
| `wordstat_browser_snippet.js` | тот же съём частот через `browser_evaluate` на залогиненной странице | paste в browser_evaluate |
| `build_report_docx.py` | упаковка brief/cluster/draft в один Word-файл для стейкхолдера | `python build_report_docx.py --title T --out r.docx --draft d.md` |

**Цикл `write`:** написать → `content_scrubber.py --in-place` → `content_scorer.py`. Если `composite < 70` — применить `priority_fixes`, переписать (до 2 итераций), затем `seo_quality_rater_ru.py` для финального скора.

## Данные и публикация (подключаете свои)

- **Wordstat / частотность** → `references/wordstat-real-recipe.md` + `scripts/wordstat_*`. Свой аккаунт Яндекса в `.env`.
- **Вебмастер-позиции / Метрика-трафик** → Яндекс API/UI, свой OAuth-токен (`.env`). См. `references/data-yandex-tilda.md`.
- **Публикация поста/лендинга** → ваш CMS (Tilda Feeds API / WordPress REST / Headless).
- **Конкуренты** → топ выдачи Яндекса (`WebFetch`/`WebSearch`/браузер) + листиклы-обзоры рынка.

`opportunity_scorer.py` ест JSON-массив ключей `{keyword, volume, position, intent, competition, cluster_size}` — собери его из вывода Wordstat/Вебмастера.

## References (читать по необходимости)

| Файл | Когда |
|------|-------|
| `references/workflow.md` | пошаговый сценарий каждой фазы |
| `references/agents-checklists.md` | аналитические роли (seo-optimizer, meta-creator, internal-linker, keyword-mapper, editor, cro-analyst, headline-generator, cluster-strategist и др.) как RU-чеклисты |
| `references/aeo-geo.md` | оптимизация под AI-выдачу: Яндекс Нейро/Alice/GigaChat/ChatGPT/Perplexity + аудит цитирований + RU-каталоги |
| `references/seo-guidelines-ru.md` | пороги: объём, плотность (с леммами), длины мета под Яндекс, читаемость |
| `references/data-yandex-tilda.md` | откуда брать данные (Яндекс) и куда публиковать (ваш CMS) |
| `references/wordstat-real-recipe.md` | **рабочий** съём реальных частот Wordstat (internal API getTable, логин, анти-завис браузера, suggest); Direct API обычно закрыт (error 58) |

## Context (заполнить под проект — `context/`)

- `context/product.md` — бренд/ICP/оффер/голос/уникальные данные (читать первым).
- `context/target-keywords.md` — ядро по кластерам (пиллар/кластер/лонг-тейл + интент + текущие позиции).
- `context/internal-links-map.md` — карта страниц для перелинковки.
- `context/ai-citation-targets.md` — где хотим цитироваться (RU-поверхности).

## Примеры (`examples/`)

- `examples/` — образец структуры артефактов прогона (keywords.json → brief → cluster → draft + schema → Word-отчёт). Брать как шаблон формата выходных файлов.

## Заметки / уроки

- **Wordstat:** Direct API обычно закрыт (`error 58`). Реальный способ — internal API `POST /wordstat/api/getTable` с залогиненного браузера (куки сами, CSRF не нужен). Свой аккаунт Яндекса — в `.env`, 2FA проходит владелец, сессия в профиле браузера сохраняется. Подробно — `references/wordstat-real-recipe.md`.
- **Объёмы:** оценочные тиры (из ширины suggest) завышают в 5–10× — всегда снимать реальный Wordstat перед приоритизацией. Точные коммерческие лонг-тейлы часто = 0–3 показа: страницы под конверсию/AEO, не под трафик.
- **`content_scrubber.py`:** дефис-нормализация не трогает `---` (frontmatter) и `|---|` (таблицы) — иначе ломались мета и таблицы.
