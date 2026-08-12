---
name: website-creation
description: Создание современных лендингов и сайтов — от vanilla HTML до React+Tailwind (Lovable-style)
---

# Website Creation Skill

## ОБЯЗАТЕЛЬНО: Выбор режима перед началом работы

Когда пользователь просит создать сайт/лендинг, **НЕ начинай верстку сразу**.
Сначала определи оптимальный режим и предложи его.

### Алгоритм выбора

```
1. Проанализируй задачу:
   - Что за сайт? (лендинг, портфолио, многостраничник, дашборд)
   - Целевая аудитория? (бизнес, креатив, образование, стартап)
   - Нужна ли интерактивность? (формы, роутинг, динамические данные)
   - Один файл или проект?

2. Автоматически выбери режим по матрице:

   Mode A (Vanilla HTML) если:
   → Нужен один HTML файл
   → Простая промо-страница без роутинга
   → "Быстро сверстай", "простой лендинг"
   → Нет требований к компонентной архитектуре

   Mode B (React + Tailwind, Lovable-style) если:
   → Многостраничный сайт (портфолио, блог, каталог)
   → Нужны shadcn/ui компоненты (Accordion, Dialog, Tabs)
   → "Как в Lovable", "профессиональный", "продакшн"
   → Требуется роутинг, состояние, API-вызовы

   Mode C (Your Slide Service, server-side) если:
   → Нужна генерация на сервере (ExampleProject, бот, автоматизация)
   → "Сгенерируй через Your Slide Service", "через сервер"
   → Массовая генерация лендингов

3. Предложи пользователю, объясни выбор в 1-2 предложениях:
```

### Шаблон ответа

```
Для [описание задачи] рекомендую **Mode [X]** ([название]):
- [Почему этот режим подходит]
- Стиль: [конкретный стиль из таблицы ниже]
- Шрифты: [display + body]
- Палитра: [описание]

Начинаю? Или хочешь другой подход?
```

### Таблица автоподбора стиля

| Тип задачи | Mode | Стиль/Палитра | Шрифты |
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

### Если пользователь не уточняет

По умолчанию:
- Один файл → **Mode A** со стилем `modern`
- "Сделай красиво" → **Mode B** с Lovable-паттернами
- "Как в Lovable/Manus" → **Mode B** (React + Tailwind)

---

## Lovable Architecture Patterns

### Tech Stack
- React 18 + TypeScript + Vite
- Tailwind CSS + `tailwindcss-animate` plugin
- shadcn/ui (Radix UI): Button, Card, Badge, Accordion, Input, Dialog
- React Router (react-router-dom) — multi-page SPA
- React Query (@tanstack/react-query)
- Lucide React — иконки (НЕ Font Awesome)

### Font Pairing (Google Fonts)
Всегда 2 шрифта: **display** (заголовки) + **body** (текст).

| Mood | Display Font | Body Font |
|------|-------------|-----------|
| Elegant/Premium | `Playfair Display` (serif) | `Inter` (sans) |
| Cinematic/Artsy | `Cormorant Garamond` (serif) | `Inter` (sans) |
| Friendly/Youth | `Nunito` (sans) | `Inter` (sans) |
| Tech/Corporate | `Space Grotesk` (sans) | `Inter` (sans) |
| Bold/Statement | `Unbounded` (sans) | `Manrope` (sans) |

```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; }
body { font-family: 'Inter', system-ui, sans-serif; }
```

Tailwind config:
```ts
fontFamily: {
  display: ['"Playfair Display"', 'Georgia', 'serif'],
  body: ['"Inter"', 'sans-serif'],
}
```

### Color System (HSL Variables)
shadcn/ui convention — все через HSL CSS vars:

```css
:root {
  /* 3 готовые палитры: */

  /* Warm (travel, food, lifestyle) */
  --background: 35 25% 96%;
  --foreground: 20 15% 12%;
  --primary: 14 55% 53%;     /* terracotta */
  --card: 30 20% 94%;

  /* Dark Moody (portfolio, cinema, luxury) */
  --background: 0 0% 4%;
  --foreground: 40 10% 85%;
  --primary: 38 92% 55%;     /* gold/amber */
  --card: 0 0% 7%;

  /* Bright Youth (education, SaaS, fun) */
  --background: 250 20% 98%;
  --foreground: 250 30% 12%;
  --primary: 262 83% 58%;    /* purple */
  --card: 0 0% 100%;

  /* Semantic tokens (same for all) */
  --border: ...; --muted: ...; --muted-foreground: ...;
  --secondary: ...; --accent: ...; --destructive: ...;
}
```

