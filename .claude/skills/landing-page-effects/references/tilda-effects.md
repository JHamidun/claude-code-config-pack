# Tilda-эффекты (36-45): готовые реализации

Источник: разбор выгрузки готового сайта на Tilda (папка публикации). Формат SBS-параметров — в теле навыка.

## 36. TILDA FADE ANIMATIONS
```html
<div data-animate-style="fadeinup">Fade in from bottom</div>
<div data-animate-style="fadeindown">Fade in from top</div>
<div data-animate-style="fadeinleft">Fade in from left</div>
<div data-animate-style="fadeinright">Fade in from right</div>
<div data-animate-style="zoomin">Zoom in</div>
<div data-animate-style="zoomout">Zoom out</div>
```

```css
.t-animate_fadeinup {
    opacity: 0;
    transform: translateY(40px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}
.t-animate_fadeinup.t-animate_visible {
    opacity: 1;
    transform: translateY(0);
}

.t-animate_fadeindown {
    opacity: 0;
    transform: translateY(-40px);
    transition: opacity 0.8s ease, transform 0.8s ease;
}
.t-animate_fadeindown.t-animate_visible {
    opacity: 1;
    transform: translateY(0);
}

.t-animate_zoomin {
    opacity: 0;
    transform: scale(0.8);
    transition: opacity 0.8s ease, transform 0.8s ease;
}
.t-animate_zoomin.t-animate_visible {
    opacity: 1;
    transform: scale(1);
}
```

## 38. TILDA BOUNCE EASING
```css
:root {
    --ease-bounce-fin: cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bounce-element {
    animation: tilda-bounce 0.7s var(--ease-bounce-fin) forwards;
}

@keyframes tilda-bounce {
    0% {
        opacity: 0;
        transform: translateY(30px);
    }
    60% {
        opacity: 1;
        transform: translateY(-5px);
    }
    80% {
        transform: translateY(2px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}
```

## 39. TILDA MARQUEE (Infinite Scroll)
```html
<div data-animate-sbs="on"
     data-animate-sbs-opts='{"mx":-2300,"my":0,"sx":1,"sy":1,"op":1,"ro":0,"ti":15000,"ea":"0","dt":0}'
     data-animate-sbs-repeat="loop">
    Scrolling text...
</div>
```

```css
.tilda-marquee {
    display: flex;
    white-space: nowrap;
    animation: tilda-scroll 15s linear infinite;
}

@keyframes tilda-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.tilda-marquee-track {
    display: flex;
    animation: tilda-marquee-infinite 20s linear infinite;
}

@keyframes tilda-marquee-infinite {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
```

## 40. TILDA SCALE ON HOVER
```html
<div data-animate-sbs-hover="on"
     data-animate-sbs-opts='{"mx":0,"my":0,"sx":1.1,"sy":1.1,"op":1,"ro":0,"ti":200,"ea":"bounceFin","dt":0}'>
    Scales on hover
</div>
```

```css
.tilda-scale-hover {
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tilda-scale-hover:hover {
    transform: scale(1.1);
}
```

## 41. TILDA CHAIN ANIMATIONS
```html
<div data-animate-group="chain">
    <div data-animate-style="fadeinup" data-animate-delay="0">First</div>
    <div data-animate-style="fadeinup" data-animate-delay="100">Second</div>
    <div data-animate-style="fadeinup" data-animate-delay="200">Third</div>
</div>
```

```css
.chain-item {
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.5s ease, transform 0.5s ease;
}

.chain-item:nth-child(1) { transition-delay: 0ms; }
.chain-item:nth-child(2) { transition-delay: 100ms; }
.chain-item:nth-child(3) { transition-delay: 200ms; }
.chain-item:nth-child(4) { transition-delay: 300ms; }
.chain-item:nth-child(5) { transition-delay: 400ms; }

.chain-item.visible {
    opacity: 1;
    transform: translateY(0);
}
```

## 42. TILDA CTA BUTTON
```css
.cta-btn--tilda {
    color: #ffffff;
    background-color: #2d2fe8;
    border-radius: 10px;
    font-family: 'Manrope', system-ui, sans-serif;
    font-weight: 600;
    padding: 15px 30px;
    border: none;
    cursor: pointer;
    transition: background-color 200ms ease-in-out, transform 200ms ease;
}

.cta-btn--tilda:hover {
    background-color: #010334;
    transform: translateY(-2px);
}

.cta-btn--tilda:focus-visible {
    outline: 2px solid #818cf8;
    outline-offset: 2px;
}
```

## 43. TILDA BURGER MENU ANIMATION
```css
.t-menuburger__line {
    width: 30px;
    height: 2px;
    background: #fff;
    transition: transform 0.3s, opacity 0.3s;
}

.t-menuburger_open .t-menuburger__line:nth-child(1) {
    transform: translateY(8px) rotate(45deg);
}
.t-menuburger_open .t-menuburger__line:nth-child(2) {
    opacity: 0;
}
.t-menuburger_open .t-menuburger__line:nth-child(3) {
    transform: translateY(-8px) rotate(-45deg);
}

@keyframes t-menuburger-anim {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}
```

## 44. TILDA SCROLL INDICATOR
```css
.tilda-scroll-indicator {
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
}

.tilda-scroll-circle {
    width: 30px;
    height: 50px;
    border: 2px solid rgba(255,255,255,0.3);
    border-radius: 15px;
    position: relative;
}

.tilda-scroll-dot {
    width: 6px;
    height: 6px;
    background: #fff;
    border-radius: 50%;
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    animation: tilda-scroll-anim 1.5s infinite;
}

@keyframes tilda-scroll-anim {
    0% { opacity: 1; top: 8px; }
    100% { opacity: 0; top: 30px; }
}
```

## 45. TILDA INTERSECTION OBSERVER (JS-инициализация)
```javascript
// Initialize Tilda-style animations
function initTildaAnimations() {
    const animatedElements = document.querySelectorAll('[data-animate-style]');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.animateDelay || 0;
                setTimeout(() => {
                    entry.target.classList.add('t-animate_visible');
                }, parseInt(delay));
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    animatedElements.forEach(el => observer.observe(el));
}

// SBS Animation Handler
function initSBSAnimations() {
    document.querySelectorAll('[data-animate-sbs="on"]').forEach(el => {
        const opts = JSON.parse(el.dataset.animateSbsOpts || '{}');
        const isLoop = el.dataset.animateSbsRepeat === 'loop';

        const duration = opts.ti || 1000;
        const easing = opts.ea === 'bounceFin'
            ? 'cubic-bezier(0.34, 1.56, 0.64, 1)'
            : 'linear';

        el.style.transition = `transform ${duration}ms ${easing}, opacity ${duration}ms ${easing}`;

        if (isLoop) {
            el.style.animation = `sbs-loop ${duration}ms ${easing} infinite`;
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initTildaAnimations();
    initSBSAnimations();
});
```
