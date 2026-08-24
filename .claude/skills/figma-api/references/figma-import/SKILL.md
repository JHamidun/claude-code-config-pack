---
name: figma-import
description: Подтянуть Figma-файл как референс. Достаёт структуру фреймов, цвета, типографику, экспортирует превью в PNG. Не пытается "сконвертировать" Figma в код 1:1 — берёт визуал и токены.
when_to_use: Пользователь дал ссылку на Figma-файл, фрейм или Figma Community. Хочет "сделать как тут", "перевести этот макет", "взять стили оттуда".
---

# Figma import

Figma даёт публичный REST API. Через него можно вытащить структуру файла, картинки фреймов и токены. SDK не нужен — обычный fetch.

## Что нужно от пользователя

1. **Personal Access Token.** Figma → Settings → Personal access tokens → Generate. Скоуп `file_content:read`. Положить в переменную `FIGMA_ACCESS_TOKEN` (скрипты понимают и старое имя `FIGMA_TOKEN`) либо в `~/.figma-token`. Бесплатного аккаунта Figma достаточно.
2. **Ссылка на файл или фрейм.**
   - Файл: `https://www.figma.com/design/<FILE_KEY>/...`
   - Фрейм: `...?node-id=123-456` (запомни node-id, понадобится).

## Парсинг ссылки

```js
function parseFigmaUrl(url) {
  const u = new URL(url);
  const m = u.pathname.match(/\/(file|design|proto)\/([A-Za-z0-9]+)/);
  if (!m) throw new Error('Не похоже на ссылку Figma');
  const fileKey = m[2];
  const nodeId = u.searchParams.get('node-id')?.replace('-', ':');
  return { fileKey, nodeId };
}
```

Имей в виду: в URL node-id записан как `123-456`, а в API его надо передавать как `123:456`.

## Что вытаскивать

### 1. Структуру файла (имена страниц, фреймов, компонентов)

```bash
curl -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY?depth=3"
```

`depth=3` — обычно достаточно, чтобы увидеть страницы и их фреймы без раздувания JSON. Дальше углубляйся точечно через `?ids=...`.

### 2. Превью фреймов как PNG

```bash
curl -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_IDS&format=png&scale=2"
```

В ответе — словарь `{ nodeId: signedUrl }`. Скачай каждый URL отдельным `curl -o` в `figma-refs/<frame-name>.png`. Эти картинки — твои референсы для дизайна.

### 3. Стили (цвета, тайпы, эффекты, сетки)

```bash
curl -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/styles"
```

Возвращает список стилей. Чтобы получить значения — запроси `nodes` для node_id каждого стиля:

```bash
curl -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/nodes?ids=$STYLE_NODE_IDS"
```

В узле для FILL смотри `fills[0].color` (RGBA в 0..1, не 0..255), для TEXT — `style.fontFamily`, `fontSize`, `fontWeight`, `lineHeightPx`, `letterSpacing`.

### 4. Variables (новые design tokens)

```bash
curl -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/variables/local"
```

⚠️ Variables API доступен только на enterprise-планах (по состоянию на 2025). Если 403 — fallback на Styles.

## Скрипт

В `templates/figma-pull.mjs` лежит готовый Node-скрипт. Запуск:

```bash
node figma-pull.mjs "https://www.figma.com/design/abc123/My-File?node-id=10-20"
```

Скрипт создаёт папку `figma-refs/` с:
- `frames/` — PNG превью всех фреймов запрошенной страницы
- `tokens.json` — извлечённые цвета и текстовые стили
- `tokens.css` — те же токены как CSS-переменные
- `structure.md` — markdown-карта файла (страницы → фреймы)

## Как использовать после импорта

1. Открой `structure.md` чтобы понять, что в файле.
2. Посмотри PNG в `frames/` — это твой визуальный референс.
3. Подключи `tokens.css` к своему HTML — получишь точные цвета и шрифты.
4. **Не пытайся** воспроизвести Figma в HTML пиксель-в-пиксель. Возьми идею, токены и пропорции, дальше делай нативный HTML.

## Ограничения

- Figma → HTML 1:1 невозможен. Auto-layout, эффекты, blend modes транслируются плохо. Используй визуал как референс, а структуру строй с нуля.
- Иконки и иллюстрации лучше экспортировать как SVG отдельно — кликни правой по узлу в Figma → Copy as SVG. Положи в проект.
- Если в файле >500 фреймов, скрипт долгий. Передай конкретный `node-id`, чтобы пулить только нужный фрейм и его детей.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-figma-import.md`. Секции там: Auth, File ID из URL, Operation 1: вытащить styles (tokens), Operation 2: скачать ключевые frames как PNG, Operation 3: вытащить components, Преобразование Figma styles → CSS tokens, Output: tokens.css, Использование PNG-референсов, Ограничения, Когда НЕ использовать, Антипаттерны.
