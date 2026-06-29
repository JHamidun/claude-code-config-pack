---
name: book-mentions-monitor
description: Мониторинг упоминаний книг в открытых источниках (СМИ + соцсети + читательские площадки) — замена системы «Медиалогия». Собирает упоминания из Google News, SerpAPI (VK/Дзен/маркетплейсы через site:), Telegram (Telethon+RSSHub), LiveLib, YouTube, ScrapeCreators (Instagram/TikTok/Reddit), RSS-фиды, считает тональность/роль/жанр (Claude opus+haiku по подписке), охват (Tranco/Cloudflare), МедиаИндекс, дедуп оригинал/перепечатка, строит XLSX-отчёт в структуре Медиалогии + дайджест в Telegram. Использовать когда пользователь говорит «мониторинг упоминаний книги», «что пишут о книге», «отслеживай книгу», «отчёт по книге как в Медиалогии», «book mentions», «упоминания автора», или просит собрать упоминания издания в СМИ и соцсетях.
---

# book-mentions-monitor

Свой инструмент медиамониторинга книг — воспроизводит логику и метрики «Медиалогии» из **открытых источников**, плюс добавляет читательский слой (рецензии/отзывы/буктьюб), которого у Медиалогии нет. Всё бесплатно или в рамках уже оплаченного стека (Claude Max, SerpAPI, ScrapeCreators-кредиты).

## Когда использовать
- Регулярный мониторинг упоминаний книги/автора в СМИ и соцсетях.
- Разовый отчёт «что пишут о книге» в структуре Медиалогии (XLSX).
- Репутационный сторож — алерт на негатив.

## Быстрый старт

```bash
cd ~/.claude/skills/book-mentions-monitor/scripts
# 1. Скопируй конфиг книги и заполни (название, авторы, якоря, минус-слова)
cp ../config/book.example.yaml ../config/mybook.yaml

# 2a. Автономный прогон на правилах (без LLM) — быстрый baseline:
python monitor.py run ../config/mybook.yaml --llm none

# 2b. С LLM-классификацией по подписке (точная дизамбигуация омонимов):
python monitor.py collect ../config/mybook.yaml          # собрать + выгрузить out/to_classify.json
#   → затем в ЭТОЙ Claude-сессии (см. ниже «LLM-слой») создать out/classified.json
python monitor.py finalize ../config/mybook.yaml         # построить XLSX + дайджест
```

Результат: `scripts/out/<книга>.xlsx` (листы как у Медиалогии) + `out/digest.md`.

## LLM-слой (тональность/роль/жанр) — ПО ПОДПИСКЕ

⚠️ **Критично:** классификацию делают **Task-субагенты Claude Code в интерактивной сессии** — это subsidized Claude Max, 0 API-трат. НЕ запускать через `claude -p` / Agent SDK (с 15.06.2026 — отдельный платный пул). Проверь: `ANTHROPIC_API_KEY` НЕ должен быть в env.

Когда пользователь просит точный отчёт, после `collect` сделай:
1. Прочитай `out/to_classify.json` (батч кандидатов).
2. Запусти **Task `model: opus`** с промптом `scripts/classify/disambiguate_prompt.md` (подставь title/authors/anchors/exclude + items) → получи `is_target_book`/`role`/`genre`/`cite`. Opus критичен — отсекает омонимы.
3. Запусти **Task `model: haiku`** с промптом `scripts/classify/tone_prompt.md` на упоминаниях с `is_target_book=true` → `tone`.
4. Слей в массив `[{id, is_target_book, role, genre, cite, tone}]` → запиши `out/classified.json`.
5. `python monitor.py finalize ../config/mybook.yaml`.

Большие батчи (100+) — дроби и/или гоняй через `Workflow` (pipeline, opus на дизамбигуацию, haiku на тональность).

## Каналы (scripts/connectors/)
| Файл | Канал | Метод | Free |
|---|---|---|---|
| `googlenews.py` | Google News RSS | RSS, кавычки+якоря | а |
| `serpapi_connector.py` | СМИ | SerpAPI news/web/yandex | б |
| `vk.py` ⭐ | VK | SerpAPI `site:vk.com` (без токена) | а |
| `dzen.py` | Дзен | SerpAPI `site:dzen.ru` | а |
| `telegram.py` | Telegram | TG_CLIENT_PATH или lib/tg_telethon.py (встроенный) + msg-views | а |
| `rsshub_tg.py` | TG-каналы | RSSHub (RSSHUB_BASE_URL) | а |
| `rss_feeds.py` | Произвольные RSS | Произвольные RSS-фиды (RSS_FEEDS) | а |
| `livelib.py` ⭐ | LiveLib | рейтинг/рецензии (cp1251 JSON-LD) | а |
| `marketplace_stores.py` | магазины | SerpAPI site: (отзывы/цена) | а |
| `youtube.py` | YouTube | YouTube Data API + ScrapeCreators | б |
| `scrapecreators.py` | IG/TikTok/Reddit | ScrapeCreators API | б |
| `wordstat.py` | спрос | Wordstat internal + Suggest | б |

Включить/выключить — список `channels:` в конфиге книги.

## Метрики (как у Медиалогии)
- **Количество** · **Оригиналы/Перепечатки** (дедуп лемма-шинглами) · **Тональность** (Поз/Нейтр/Нег) · **Роль** (Главная/Эпизодическая) · **Жанр** (Новость/Аналитика/Интервью/Анонс) · **Цитирование** · **Охват** (Tranco/Cloudflare + соц-просмотры) · **МедиаИндекс** = заметность (формула в `references/metrics.md`) · **Вовлечённость** (views/likes/reposts).
- Сверх Медиалогии: **читательские рейтинги/рецензии** (LiveLib), **отзывы магазинов**, **буктьюб**, **спрос Wordstat**.

## Структура
```
config/   book.example.yaml · media-registry.json · stopwords-ru.txt
scripts/
  monitor.py              оркестратор (collect/finalize/run)
  lib/    mention.py (контракт) · enrich.py · reach.py · dedup.py · report_xlsx.py · report_digest.py
          keyword_analyzer_ru.py · content_scrubber.py · readability_ru.py · wordstat_fetch.py  (из seo-machine, pymorphy3)
  connectors/  11 коннекторов (контракт: collect(book, creds, limit) -> list[mention])
  classify/    disambiguate_prompt.md (opus) · tone_prompt.md (haiku)
references/  channels.md · metrics.md · medialogia-structure.md · disambiguation.md · llm-billing.md · cookbook.md
```

## Зависимости
`pip install pyyaml openpyxl pymorphy3 pymorphy3-dicts-ru requests telethon` (pymorphy3 — лемматизация, НЕ pymorphy2: на Python 3.13 мёртв).

## Регулярный мониторинг
`/loop` в интерактивной сессии (LLM по подписке) или `/schedule`. Инкрементально — `period.mode: incremental` (только новое с прошлого прогона). Подробности и рецепты — `references/cookbook.md`.

## Главный урок (см. references/disambiguation.md)
Названия книг часто **омонимичны** (например, с госпроектами, топонимами, одноимёнными фильмами). Защита двухслойная: (1) запрос = точная фраза в кавычках + якоря; (2) opus-агент `is_target_book` отсекает омонимы. Без этого precision проваливается.

## Установка

См. [README.md](README.md) — полная инструкция: зависимости, переменные окружения, где получить каждый API-ключ.
