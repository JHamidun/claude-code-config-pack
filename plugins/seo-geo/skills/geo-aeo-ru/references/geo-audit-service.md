# GEO-аудит как услуга (Your Consulting)

> Краткая заметка по вердикту ninja-recon (2026-07-18): продажная обвязка из
> zubair-trabzada/geo-seo-claude (geo-prospect → geo-audit → geo-proposal → geo-report-pdf →
> white-label). Идеи зафиксированы для адаптации; цифры западного рынка — референс, не RU-прайс.

## Идея продукта

Полный конвейер «продавать GEO-аудит как услугу», а не разовые советы:

1. **Prospect** — реестр потенциальных клиентов (домен, контакт, статус
   New → Qualified → Proposal → Client). У нас это Your CRM/`lead-enrichment`, не отдельный CRM.
2. **Audit** — скоринговый аудит домена: скрипты `scripts/` (citability, robots/AI-краулеры,
   llms.txt, SSR, schema, brand mentions) + промпт-аудит по 6 платформам (workflow из SKILL.md —
   наш уникальный RU-слой: (regional LLM B)/(regional LLM A)/Нейро, которых нет ни у одного западного тула).
3. **Proposal** — из аудита автогенерится КП: находки → бизнес-боли → 3 пакета → ROI → таймлайн.
   Генерить через `kp-deck-factory` (трек B), не отдельным шаблоном.
4. **Report** — брендированный PDF-отчёт клиенту (score breakdown, критические находки, quick wins).
5. **White-label** — весь брендинг отчёта в одном `brand.json` (имя агентства, контакты, цвета),
   генератор кода не трогается. Паттерн взять при упаковке отчётов для партнёров.

## Структура proposal (проверенная у Zubair, адаптировать)

- **Executive summary:** GEO Score X/100 + 3 самые дорогие проблемы, переведённые в бизнес-язык.
- **Score → рекомендуемый пакет:** 0-40 → Premium (критично), 41-60 → Standard (месячная работа),
  61-75 → Basic (мониторинг), 76+ → квартальный чек-ин.
- **3 пакета** (у Zubair €2.5K / €5K / €9.5K в месяц, контракт от 6 мес — это EU-бенчмарк;
  RU-прайс калибровать отдельно, якорь снизу уже есть: AI Visibility Dashboard 5-15K ₽/мес
  из `action-plan-your-product.md`; консалтинговый аудит руками — существенно дороже дашборда).
- **ROI-таблица** «no action vs пакеты» + консервативные допущения прописью.
- **Таймлайн 6 мес:** M1 quick wins (robots/schema/llms.txt) → M2-3 citability-переписывание
  топ-страниц + E-E-A-T → M4-6 authority building (упоминания) → M6 re-audit before/after.
- Дисклеймер: «гарантируем методологию и усилия, не позиции» — обязателен.

## RU-дифференциация (наш moat)

- Западные GEO-агентства и тулы не видят (regional LLM B)/(regional LLM A)/Нейро (`references/russian-llm.md`) —
  аудит «все платформы включая русские» не может предложить никто из конкурентов.
- Два продукта из одного конвейера: (а) консалтинговый аудит+сопровождение (Your Consulting),
  (б) self-serve мониторинг как фича YourProduct (`references/action-plan-your-product.md`).
- Первые кандидаты на пилотный аудит (и кейс для продажи): your-domain.com, news.your-domain.com,
  academy — прогон скриптов по ним = отдельная задача владельца.

## Что НЕ переносим

- Prospect-CRM (rich-CLI) и Flask-webapp Zubair — у нас Your CRM.
- Отдельный PDF-генератор — рендер через deck-stage/Playwright из `kp-deck-factory`.
- EUR-прайсинг как есть — только структура пакетов.