Градиенты:
```css
--gradient-primary: linear-gradient(135deg, hsl(262 83% 58%), hsl(220 70% 55%));
.text-gradient {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Landing Page Anatomy (секции)

Стандартный лендинг состоит из 8-12 секций:

1. **Header** — fixed, backdrop-blur, transparent→solid on scroll
2. **Hero** — fullscreen, gradient overlay на фото, CTA кнопка
3. **Stats/Social Proof** — 3 числа с counter-анимацией
4. **How It Works** — 3 шага с иконками (grid md:grid-cols-3)
5. **Products/Services** — карточки с hover-эффектами
6. **About/Story** — цитата или текстовый блок
7. **Testimonials** — 3 отзыва в сетке с Quote иконкой
8. **Email/CTA Form** — подписка с success state
9. **FAQ** — Accordion (Radix)
10. **Final CTA** — фото-overlay с кнопкой
11. **Footer** — минимальный, border-top

### Section Spacing (обязательно)
```tsx
// Стандартный padding секций
<section className="py-24 md:py-32 px-6">
  <div className="max-w-5xl mx-auto">

// Max-width варианты
max-w-xl    // узкий текст, формы
max-w-2xl   // FAQ
max-w-3xl   // hero текст, about
max-w-5xl   // карточки, отзывы
max-w-6xl   // широкие гриды
```

### Hero Section Pattern
```tsx
<section className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center overflow-hidden">
  {/* Background image */}
  <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${heroImg})` }} />
  {/* Gradient overlay */}
  <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
  {/* Content */}
  <div className="relative z-10 max-w-3xl">
    <div className="w-20 h-px bg-white/40 mx-auto mb-10" />
    <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-semibold leading-tight tracking-tight mb-8 text-white">
      Headline
    </h1>
    <p className="text-lg md:text-xl text-white/80 italic max-w-xl mx-auto mb-12">
      Subheadline
    </p>
    <Button size="lg" className="rounded-md px-10 py-6 bg-primary hover:bg-primary/90 shadow-xl hover:shadow-2xl hover:scale-[1.03] transition-all duration-300">
      CTA <ArrowRight className="w-5 h-5 ml-2" />
    </Button>
  </div>
</section>
```

### Header Pattern (fixed, blur, transparent→solid)
```tsx
const [scrolled, setScrolled] = useState(false);
useEffect(() => {
  const onScroll = () => setScrolled(window.scrollY > 50);
  window.addEventListener("scroll", onScroll);
  return () => window.removeEventListener("scroll", onScroll);
}, []);

<header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
  scrolled ? "bg-background/95 backdrop-blur-md border-b border-border shadow-sm" : "bg-transparent"
}`}>
  <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
    <span className="font-display text-lg">Logo</span>
    <nav className="hidden md:flex gap-8 text-sm text-muted-foreground">
      <a href="#section" className="hover:text-primary transition-colors">Link</a>
    </nav>
    {/* Mobile hamburger */}
    <button className="md:hidden"><Menu size={20} /></button>
  </div>
</header>
```

### Card Hover Pattern
```tsx
<div className="group rounded-lg overflow-hidden bg-card border border-border
  hover:shadow-xl hover:-translate-y-2 transition-all duration-400">
  {/* Image with zoom on hover */}
  <div className="relative h-48 overflow-hidden">
    <img className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
    {/* Floating badges */}
    <div className="absolute bottom-3 left-3 flex gap-1.5">
      <Badge className="text-[10px] bg-white/20 backdrop-blur-sm text-white border-white/30">Tag</Badge>
    </div>
  </div>
  <div className="p-5">
    <h3 className="text-lg font-semibold group-hover:text-primary transition-colors">Title</h3>
    <p className="text-sm text-muted-foreground">Description</p>
  </div>
