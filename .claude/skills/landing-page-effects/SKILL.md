---
name: landing-page-effects
description: "Библиотека 50+ эффектов лендингов: шрифты, тёмная неоновая палитра, Tilda SBS-анимации. Триггеры: «эффекты лендинга», «глитч», «неоновая кнопка», «кастомный курсор»."
---

# Landing Page Effects Library

Библиотека нужна для одного: чтобы один и тот же эффект на всех твоих страницах выглядел одинаково. Сомневаешься в реализации — бери код из `references/effects-catalog.md`, а не пиши свою версию.

Собрал страницу, которая тебе нравится, — запиши её как эталон в `references/reference-page.md` (шаблон внутри) и дальше сверяйся с ней.

## Шрифты (канон, 15 штук)

Не более 3-4 шрифтов на одной странице.

```css
:root {
    --font-unbounded: 'Unbounded', sans-serif;      /* Заголовки, bold */
    --font-manrope: 'Manrope', sans-serif;          /* Основной текст */
    --font-jetbrains: 'JetBrains Mono', monospace;  /* Код */
    --font-orbitron: 'Orbitron', sans-serif;        /* Tech/cyber */
    --font-share-tech: 'Share Tech Mono', monospace; /* Терминал */
    --font-playfair: 'Playfair Display', serif;     /* Elegant */
    --font-space-grotesk: 'Space Grotesk', sans-serif; /* Geometric */
    --font-inter: 'Inter', sans-serif;              /* UI */
    --font-fira: 'Fira Code', monospace;            /* Код alt */
    --font-bebas: 'Bebas Neue', sans-serif;         /* Display caps */
    --font-montserrat: 'Montserrat', sans-serif;    /* Geometric sans */
    --font-space-mono: 'Space Mono', monospace;     /* Mono */
    --font-ibm: 'IBM Plex Sans', sans-serif;        /* Corporate */
    --font-outfit: 'Outfit', sans-serif;            /* Clean sans */
    --font-syne: 'Syne', sans-serif;                /* Bold modern */
}
```

Google Fonts (все веса уже подобраны):
```html
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;800&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Orbitron:wght@400;700&family=Share+Tech+Mono&family=Playfair+Display:ital@1&family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&family=Bebas+Neue&family=Montserrat:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=IBM+Plex+Sans:wght@400;500;600&family=Outfit:wght@400;500;600;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
```

## Палитра (тёмная неоновая)

Готовый набор токенов под тёмный лендинг с неоновыми акцентами — берётся целиком и перекрашивается под свой бренд: меняешь `--brand-*` и `--neon-*`, остальное подстраивается. Свои цвета из логотипа → навык `color-system-builder` (сгенерирует шкалу и проверит контраст).

```css
:root {
    /* === BACKGROUNDS === */
    --bg-primary: #050510;        /* Основной тёмный */
    --bg-dark: #010106;           /* Tilda dark */
    --bg-terminal: #0a0a15;       /* Терминал */
    --bg-card: rgba(20, 20, 40, 0.8);
    --bg-purple: #14092e;         /* Tilda purple dark */
    --bg-gradient: linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%);

    /* === PRIMARY BRAND === */
    --brand-blue: #2d2fe8;        /* Tilda CTA primary */
    --brand-blue-dark: #010334;   /* Tilda CTA hover */
    --brand-indigo: #5050f5;      /* Indigo accent */
    --brand-violet: #6464FA;      /* Violet */
    --brand-electric: #2015FF;    /* Electric blue */
    --brand-purple-blue: #3733FF; /* Purple-blue */

    /* === NEON ACCENTS === */
    --neon-lime: #818cf8;         /* Primary accent */
    --neon-yellow: #a5b4fc;       /* Yellow-ish */
    --neon-cyan: #22d3ee;         /* Cyan */
    --neon-aqua: #00FFFF;         /* Pure cyan */
    --neon-blue: #60a5fa;         /* Blue */
    --neon-sky: #00AAFF;          /* Tilda bright blue */
    --neon-royal: #0064FF;        /* Royal blue */
    --neon-pink: #f472b6;         /* Pink */
    --neon-coral: #fa876b;        /* Coral */
    --neon-orange: #FF914B;       /* Tilda orange */
    --neon-purple: #a78bfa;       /* Purple */
    --neon-red: #fb7185;          /* Red */
    --gold: #fbbf24;              /* Gold */
    --silver: #cbd5e1;            /* Silver */

    /* === TEXT === */
    --text-primary: #ffffff;
    --text-secondary: #e2e8f0;
    --text-muted: #94a3b8;
    --text-gray: #9b9ba7;         /* Tilda muted */
    --text-dark-gray: #5b5b68;    /* Tilda dark gray */
    --text-purple-gray: #8c85a1;  /* Purple gray */

    /* === SURFACES === */
    --surface-light: #e9e9ed;     /* Tilda light */
    --surface-lavender: #f1effa;  /* Light lavender */
    --surface-hover: #E6E6F0;     /* Hover state */
    --surface-border: #cecede;    /* Border */

    /* === GLOW EFFECTS === */
    --glow-lime: 0 0 25px rgba(129, 140, 248, 0.6);
    --glow-cyan: 0 0 20px rgba(34, 211, 238, 0.5);
    --glow-pink: 0 0 20px rgba(244, 114, 182, 0.5);
    --glow-blue: 0 0 30px rgba(45, 47, 232, 0.4);
    --glow-white: 0 0 30px rgba(255, 255, 255, 0.3);
}
```

