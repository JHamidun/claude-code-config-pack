---
name: microinteractions
description: "Готовые snippets анимированных микро-фич: skeleton, success-tick, stagger reveal, parallax. Триггеры: «оживи прототип», «hover эффекты»."
---

# Microinteractions

Каждый snippet — копипаст в проект. Минимум зависимостей.

## Skeleton loader

```html
<div class="skel-line" style="width: 60%"></div>
<div class="skel-line" style="width: 80%"></div>
<div class="skel-line" style="width: 40%"></div>
```

```css
.skel-line {
  height: 14px; border-radius: 4px;
  background: linear-gradient(90deg, #eee 0%, #f6f6f6 50%, #eee 100%);
  background-size: 200% 100%;
  animation: skel-pulse 1.4s linear infinite;
  margin-bottom: 8px;
}
@keyframes skel-pulse { 0% { background-position: 200% 0 } 100% { background-position: -200% 0 } }
```

## Success-tick (галочка появляется по SVG-stroke)

```html
<svg class="check" viewBox="0 0 52 52">
  <circle cx="26" cy="26" r="25" fill="none" stroke="#4caf50" stroke-width="2"/>
  <path fill="none" stroke="#4caf50" stroke-width="3" stroke-linecap="round"
        d="M14 27l8 8 16-18"/>
</svg>
```

```css
.check { width: 56px; height: 56px; }
.check circle { stroke-dasharray: 166; stroke-dashoffset: 166;
  animation: stroke .6s cubic-bezier(0.65,0,0.45,1) forwards; }
.check path { stroke-dasharray: 48; stroke-dashoffset: 48;
  animation: stroke .3s cubic-bezier(0.65,0,0.45,1) .6s forwards; }
@keyframes stroke { to { stroke-dashoffset: 0 } }
```

## Counter (число анимируется до значения)

```html
<span data-counter="42893">0</span>
```

```js
document.querySelectorAll('[data-counter]').forEach(el => {
  const target = +el.dataset.counter;
  const start = performance.now();
  const dur = 1200;
  const fmt = n => n.toLocaleString('ru-RU');
  function tick(t) {
    const p = Math.min(1, (t - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(Math.round(target * eased));
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
});
```

## Stagger reveal (элементы появляются по очереди)

```css
.reveal > * {
  opacity: 0; transform: translateY(20px);
  animation: reveal .5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
.reveal > *:nth-child(1) { animation-delay: 0.05s }
.reveal > *:nth-child(2) { animation-delay: 0.10s }
.reveal > *:nth-child(3) { animation-delay: 0.15s }
.reveal > *:nth-child(4) { animation-delay: 0.20s }
.reveal > *:nth-child(5) { animation-delay: 0.25s }
@keyframes reveal { to { opacity: 1; transform: none } }
```

Запуск через intersection observer:

```js
new IntersectionObserver(es => {
  es.forEach(e => e.isIntersecting && e.target.classList.add('reveal'));
}, { threshold: 0.2 }).observe(document.querySelector('.list'));
```

## Draggable list (HTML5 native)

```html
<ul id="list">
  <li draggable="true">Один</li>
  <li draggable="true">Два</li>
  <li draggable="true">Три</li>
</ul>
```

```js
const list = document.getElementById('list');
let dragging = null;
list.addEventListener('dragstart', e => { dragging = e.target; e.target.style.opacity = .4; });
list.addEventListener('dragend',   e => { e.target.style.opacity = ''; });
list.addEventListener('dragover',  e => {
  e.preventDefault();
  const after = [...list.children].find(c => {
    const r = c.getBoundingClientRect();
    return e.clientY < r.top + r.height / 2 && c !== dragging;
  });
  if (after) list.insertBefore(dragging, after);
  else list.appendChild(dragging);
});
```

## Infinite scroll

```js
const sentinel = document.querySelector('#load-more-sentinel');
let page = 1;
new IntersectionObserver(async es => {
  if (es[0].isIntersecting) {
    const items = await fetch(`/api/items?page=${++page}`).then(r => r.json());
    items.forEach(renderItem);
    if (items.length < 20) sentinel.remove();   // конец
  }
}, { rootMargin: '200px' }).observe(sentinel);
```

## Parallax (мягкий, не агрессивный)

```css
.parallax { transform: translateY(var(--p, 0px)); transition: transform .1s linear; }
```

```js
addEventListener('scroll', () => {
  const y = window.scrollY;
  document.querySelectorAll('[data-parallax]').forEach(el => {
    const factor = +el.dataset.parallax || 0.3;
    el.style.setProperty('--p', `${-y * factor}px`);
  });
}, { passive: true });
```

```html
<img src="hero.jpg" data-parallax="0.4" class="parallax">
```

## Toast queue

```js
const toasts = [];
function toast(msg, ms = 2500) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  el.style.transform = `translateY(${toasts.length * 60}px)`;
  document.body.appendChild(el);
  toasts.push(el);
  requestAnimationFrame(() => el.classList.add('on'));
  setTimeout(() => {
    el.classList.remove('on');
    el.addEventListener('transitionend', () => {
      el.remove();
      const idx = toasts.indexOf(el);
      toasts.splice(idx, 1);
      toasts.forEach((t,i) => t.style.transform = `translateY(${i*60}px)`);
    }, { once: true });
  }, ms);
}
```

## Что НЕ делать

- ❌ Loop-анимации без триггера. Раздражают.
- ❌ Анимация всего сразу. Глаз не знает, на что смотреть.
- ❌ Длительность >300ms для UI-микро. Только для больших переходов экранов.
- ❌ Без `prefers-reduced-motion` опт-аут.

## prefers-reduced-motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Legacy reference

Прежняя расширенная версия скилла сохранена целиком в `references/legacy-microinteractions.md`. Секции там: 1. Skeleton loader, 2. Hover effects, 3. Scroll-reveal (intersection observer), 4. Click ripple (Material-style), 5. Number ticker, 6. Pulse (attention), prefers-reduced-motion, Антипаттерны.