</div>
```

### Animation Patterns (3 подхода)

#### 1. CSS fade-up + IntersectionObserver hook (самый лёгкий)
```css
.fade-up {
  opacity: 0; transform: translateY(30px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}
.fade-up.visible { opacity: 1; transform: translateY(0); }
```
```tsx
function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const targets = ref.current?.querySelectorAll('.fade-up') || [];
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); }
      }),
      { threshold: 0.15 }
    );
    targets.forEach((t) => observer.observe(t));
    return () => observer.disconnect();
  }, []);
  return ref;
}
// Stagger delay: style={{ transitionDelay: `${i * 100}ms` }}
```

#### 2. FadeInSection component (React-native, с delay prop)
```tsx
const FadeInSection = ({ children, delay = 0 }) => {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); observer.unobserve(e.target); } },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return (
    <div ref={ref} className={`transition-all duration-700 ease-out ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  );
};
```

#### 3. Framer Motion (whileInView + stagger)
```tsx
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};
<motion.div custom={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}>
```

### Counter Animation (social proof)
```tsx
function useCounter(target: number, visible: boolean) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!visible) return;
    let current = 0;
    const step = Math.max(1, Math.floor(target / 40));
    const interval = setInterval(() => {
      current += step;
      if (current >= target) { setCount(target); clearInterval(interval); }
      else setCount(current);
    }, 30);
    return () => clearInterval(interval);
  }, [visible, target]);
  return count;
}
```

### Typography Scale (responsive)
```
Hero H1:     text-4xl sm:text-5xl md:text-6xl lg:text-7xl
Section H2:  text-3xl md:text-4xl
Card H3:     text-lg или text-xl
Body:        text-sm до text-base
Labels:      text-xs tracking-[0.35em] uppercase text-primary
Meta:        text-[10px] tracking-widest uppercase
```

### Decorative Elements
```tsx
{/* Divider line */}
<div className="w-16 h-px bg-primary mx-auto" />

{/* Film grain overlay */}
<div className="absolute inset-0 opacity-[0.03] bg-[url('data:image/svg+xml;base64,...')]" />

{/* Subtle section backgrounds */}
className="bg-muted/50"     // alternating sections
className="bg-card/30"      // slight differentiation
className="bg-primary/10"   // accent section

{/* Scroll indicator (hero bottom) */}
<div className="absolute bottom-10 left-1/2 -translate-x-1/2">
  <div className="w-px h-12 bg-gradient-to-b from-primary/60 to-transparent animate-pulse" />
</div>

{/* Custom scrollbar */}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: hsl(0 0% 4%); }
::-webkit-scrollbar-thumb { background: hsl(0 0% 20%); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: hsl(var(--primary)); }
```

### Responsive Grid Patterns
```tsx
// 4-column cards
grid sm:grid-cols-2 lg:grid-cols-4 gap-5

// 3-column features
grid md:grid-cols-3 gap-6

// 2-column blog
grid md:grid-cols-2 gap-6

// Inline form (mobile stack)
flex flex-col sm:flex-row gap-3

// Nav (hide on mobile)
<nav className="hidden md:flex gap-8">
<button className="md:hidden">
```

### Timeline/Experience Pattern
```tsx
<div className="relative">
  {/* Vertical line */}
  <div className="absolute left-3 top-2 bottom-2 w-px bg-border md:left-1/2" />
  {jobs.map((job, i) => (
    <div className={`relative flex ${i % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"}`}>
      {/* Dot */}
      <div className="absolute left-3 md:left-1/2 w-2 h-2 rounded-full bg-primary -translate-x-1/2" />
      <div className={`ml-10 md:ml-0 md:w-1/2 ${i % 2 === 0 ? "md:pr-12 md:text-right" : "md:pl-12"}`}>
        <span className="text-[10px] tracking-widest uppercase text-primary">{job.period}</span>
        <h3 className="font-display text-lg">{job.title}</h3>
      </div>
    </div>
  ))}
</div>
```

---

## Mode A: Vanilla HTML Quick Start

### Библиотека эффектов
**ОБЯЗАТЕЛЬНО** используй: `~/.claude/skills/landing-page-effects/SKILL.md (скилл `landing-page-effects` в пак не входит)`
- 50+ готовых эффектов (CSS + JS)
- 15 шрифтов, цветовая палитра
- Трендовые эффекты 2025

### Эталонный лендинг
`${HOME}\your-project-landing\index.html`

### Чеклист
- [ ] Preloader + Custom cursor (опц.)
- [ ] 2-3 шрифта + CSS переменные
- [ ] Scroll reveal (IntersectionObserver)
- [ ] Hover эффекты на кнопках и карточках
- [ ] Grain overlay + Animated gradient
- [ ] Responsive (mobile-first)

### Быстрый старт
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;800&family=Manrope:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #050510; --neon: #818cf8; --cyan: #22d3ee; --pink: #f472b6;
            --font-display: 'Unbounded', sans-serif;
            --font-body: 'Manrope', sans-serif;
        }
        body { background: var(--bg); color: white; font-family: var(--font-body); }
        h1, h2, h3 { font-family: var(--font-display); }
        .reveal { opacity: 0; transform: translateY(30px); transition: all 0.8s ease; }
        .reveal.active { opacity: 1; transform: translateY(0); }
    </style>
</head>
<body>
    <h1>Headline</h1>
    <script>
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('active'); });
        }, { threshold: 0.1 });
        document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    </script>
</body>
</html>
```

