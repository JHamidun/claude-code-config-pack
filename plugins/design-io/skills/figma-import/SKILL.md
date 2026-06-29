---
name: figma-import
description: Figma → токены и фреймы. Извлекает дизайн-tokens (colors/typography/spacing), скачивает ключевые ноды как PNG-референсы для interactive-prototype или slides. Работает через Figma REST API.
when_to_use: Юзер указал Figma file ID / ссылку, хочет «возьми из Figma» / «начни с этого файла» / «скопируй стиль из node X». Перед design-system-create когда есть готовый бренд.
---

# Figma import

Other page-builders/Sketch не нужны — все берём из Figma через REST API. Что вытаскиваем: tokens (colors / fonts / spacing), скриншоты frames как референсы, отдельные components.

## Auth

```bash
# Personal access token: figma.com/settings → Personal access tokens
export FIGMA_TOKEN=figd_...
```

Скилл `figma-api` (если установлен) уже имеет credentials и обёртки.

## File ID из URL

```
https://www.figma.com/design/YOUR_FIGMA_FILE_ID/YourName-Brandbook?node-id=340-99
                              ^^^^^^^^^^^^^^^^^^^^^^             ^^^^^^^^
                              file_id                            node_id (340:99)
```

`node_id` в URL через дефис, в API через двоеточие.

## Operation 1: вытащить styles (tokens)

```bash
curl "https://api.figma.com/v1/files/<FILE_ID>/styles" \
  -H "X-Figma-Token: $FIGMA_TOKEN"
```

Возвращает все «published styles» — colors, text styles, effects (shadows). Для каждого: `node_id`, `name`, `style_type`.

Затем для каждого style — fetch его данные:
```bash
curl "https://api.figma.com/v1/files/<FILE_ID>/nodes?ids=<NODE_IDS>" \
  -H "X-Figma-Token: $FIGMA_TOKEN"
```

В response — fills (RGB цвета), typeStyle (font, size, weight), effects (drop-shadow).

## Operation 2: скачать ключевые frames как PNG

```bash
# Получить URL для рендера
curl "https://api.figma.com/v1/images/<FILE_ID>?ids=340:99,230:16&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_TOKEN"
```

Возвращает временные S3-URL'ы (~15 минут validity). Скачиваешь curl'ом и кладёшь в `uploads/`:

```bash
curl -o uploads/figma_node_340_99.png "<temp-url>"
```

## Operation 3: вытащить components

Components = переиспользуемые элементы (Button, Card, Avatar). Получить:

```bash
curl "https://api.figma.com/v1/files/<FILE_ID>/components" \
  -H "X-Figma-Token: $FIGMA_TOKEN"
```

Каждый component — `node_id` + `name`. Дальше скачиваешь как frame (operation 2) или fetch'ишь его JSON структуру (operation 1).

## Преобразование Figma styles → CSS tokens

```python
# Псевдокод трансформера
def figma_styles_to_css_tokens(styles_response):
  tokens = {}

  for style in styles_response['styles']:
    if style['style_type'] == 'FILL':
      # «primary/blue» → --color-primary-blue
      slug = style['name'].lower().replace('/', '-').replace(' ', '-')
      rgba = style['fills'][0]['color']  # {r,g,b,a} 0-1
      hex_code = rgb_to_hex(rgba)
      tokens[f'--color-{slug}'] = hex_code

    elif style['style_type'] == 'TEXT':
      # «heading/h1» → --text-heading-h1-* (font, size, weight, lh)
      slug = style['name'].lower().replace('/', '-').replace(' ', '-')
      ts = style['typeStyle']
      tokens[f'--text-{slug}-family'] = ts['fontFamily']
      tokens[f'--text-{slug}-size'] = f"{ts['fontSize']}px"
      tokens[f'--text-{slug}-weight'] = str(ts['fontWeight'])
      tokens[f'--text-{slug}-lh'] = f"{ts['lineHeightPx']}px"
  return tokens
```

## Output: tokens.css

```css
/* Imported from Figma file YOUR_FIGMA_FILE_ID, (see git history) */
:root {
  --color-primary: #YOUR_PRIMARY;
  --color-deep:    #YOUR_INK;
  --color-cyan:    #YOUR_ACCENT;
  --color-cream:   #YOUR_CREAM;

  --font-head: "Inter Tight", sans-serif;
  --font-body: "Manrope", sans-serif;

  /* H1 from Figma: heading/h1 */
  --t-h1-size: 40px;
  --t-h1-weight: 700;
  --t-h1-lh: 44px;
}
```

Дальше — `design-system-create` или `color-system-builder` дополняют этот скелет (9-step scales, dark mode, etc).

## Использование PNG-референсов

После скачивания frame как PNG:
- Кладёшь в `uploads/figma-<node>-<name>.png`
- В promptе для interactive-prototype или slides: «как на referenece uploads/figma-340-99-final-design.png, но в нашем стеке»
- Или загружаешь в `moodboard` как один из refs

## Ограничения

- **Фигма frames с переменными режимами (variables modes)** — API возвращает текущий mode, не все
- **Auto-layout** не сохраняется в `tokens.css` — только конкретные размеры
- **Эффекты** (blur, layer effects) рендерятся в PNG, в CSS не переносятся автоматически
- **Animation/Smart-animate** не доступны через API

## Когда НЕ использовать

- В Figma только wireframes без фиксированных стилей → лучше `wireframe` с нуля
- Один экран целиком как рефренс → проще скачать вручную и положить в `uploads/`
- Компоненты с complex variants → лучше figma-import только tokens, components кодить с нуля

## Антипаттерны

- Скачать ВСЕ frames в Figma file → 200+ PNG на 200MB
- Брать tokens без проверки naming → дубликаты типа `--color-primary` и `--color-primary-blue` для одного цвета
- Игнорировать figma-styles, импортить только PNG → теряешь типизацию
- Не сохранять file_id + дату импорта в комментарии tokens.css → следующая итерация не понимает что откуда
- Делать figma-import каждую сессию → дёргаешь API лимиты, лучше один раз и закоммитить
