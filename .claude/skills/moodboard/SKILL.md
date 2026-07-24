---
name: moodboard
description: Собрать HTML-мудборд из 5-15 референсов с подписями и палитрой, извлечённой из изображений.
when_to_use: Старт нового проекта без чёткого направления, нужно согласовать визуальный язык с пользователем.
---

# Moodboard

Цель — за 1 страницу показать, **в какую сторону** идём, до того как тратить время на финальный дизайн.

## Шаги

1. Попроси у пользователя 5-15 референсов: ссылки, картинки, скриншоты.
2. Сохрани все в `moodboard/refs/`.
3. Из каждой картинки извлеки 3-5 цветов (см. ниже).
4. Собери HTML в pinterest-стиле (masonry-grid).
5. Добавь общую сводку: typography candidates, dominant palette, mood tags.

## Структура HTML

```html
<main class="moodboard">
  <header>
    <h1>Moodboard — <span>проект</span></h1>
    <p class="brief">Тон: спокойный, editorial. Один акцент — тёплый.</p>
  </header>

  <section class="palette">
    <div class="swatch" style="background:#1c1a16"><span>#1c1a16</span></div>
    <div class="swatch" style="background:#f3eee5"><span>#f3eee5</span></div>
    <div class="swatch" style="background:#a23f2c"><span>#a23f2c</span></div>
  </section>

  <section class="grid">
    <figure>
      <img src="refs/1.jpg" alt="">
      <figcaption>
        <span>Source · architectural</span>
        <span class="tags">large type · neutral</span>
        <span class="row">
          <i style="background:#222"></i><i style="background:#e8e2d4"></i><i style="background:#7a6f5e"></i>
        </span>
      </figcaption>
    </figure>
    <!-- ...повтори -->
  </section>
</main>
```

CSS:

```css
.moodboard { padding: 48px; font-family: ui-monospace, monospace; background: #f4f4f2; }
.moodboard header h1 { font-family: serif; font-size: 56px; margin: 0 0 8px; }
.moodboard header h1 span { font-style: italic; color: #888; }
.brief { font-size: 14px; max-width: 60ch; line-height: 1.5; }

.palette { display: flex; gap: 12px; margin: 32px 0; }
.swatch  { width: 96px; height: 96px; display: grid; place-items: end start; padding: 8px; color: #fff; mix-blend-mode: difference; font-size: 11px; }

.grid {
  column-count: 4; column-gap: 16px;
}
.grid figure { break-inside: avoid; margin: 0 0 16px; background: #fff; padding: 8px; }
.grid img { width: 100%; display: block; }
.grid figcaption {
  display: grid; gap: 4px; padding: 8px 4px 0;
  font-size: 11px; color: #555;
}
.tags { color: #999; }
.row  { display: flex; gap: 4px; margin-top: 4px; }
.row i { width: 16px; height: 16px; border: 1px solid rgba(0,0,0,.06); }

@media (max-width: 1200px) { .grid { column-count: 3; } }
@media (max-width: 800px)  { .grid { column-count: 2; } }
```

## Извлечение палитры из картинки

`templates/extract-palette.mjs`:

```js
import fs from 'node:fs/promises';
import path from 'node:path';
import { createCanvas, loadImage } from 'canvas';   // npm i canvas

const dir = process.argv[2] || 'moodboard/refs';
const k = +(process.argv[3] || 5);

for (const f of await fs.readdir(dir)) {
  if (!/\.(jpg|jpeg|png|webp)$/i.test(f)) continue;
  const img = await loadImage(path.join(dir, f));
  const w = 80, h = Math.round(80 * img.height / img.width);
  const c = createCanvas(w, h); const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0, w, h);
  const data = ctx.getImageData(0, 0, w, h).data;

  // K-means crude
  const points = [];
  for (let i = 0; i < data.length; i += 4) {
    if (data[i+3] < 100) continue;
    points.push([data[i], data[i+1], data[i+2]]);
  }
  let centers = Array.from({length: k}, () => points[Math.floor(Math.random()*points.length)]);
  for (let iter = 0; iter < 8; iter++) {
    const buckets = Array.from({length: k}, () => []);
    for (const p of points) {
      let best = 0, bd = Infinity;
      for (let i = 0; i < k; i++) {
        const d = (p[0]-centers[i][0])**2 + (p[1]-centers[i][1])**2 + (p[2]-centers[i][2])**2;
        if (d < bd) { bd = d; best = i; }
      }
      buckets[best].push(p);
    }
    centers = buckets.map(b => {
      if (!b.length) return centers[0];
      const sum = b.reduce((a,x) => [a[0]+x[0], a[1]+x[1], a[2]+x[2]], [0,0,0]);
      return [sum[0]/b.length|0, sum[1]/b.length|0, sum[2]/b.length|0];
    });
  }
  const hex = centers.map(c => '#' + c.map(n => n.toString(16).padStart(2,'0')).join(''));
  console.log(f, hex);
}
```

## После мудборда

- Спроси у пользователя: «Какие 3 референса самые точные?»
- На основе ответа выбери `frontend-design`-направление и дальше — `color-system-builder`, `type-scale`.
- **Сохрани** мудборд как часть проекта — будущие правки сверяй с ним.

## Антипаттерны

- ❌ Делать мудборд из 50 картинок. Превращается в кашу. 8-12 — оптимум.
- ❌ Использовать unsplash-стоки. Берите конкретные референсы из реальных сайтов / приложений / журналов.
- ❌ Соглашаться на «всё нравится». Выбор — часть согласования.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-moodboard.md`. Секции там: Каркас, Извлечение палитры из изображений, Tags — что это, Использование с design-system-create, Антипаттерны.
