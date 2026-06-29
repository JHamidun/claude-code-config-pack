---
name: dev-handoff
description: Собрать handoff-пакет для разработчика. Извлекает токены из готового HTML, генерирует README с компонентами, размерами и состояниями.
when_to_use: Пользователь говорит "хендофф", "передать разработчику", "выгрузить для разраба", "сделай документацию по дизайну".
---

# Dev handoff

Превращает готовый HTML-макет/прототип в передаваемый пакет: токены, инвентарь компонентов, состояния, копирайт.

## Структура пакета

```
handoff/
  README.md              ← обзор: что это, как открыть, ссылки
  tokens.css             ← извлечённые CSS-переменные (или скопированные)
  tokens.json            ← те же токены как JSON для дизайн-инструментов
  components.md          ← инвентарь компонентов с размерами и состояниями
  copy.md                ← все тексты из макета
  screens/               ← PNG каждого ключевого экрана
  source/                ← исходные HTML/CSS/JS
```

## Алгоритм

1. **Прочитай исходный HTML.** Найди все CSS-переменные в `:root` — это твоя база токенов. Сохрани в `tokens.css`.
2. **Сделай из них JSON** для совместимости с Style Dictionary / Tokens Studio:
   ```json
   { "color": { "primary": { "value": "#D97757" } } }
   ```
3. **Инвентарь компонентов.** Пройди по разметке, выпиши уникальные блоки (кнопки, карточки, инпуты). Для каждого:
   - Размеры (width/height, padding, gap).
   - Радиус, тень, бордер.
   - Состояния, которые есть в коде (hover, focus, disabled). Если каких-то нет — отметь как «to be defined».
4. **Копирайт.** Собери все видимые тексты в `copy.md` с привязкой к экрану. Это полезно для перевода и редактуры.
5. **Скриншоты экранов.** Через Playwright (см. `export-png`) сними каждый ключевой стейт.
6. **README.md** в корне handoff: ссылки на оригинал, как запустить локально, на каких разрешениях тестировалось, какие фичи не реализованы.

## Шаблон components.md

```md
# Components

## Button — primary
- **Где:** Header, Onboarding step 2
- **Размеры:** padding 12px 20px, border-radius 8px, min-height 44px
- **Цвета:** bg `var(--color-primary)`, text `#fff`
- **Шрифт:** 14px / 600 / -0.01em
- **Состояния:**
  - default: `var(--color-primary)`
  - hover: `oklch(from var(--color-primary) calc(l - 0.05) c h)`
  - active: `oklch(from var(--color-primary) calc(l - 0.1) c h)`
  - disabled: opacity 0.4, cursor not-allowed
  - focus: outline 2px var(--color-primary), offset 2px

## Card
...
```

## Шаблон tokens.json

```json
{
  "color": {
    "bg": { "value": "#FAF9F6" },
    "fg": { "value": "#111111" },
    "primary": { "value": "#D97757" }
  },
  "font": {
    "display": { "value": "Helvetica Neue, sans-serif" },
    "body": { "value": "Helvetica Neue, sans-serif" }
  },
  "radius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "16px" }
  },
  "spacing": {
    "1": { "value": "4px" }, "2": { "value": "8px" },
    "3": { "value": "12px" }, "4": { "value": "16px" },
    "6": { "value": "24px" }, "8": { "value": "32px" }
  }
}
```

## Что добавить, если попросят углублённый handoff

- **Storybook stub.** Каждый компонент как `.stories.tsx` с props и controls.
- **Spec-листы:** PDF с разметкой расстояний и подписями (легко делать через `export-pdf` поверх макета с overlay-сеткой).
- **Анимации:** список переходов с длительностью и easing. Например: `transition: opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)`.
- **Адаптивность:** breakpoints + что меняется на каждом.

## Чего не делать

- Не выгружай как handoff макет, в котором ещё всё в `inline-style` и магических числах. Сначала вынеси в переменные.
- Не пиши «hover: чуть темнее» — давай конкретное значение или формулу через `oklch(from ...)`.
- Не плоди `tokens.unused.json`. Включай только то, что реально используется в макете.
