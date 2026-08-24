# Workflow — пошаговые сценарии фаз

> Сценарии портированы из команд seomachine (`/research`, `/write`, `/cluster`, `/optimize`, `/landing-*`), адаптированы под Яндекс+Tilda+RU. Везде сначала читай `~/.claude/business-context.md`.

## research — бриф под тему

1. Прочитать `context/target-keywords.md` + `~/.claude/business-context.md`.
2. Через скилл `yandex` (Wordstat): собрать частотность по теме, расширения, вопросы (что/как/почему).
3. Через `yandex` (Вебмастер): текущие позиции своих страниц по теме.
4. Топ-10 Яндекса по главному ключу (WebSearch/WebFetch или dev-browser) → выписать: интент, формат, объём конкурентов, структуру, что покрыто/не покрыто (гэпы).
5. Собрать ключи в JSON → `python scripts/opportunity_scorer.py kw.json` → отобрать quick-win (позиции 11-20) и high.
6. Выход — бриф: целевой ключ + LSI, интент, рекомендованный объём (медиана топ-10 ×1.1), структура H2/H3, гэпы для покрытия, мета-превью, внутренние ссылки-кандидаты. Сохранить в `research/brief-<slug>.md`.

## cluster — тематический кластер

1. Главная тема → через Wordstat собрать 30-100 связанных запросов.
2. Сгруппировать в пиллар (1 широкий) + 8-12 спутников (узкие интенты). Роль `cluster-strategist` (см. agents-checklists).
3. Проверить каннибализацию: один интент = одна страница.
4. Карта перелинковки: спутники → пиллар (анкор = ключ пиллара), пиллар → спутники.
5. Приоритизация спутников: `opportunity_scorer.py` (объём/сложность/коммерческость).
6. Выход — `research/cluster-<slug>.md`: структура, ядро по каждой статье, карта ссылок, очередь написания.

## write — написание статьи

1. Бриф + контекст-голос (`~/.claude/business-context.md`; для личного блога — `~/.claude/author-profile.md` + соответствующий writing-скилл).
2. Структура: **прямой ответ в первых 2-3 предложениях** (критично для AEO), затем раскрытие по H2.
3. Писать 1500-3000 слов: мини-истории, конкретика и цифры, списки/таблицы (сканируемость + AEO), контекстные CTA. Соблюдать `seo-guidelines-ru.md`.
4. Роли после черновика: `seo-optimizer`, `meta-creator`, `internal-linker`, `keyword-mapper` (agents-checklists.md).
5. **Очистка:** `python scripts/content_scrubber.py drafts/<slug>.md --in-place`.
6. **Скоринг:** `python scripts/content_scorer.py drafts/<slug>.md --kw "ключ"`. Если `composite < 70` — применить `priority_fixes`, переписать (≤2 итерации). Если после 2 итераций <70 → пометить «review-required» и показать пользователю.
7. Финал: `python scripts/seo_quality_rater_ru.py drafts/<slug>.md --kw "ключ"` (цель ≥75).

## optimize / rewrite — доводка существующего

1. `seo_quality_rater_ru.py` по файлу/URL → список провисаний.
2. `keyword_analyzer_ru.py` → плотность/распределение/переспам.
3. Роли seo-optimizer + meta-creator + internal-linker применяют правки.
4. rewrite: освежить цифры/даты, добавить новые ключи из Wordstat, переписать устаревшее; сохранить URL/слаг (не плодить дубли).

## audit — почему не ранжируется

1. `yandex` Вебмастер: индексация, позиции, запросы, ошибки.
2. `seo_quality_rater_ru.py` + `readability_ru.py` по странице.
3. Топ-10 конкурентов по ключу: чем они полнее (гэп-анализ).
4. Чеклист причин: интент не совпал / тонко / нет структуры / каннибализация / нет внутренних ссылок / медленная страница / нет прямого ответа (AEO).
5. Выход — приоритизированный план фиксов.

## landing — лендинг + CRO

1. research под лендинг (узкое ядро, коммерческий интент).
2. Написать: SEO-лендинг 1500-2500 слов или PPC 400-800 слов, цель trial/demo/lead.
3. Роли `headline-generator`, `cro-analyst`, `landing-page-optimizer` (agents-checklists.md).
4. CRO-аудит — передать в кластер `*-cro-ru` (page-cro-ru).
5. Публикация — скилл `tilda` (page editor / T123).

## publish — публикация

- Пост в блог/медиа → скилл `tilda` (Feeds API) или конвейер `ai-news-bot` если это новостной материал.
- Лендинг → `tilda` page editor.
- Проставить мета (title/description/og) в SEO-полях Tilda — см. `data-yandex-tilda.md`.
- После публикации: добавить в Вебмастер на переобход (скилл `yandex`).
