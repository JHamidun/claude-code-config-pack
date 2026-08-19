---
name: wireframe
description: "Много идей в низкой детализации на одном листе — скелет до хай-фай. Триггеры: «вайрфрейм», «грубый каркас», «lo-fi»."
---

# Wireframe

Цель — **много идей быстро**, не одна красивая. Wireframe-этап нужен, чтобы пользователь и ты согласовали структуру до того, как ты потратишь время на пиксели.

## Правила

- **Низкая детализация.** Серые блоки, моноширинный шрифт, минимум цвета (только чёрный + один акцент для CTA).
- **Минимум 4–8 вариантов** на одном листе.
- **Каждый вариант явно отличается** по одной оси (структура, иерархия, плотность, парадигма).
- **Без шрифтовой работы.** Один моно-шрифт на всё. Чтобы взгляд не цеплялся за typography choices, а только за структуру.
- **Подписи под каждым вариантом.** «A — hero сверху, фичи сеткой 3×2», не «Variant 1».

## Каркас

Используй `templates/wireframe-grid.html`:

```html
<section class="wireframe-grid">
  <article class="wf">
    <header><h3>A — hero + features 3×2</h3></header>
    <div class="frame">
      <div class="block hero">HERO</div>
      <div class="block grid">FEATURES (3×2)</div>
      <div class="block band">CTA BAND</div>
    </div>
  </article>
  <article class="wf">
    <header><h3>B — split hero, features столбцом</h3></header>
    ...
  </article>
</section>
```

CSS:

```css
.wireframe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 32px; padding: 32px;
  background: #ececec;
  font-family: ui-monospace, monospace;
}
.wf header h3 { font-size: 12px; margin: 0 0 8px; color: #333; }
.wf .frame {
  background: #fff;
  border: 1px solid #ccc;
  aspect-ratio: 4/3;
  display: grid; grid-template-rows: auto 1fr auto; gap: 8px;
  padding: 8px;
}
.wf .block {
  background: #d8d8d8;
  display: grid; place-items: center;
  font-size: 11px; color: #666;
  text-transform: uppercase; letter-spacing: 0.1em;
}
.wf .block.hero { aspect-ratio: 16/8; }
.wf .block.grid { aspect-ratio: 16/10; }
.wf .block.band { padding: 12px; }
```

## Storyboard-режим

Если задача — флоу из N экранов, делай storyboard: горизонтальная лента из 6-8 экранов с подписями «1 — landing → 2 — signup → 3 — onboarding step 1 ...». Стрелки между ними — часть рисунка.

## После wireframe

Когда пользователь утвердил структуру — переходи в hi-fi. Wireframe-файл оставь, не удаляй: он становится спецификацией.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-wireframe.md`. Секции там: Чем хорош грубый wireframe, Каркас, Правила, Что вынести в варианты, Стек с design-canvas, Антипаттерны.
