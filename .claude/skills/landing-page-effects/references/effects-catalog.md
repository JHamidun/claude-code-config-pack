# Каталог эффектов 1-35: канонические реализации

Эффекты 1-21 — обкатанные, проверены на живых страницах.
Эффекты 22-35 — трендовые, реализации даны, но на потоке ещё не гонялись.

> Свой эталонный лендинг (страница, где эффекты стоят вместе и видно, как они
> сочетаются) заведи сам и пропиши путь к нему в `references/reference-page.md` —
> дальше сверяйся с ним, а не с этим каталогом построчно.

## 1. PRELOADER
```css
.preloader {
    position: fixed;
    inset: 0;
    background: var(--bg-primary);
    z-index: 10000;
    transition: opacity 0.5s, visibility 0.5s;
}
.preloader.hidden { opacity: 0; visibility: hidden; }

@keyframes loading {
    0% { width: 0; }
    100% { width: 100%; }
}
```

## 2. CUSTOM CURSOR
```css
.cursor {
    width: 40px;
    height: 40px;
    border: 1px solid var(--neon-lime);
    border-radius: 50%;
    position: fixed;
    pointer-events: none;
    z-index: 9999;
    mix-blend-mode: difference;
}
```

## 3. ANIMATED GRAIN
```css
.grain {
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.03;
    animation: grain-move 0.5s steps(10) infinite;
}
```

## 4. PROGRESS BAR
```css
.page-progress {
    position: fixed;
    top: 0; left: 0;
    height: 3px;
    background: linear-gradient(90deg, #2d2fe8, #818cf8, #22d3ee);
    animation: progress-load 1.5s ease-out forwards;
}
```

## 5. GLITCH TEXT (автоматический)
```css
.glitch-text::before {
    animation: glitch-1 3s infinite;
    color: var(--neon-pink);
    z-index: -1;
}
.glitch-text::after {
    animation: glitch-2 3s infinite;
    color: var(--neon-cyan);
    z-index: -2;
}
```

## 6. GLITCH HOVER
```css
.glitch-hover:hover {
    animation: glitch-shake 0.2s infinite;
}
.glitch-hover:hover::before {
    animation: glitch-clip-hover-1 0.4s steps(2) infinite;
    color: var(--neon-cyan);
    text-shadow: 2px 0 var(--neon-cyan);
    opacity: 0.8;
}
```

## 7. NEON BUTTON
```css
.btn-neon:hover {
    background: #ffffff;
    color: #050510;
    box-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
    transform: scale(1.05);
}
```

## 8. RIPPLE EFFECT
```css
@keyframes ripple-effect {
    to { transform: scale(4); opacity: 0; }
}
```

## 9. MARQUEE
```css
.marquee-track {
    animation: marquee 20s linear infinite;
}
@keyframes marquee {
    100% { transform: translateX(-50%); }
}
```

## 10. BOUNCING DOT
```css
.bouncing-dot {
    animation: bounce-vertical 0.5s ease-in-out infinite;
}
.bouncing-dot-container {
    animation: bounce-horizontal 8s ease-in-out infinite;
}
```

## 11. 3D CARD TILT
```javascript
card.addEventListener('mousemove', (e) => {
    const rotateX = (y - centerY) / 10;
    const rotateY = (centerX - x) / 10;
    inner.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
});
```

## 12. TYPEWRITER
```css
.typewriter-text {
    animation: typing 3s steps(40) forwards, blink-cursor 0.75s step-end infinite;
}
```

## 13. SCROLL REVEAL
```css
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s, transform 0.6s;
}
.reveal.active {
    opacity: 1;
    transform: translateY(0);
}
```

## 14. HORIZONTAL SCROLL
```css
.horizontal-scroll-track {
    animation: scroll-horizontal 30s linear infinite;
}
```

## 15. COUNTER ANIMATION
```javascript
const easeOut = 1 - Math.pow(1 - progress, 3);
element.textContent = Math.floor(easeOut * target).toLocaleString();
```

## 16. PIXEL GRID PATTERN
```css
.pixel-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 3px;
}
.pixel-cell.active {
    background: var(--neon-lime);
    box-shadow: 0 0 8px rgba(129, 140, 248, 0.5);
}
```

## 17. FLOATING STICKERS
```css
@keyframes float-badge {
    0%, 100% { transform: translateY(0) rotate(-2deg); }
    50% { transform: translateY(-10px) rotate(2deg); }
}
```

## 18. TERMINAL WINDOW
```css
.terminal-dot.red { background: #ff5f56; }
.terminal-dot.yellow { background: #ffbd2e; }
.terminal-dot.green { background: #27ca40; }
```

## 19. SCROLL INDICATOR (Mouse)
```css
@keyframes scroll-wheel {
    0%, 100% { transform: translateY(0); opacity: 1; }
    50% { transform: translateY(10px); opacity: 0; }
}
```

## 20. TEXT SCRAMBLE
```javascript
class TextScramble {
    chars = '!<>-_\\/[]{}—=+*^?#';
    // Постепенная замена букв на случайные символы
}
```

## 21. CONFETTI
```css
@keyframes confetti-fall {
    0% { transform: translateY(-100%) rotate(0deg); }
    100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}
```

---

# Трендовые эффекты 2025 (22-35, не реализованы в эталоне)

## 22. SCROLL-DRIVEN ANIMATIONS (CSS native)
```css
@keyframes fly-by {
    0% { transform: translateX(-100vw) scale(0.5); opacity: 0; }
    50% { transform: translateX(0) scale(1); opacity: 1; }
    100% { transform: translateX(100vw) scale(0.5); opacity: 0; }
}

.fly-object {
    animation: fly-by linear;
    animation-timeline: scroll();
    animation-range: entry 0% exit 100%;
}
```

