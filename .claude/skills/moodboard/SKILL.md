---
name: moodboard
description: "HTML-мудборд из 5-15 референсов с палитрой из картинок — согласовать визуальный язык на старте. Триггеры: «собери референсы», «извлеки палитру»."
---

# Moodboard

Цель — за 1 страницу показать, **в какую сторону** идём, до того как тратить время на финальный дизайн.

## Откуда брать референсы — библиотека под тип продукта

Пользователь редко приносит ссылки сам, и «поищи красивое» — не поиск. **Библиотеку
выбирают по типу продукта, а не по красоте картинок:** экран банковского приложения и
главная ресторана — разные задачи. Типовая ошибка — притащить эффектный концепт с
Dribbble туда, где нужна спокойная B2B-форма.

| Тип задачи | Библиотека | Что там искать |
|---|---|---|
| Мобильное приложение, полный сценарий: регистрация, оплата, бронирование | [Mobbin](https://mobbin.com/) | Реальные экраны и последовательности из выпущенных продуктов (напр. как Revolut и Wise объясняют первый перевод). Начинался как mobile, сейчас есть и web |
| Путь пользователя целиком, часто видео | [Page Flows](https://pageflows.com/) | Не один экран, а запись всего флоу с пояснениями — пройти чужой onboarding от первого запуска до готового аккаунта |
| SaaS-продукт: кабинет, dashboard, настройки, pricing | [SaaSFrame](https://www.saasframe.io/) | Разбито по страницам, блокам и шагам — можно сравнить 20 pricing-страниц или дашбордов подряд |
| Web-продукт и рабочие экраны: навигация, таблицы, формы, B2B | [Refero](https://refero.design/) | Спокойные реальные интерфейсы вместо концептов |
| Обычный лендинг по отрасли: агентство, ресторан, курс, портфолио | [Land-book](https://land-book.com/) | **Начинать здесь.** Фильтры по отрасли, стилю и типу страницы — напр. пять сайтов частных школ |
| Лендинг поблочно: hero, pricing, отдельные секции | [Lapa Ninja](https://www.lapa.ninja/) | 30 вариантов первого экрана за один заход |
| Смелое направление: сильная типографика, движение, fashion/портфолио | [Recent Design](https://recent.design/) | Бывший Godly — выразительные сайты, когда нужен более дерзкий вектор |
| AI-приложение с загрузкой фото, голосом, генерацией — непривычная мультимодальная раскладка | [AI Studio App Gallery](https://aistudio.google.com/apps?source=showcase&showcaseTag=featured) | Витрина апплетов Google с проработанным UI. Remix даёт редактируемую копию в AI Studio Build — видно, как устроены промпты и компоненты |

Норма набора: **5-10 референсов, из них 3-5 действительно близких**. Не смешивай все
семь источников в один мудборд — получится каша, а не направление.

Смежное:
- референс назван брендом («как у Linear») → `design-md-brands`, готовый DESIGN.md быстрее скрейпа;
- есть конкретный URL → `brand-extractor` вытащит цвета/шрифты/копирайт;
- нужны не интерфейсы, а ассеты (шрифты, стоки, иконки, палитры, мокапы) → `design-orchestrator/references/design-services-catalog.md`, 88 сервисов.

**Этика:** референс — источник решений (ритм, плотность, структура блоков), а не
исходник для копирования. Воспроизводить чужой UI один-в-один нельзя — см. `content-policy`.

## Шаги

1. Попроси у пользователя 5-15 референсов: ссылки, картинки, скриншоты. Нет своих — набери сам по таблице выше, отталкиваясь от типа продукта.
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

## Скриншот → описание стиля для промпта

Палитра из скрипта выше даёт цвета, но не язык: плотность, обработку карточек, иерархию
шрифтов. Когда референс нужен как **направление**, а не как раскладка для копирования,
пусть модель с изображениями опишет дизайн-систему скриншота словами. Готовое описание
вставляется в промпт сборки дословно и работает точнее, чем «сделай как на картинке».

Промпт из гайда Google AI Studio (16.09.2026), дословно:

```text
Analyze this website screenshot and describe its visual design system in 5-6 concise
sentences. Return your answer as a prompt that I can directly put into an AI coding tool
like AI Studio. Include specific details on its color palette (with hex approximations),
typography hierarchy, card border treatments, spacing density, and overall aesthetic mood
(e.g., editorial minimalist, dark glassmorphism, or neo-brutalist).
```

То же по-русски, для русскоязычного брифа:

```text
Разбери этот скриншот сайта и опиши его визуальную дизайн-систему в 5–6 коротких
предложениях. Верни ответ как готовый промпт для ИИ-инструмента, который пишет код.
Укажи: палитру с примерными hex, иерархию шрифтов, как оформлены карточки (рамки, тени,
скругления), плотность отступов и общее настроение (например, editorial-минимализм,
тёмный glassmorphism, необрутализм).
```

Несколько скриншотов — одним запросом, тогда описание сводит их в одно направление.
Модель — любая с изображениями; у Google для разбора UI по скриншоту сильнее всего
`gemini-3.8-flash` и `gemini-3.7-flash` (так в гайде). Описание кладётся в сводку
мудборда рядом с палитрой. Разбор всего гайда — `design-orchestrator/references/ai-studio-ui-polish.md`.

## После мудборда

- Спроси у пользователя: «Какие 3 референса самые точные?»
- На основе ответа выбери `frontend-design`-направление и дальше — `color-system-builder`, `type-scale`.
- **Сохрани** мудборд как часть проекта — будущие правки сверяй с ним.

## Антипаттерны

- ❌ Делать мудборд из 50 картинок. Превращается в кашу. 8-12 — оптимум.
- ❌ Использовать unsplash-стоки. Берите конкретные референсы из реальных сайтов / приложений / журналов.
- ❌ Брать библиотеку не под тип продукта: лендинг-галерея под B2B-форму или Dribbble-концепт под платёжный флоу. Сначала тип задачи — потом библиотека.
- ❌ Соглашаться на «всё нравится». Выбор — часть согласования.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-moodboard.md`. Секции там: Каркас, Извлечение палитры из изображений, Tags — что это, Использование с design-system-create, Антипаттерны.
