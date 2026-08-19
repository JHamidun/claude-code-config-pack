---
name: fonts-bundle
description: "Готовые блоки <link> для пар шрифтов Google Fonts (веса, subset) + system-стек. Триггеры: «подключи шрифты», «пара шрифтов»."
---

# Fonts bundle

Готовые сниппеты. Скопируй в `<head>` нужный блок. Все — с `display=swap`, минимальными весами и Cyrillic-subset (где применимо).

## System stack (без подключений)

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  --font-serif: ui-serif, Georgia, Cambria, 'Times New Roman', serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
body { font-family: var(--font-sans); }
```

Самый быстрый — нет загрузок. Подходит когда не критичен бренд.

## Inter (sans, нейтральный)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
```
```css
body { font-family: 'Inter', system-ui, sans-serif; }
```

⚠ В `frontend-design`-памятке Inter помечен как «overused». Используй только когда нет вариантов.

## Fraunces + Inter (serif display + sans body)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500&display=swap">
```
```css
h1, h2, h3 { font-family: 'Fraunces', Georgia, serif; }
body { font-family: 'Inter', system-ui, sans-serif; }
```

Editorial-направление. Хорошо для лендингов, питчей.

## Bricolage Grotesque + Inter

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Inter:wght@400;500&display=swap">
```

Для современных продуктов с мягкой типографикой.

## Space Grotesk + Space Mono

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Space+Mono:wght@400;700&display=swap">
```

Для tech / dev tools / brutalist.

## DM Serif Display + DM Sans

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap">
```

Бесплатная alternativa Tiempos. Высокий контраст, dramatic.

## JetBrains Mono (только моно)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap">
```

Для кода, dev tools.

## Outfit (один шрифт на всё)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap">
```

Геометрический sans, если нужен один на display + body.

## Кириллица

Не все Google Fonts поддерживают Cyrillic. Проверенные с кириллицей:
- Inter ✅
- DM Sans / DM Serif Display ✅
- Bricolage Grotesque ✅
- Outfit ❌
- Fraunces ❌
- Space Grotesk / Space Mono ✅

Для не-поддерживаемых добавь fallback:
```css
font-family: 'Outfit', 'Inter', system-ui, sans-serif;
```

## Правила

### 1. Не больше 4 файлов
Каждый `<link>` к Google Fonts — отдельный запрос. Если просишь 8 весов — это 8 запросов.

### 2. `display=swap`
Без него на медленной сети текст невидим до загрузки шрифта. Со swap — рисуется фолбеком, потом подменяется.

### 3. `preconnect` к gstatic
Снимает 100-300мс с первой загрузки.

### 4. `font-weight` ровно те, что нужны
Для тела + одного хедера обычно хватает 400 + 600. Не качай 100, 200, 300, 400, 500, 600, 700, 800, 900 «на всякий случай».

### 5. Для лендинга — preload основного шрифта
```html
<link rel="preload" as="font" type="font/woff2"
  href="https://fonts.gstatic.com/s/inter/v13/UcCo3FwrK3iLTcvneQg7Ca725JhhKnNqk4j1ebLhAm8SrXTcce8.woff2"
  crossorigin>
```
Ускоряет LCP. Имя файла нужно вытащить из Network-таба.

### 6. Self-hosting (production)
Для финальных проектов — скачай `.woff2` с `gwfh.mranftl.com`, положи в `/fonts/`, задай `@font-face`. Снимает зависимость от Google.

```css
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
  src: url('/fonts/inter.woff2') format('woff2');
}
```

## Лицензии

- **Все Google Fonts** — Open Font License (OFL) или Apache. Свободны.
- **Bunny Fonts** (`fonts.bunny.net`) — drop-in замена Google без трекинга.
- **Adobe Fonts / Typekit** — нужна подписка, не для свободной раздачи.
- **Commercial foundry fonts** (Söhne, GT America, Tiempos) — лицензия за $$. Не подключай если нет у клиента.

## Антипаттерны

- ❌ `<link>` без `display=swap` — FOIT (flash of invisible text).
- ❌ Тащить Inter для одного места, где хватило бы system-ui.
- ❌ Пять разных шрифтов на странице.
- ❌ Подключить Google Fonts и параллельно `@font-face` для того же шрифта.
