<!-- LEGACY: полное тело скилла 'type-scale' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: type-scale
description: Modular type scale + проверенные font-pairs. Дает 7-9 размеров от tiny до hero, с чёткой математикой между ними. И 5 готовых пар head+body+mono шрифтов под разные эстетики.
when_to_use: При создании дизайн-системы (внутри design-system-create), при проверке существующего проекта на типографику. Без модульной шкалы все размеры выглядят случайными.
---

# Type scale

Modular scale = одно число (ratio), от которого вырастают все размеры. Меньше произвола, больше согласованности.

## Math

```
base = 16px (body)
ratio = выбираешь из таблицы

t-tiny  = base / ratio²
t-small = base / ratio
t-body  = base
t-lead  = base × ratio
t-h3    = base × ratio²
t-h2    = base × ratio³
t-h1    = base × ratio⁴
t-hero  = base × ratio⁵   (или clamp() для responsive)
```

## Готовые ratio

| Ratio | Значение | Vibe | Когда |
|---|---|---|---|
| 1.125 | Major Second | Спокойный, плотный | Dashboard, dense UI |
| 1.200 | Minor Third | Сбалансированный | Default, b2b лендинг |
| 1.250 | Major Third | Дружелюбный | Edtech, b2c, mainstream |
| 1.333 | Perfect Fourth | Чёткая иерархия | Editorial, longform |
| 1.414 | Augmented Fourth | Драматичный | Pitch deck, marketing |
| 1.500 | Perfect Fifth | Бренд-выразительный | Hero-heavy лендинги |
| 1.618 | Golden Ratio | Премиум | Luxury, fashion, art |

## Пример: ratio 1.25 (Major Third), base 16

```css
:root {
  --t-tiny:  10.24px;   /* 16 ÷ 1.25² */
  --t-small: 12.8px;    /* 16 ÷ 1.25  */
  --t-body:  16px;
  --t-lead:  20px;      /* 16 × 1.25  */
  --t-h3:    25px;      /* 16 × 1.25² */
  --t-h2:    31.25px;   /* 16 × 1.25³ */
  --t-h1:    39.06px;   /* 16 × 1.25⁴ */
  --t-hero:  clamp(48px, 5vw, 76px);  /* responsive cap */
}
```

В реальности округляй до целых: 10/13/16/20/25/31/39/76.

## Line-height по уровню

| Размер | line-height |
|---|---|
| tiny / small (10-13px) | 1.4-1.5 |
| body (14-16px) | 1.5-1.65 |
| lead (18-22px) | 1.4-1.5 |
| h3 (24-32px) | 1.25-1.35 |
| h1-h2 (36-60px) | 1.05-1.2 |
| hero (60+) | 0.9-1.0 |

## Letter-spacing

| Размер | letter-spacing |
|---|---|
| Заголовки (h1-h2) | -0.02em до -0.05em (tight, хорошо для display) |
| Body | 0 (default) |
| Eyebrow / label / mono | +0.04em до +0.16em (loose, читается как «бейдж») |
| Buttons | +0.02em |

## Font-weight scale

```
300 — light (display only, не для body!)
400 — regular (body default)
500 — medium (mid emphasis)
600 — semibold (subheaders, labels)
700 — bold (headings)
900 — black (display hero only)
```

**Не миксуй** 5 weights в одном проекте — выбери 2-3.

## 5 проверенных пар head + body + mono

### 1. Editorial monochrome
```
head: "Helvetica Neue", "Inter Tight"
body: "Helvetica Neue", "Inter"
mono: "JetBrains Mono", ui-monospace
```

### 2. Soft brutalism
```
head: "Space Grotesk Black", "Inter Tight Black"
body: "IBM Plex Sans"
mono: "IBM Plex Mono"
```

### 3. Premium dark
```
head: "Inter Tight"
body: "Inter"
mono: "Geist Mono"
```

### 4. Warm minimalism
```
head: "Inter Tight"
body: "Manrope"
mono: "JetBrains Mono"
```

### 5. Data-dense
```
head: "Inter"
body: "Inter"
mono: "Geist Mono", "JetBrains Mono"
```

**Правило:** не миксуй 3+ font families. Head + body (часто одна family с двумя weights) + mono = достаточно.

## Self-hosted vs Google Fonts

- **Production:** self-host через `@font-face` в `styles/fonts.css` (RF-safe, GDPR-safe, faster)
- **Prototype:** через Google Fonts CDN — `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">`

Для России (your-regulator блокировки) — всегда self-host для production.

## Как применить в tokens.css

```css
:root {
  /* Type scale (ratio 1.25, base 16) */
  --t-tiny:  10px;
  --t-small: 13px;
  --t-body:  16px;
  --t-lead:  20px;
  --t-h3:    24px;
  --t-h2:    32px;
  --t-h1:    40px;
  --t-hero:  clamp(44px, 5vw, 72px);

  /* Font families */
  --font-head: "Inter Tight", "Helvetica Neue", sans-serif;
  --font-body: "Inter", "Helvetica Neue", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  /* Line heights */
  --lh-tight: 1.1;
  --lh-snug:  1.3;
  --lh-base:  1.55;
  --lh-loose: 1.7;
}

body { font: var(--t-body)/var(--lh-base) var(--font-body); }
h1   { font: 700 var(--t-h1)/var(--lh-tight) var(--font-head); letter-spacing: -0.03em; }
h2   { font: 700 var(--t-h2)/var(--lh-snug) var(--font-head); letter-spacing: -0.02em; }
h3   { font: 600 var(--t-h3)/var(--lh-snug) var(--font-head); }
```

## Антипаттерны

- 12+ размеров в шкале → теряется иерархия
- Размеры из головы (`14px, 17px, 22px, 29px`) без логики → каждый разработчик добавляет ещё один
- Mix 4 шрифтов → визуальная фрагментация
- Body 14px на лендинге → плохо читается, нужно 16px минимум, 18px на hero-section
- Заголовок hero 32px на 1920×1080 → выглядит как заголовок секции, не как hero
- line-height 1.0 для body → слиплось
- Нет mono → числа в таблицах прыгают, не выровнены
