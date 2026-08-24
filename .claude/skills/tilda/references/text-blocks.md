---
title: Tilda blog post body — block types and rich formatting
---

# Tilda Blog Post Body (`text` field) — block types

Поле `text` поста в Feed-блоке — это **JSON-массив блоков**, не просто HTML. Каждый блок имеет тип `ty` и набор полей. Tilda на странице рендерит каждый блок со своим CSS-классом из дизайн-системы (`t-redactor__*`).

## Формат

```json
text = JSON.stringify([
  {ty: "text", te: "<p>Параграф</p>"},
  {ty: "heading", te: "<strong>Подзаголовок</strong>", le: 2},
  {ty: "quote", te: "Цитата или блок промпта"},
  {ty: "br", color: "#000000"},
  {ty: "html", co: "<div>Кастомный HTML</div>"}
])
```

На API возврате (`posts_Get`) text приходит HTML-encoded для transport (`<` → `&lt;`, `"` → `&quot;`). Перед `JSON.parse` нужно decode через `textarea.innerHTML → .value`.

## Типы блоков (открытые реверс-инжинирингом)

| `ty` | Поля | Что это | CSS-класс на сайте |
|---|---|---|---|
| `text` | `te` | Параграфы — главный блок для контента | `t-redactor__text` |
| `heading` | `te`, `le` | Подзаголовок (`le: 2` = h2, `le: 3` = h3) | `t-redactor__h2` / `t-redactor__h3` |
| `quote` | `te` | Цитата с боковым акцентом | `t-redactor__quote` |
| `br` | `color` | Горизонтальный разделитель | стандартный hr |
| `html` | `co` | Кастомный HTML без типографики Tilda | без класса (raw HTML) |

**Важно: используй `text` (а не `html`) когда возможно.** Tilda применяет нативную типографику только к блокам с правильным `ty`. С `html` текст рендерится без стилей Tilda — мелкий, без правильных отступов.

## Что внутри `te` / `co`

HTML-разметка с Tilda-совместимыми тегами:

- **Параграфы:** `<p>...</p>` — обязательно оборачивай каждый абзац
- **Списки:** `<ul><li>пункт</li></ul>` или `<ol><li>пункт</li></ol>` — внутри `text` блока
- **Inline:** `<strong>`, `<em>`, `<a href="..." target="_blank" rel="nofollow noopener">`, `<code>`, `<br />`
- **Изображения:** `<img src="https://static.tildacdn.com/..." alt="...">` — лучше через CDN Tilda
- **Embeds:** `<iframe src="https://rutube.ru/play/embed/..." ...></iframe>` для видео

**Не используй:**
- `<h1>`, `<h2>`, `<h3>` напрямую внутри `te` — конфликтуют со стилями. Вместо них — отдельный блок `{ty:"heading", le:2}`
- `<blockquote>` напрямую — используй блок `{ty:"quote"}`
- `<hr>` — используй `{ty:"br"}`

## Готовые рецепты

### Рецепт 1: Простой пост (короткая заметка из TG)

```javascript
const blocks = [
  {ty: "text", te: `<p><strong>${title}</strong></p>`},
  {ty: "text", te: `<p>${paragraph1}</p><p>${paragraph2}</p>`},
  {ty: "br", color: "#000000"},
  {ty: "text", te: `<p><em>Оригинал: <a href="https://t.me/${TG_CHANNEL}/${tg_id}" target="_blank" rel="noopener">пост в Telegram</a></em></p>`},
];
```

### Рецепт 2: Пост с подзаголовками и списком

```javascript
const blocks = [
  {ty: "text", te: `<p><strong>${title}</strong></p>`},
  {ty: "text", te: `<p>${intro}</p>`},
  {ty: "heading", te: "<strong>Что умеет режим:</strong>", le: 2},
  {ty: "text", te: "<ul><li>пункт 1</li><li>пункт 2</li><li>пункт 3</li></ul>"},
  {ty: "heading", te: "<strong>Когда использовать:</strong>", le: 2},
  {ty: "text", te: `<p>${conclusion}</p>`},
  {ty: "br", color: "#000000"},
  {ty: "text", te: `<p><em>Оригинал: <a href="https://t.me/${TG_CHANNEL}/${tg_id}" target="_blank">пост в Telegram</a></em></p>`},
];
```