## Каталог эффектов

Канонические реализации (CSS/JS) → `references/effects-catalog.md`. Бери оттуда, а не пиши свою версию — иначе один и тот же глитч на разных страницах выглядит по-разному.

- **1-21 Core** (обкатанные): preloader, custom cursor, animated grain, progress bar, glitch text/hover, neon button, ripple, marquee, bouncing dot, 3D card tilt, typewriter, scroll reveal, horizontal scroll, counter, pixel grid, floating stickers, terminal window, scroll indicator, text scramble, confetti.
- **22-35 Trendy 2025** (на потоке не гонялись): scroll-driven CSS animations, parallax layers, scroll-triggered 3D, magnetic elements, Lenis smooth scroll, GSAP ScrollTrigger, split text, morphing shapes, animated gradient, reveal mask, Three.js particles, liquid distortion, cursor trail, scroll velocity. Там же таблица библиотек (GSAP, Lenis, Three.js…).

## Tilda-эффекты (36-45)

Формат Tilda SBS-анимаций не угадывается — параметры `data-animate-sbs-opts`:

```
data-animate-sbs-opts='{"mx":0,"my":30,"sx":1,"sy":1,"op":1,"ro":0,"ti":700,"ea":"bounceFin","dt":0}'
```

| Param | Что | Пример |
|-------|-----|--------|
| `mx` / `my` | Move X/Y (px) | -2300, 30 |
| `sx` / `sy` | Scale X/Y | 1, 1.1, 0.8 |
| `op` | Opacity | 0…1 |
| `ro` | Rotation (deg) | 0, 45, 360 |
| `ti` | Timing (ms) | 200, 700, 15000 |
| `ea` | Easing | "bounceFin", "0" (linear) |
| `dt` | Delay (ms) | 0, 100 |
| `di` | Distance (scroll trigger) | 200, 500 |
| `dd` | Direction delay | 0, 100 |
| `fi` | Fixed position | true/false |

Loop: `data-animate-sbs-repeat="loop"`. Hover-вариант: `data-animate-sbs-hover="on"`.

Готовые реализации (fade `t-animate_*`, bounce, marquee, scale-hover, chain, CTA-кнопка, burger, scroll indicator, JS-инициализация через IntersectionObserver) → `references/tilda-effects.md`.

## Канонические easing

| Easing | Значение |
|--------|----------|
| Bounce Fin (Tilda) | `cubic-bezier(0.34, 1.56, 0.64, 1)` |
| Smooth | `cubic-bezier(0.77, 0, 0.175, 1)` |
| Elastic | `cubic-bezier(0.68, -0.55, 0.265, 1.55)` |

## Гигиена

`will-change` на анимируемых элементах; отключение через `prefers-reduced-motion`; тяжёлые эффекты (Three.js, particles) — lazy load, иначе LCP страдает.
