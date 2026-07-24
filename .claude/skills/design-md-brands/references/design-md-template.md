# DESIGN.md — авторский шаблон (схема Google Stitch, 9 блоков)

Скелет для собственного `DESIGN.md`, когда бренда нет в банке awesome-design-md.
Заполняй из `brand-extractor` (живой сайт) или `design-system-create` (с нуля).
Держи plain-markdown: файл читают и человек, и ИИ-агент. Клади в корень проекта.

```markdown
# <Brand> — DESIGN.md

## Overview
Одним абзацем: визуальная тема, атмосфера, философия. Кому и о чём говорит бренд,
какое ощущение должен вызывать UI (напр. «строгий, инженерный, много воздуха»).

## Colors
Семантические РОЛИ + токен + hex + где применять (не просто список hex).
### Brand & Accent
- **<Name>** (`{colors.primary}` — `#RRGGBB`): основной CTA / акцент. Где: кнопка, ссылка, ...
### Surface
- **<Name>** (`{colors.bg}` — `#RRGGBB`): фон страницы / карточек / оверлеев.
### Text
- **<Name>** (`{colors.text}` — `#RRGGBB`): основной / вторичный / muted.
### Semantic
- success / warning / error / info — hex + применение.

## Typography
### Font Family
- Headings: <Font> (fallback <...>)
- Body: <Font> (fallback <...>)
- Mono (если есть): <Font>
### Hierarchy
- H1 / H2 / H3 / Body / Caption — размер, вес, line-height, letter-spacing.
### Principles
Тон типографики (плотный/воздушный), правила кернинга/капса.
### Note on Font Substitutes
Чем заменить, если фирменный шрифт недоступен.

## Layout
### Spacing System
База (4/8pt) и шкала: 4, 8, 12, 16, 24, 32, 48, 64...
### Grid & Container
Max-width контейнера, число колонок, гаттеры, брейкпоинты сетки.
### Whitespace Philosophy
Плотно или воздушно; где дышит, где собрано.

## Elevation & Depth
Таблица уровней: surface level → box-shadow → назначение (карточка / попап / модалка).

## Shapes
### Border Radius Scale
none / sm / md / lg / pill — px.
### Photography / Illustration Geometry
Скругления, кадрирование, стиль иллюстраций/иконок.

## Components
Для каждого — базовый вид + СТЕЙТЫ (hover / active / focus / disabled).
### Buttons
Primary / secondary / ghost — фон, текст, радиус, паддинги, стейты.
### Cards & Containers
Фон, бордер, тень, радиус, внутренние отступы.
### Inputs & Forms
Бордер, focus-ring, плейсхолдер, ошибка, размер тач-таргета.
### Navigation
Хедер/сайдбар: высота, фон, актив-стейт.
### Pills / Tags / Chips
Фон, текст, радиус (обычно pill).
### Signature Components
Что делает бренд узнаваемым (градиент-акцент, спец-карточка, паттерн).

## Do's and Don'ts
### Do
- Конкретные правила «делай так».
### Don't
- Анти-паттерны «так нельзя».

## Responsive Behavior
### Breakpoints
mobile / tablet / desktop — px.
### Touch Targets
Мин. размер интерактива (≥44px).
### Collapsing Strategy
Как схлопывается nav / grid / контент на узких экранах.
### Image Behavior
object-fit, арт-дирекшн, ретина.

## Iteration Guide (Agent Prompt Guide)
Краткая шпаргалка для промпта ИИ-агенту: 3-5 ключевых цветов + шрифт + одно
предложение «дух бренда». Чтобы можно было вставить прямо в промпт генерации.
```

## Правила заполнения

- **Роли, не голые hex** — `{colors.primary}` привязан к смыслу, а не «синий #533afd».
- **Стейты обязательны** для интерактивных компонентов (hover/focus/disabled).
- **Не выдумывай** значения — тяни из `brand-extractor` (реальный сайт) или задай в `design-system-create`.
- Финальный блок Iteration/Agent Guide — самый ценный для быстрой генерации: держи его сжатым.
