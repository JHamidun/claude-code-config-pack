---
name: website-creation
description: "Создание современных лендингов и сайтов — от vanilla HTML до React+Tailwind (Lovable-style). Триггеры: «создай сайт», «landing page», «website»."
---

# Website Creation

## Сначала режим, потом вёрстка

Не начинай верстать по первой фразе. Режим определяет всё дальнейшее — файловую
структуру, стек, способ правок, — и переезд между режимами на середине означает
переписать лендинг целиком. Выбери режим, назови его пользователю в одну-две
фразы вместе со стилем и шрифтами, и работай.

| Режим | Когда | Что на выходе |
|---|---|---|
| **A — Vanilla HTML** | один файл, промо-страница без роутинга, «быстро сверстай», «простой лендинг» | один .html со всем внутри |
| **B — React + Tailwind (Lovable-style)** | многостраничник (портфолио, блог, каталог), нужны компоненты shadcn/ui, роутинг, состояние, вызовы API, «как в Lovable», «продакшн» | проект React SPA |
| **C — server-side генерация** | массовая генерация лендингов, вызов из бота/автоматизации, «сгенерируй через сервис» | один .html от сервиса |

Если пользователь не уточняет: один файл → **A**, стиль `modern`; «сделай
красиво» → **B**; «как в Lovable/Manus» → **B**.

### Автоподбор стиля

| Тип задачи | Режим | Стиль/Палитра | Шрифты |
|------------|------|--------------|--------|
| Лендинг стартапа/SaaS | A или B | Bright (purple + white) | Nunito + Inter |
| Портфолио/резюме | B | Dark moody (gold + black) | Cormorant Garamond + Inter |
| Travel/lifestyle блог | B | Warm (terracotta + beige) | Playfair Display + Inter |
| Корпоративный B2B | A | Corporate (navy + white) | Space Grotesk + Inter |
| Образование/дети | B | Bright + gradients | Nunito + Inter |
| Промо-акция/event | A | Bold (контрасты, большой текст) | Unbounded + Manrope |
| Luxury/fashion | B | Dark + minimal | Cormorant Garamond + Inter |
| Tech/developer | A | Dark-tech (neon accents) | JetBrains Mono + Inter |
| Магазин/каталог | B | Clean light | Inter + Inter |
| Автоматизация/бот | C | modern/minimal | Inter (CDN) |

---

## Mode B — React + Tailwind

### Стек

React 18 + TypeScript + Vite · Tailwind CSS + `tailwindcss-animate` · shadcn/ui
(Radix): Button, Card, Badge, Accordion, Input, Dialog · React Router · React
Query (`@tanstack/react-query`) · **Lucide React для иконок — не Font Awesome**:
lucide идёт деревом импортов и не тянет шрифт-пак ради трёх глифов.

### Пара шрифтов

Всегда два: **display** для заголовков + **body** для текста. Один шрифт на всё
читается как черновик, три — как несогласованный макет.

| Настроение | Display | Body |
|------|-------------|-----------|
| Elegant/Premium | `Playfair Display` (serif) | `Inter` |
| Cinematic/Artsy | `Cormorant Garamond` (serif) | `Inter` |
| Friendly/Youth | `Nunito` | `Inter` |
| Tech/Corporate | `Space Grotesk` | `Inter` |
| Bold/Statement | `Unbounded` | `Manrope` |

```ts
// tailwind.config
fontFamily: {
  display: ['"Playfair Display"', 'Georgia', 'serif'],
  body: ['"Inter"', 'sans-serif'],
}
```

### Цвет: HSL-переменные

Соглашение shadcn/ui — цвета задаются тройками HSL **без** `hsl()` вокруг, чтобы
Tailwind мог подмешивать альфу (`bg-primary/10`). Три готовые палитры:

```css
/* Warm — travel, food, lifestyle */
--background: 35 25% 96%;  --foreground: 20 15% 12%;
--primary: 14 55% 53%;     /* terracotta */   --card: 30 20% 94%;

/* Dark Moody — портфолио, кино, luxury */
--background: 0 0% 4%;     --foreground: 40 10% 85%;
--primary: 38 92% 55%;     /* gold/amber */   --card: 0 0% 7%;

/* Bright Youth — образование, SaaS, fun */
--background: 250 20% 98%; --foreground: 250 30% 12%;
--primary: 262 83% 58%;    /* purple */       --card: 0 0% 100%;
```

Остальные семантические токены (`--border`, `--muted`, `--muted-foreground`,
`--secondary`, `--accent`, `--destructive`) выводятся от этих четырёх.

Градиентный текст:

