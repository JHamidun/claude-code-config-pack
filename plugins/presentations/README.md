# Presentations

> Gamma, Manus slides, Marp, native PPTX create/edit/import.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `gamma` | Генерация презентаций и доков через Gamma Generate API + экспорт PDF/PPTX/PNG; ключ GAMMA_API_KEY мёртв — сперва перевыпустить. |
| `manus-slides` | Слайды: 32 AI-стиля, HTML-шаблоны, темы Manus, рисованный exec-sketch (светлый/тёмный, ноутсы по ID). |
| `marp-presentations` | Marp: Markdown → слайды (HTML/PDF/PPTX) через npx marp-cli, бесплатная альтернатива Gamma. |
| `pptx` | Создание, правка и разбор .pptx файлов: layouts, спикер-ноты, комментарии. |
| `pptx-editable-extractor` | HTML → редактируемый PPTX: каждый текст-узел — нативный TextBox, правится в PowerPoint. |
| `pptx-import` | Распаковать PPTX как zip, извлечь текст/картинки/координаты из XML — переверстать чужой дек в HTML. |

### Agents

- `presentation-master`

### Commands

- `/slides`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install presentations@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`office-docs` · `web-publish`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
