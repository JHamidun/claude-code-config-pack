# Design System

> Design tokens, color scales, type scale, dark mode, themes, brand kit.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `brand-extractor` | Вытащить цвета, шрифты, копирайт из сайта по URL (headless Playwright). |
| `brand-guidelines` | Официальные цвета и шрифты бренда Anthropic для артефактов. |
| `color-system-builder` | Из одного акцента — полная палитра: light+dark, 9-step scale, semantic, WCAG-контраст. |
| `dark-mode-add` | Добавить dark mode к light-дизайну: продуманные dark-токены, не инверт. |
| `deck-themes` | Готовые CSS-темы для slides без бренда: минимал, editorial, dark, data, brutalist. |
| `design-md-brands` | A bank of ready-made DESIGN.md design systems for 73+ known brands (Stripe, Linear, Vercel, Notion, Apple) — pulled on demand. |
| `design-system-create` | Собрать дизайн-систему с нуля: токены, типографика, компоненты, гайдлайны. |
| `design-tokens-w3c` | Экспорт дизайн-токенов в W3C DTCG tokens.json: Style Dictionary, Token Studio. |
| `fonts-bundle` | Готовые блоки <link> для пар шрифтов Google Fonts (веса, subset) + system-стек. |
| `moodboard` | HTML-мудборд из 5-15 референсов с палитрой из картинок — согласовать визуальный язык на старте. |
| `theme-factory` | Стилизация артефакта темой: 10 пресетов цвета/шрифтов или новая тема на лету. |
| `type-scale` | Modular type scale из base + ratio, плюс 30 проверенных font-пар. |

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install design-system@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`design-process` · `prototyping` · `ui-motion` · `design-io` · `web-publish`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
