---
name: react-pinning
description: Закреплённые версии React/ReactDOM/Babel с integrity-хешами. Готовый блок script-тегов для interactive-prototype.
when_to_use: Любой HTML-артефакт с inline JSX. Подключай ровно эти теги, не апгрейдь без причины.
---

# React pinning

Babel + JSX + React в браузере без bundler'а — хрупкая связка. Минор-апгрейд React'а ломает Babel transform; апгрейд Babel ломает React 18 deprecations. Только закреплённые версии с проверенными integrity-хешами.

## Готовый блок

Скопируй в `<head>`:

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js"
  integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L"
  crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"
  integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm"
  crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js"
  integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y"
  crossorigin="anonymous"></script>
```

## Правила

### 1. Не используй `react@18` без minor
- ❌ `https://unpkg.com/react@18/umd/...` — unpkg отдаст последний `18.x`, может оказаться `18.4` с breaking changes.
- ✅ `react@18.3.1` — точная версия.

### 2. Не убирай integrity
Без integrity unpkg может отдать что угодно при компрометации CDN. С хешем — браузер откажется грузить.

### 3. Не миксуй development и production-сборки
В development-сборках есть warnings и hot-reload поддержка. В production — оптимизировано. **Для прототипов используй development.dev.js** — лучше ловить ошибки.

### 4. Babel — `@babel/standalone`, не отдельные плагины
Inline JSX работает только через standalone. Не пытайся подключить `@babel/preset-react` отдельно — не загрузится.

### 5. Подключение JSX-файлов
```html
<script type="text/babel" src="components.jsx"></script>
<script type="text/babel" src="app.jsx"></script>
```

Не `type="module"` — Babel не транспилит модули.

### 6. Каждый `<script type="text/babel">` — свой scope
Babel оборачивает в IIFE. Чтобы делиться компонентами между файлами:

```jsx
// в конце components.jsx
Object.assign(window, { Button, Card, Modal });
```

И никаких `const styles = {...}` — обязательно `const cardStyles = {...}` или inline-styles. Конфликт имён в global scope тихо ломает.

## Альтернативы (когда не подходит)

### Vite/Next, если есть npm
Когда у пользователя есть Node + желание собирать — это надёжнее. Но требует setup.

### esm.sh
```html
<script type="module">
  import React from 'https://esm.sh/react@18.3.1';
</script>
```
Работает в чистом ES-модуле, без Babel. Но JSX тогда не транспилировать — пиши на `React.createElement`.

## Что не делать

- ❌ `https://cdn.jsdelivr.net/...` без integrity — те же риски.
- ❌ `latest` в URL — невоспроизводимо.
- ❌ Скопировать react.development.js локально и забыть. Если у пользователя нет npm — он не починит при обновлении.
- ❌ `import` в `<script type="text/babel">` — не работает. Только `Object.assign(window, ...)` или `<script>` подряд.

## Чек

После подключения проверь:
```js
console.log(React.version);     // 18.3.1
console.log(ReactDOM.version);  // 18.3.1
console.log(Babel.version);     // 7.29.0
```

Если хоть одна — `undefined`, integrity не прошёл или CDN недоступен.