### Рецепт 3: Пост с промптом / цитатой

Когда в TG посте есть длинный промпт (например `**ПРОМПТ**` блок) — рендери его как `quote`:

```javascript
const blocks = [
  {ty: "text", te: `<p><strong>${title}</strong></p>`},
  {ty: "text", te: `<p>${context}</p>`},
  {ty: "heading", te: "<strong>ПРОМПТ</strong>", le: 2},
  {ty: "quote", te: prompt_text.replace(/\n/g, '<br />')},
  {ty: "text", te: `<p>${followup}</p>`},
  {ty: "br", color: "#000000"},
];
```

### Рецепт 4: Длинный лонгрид с Table of Contents

Tilda поддерживает auto-генерацию TOC через `<div class="toc"></div>`. Скрипт автоматически собирает все `heading` блоки в TOC.

```javascript
const blocks = [
  {ty: "text", te: `<p><strong>${title}</strong></p>`},
  {ty: "html", co: `<div class="toc" style="background:#f7f7f7;padding:16px 24px;border-left:3px solid #ffce00;margin:16px 0;border-radius:4px"></div>`},
  {ty: "text", te: `<p>${intro}</p>`},
  {ty: "heading", te: "<strong>Раздел 1</strong>", le: 2},
  // ... больше разделов
  {ty: "br", color: "#000000"},
];
```

TOC появляется только если есть 3+ `heading` блоков.

### Рецепт 5: Embed RuTube/YouTube

