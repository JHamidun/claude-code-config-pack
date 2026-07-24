---
name: deck-themes
description: Несколько готовых "тем" для slides — минимал, editorial, dark, data, brutalist. Стартовая точка вместо пустого шаблона. Соседние: theme-factory (10 универсальных тем для любых артефактов), frontend-design (эстетика без дизайн-системы); развилка — в design-orchestrator.
when_to_use: Когда нужен дек, и пользователь не дал бренд. Выбери тему, дальше работай с ней.
---

# Deck themes

Готовые CSS-темы для `<deck-stage>`. Каждая — один CSS-файл, который подключается рядом с `deck-stage.js`. Конкретный набор шрифтов, цветов, размеров.

## Файлы

- `templates/theme-minimal.css` — спокойный, для B2B и продуктовых ревью.
- `templates/theme-editorial.css` — антиква + воздух, для лонгридов и питчей.
- `templates/theme-dark.css` — тёмный фон, для конференций и кинематографичности.
- `templates/theme-data.css` — для отчётов с цифрами и таблицами.
- `templates/theme-brutalist.css` — моноширинная утилитарность, для девелопер-брендов.

## Использование

```html
<link rel="stylesheet" href="theme-editorial.css" />
<script src="deck-stage.js"></script>
<deck-stage width="1920" height="1080">
  <section>
    <h1>Заголовок</h1>
    <p>Текст</p>
  </section>
</deck-stage>
```

Темы не используют !important — переопределяй конкретные слайды inline-стилями.

## Что общего у всех тем

Каждая тема задаёт:
- `--bg`, `--fg`, `--muted`, `--accent`
- `--font-display`, `--font-body`, `--font-mono`
- размеры `h1`, `h2`, `h3`, `p`, `.eyebrow`
- `.statement`, `.two-col`, `.title-stack`, `.dark` (инвертированный режим)
- `.placeholder`

Слайды переносимы между темами — поменяй `<link>`, и тот же HTML выглядит иначе.

## Правила выбора

| Тема | Подходит | Не подходит |
|---|---|---|
| minimal | внутренние ревью, продукт | креатив-агентства |
| editorial | питчи, манифесты, бренды | data-репорты |
| dark | конференции, AI/tech | финансы, образование |
| data | отчёты, KPI, аналитика | креатив, маркетинг |
| brutalist | dev-tools, опен-сорс | продажи b2c |
