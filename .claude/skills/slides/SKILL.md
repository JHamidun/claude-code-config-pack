---
name: slides
description: Презентация в HTML. 1920×1080 канва, навигация стрелками, переход через ?slide=N в URL. Каждый слайд — section с фиксированными размерами. Поверх можно стекать deck-themes (5 готовых тем) и animations.
when_to_use: Юзер просит «сделай дек», «слайды», «презентация», «pitch deck», «keynote». Перед чем угодно про слайды (deck-themes, export-pdf, export-pptx) — этот скилл первый.
---

# Slides

HTML-презентация: один файл, навигация со стрелок, фиксированный canvas 1920×1080.

## Каркас

```html
<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title><Title></title>
<link rel="stylesheet" href="styles/tokens.css">
<style>
  html, body { margin: 0; padding: 0; background: #000; overflow: hidden; }
  .deck { width: 100vw; height: 100vh; position: relative; }
  .slide {
    position: absolute; inset: 0;
    width: 1920px; height: 1080px;
    transform-origin: 0 0; opacity: 0; pointer-events: none;
    transition: opacity .25s ease;
    background: var(--bg, #fff); color: var(--ink, #111);
    font-family: var(--font-body, "Inter", system-ui, sans-serif);
    padding: 96px;
  }
  .slide.active { opacity: 1; pointer-events: auto; }
  .slide .num { position: absolute; bottom: 32px; right: 48px; font: 600 14px/1 monospace; opacity: 0.4; }
</style></head>
<body>
  <div class="deck" id="deck">
    <section class="slide" data-i="1">
      <h1 style="font:700 96px/1 var(--font-head, 'Inter Tight'); letter-spacing:-0.04em">
        Заголовок<br/>дека
      </h1>
      <p style="font-size:32px;color:#666;margin-top:24px;max-width:1200px">
        Подзаголовок: одна строка про сабж.
      </p>
      <div class="num">01</div>
    </section>

    <section class="slide" data-i="2">
      <!-- следующий слайд -->
      <div class="num">02</div>
    </section>
  </div>

  <script>
    (function(){
      const deck = document.getElementById('deck');
      const slides = [...deck.querySelectorAll('.slide')];
      const total = slides.length;
      function fit() {
        // Вписать 1920×1080 канву в текущий viewport
        const sx = window.innerWidth / 1920, sy = window.innerHeight / 1080;
        const s = Math.min(sx, sy);
        const left = (window.innerWidth - 1920 * s) / 2;
        const top = (window.innerHeight - 1080 * s) / 2;
        slides.forEach(el => el.style.transform = `translate(${left}px, ${top}px) scale(${s})`);
      }
      let i = +new URL(location).searchParams.get('slide') || 1;
      function go(n) {
        i = Math.max(1, Math.min(total, n));
        slides.forEach(el => el.classList.toggle('active', +el.dataset.i === i));
        history.replaceState({}, '', `?slide=${i}`);
      }
      window.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ') go(i + 1);
        else if (e.key === 'ArrowLeft') go(i - 1);
        else if (e.key === 'Home') go(1);
        else if (e.key === 'End') go(total);
      });
      window.addEventListener('resize', fit);
      fit(); go(i);
    })();
  </script>
</body></html>
```

## Правила слайдов

| Что | Минимум | Дефолт | Максимум |
|---|---|---|---|
| Текст body | 24px | 32px | 48px |
| Заголовок | 48px | 80-96px | 144px |
| Бок-отступы | 64px | 96px | 128px |
| Слов в заголовке | 1 | 3-7 | 12 |
| Bullet-points в списке | — | 3-5 | 7 |

**1920×1080 — canvas-base.** Текст менее 24px не читается с дальних рядов.

## Структура дека (типовая)

```
01. Cover               — заголовок + подзаголовок + автор + дата
02. The problem         — что болит, в одной фразе + 1 цифра
03. Why now             — почему сейчас, не раньше / позже
04. Our solution        — суть, 1-3 ключевых слова
05. Demo / how it works — скриншот / схема / гифка
06. Traction / proof    — цифры / клиенты / отзыв
07. Market              — TAM/SAM/SOM или просто размер
08. Team                — фото + 1 строка про каждого
09. Ask / next steps    — деньги / партнёрство / что просим
10. Thank you           — контакты + CTA
```

Не обязательно 10 слайдов. Pitch — 8-12. Презентация на конф — 15-25. Workshop — 30+.

## Стек со связанными скиллами

- `deck-themes` — 5 готовых CSS-тем (minimal/editorial/dark/data/brutalist) поверх каркаса
- `placeholders` — стандартные плейсхолдеры для иллюстраций
- `animations` — таймлайн-движок для motion внутри слайда
- `export-pdf` — Playwright headless → PDF
- `export-pptx` — screenshots → PPTX
- `pptx-editable-extractor` — нативные текст-боксы → редактируемый PPTX
- `verifier` — открыть в headless, проверить консоль

## URL-навигация

`?slide=N` в URL → линкуешься на конкретный слайд. Полезно для шеринга.

## Антипаттерны

- Текст 16px на слайде → не читается на проекторе
- Wall of text (>50 слов на слайде) → никто не читает
- 6+ цветов на слайде → визуальный шум
- Эмодзи 🚀💡✨ как декорация → AI-tell, корпоративная клишированность
- Картинки уровня stock-фото без обработки → выглядит как шаблон
- Заголовок «Welcome» / «Thank you» в стандартном шрифте → 3-сек слайд впустую
- Нумерация слайдов как «Slide 5» вместо «05 / 12» → не помогает понять прогресс
