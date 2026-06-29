---
name: interactive-prototype
description: Кликабельный прототип на React + JSX через Babel-standalone в HTML. Сценарии переходов между экранами, навигация, состояния. Один файл — один прототип, никакого webpack. Стек с device-frames для рамки устройства, mobile-overlays для UI-слоёв, tweaks-panel для крутилок.
when_to_use: Юзер просит «прототип», «кликабельный», «как настоящее приложение», «можно покликать», «потыкать UX», «flow между экранами». Лучше slides когда нужны переходы и состояния.
---

# Interactive prototype

React 18 + Babel standalone через CDN unpkg. JSX-секции через `<script type="text/babel" src=...>`. Никакой сборки.

## Каркас

```html
<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title><Project></title>
<link rel="stylesheet" href="styles/tokens.css">
<style>html,body{margin:0;background:#f0eee9;font-family:var(--font-body)}</style>
</head><body>
<div id="root"></div>

<!-- React + Babel через CDN -->
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin></script>

<!-- Атомы и секции -->
<script type="text/babel" src="components/icons.jsx"></script>
<script type="text/babel" src="components/shared.jsx"></script>
<script type="text/babel" src="screens/welcome.jsx"></script>
<script type="text/babel" src="screens/main.jsx"></script>

<!-- Главный entry -->
<script type="text/babel" data-presets="env,react">
  const { useState } = React;
  const { Welcome, Main } = window;

  function App() {
    const [screen, setScreen] = useState('welcome');
    const screens = {
      welcome: <Welcome onNext={() => setScreen('main')} />,
      main:    <Main onBack={() => setScreen('welcome')} />,
    };
    return screens[screen] || screens.welcome;
  }

  ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body></html>
```

## Файловая структура

```
<project>/
├── <Project>.html
├── styles/tokens.css
├── components/
│   ├── icons.jsx          # SVG-icons в JSX
│   ├── shared.jsx         # Button, Input, Card, Badge
│   └── chrome.jsx         # Topbar, Sidebar если есть
├── screens/
│   ├── welcome.jsx        # каждый экран — отдельный файл
│   ├── main.jsx
│   └── settings.jsx
└── uploads/               # картинки от юзера
```

## Правила JSX в Babel-standalone

- **Каждый файл-секция вешает компонент на `window`** в конце:
  ```jsx
  function Welcome({ onNext }) { return <div>...</div>; }
  window.Welcome = Welcome;
  ```
- **Не используй `import` / `export`** — Babel standalone их не выполняет в этой конфигурации
- **`useState` берёшь как `const { useState } = React`** в каждом файле где нужен
- **JSX-кавычки нормальные** — `"prop"` или `'prop'`, не curly

## Состояние между экранами

Простой паттерн для prototype:

```jsx
function App() {
  const [screen, setScreen] = useState('welcome');
  const [data, setData] = useState({ name: '', email: '' });

  // Передаешь setData в формы как onChange
  return screens[screen];
}
```

Если состояние сложное — заменяй на `useReducer` в App, передавай `dispatch` вниз.

## Сценарии типового прототипа

| Тип | Экраны (минимум) |
|---|---|
| Onboarding | welcome → personal-info → permissions → done |
| Authentication | login → 2fa → forgot-password → reset |
| E-commerce | catalog → product → cart → checkout → confirmation |
| Dashboard | empty-state → loaded → drill-down → settings |
| Form-flow | step-1 → step-2 → step-3 → review → submitted |

## Стек со связанными скиллами

- `device-frames` — обернуть прототип в iPhone / Android / Browser frame
- `mobile-overlays` — клавиатура, sheet, тосты, action sheet поверх экрана
- `tweaks-panel` — sidebar с крутилками (цвет primary, размер шрифта, состояние demo)
- `microinteractions` — hover, skeleton, scroll-reveal внутри экранов
- `claude-in-html` — встроить LLM в прототип (чат-бот / AI-консультант)
- `states-checklist` — empty / loading / error / disabled на каждом экране
- `forms-a11y` — если в прототипе есть формы

## Антипаттерны

- Один монолитный файл `App.jsx` 800 строк → невозможно править секции
- `import` / `export` в Babel standalone → не работает, путает
- Реальные API вызовы → прототип должен работать офлайн с mock-data
- Lorem ipsum → плохо считывается реальным юзером, лучше realistic dummy («John Doe», «456 ₽»)
- Анимации сложнее opacity/transform → JS-производительность падает на mobile
- 10+ экранов в одном прототипе → сложно тестить, лучше разбить на несколько проектов

## Когда НЕ делать interactive-prototype

- Нужно показать только статичный flow → `slides` с скриншотами проще
- Нужен один экран → просто HTML без React
- Юзер хочет реальный код → не прототип, иди в `feature-dev` agent
