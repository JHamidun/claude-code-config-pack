<!-- Расширенная (прежняя) версия скилла 'frontend-design'. Актуальный канон — ../SKILL.md;
     здесь лежит подробный материал: таблицы, рецепты, антипаттерны.
     Открывай, когда короткого SKILL.md под задачу не хватило. -->

---
name: frontend-design
description: 5 готовых эстетических пресетов когда у проекта нет дизайн-системы. Не путать с одноимённым plugin'ом — этот скилл узче, дает быстрый старт по стилю.
when_to_use: Юзер просит «сделай красиво», в проекте нет токенов или гайдлайна, нужно выбрать направление визуала.
---

# Frontend design — пресеты

Когда нет дизайн-системы, не изобретай вкусы — выбери из 5 проверенных направлений. Каждое самодостаточно: палитра + шрифт + ритм + примеры.

## Пресеты

### 1. Editorial monochrome
Газетный тон, два цвета максимум, упор на типографику.
- **Палитра:** `#FAF9F6` фон, `#111` текст, `oklch(62% 0.14 25)` акцент (приглушённый rust).
- **Шрифт:** один — Helvetica Neue / Inter Tight (heading + body)
- **Ритм:** широкие верт. отступы (96-128px), блоки по сетке 12 колонок, белый воздух
- **Когда:** B2B, контентный сайт, presentations, longform-лендинг

### 2. Soft brutalism
Brutalist каркас + мягкие сюрпризы. Чёрные рамки, сдвиги, неожиданная палитра.
- **Палитра:** `#FFEFD5` peach фон, `#0A0A0A` текст, `#FF4D00` orange acc, `#005CFF` blue acc
- **Шрифт:** Display — Space Grotesk или Inter Tight Black; body — IBM Plex Sans
- **Ритм:** толстые `border: 2px solid #000`, асимметрия, `transform: rotate(-2deg)` на акцентах
- **Когда:** AI/dev tools, edgy startup, design portfolio

### 3. Premium dark
Premium-восприятие: глубокий navy, единственный яркий акцент, blur и subtle gradients.
- **Палитра:** `#0a0e27` фон, `#FFFFFF` текст, `#7C5CFF` violet acc, `rgba(255,255,255,0.08)` карточки
- **Шрифт:** Inter Tight (heading), Inter (body); или Geist
- **Ритм:** Glass-morphism (`backdrop-filter: blur(20px)`), радиусы 16-24, тонкие границы
- **Когда:** AI/SaaS premium, finance, b2b enterprise

### 4. Warm minimalism
Cream + ink + один акцент. Spacious, читабельный, дружелюбный.
- **Палитра:** `#F1F3F5` cream фон, `#1B1B1F` ink, `#3a83f6` либо `#3B5BDB` primary
- **Шрифт:** Manrope / Inter (body), Inter Tight (heading)
- **Ритм:** spacing кратно 4 (4/8/12/16/24/32/48/64/96), радиусы 8-12, тени почти нет
- **Когда:** edtech, healthcare, mainstream b2c, продукты для России

### 5. Data-dense
Информационная плотность: списки, таблицы, узкие отступы, mono-шрифт для цифр.
- **Палитра:** `#FFFFFF` фон, `#0F172A` text, `#0EA5E9` highlight, `#6B7280` muted
- **Шрифт:** Inter (body), JetBrains Mono / Geist Mono для цифр и кодов
- **Ритм:** компактные строки (44px row height), tabular-nums, sticky-заголовки
- **Когда:** dashboard, admin, analytics, fintech-tables

## Как использовать

1. Спроси у юзера в `questions-protocol` про тон («editorial / brutalism / premium dark / warm / data-dense») если бриф не уточняет
2. Возьми палитру и шрифты пресета как базу, не отступай без причины
3. На основе пресета вызови `design-system-create` чтобы построить токены проекта
4. Если нужно несколько вариантов сравнить — `design-canvas` с артбордами по пресетам

## Не путать

- Существует **plugin `frontend-design`** (от plugin-dev marketplace) — он шире, про UI/UX в целом
- Этот скилл узкий: только эти 5 пресетов как стартовая точка для проекта без дизайн-системы

## Антипаттерны

- Смешивать пресеты («brutalism + premium dark») → визуальный шум
- Делать пресет 6+ цветов → перестаёт быть пресетом
- Отступать от ритма пресета («editorial с тенями и градиентами») → теряет идентичность
- Не фиксировать выбор → каждая итерация добавляет новые цвета и шрифты