---

## Рекомендуемые библиотеки

| Библиотека | Использование | Режим |
|------------|--------------|-------|
| shadcn/ui (Radix) | UI компоненты | React |
| Tailwind CSS | Стилизация | React |
| Lucide React | Иконки | React |
| Framer Motion | Анимации | React |
| tailwindcss-animate | CSS анимации | React |
| GSAP + ScrollTrigger | Сложные анимации | Vanilla |
| Three.js | 3D эффекты | Vanilla |
| Lenis | Smooth scroll | Оба |

---

## Mode C: Your Slide Service (server-side generation)

Your Slide Service на your-server (`/opt/your-slide-service`), реверс Manus.
Генерирует single-file HTML лендинги через Claude CLI carousel.

### Endpoint
```
POST /api/generate/website
Body: { "prompt": "...", "style": "modern" }
Response: { "html": "...", "htmlPath": "...", "previewUrl": "..." }
```

### 4 стиля генерации

| Style | Описание | Когда использовать |
|-------|----------|-------------------|
| `modern` | Градиенты, glassmorphism, яркие цвета | SaaS, стартапы |
| `minimal` | Whitespace, монохром, 1 акцент | Портфолио, luxury |
| `bold` | Большая типографика, контрасты | Events, промо |
| `corporate` | Navy/white, trust badges, grid | B2B, корпоративы |

### System Prompt (Your Slide Service pattern)

Проверенный system prompt для генерации landing page одним промптом:

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

### Your Slide Service на сервере

| Компонент | Путь | Описание |
|-----------|------|----------|
| Engine | `/opt/your-slide-service/engine/` | FastAPI + Python, генерация |
| Gateway | `/opt/your-slide-service/gateway/` | Node.js, маршрутизация |
| Web UI | `/opt/your-slide-service/web/` | React + Vite frontend |
| Data | `/opt/your-slide-service/data/` | SQLite + проекты |
| Styles | `/opt/your-slide-service/data/style-previews/` | N PNG превью стилей |

### Как связаны Your Slide Service, Manus и Lovable

| Аспект | Manus | Your Slide Service (yours) | Lovable |
|--------|-------|-----------------|---------|
| Подход | System prompt → single HTML | Fork Manus паттернов | React app (полный проект) |
| Стек | Claude + sandbox | Claude CLI carousel | React + Tailwind + shadcn |
| Стили | 4 hints (modern/minimal/bold/corp) | 4 hints (то же) | HSL CSS vars + 2 шрифта |
| Компоненты | inline HTML | inline HTML | shadcn/ui (Radix) |
| Анимации | IntersectionObserver | IntersectionObserver | IO + Framer Motion |
| Результат | 1 HTML файл | 1 HTML файл | React SPA (build) |
| Когда | Быстрый прототип | Быстрый прототип | Продакшн сайт |

---

## Reference Projects

### Lovable (React + Tailwind)

| Проект | Стиль | Палитра | Шрифт Display |
|--------|-------|---------|---------------|
| example-project-1 | Travel/warm | Terracotta + beige | Playfair Display |
| example-project-2 | Portfolio/dark | Gold + black | Cormorant Garamond |
| example-project-3 | Education/bright | Purple + white | Nunito |

Код: `${HOME}\presentations\your-workshop\repos\`

### Manus/Your Slide Service (Single-file HTML)

| Компонент | Источник |
|-----------|---------|
| Manus analysis | `${WORKSPACE}/projects/ExampleProject/docs/11-manus.md` |
| Your Slide Service server | `ssh your-server` → `/opt/your-slide-service/` |
| Website builder | `/opt/your-slide-service/engine/src/services/website_builder.py` |
| 24 slide styles | `/opt/your-slide-service/engine/src/styles/catalog.py` |
| Style previews | `/opt/your-slide-service/data/style-previews/*.png` |
