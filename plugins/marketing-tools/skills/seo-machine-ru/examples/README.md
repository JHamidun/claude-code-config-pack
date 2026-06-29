# Пример прогона (демо)

Нейтральный пример на фиктивном продукте **«TaskFlow»** (вымышленная SaaS для управления задачами).
Показывает форму артефактов каждой фазы. Цифры и факты — выдуманные, замените на свои.

## Файлы
- `keywords.sample.json` — вход для `scripts/opportunity_scorer.py` (форма JSON ядра).
- `sample-article.md` — статья под главный кластер: YAML-мета + прямой ответ сверху (AEO) + H2/H3 + таблица + FAQ.
- `sample-article.schema.json` — JSON-LD (Article + FAQPage) для `<head>` страницы.

## Как воспроизвести под себя
1. Заполни `context/product.md` под свой бренд.
2. Собери ядро (Wordstat — `references/wordstat-real-recipe.md`), сложи в `keywords.json`, прогони `opportunity_scorer.py`.
3. Напиши статью по `references/workflow.md` (фаза `write`), прогони `content_scrubber.py` → `content_scorer.py` → `seo_quality_rater_ru.py` (цель ≥75).
4. Упакуй для стейкхолдера: `python scripts/build_report_docx.py --title "Бренд — SEO" --out report.docx --draft examples/sample-article.md`.
