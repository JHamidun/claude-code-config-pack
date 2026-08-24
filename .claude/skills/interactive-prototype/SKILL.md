---
name: interactive-prototype
description: "Кликабельный React-прототип в одном HTML (inline JSX, Babel): state, переходы, валидация форм. Триггеры: «интерактивный прототип», «кликабельный мокап»."
---

# Interactive prototype

Один HTML-файл с inline JSX через Babel-standalone. React-приложение, имитирующее настоящее.

## Когда подключать

- Многошаговый флоу (онбординг, чекаут, регистрация).
- Состояние UI: формы, табы, аккордеоны, модалки.
- Переходы между экранами с анимацией.
- Имитация работы реального приложения, а не статический мокап.

Если задача — статичный экран или один лендинг, прототип не нужен. Делай обычный HTML.

## Технический каркас

Используй точно эти версии React + Babel — другие могут отвалиться:

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js"
        crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"
        crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js"
        crossorigin="anonymous"></script>
```

Точку входа держи в одном `<script type="text/babel">` в конце body, а компоненты раскидай по отдельным файлам и подключай тоже как `text/babel`. Каждый Babel-скрипт получает собственный scope при транспиляции, поэтому компоненты, которые используются из другого файла, в конце экспортируй на window:

```jsx
Object.assign(window, { Button, Card, Input });
```

## Правила состояния

- **Не выдумывай данные.** Если нужны имена, товары, числа — используй реалистичные заглушки, согласованные с темой приложения. Не «Lorem ipsum».
- **Состояние локальное по умолчанию.** Поднимай его выше только когда два компонента действительно разделяют данные.
- **Реальные переходы.** Кнопка «Далее» должна правда переключать экран, а не быть украшением.
- **Валидация форм.** Хотя бы базовая (required, длина, формат email) с человеческим текстом ошибок.
- **Состояния всех состояний.** Hover, focus, active, disabled, loading, empty, error. Не только default.

## Анти-паттерны

- Глобальный объект `const styles = { ... }`. Если он определён в двух babel-скриптах — коллизия. Имя должно быть уникальным: `cardStyles`, `formStyles`. Или используй inline-стили / Tailwind / CSS-модули.
- `scrollIntoView` — иногда ломает iframe-хосты. Используй `element.scrollTo()`.
- Анимации через JS-таймауты вместо CSS-transitions / `requestAnimationFrame`.
- Один `useEffect` на всё. Разбивай по отдельным эффектам с понятными зависимостями.

## Размер и контейнер

- Если прототип мобильный — оборачивай в рамку устройства (см. `device-frames`).
- Если десктопный — оборачивай в окно браузера или macOS (тоже `device-frames`).
- Свободный лендинг — full-bleed с разумными max-width.

## Persistence

Если в прототипе важно сохранять состояние между перезагрузками (для итеративного дизайна), пиши его в `localStorage` при изменении и читай при старте:

```jsx
const [step, setStep] = useState(() => {
  const saved = localStorage.getItem('proto.step');
  return saved ? parseInt(saved, 10) : 0;
});

useEffect(() => {
  localStorage.setItem('proto.step', String(step));
}, [step]);
```

Особенно полезно для видео-таймера, текущего экрана флоу, заполненных полей формы.

## Использование Claude из прототипа (опционально)

Если прототипу нужна «магия» — суммаризация, генерация ответа, классификация ввода — можешь дёрнуть LLM напрямую через Anthropic SDK или fetch на твой бэк. В Claude Code это работает иначе, чем в этой среде: ключ ставит сам пользователь.

Простейший вариант — спросить пользователя, готов ли он вставить ключ. Дальше:

```html
<script type="module">
  import Anthropic from "https://esm.sh/@anthropic-ai/sdk";
  const client = new Anthropic({
    apiKey: localStorage.getItem('anthropic_key'),
    dangerouslyAllowBrowser: true,
  });
  // ... client.messages.create({...})
</script>
```

Если `apiKey` нет — оставляй прототип статическим, не блокируй UI.

## Чек-лист перед сдачей

- [ ] Все основные кнопки кликабельны и ведут куда обещают.
- [ ] Формы валидируются.
- [ ] Есть hover/focus/active.
- [ ] Loading и error состояния хотя бы заглушены.
- [ ] Никаких console-ошибок (открой DevTools).
- [ ] Прототип влезает в типичный viewport без горизонтального скролла.
- [ ] Если флоу — пройден от начала до конца.

## Подробности

Расширенный материал вынесен в `references/legacy-interactive-prototype.md` — открывай, когда короткого канона выше не хватает. Секции там: Каркас, Файловая структура, Правила JSX в Babel-standalone, Состояние между экранами, Сценарии типового прототипа, Стек со связанными скиллами, Антипаттерны, Когда НЕ делать interactive-prototype.