```javascript
const embed = `<iframe width="720" height="405" src="https://rutube.ru/play/embed/${rutube_id}/" frameborder="0" allow="autoplay" allowfullscreen></iframe>`;
const blocks = [
  {ty: "text", te: `<p><strong>${title}</strong></p>`},
  {ty: "html", co: `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px"><div style="position:absolute;top:0;left:0;width:100%;height:100%">${embed.replace(/width="\d+"/, 'width="100%"').replace(/height="\d+"/, 'height="100%"')}</div></div>`},
  {ty: "text", te: `<p>${description}</p>`},
];
```

## Inline-стилизация (что хорошо работает в `text` блоках)

### Hashtags как pill-бейджи

```javascript
text.replace(/#(\w+)/g, '<span style="display:inline-block;padding:1px 8px;background:#fff7e0;color:#a87808;border-radius:12px;font-size:0.85em;margin:0 2px">#$1</span>')
```

### Inline code

```html
<code style="background:#f0f0f0;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:0.9em">api_key</code>
```

### Drop-cap (буквица) для лонгридов

В первом параграфе:

```html
<p><span style="float:left;font-size:3.5em;line-height:0.85;padding-right:8px;font-weight:700">П</span>ервая буква отформатирована как буквица...</p>
```

### Цветные коробки для тезисов / предупреждений

В блоке `html`:

```html
<div style="background:linear-gradient(135deg,#fff7ed 0%,#fef3c7 100%);border-radius:12px;border:1px solid #fcd34d;padding:20px 24px;margin:24px 0">
  <p style="margin:0;font-size:13px;opacity:0.7;text-transform:uppercase;letter-spacing:0.5px">Совет</p>
  <p style="margin:8px 0 0;font-size:16px;line-height:1.6">Текст совета...</p>
</div>
```

Цветовые палитры:
- **Совет/info:** `#fff7ed → #fef3c7`, акцент `#fcd34d`
- **Кейс/cyan:** `#ecfeff → #cffafe`, акцент `#67e8f9`
- **Предупреждение:** `#fef2f2 → #fee2e2`, акцент `#f87171`
- **Цитата:** border-left `#14b8a6` (бирюзовый), бг `#f0fdfa`

### Стат-карточки (для дайджестов и обзоров)

```html
<div style="display:flex;gap:12px;margin:24px 0;flex-wrap:wrap">
  <div style="background:#0f2030;color:#fff;padding:18px 22px;border-radius:12px;min-width:140px;flex:1">
    <div style="font-size:26px;font-weight:700">9 000+</div>
    <div style="font-size:12px;opacity:0.7;margin-top:4px">метрика</div>
  </div>
  <!-- ... -->
</div>
```

### CTA-блок со ссылкой на источник

```html
<div style="margin:48px 0 24px;padding:24px 28px;background:linear-gradient(135deg,#fff7ed 0%,#fef3c7 100%);border-radius:12px;border:1px solid #fcd34d">
  <p style="margin:0 0 8px;font-size:13px;opacity:0.7;text-transform:uppercase;letter-spacing:0.5px">Оригинал</p>
  <p style="margin:0 0 12px;font-size:20px;font-weight:700;line-height:1.3">Заголовок статьи в источнике</p>
  <p style="margin:0 0 16px;font-size:14px;opacity:0.8">Издание · Дата · Автор</p>
  <a href="https://..." target="_blank" rel="nofollow noopener" style="display:inline-block;padding:12px 24px;background:#0f2030;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
    Читать полный текст →
  </a>
</div>
```

## Footer-паттерн для блог-постов из TG

Стандартный паттерн в конце поста:

```javascript
{ty: "br", color: "#000000"},
{ty: "text", te: `<p><em>Оригинал: <a href="https://t.me/${TG_CHANNEL}/${tg_id}" target="_blank" rel="noopener">пост в Telegram</a> · <a href="https://t.me/${TG_CHANNEL}" target="_blank" rel="noopener">подписаться на «Готовим ИИшницу»</a></em></p>`}
```

Делает 2 вещи: даёт читателю путь к оригиналу + подписке на канал. Tilda стилизует `<em>` как курсив с пониженной opacity — выглядит как футер.

## Типичные ошибки

| Ошибка | Что происходит | Фикс |
|---|---|---|
| `text` поле как одна большая `html` строка | Текст без типографики, мелкий, кривые отступы | Разбей на блоки `text/heading/quote/br` |
| `<h2>` внутри `te` блока `text` | Конфликт стилей — может рендериться разрозненно | Используй `{ty:"heading", le:2}` |
| Параграфы без `<p>` обёрток | Слитный текст без отступов | Каждый абзац — `<p>...</p>` |
| Markdown `**bold**` напрямую в `te` | Звёздочки видны на странице | Конвертируй в `<strong>` ДО сохранения |
| `target="_blank"` без `rel="noopener"` | Security-warning от линтеров | Всегда добавляй `rel="nofollow noopener"` |
| Inline `<style>` блоки | Tilda фильтрует часть тегов | Используй `style=""` атрибут на элементах |
| Двойное `&amp;amp;` после API round-trip | Literal entity на странице | DecodeAll через textarea (см. troubleshooting) |

## Реальные кейсы

### Массовый upgrade постов блога (разбор)

**Симптом:** 227 постов имели `text` пустой → reading time «1 минута» на всех + descr обрезан на ~250 chars без полного текста.

**Решение:** массовый импорт из своего TG-канала (677 сообщений) с матчингом по нормализованному заголовку (216 матчей с первого прохода) + fuzzy date+score (11 коротких заголовков типа «RIP Sora», «Барабулька))»).

**Конвертер v2** превращает TG markdown в Tilda block JSON:
- `**Title**` в первой строке → отдельный `text` блок с `<p><strong>Title</strong></p>`, далее тело без дублирования
- `**Подзаголовок**` посреди текста → `{ty:"heading", le:2}`
- Списки `- item` или `1. item` → `<ul>` / `<ol>` внутри `text` блока
- После `**ПРОМПТ**` следующий длинный параграф → `quote` блок
- Hashtags `#тег` → стилизованные pill-бейджи
- TOC автоматически если 3+ headings и текст > 2000 chars
- Footer с ссылкой на оригинал в Telegram + подписка

**Результат:** 434/434 постов с rich-форматированием, нативные стили Tilda работают (h2 с `t-redactor__h2`, списки с правильными отступами, цитаты с акцентом).

См. `format_blog_v2.py` (локально — не в скилле, но паттерн универсальный).

## Полезные ссылки

- `feeds-api.md` — Feeds API (`posts_Get`, `posts_Edit`, etc.)
- `troubleshooting.md` — типичные проблемы с posts_Edit, entity encoding
- `cdn-upload.md` — загрузка изображений на Tilda CDN для использования в `<img>`
