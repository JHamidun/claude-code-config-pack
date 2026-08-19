---
name: design-tokens-w3c
description: "Экспорт дизайн-токенов в W3C DTCG tokens.json: Style Dictionary, Token Studio. Триггеры: «экспорт токенов», «отдай токены команде»."
---

# W3C Design Tokens

DTCG (Design Tokens Community Group) — стандарт `tokens.json`, который читают:
- Style Dictionary
- Token Studio (Figma plugin)
- Tokens Studio CLI
- Specify
- Native (Swift / Kotlin) генераторы

## Формат

Каждый токен — объект с `$value` и `$type`:

```json
{
  "color": {
    "primary": {
      "500": { "$value": "#D97757", "$type": "color" },
      "600": { "$value": "#C56640", "$type": "color" }
    }
  },
  "spacing": {
    "sm": { "$value": "8px", "$type": "dimension" },
    "md": { "$value": "16px", "$type": "dimension" }
  },
  "typography": {
    "heading": {
      "$value": {
        "fontFamily": "Fraunces",
        "fontSize": "48px",
        "fontWeight": 600,
        "lineHeight": 1.1
      },
      "$type": "typography"
    }
  },
  "shadow": {
    "card": {
      "$value": {
        "color": "rgba(0,0,0,0.08)",
        "offsetX": "0px", "offsetY": "2px",
        "blur": "8px", "spread": "0px"
      },
      "$type": "shadow"
    }
  }
}
```

## Конвертер из CSS-переменных

`templates/css-to-dtcg.mjs`:

```js
import fs from 'node:fs/promises';
import postcss from 'postcss';

const file = process.argv[2] || 'tokens.css';
const css = await fs.readFile(file, 'utf8');
const root = postcss.parse(css);

const tokens = {};

root.walkRules(':root', rule => {
  rule.walkDecls(decl => {
    if (!decl.prop.startsWith('--')) return;
    const name = decl.prop.slice(2);
    const value = decl.value.trim();
    const path = name.split('-');     // primary-500 → ['primary', '500']

    let cur = tokens;
    for (let i = 0; i < path.length - 1; i++) {
      cur[path[i]] = cur[path[i]] || {};
      cur = cur[path[i]];
    }

    let type = 'other';
    if (/^#|rgb|hsl|oklch/.test(value)) type = 'color';
    else if (/^\d+(\.\d+)?(px|rem|em|%)$/.test(value)) type = 'dimension';
    else if (/^\d+(\.\d+)?$/.test(value)) type = 'number';
    else if (/^['"]/.test(value) || /^[A-Z][a-zA-Z\s,]+$/.test(value)) type = 'fontFamily';

    cur[path.at(-1)] = { '$value': value, '$type': type };
  });
});

await fs.writeFile(file.replace(/\.css$/, '.tokens.json'), JSON.stringify(tokens, null, 2));
console.log('✓', file.replace(/\.css$/, '.tokens.json'));
```

```bash
npm i postcss
node css-to-dtcg.mjs tokens.css
# → tokens.tokens.json
```

## Style Dictionary integration

Для команды на Style Dictionary:

```bash
npm i -D style-dictionary
```

`config.json`:
```json
{
  "source": ["tokens.tokens.json"],
  "platforms": {
    "css":     { "transformGroup": "css",     "files": [{ "destination": "tokens.css",  "format": "css/variables" }] },
    "scss":    { "transformGroup": "scss",    "files": [{ "destination": "_tokens.scss", "format": "scss/variables" }] },
    "js":      { "transformGroup": "js",      "files": [{ "destination": "tokens.js",   "format": "javascript/es6" }] },
    "android": { "transformGroup": "android", "files": [{ "destination": "colors.xml",  "format": "android/colors" }] },
    "ios":     { "transformGroup": "ios",     "files": [{ "destination": "Colors.swift","format": "ios-swift/class.swift" }] }
  }
}
```

```bash
npx style-dictionary build
# → tokens.css + tokens.js + colors.xml + Colors.swift
```

Один источник, все платформы.

## Связь токенов (aliases)

DTCG поддерживает ссылки на другие токены:

```json
{
  "color": {
    "brand": { "$value": "#D97757", "$type": "color" },
    "primary": { "$value": "{color.brand}", "$type": "color" }
  },
  "button": {
    "background": { "$value": "{color.primary}", "$type": "color" }
  }
}
```

Style Dictionary разрезолвит при сборке.

## Темы (light/dark)

В DTCG сейчас два подхода:
- **Token Sets** в Token Studio — два набора, `light` и `dark`, переключаются на этапе сборки.
- **Mode-aware** через `$mode` (новая фича DTCG, ещё не везде):

```json
{
  "color": {
    "background": {
      "$value": { "light": "#fff", "dark": "#0d0d0d" },
      "$type": "color"
    }
  }
}
```

Для совместимости — два файла:
```
tokens.light.json
tokens.dark.json
```

## После экспорта

- Передай файл разрабам — Style Dictionary build → нативные платформы.
- Импортируй в Figma через Token Studio (FOSS plugin).
- Положи в monorepo как `@company/tokens`.

## Антипаттерны

- ❌ Засовывать всё в плоский namespace `--color-primary-500`. Иерархия в DTCG — это ценность.
- ❌ Хардкодить hex'ы в нескольких местах. Только через aliases.
- ❌ Лишние токены. Только то, что используется.
