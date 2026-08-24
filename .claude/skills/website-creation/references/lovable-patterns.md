# Готовые куски вёрстки (Mode B, React + Tailwind)

Читать, когда собираешь лендинг в Mode B и нужен конкретный кусок: hero,
шапка-на-скролле, карточка с hover, scroll-reveal, счётчик, таймлайн. Это
заготовки под копипаст с уже выставленными числами (длительности, threshold,
смещения) — не общий гайд по React.

## Hero

```tsx
<section className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center overflow-hidden">
  <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${heroImg})` }} />
  <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
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

Тройной градиент сверху-вниз (60/40/70), а не ровная заливка: середина кадра
светлее, поэтому текст читается и фото не выглядит закрашенным.

## Шапка: прозрачная → плотная на скролле

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
    <button className="md:hidden"><Menu size={20} /></button>
  </div>
</header>
```

## Карточка с hover

```tsx
<div className="group rounded-lg overflow-hidden bg-card border border-border
  hover:shadow-xl hover:-translate-y-2 transition-all duration-400">
  <div className="relative h-48 overflow-hidden">
    <img className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
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

Зум картинки (700 мс) намеренно медленнее подъёма карточки (400 мс) — иначе
движение читается как рывок.

## Scroll reveal — три варианта

### 1. CSS-класс + один observer на секцию (самый лёгкий)

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
// Каскад: style={{ transitionDelay: `${i * 100}ms` }}
```

`unobserve` после срабатывания обязателен — иначе элемент переигрывает анимацию
при каждом проходе мимо, и страница «моргает» на обратном скролле.

### 2. Компонент-обёртка с prop delay

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

### 3. Framer Motion

```tsx
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};
<motion.div custom={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp}>
```

## Счётчик для блока цифр

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

40 шагов по 30 мс = 1,2 с на любое число: шаг считается от цели, поэтому
и 12, и 12 000 досчитываются за одно время.

## Таймлайн (опыт, этапы)

```tsx
<div className="relative">
  <div className="absolute left-3 top-2 bottom-2 w-px bg-border md:left-1/2" />
  {jobs.map((job, i) => (
    <div className={`relative flex ${i % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"}`}>
      <div className="absolute left-3 md:left-1/2 w-2 h-2 rounded-full bg-primary -translate-x-1/2" />
      <div className={`ml-10 md:ml-0 md:w-1/2 ${i % 2 === 0 ? "md:pr-12 md:text-right" : "md:pl-12"}`}>
        <span className="text-[10px] tracking-widest uppercase text-primary">{job.period}</span>
        <h3 className="font-display text-lg">{job.title}</h3>
      </div>
    </div>
  ))}
</div>
```

На мобильном линия и точки прижаты влево (`left-3`), на десктопе уезжают в центр
(`md:left-1/2`) — одна разметка на оба случая, без дублирования блока.

## Мелочи оформления

```tsx
{/* разделительная черта */}
<div className="w-16 h-px bg-primary mx-auto" />

{/* фоновые оттенки для чередования секций */}
className="bg-muted/50"   // соседняя секция
className="bg-card/30"    // лёгкое отличие
className="bg-primary/10" // акцентная секция

{/* индикатор скролла под hero */}
<div className="absolute bottom-10 left-1/2 -translate-x-1/2">
  <div className="w-px h-12 bg-gradient-to-b from-primary/60 to-transparent animate-pulse" />
</div>
```

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: hsl(0 0% 4%); }
::-webkit-scrollbar-thumb { background: hsl(0 0% 20%); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: hsl(var(--primary)); }
```

Плёночное зерно — слой `absolute inset-0` с `opacity-[0.03]` и повторяющимся
SVG-шумом в `background-image` (data-URI), поверх всей секции, `pointer-events-none`.

## Каркас Mode A (vanilla, один файл)

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
