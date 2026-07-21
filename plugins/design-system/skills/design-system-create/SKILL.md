---
name: design-system-create
description: "Собрать дизайн-систему с нуля: токены, типографика, компоненты, гайдлайны."
when_to_use: Пользователь просит "сделай дизайн-систему", "UI-кит", "общие токены для проекта".
---

# Design system create

Минимально жизнеспособная дизайн-система — это:

1. **Tokens** (цвета, типографика, отступы, радиусы, тени).
2. **Components** (кнопка, инпут, карточка, бейдж — ядро).
3. **Принципы** (1 страница: что считается «правильным»).
4. **Примеры** — компоненты в работе на 2-3 экранах.

Не делай сразу 50 компонентов. Начни с ядра, расширяй по мере появления реальных нужд.

## Структура файлов

```
design-system/
  README.md
  tokens.css
  tokens.json
  type.html         ← страница со всеми текстовыми стилями
  colors.html       ← страница с палитрой
  components/
    button.html
    input.html
    card.html
    badge.html
  examples/
    landing.html
    settings.html
```

## tokens.css — обязательный минимум

```css
:root {
  /* Цвета */
  --color-bg:        #FAF9F6;
  --color-fg:        #111111;
  --color-muted:     #6B6B6B;
  --color-rule:      rgba(0, 0, 0, 0.08);
  --color-primary:   #D97757;
  --color-success:   #2E7D5F;
  --color-warning:   #C58B14;
  --color-danger:    #C24E3A;

  /* Типографика */
  --font-display: "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-body:    "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-mono:    ui-monospace, SFMono-Regular, Menlo, monospace;

  /* Шкала размеров */
  --text-xs:   12px;
  --text-sm:   14px;
  --text-base: 16px;
  --text-lg:   18px;
  --text-xl:   24px;
  --text-2xl:  32px;
  --text-3xl:  48px;
  --text-4xl:  72px;

  /* Spacing — кратно 4 */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-6:  24px;
  --space-8:  32px;
  --space-12: 48px;
  --space-20: 80px;

  /* Радиусы */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-pill: 999px;

  /* Тени */
  --shadow-sm: 0 1px 2px rgba(0,0,0,.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --shadow-lg: 0 30px 80px rgba(0,0,0,.12);

  /* Время и easing */
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 120ms;
  --duration-base: 200ms;
}
```

## Принципы (template)

В `README.md` системы укажи:

- **Цвета.** Когда какой использовать. «Primary только для главного CTA на странице. Не больше двух primary-кнопок в один экран».
- **Расстояния.** Никаких magic numbers. Если 17px — значит, ты ошибся; нужно 16 или 24.
- **Типографика.** Какой шрифт где. Не больше 3 размеров на экран.
- **Бордеры и тени.** Когда уместны, когда нет.
- **Состояния.** Что должно быть у любого интерактивного элемента.

## Минимальные компоненты ядра

### Button

3 варианта × 3 размера = 9 кнопок:
- variants: primary, secondary, ghost
- sizes: sm (32px), md (40px), lg (48px)
- states: default, hover, active, focus-visible, disabled, loading

### Input
- text, password, email, number, search, textarea
- states: default, focus, filled, error, disabled
- с label, helper, error

### Card
- minimum padding, border, optional shadow
- header / body / footer slots

### Badge
- info, success, warning, danger, neutral
- sizes: sm, md

Дальше — что реально нужно.

## Что НЕ нужно делать на старте

- ❌ Колорпикер с 12 оттенками каждого цвета. Достаточно 3-4.
- ❌ 20 размеров шрифта. Достаточно 8.
- ❌ Сложные компоненты (data-grid, file-uploader) до того, как нужны.
- ❌ Несколько тем (light/dark) до базовой системы.

## Финальная проверка

Открой `examples/landing.html` или `settings.html`. Если для построения нужно было что-то «доделать руками» — это пробел в системе. Закрой пробел токеном или компонентом, не inline-стилем.