```css
--gradient-primary: linear-gradient(135deg, hsl(262 83% 58%), hsl(220 70% 55%));
.text-gradient {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Анатомия лендинга

8-12 секций в этом порядке: Header (fixed, blur, прозрачный→плотный на скролле) ·
Hero (fullscreen, градиент поверх фото, CTA) · Stats/соцдоказательство (3 числа
со счётчиком) · How It Works (3 шага) · Products/Services (карточки с hover) ·
About/Story · Отзывы (3 в сетке) · Форма/CTA с success-состоянием · FAQ
(Accordion) · финальный CTA на фото · Footer (минимальный, `border-top`).

### Ритм и размеры

Секции и максимальные ширины держатся одинаковыми по всей странице — вразнобой
подобранные `max-w` читаются как съехавшая вёрстка, даже если каждая секция
сама по себе аккуратна.

```
Секция:   py-24 md:py-32 px-6
max-w-xl  узкий текст, формы      max-w-3xl  hero-текст, about
max-w-2xl FAQ                     max-w-5xl  карточки, отзывы
                                  max-w-6xl  широкие гриды

Hero H1:     text-4xl sm:text-5xl md:text-6xl lg:text-7xl
Section H2:  text-3xl md:text-4xl
Card H3:     text-lg / text-xl
Body:        text-sm … text-base
Labels:      text-xs tracking-[0.35em] uppercase text-primary
Meta:        text-[10px] tracking-widest uppercase
```

### Готовые куски вёрстки

Hero, шапка-на-скролле, карточка с hover, три варианта scroll-reveal, счётчик
цифр, таймлайн, зерно/скроллбар, каркас Mode A → **`references/lovable-patterns.md`**.
Открывай, когда собираешь конкретный блок: там числа (длительности, threshold,
задержки каскада) уже подобраны.

---

## Mode A — Vanilla HTML

Готовой библиотеки эффектов в паке нет. Снипеты частых мелочей (stagger reveal,
parallax, counter, skeleton) — в скилле `microinteractions`; вкус, шрифты и
палитру держат `design-taste`/`frontend-design`. Остальное из чеклиста
(preloader, grain overlay, hover, animated gradient) пишется руками — это по
10-30 строк CSS/JS каждое.

Эталон лендинга в паке не поставляется: держи собственный (лучший из своих
прошлых) и переиспользуй его структуру.

Чеклист перед сдачей:

- [ ] Preloader + кастомный курсор (опц.)
- [ ] 2-3 шрифта + CSS-переменные
- [ ] Scroll reveal (IntersectionObserver)
- [ ] Hover на кнопках и карточках
- [ ] Grain overlay + анимированный градиент
- [ ] Responsive (mobile-first)

**Библиотеки:** GSAP + ScrollTrigger для сложных анимаций, Three.js для 3D,
Lenis для smooth scroll (работает в обоих режимах). В Mode B — Framer Motion.

---

## Mode C — server-side генерация

Сервис-генератор на своём сервере (`/opt/<slide-service>`), реверс Manus. Отдаёт
single-file HTML лендинги через carousel Claude CLI.

```
POST /api/generate/website
Body:     { "prompt": "...", "style": "modern" }
Response: { "html": "...", "htmlPath": "...", "previewUrl": "..." }
```

Четыре стиля: `modern` (градиенты, glassmorphism — SaaS, стартапы) · `minimal`
(воздух, монохром, один акцент — портфолио, luxury) · `bold` (крупная
типографика, контрасты — события, промо) · `corporate` (navy/white, trust-badges,
сетка — B2B).

Проверенный system prompt генерации:

```
You are an expert web designer and front-end developer.
Generate a COMPLETE, production-ready, single-file HTML landing page.

Requirements:
- Single HTML file with ALL CSS and JavaScript inline
- Load Inter font from Google Fonts CDN
- Fully responsive (mobile-first, 320px to 2560px)
- Smooth scrolling (html { scroll-behavior: smooth })
- Sections: Hero, Features (3-4 cards), About, Pricing/CTA, Footer
- {STYLE_HINT}
- All text in the SAME LANGUAGE as user's prompt
- CSS animations (fade-in via IntersectionObserver, hover effects)
- Semantic HTML5 (header, main, section, footer)
- Fixed nav with smooth-scroll anchor links
- Buttons with hover/active states

Output: ONLY the HTML document, starting with <!DOCTYPE html>.
```

Строка `All text in the SAME LANGUAGE as user's prompt` обязательна: без неё
модель по умолчанию отдаёт английский лендинг на русский бриф.

Раскладка сервиса: `engine/` (FastAPI, генерация) · `gateway/` (Node.js,
маршрутизация) · `web/` (React + Vite) · `data/` (SQLite + проекты) ·
`data/style-previews/` (PNG-превью стилей).
