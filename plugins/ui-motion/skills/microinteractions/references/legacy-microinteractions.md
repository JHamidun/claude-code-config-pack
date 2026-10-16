<!-- Расширенная (прежняя) версия скилла 'microinteractions'. Актуальный канон — ../SKILL.md;
     здесь лежит подробный материал: таблицы, рецепты, антипаттерны.
     Открывай, когда короткого SKILL.md под задачу не хватило. -->

---
name: microinteractions
description: Skeleton loaders, hover-эффекты, scroll-reveal, button feedback. Маленькие анимации которые делают прототип живым. Не тяжёлый motion (см. animations) — а micro-feedback на действия пользователя.
when_to_use: Юзер просит «оживи прототип», «добавь hover», «когда грузится — что показываем», «при клике должно реагировать». В interactive-prototype после статики.
---

# Microinteractions

Маленькие анимации = большая разница в восприятии «это live» vs «это макет».

## 1. Skeleton loader

Серая плашка-плейсхолдер пока грузится контент. Используй вместо спиннера для контента-предсказуемой формы (карточка, строка таблицы, аватар).

```css
@keyframes skel-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skel {
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: skel-shimmer 1.5s linear infinite;
  border-radius: 6px;
}
.skel-line { height: 12px; margin: 6px 0; }
.skel-line.short { width: 40%; }
.skel-line.long  { width: 90%; }
.skel-circle { width: 40px; height: 40px; border-radius: 50%; }
```

```jsx
{loading ? (
  <div style={{ padding: 16 }}>
    <div className="skel skel-circle" />
    <div className="skel skel-line long" />
    <div className="skel skel-line short" />
  </div>
) : <RealCard data={data} />}
```

## 2. Hover effects

Стандартный набор для interactive elements:

```css
.btn { transition: background .15s, transform .15s, box-shadow .15s; }
.btn:hover { background: var(--primary-hover); }
.btn:active { transform: translateY(1px); }

.card { transition: transform .2s, box-shadow .2s; }
.card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }

.link { position: relative; }
.link::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 100%;
               height: 1px; background: currentColor; transform: scaleX(0); transform-origin: right;
               transition: transform .25s; }
.link:hover::after { transform: scaleX(1); transform-origin: left; }
```

**Правило:** hover работает только на устройствах с курсором. Мобильные: используй `:active` или JS-туч-фидбек.

## 3. Scroll-reveal (intersection observer)

Появление при скролле, без библиотек:

```jsx
function Reveal({ children, delay = 0 }) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const o = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setShown(true); o.disconnect(); }
    }, { threshold: 0.1 });
    if (ref.current) o.observe(ref.current);
    return () => o.disconnect();
  }, []);
  return (
    <div ref={ref} style={{
      opacity: shown ? 1 : 0,
      transform: shown ? 'translateY(0)' : 'translateY(20px)',
      transition: `opacity .6s ${delay}ms, transform .6s ${delay}ms`,
    }}>{children}</div>
  );
}
```

```jsx
<Reveal>           <Hero /></Reveal>
<Reveal delay={100}><Features /></Reveal>
<Reveal delay={200}><Pricing /></Reveal>
```

## 4. Click ripple (Material-style)

```css
.ripple { position: relative; overflow: hidden; }
.ripple::after {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle, rgba(255,255,255,0.3) 1px, transparent 60%);
  background-size: 0 0; background-position: var(--rx, 50%) var(--ry, 50%);
  transition: background-size .5s;
}
.ripple:active::after { background-size: 200% 200%; }
```

```jsx
<button className="ripple" onMouseDown={(e) => {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty('--rx', `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty('--ry', `${e.clientY - r.top}px`);
}}>Click</button>
```

## 5. Number ticker

Цифры «крутятся» к финальному значению:

```jsx
function Tick({ value, duration = 1000 }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const t = Math.min(1, (Date.now() - start) / duration);
      setN(Math.round(value * (1 - Math.pow(1 - t, 3))));  // easeOut cubic
      if (t === 1) clearInterval(id);
    }, 16);
    return () => clearInterval(id);
  }, [value]);
  return <span>{n.toLocaleString()}</span>;
}
```

## 6. Pulse (attention)

```css
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 12px rgba(59, 130, 246, 0); }
}
.pulse { animation: pulse 2s infinite; }
```

Используй на одном CTA, не на каждой кнопке.

## prefers-reduced-motion

Уважай accessibility:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0s !important;
    transition-duration: 0s !important;
  }
}
```

## Антипаттерны

- Анимации длиннее 400мс на UI-feedback → юзер думает что лагает
- Параллакс-эффекты на каждом блоке → headache + JS performance
- Pulse на каждой кнопке → теряет сигнальность
- Hover-эффект меняющий layout (margin / padding) → дёрганье соседей
- Анимация без `prefers-reduced-motion` → ломаешь a11y
- Skeleton дольше 2 сек → юзер думает что зависло, лучше показать «still loading...»
- Scroll-reveal с длинным delay (>200мс) → секции «гонятся» друг за другом