## 23. PARALLAX LAYERS (объекты пролетают мимо)
```css
.parallax-container {
    perspective: 1000px;
    overflow: hidden;
}

.parallax-layer-1 { transform: translateZ(-100px) scale(1.1); }
.parallax-layer-2 { transform: translateZ(-200px) scale(1.2); }
.parallax-layer-3 { transform: translateZ(-300px) scale(1.3); }
```

```javascript
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    document.querySelectorAll('.parallax-object').forEach((obj, i) => {
        const speed = obj.dataset.speed || (i + 1) * 0.5;
        obj.style.transform = `translateY(${scrolled * speed}px)`;
    });
});
```

## 24. SCROLL-TRIGGERED 3D OBJECTS
```css
.scroll-3d-object {
    transform-style: preserve-3d;
    transition: transform 0.3s;
}

.scroll-3d-object.in-view {
    animation: rotate-3d 10s linear infinite;
}

@keyframes rotate-3d {
    0% { transform: rotateY(0deg) rotateX(10deg); }
    100% { transform: rotateY(360deg) rotateX(10deg); }
}
```

## 25. MAGNETIC ELEMENTS
```javascript
document.querySelectorAll('.magnetic').forEach(elem => {
    elem.addEventListener('mousemove', (e) => {
        const rect = elem.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        elem.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
    });
    elem.addEventListener('mouseleave', () => {
        elem.style.transform = 'translate(0, 0)';
    });
});
```

## 26. LENIS SMOOTH SCROLL
```javascript
import Lenis from '@studio-freight/lenis';

const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
});

function raf(time) {
    lenis.raf(time);
    requestAnimationFrame(raf);
}
requestAnimationFrame(raf);
```

## 27. GSAP SCROLL TRIGGER
```javascript
gsap.registerPlugin(ScrollTrigger);

// Объект влетает слева при скролле
gsap.from('.fly-left', {
    x: -200,
    opacity: 0,
    scrollTrigger: {
        trigger: '.fly-left',
        start: 'top 80%',
        end: 'top 20%',
        scrub: 1,
    }
});

// Объект пролетает мимо
gsap.to('.fly-through', {
    x: '200vw',
    scrollTrigger: {
        trigger: '.section',
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
    }
});
```

## 28. SPLIT TEXT ANIMATION
```javascript
const text = element.textContent;
element.innerHTML = text.split('').map((char, i) =>
    `<span style="animation-delay: ${i * 0.05}s">${char}</span>`
).join('');
```

```css
.split-text span {
    display: inline-block;
    opacity: 0;
    transform: translateY(50px) rotateX(-90deg);
    animation: letter-appear 0.5s forwards;
}

@keyframes letter-appear {
    to { opacity: 1; transform: translateY(0) rotateX(0); }
}
```

## 29. MORPHING SHAPES
```css
.morph-shape {
    animation: morph 8s ease-in-out infinite;
}

@keyframes morph {
    0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
    25% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
    50% { border-radius: 50% 60% 30% 60% / 30% 60% 70% 40%; }
    75% { border-radius: 60% 40% 60% 30% / 70% 30% 50% 60%; }
}
```

## 30. GRADIENT ANIMATION
```css
.animated-gradient {
    background: linear-gradient(-45deg, #818cf8, #22d3ee, #f472b6, #a78bfa);
    background-size: 400% 400%;
    animation: gradient-shift 15s ease infinite;
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
```

## 31. REVEAL ON SCROLL (с маской)
```css
.reveal-mask {
    clip-path: inset(100% 0 0 0);
    transition: clip-path 1s cubic-bezier(0.77, 0, 0.175, 1);
}

.reveal-mask.visible {
    clip-path: inset(0 0 0 0);
}
```

## 32. FLOATING PARTICLES (Three.js)
```javascript
const particles = new THREE.Points(
    new THREE.BufferGeometry(),
    new THREE.PointsMaterial({ size: 0.02, color: 0x818cf8 })
);
scene.add(particles);

function animate() {
    particles.rotation.y += 0.001;
    requestAnimationFrame(animate);
}
```

## 33. LIQUID DISTORTION
```css
.liquid {
    filter: url(#liquid-filter);
}
```
```html
<svg>
    <filter id="liquid-filter">
        <feTurbulence type="fractalNoise" baseFrequency="0.01" numOctaves="3" />
        <feDisplacementMap in="SourceGraphic" scale="30" />
    </filter>
</svg>
```

## 34. CURSOR TRAIL
```javascript
const trail = [];
document.addEventListener('mousemove', (e) => {
    const dot = document.createElement('div');
    dot.className = 'trail-dot';
    dot.style.left = e.clientX + 'px';
    dot.style.top = e.clientY + 'px';
    document.body.appendChild(dot);
    trail.push(dot);

    setTimeout(() => {
        dot.remove();
        trail.shift();
    }, 500);
});
```

## 35. SCROLL VELOCITY EFFECTS
```javascript
let lastScroll = 0;
let velocity = 0;

window.addEventListener('scroll', () => {
    velocity = window.scrollY - lastScroll;
    lastScroll = window.scrollY;

    // Быстрый скролл = больше эффект
    document.querySelectorAll('.velocity-element').forEach(el => {
        el.style.transform = `skewY(${velocity * 0.1}deg)`;
    });
});
```

---

# Библиотеки для эффектов

| Библиотека | Назначение |
|------------|-----------|
| **GSAP** | Анимации, ScrollTrigger |
| **Lenis** | Smooth scroll |
| **Three.js** | 3D эффекты |
| **Framer Motion** | React анимации |
| **Locomotive Scroll** | Parallax, smooth scroll |
| **Barba.js** | Page transitions |
| **Splitting.js** | Text splitting |
| **Rellax.js** | Простой parallax |
