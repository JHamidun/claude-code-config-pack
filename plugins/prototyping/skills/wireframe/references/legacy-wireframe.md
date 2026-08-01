<!-- LEGACY: полное тело скилла 'wireframe' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: wireframe
description: Грубые варианты структуры экрана/страницы перед визуалом. Вайрфрейм — про блоки и поток, не про красоту. Делает 2-4 варианта структуры для сравнения, потом юзер выбирает один и ты идёшь в hi-fi.
when_to_use: Юзер просит «прикинь структуру», «как разложим», «нужны варианты компоновки», «сначала каркас». Перед `interactive-prototype` или `slides`, когда контент не финальный.
---

# Wireframe

Сначала структура, потом цвет. Вайрфрейм отвечает на «что и в каком порядке», не на «как выглядит».

## Чем хорош грубый wireframe

- Дёшево перемещать блоки, пока никто не привык к визуалу
- Видно дыры в контенте раньше («тут CTA — а текст для CTA есть?»)
- Юзер не цепляется к шрифту/цвету и обсуждает суть

## Каркас

Один HTML, серая палитра, никаких изображений, плейсхолдеры подписаны словами.

```html
<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Wireframe</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.4 -apple-system, system-ui, sans-serif; background: #f5f5f5; color: #333; }
  .wf-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .wf-block { background: #fff; border: 1px dashed #999; padding: 16px;
              margin-bottom: 12px; border-radius: 4px; }
  .wf-img { background: linear-gradient(135deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd),
                        linear-gradient(135deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd);
            background-size: 16px 16px; background-position: 0 0, 8px 8px; min-height: 200px;
            display: flex; align-items: center; justify-content: center; color: #777; font-size: 12px; }
  .wf-cta { display: inline-block; padding: 8px 20px; border: 2px solid #333; border-radius: 4px; }
  .wf-row { display: grid; gap: 12px; }
  .wf-row.cols-2 { grid-template-columns: 1fr 1fr; }
  .wf-row.cols-3 { grid-template-columns: repeat(3, 1fr); }
  .wf-label { color: #999; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
</style></head>
<body><div class="wf-page">
  <div class="wf-block">
    <div class="wf-label">Hero</div>
    <h1 style="margin:8px 0">Заголовок: одна строка, сильный value prop</h1>
    <p>Подзаголовок: 1-2 строки, уточняет для кого и что</p>
    <a class="wf-cta">CTA: «Начать бесплатно»</a>
    <div class="wf-img" style="margin-top:16px">[Иллюстрация продукта]</div>
  </div>

  <div class="wf-block">
    <div class="wf-label">Features · 3 столпа</div>
    <div class="wf-row cols-3">
      <div>① Икона + 1 строка</div>
      <div>② Икона + 1 строка</div>
      <div>③ Икона + 1 строка</div>
    </div>
  </div>
  <!-- ...остальные блоки... -->
</div></body></html>
```

## Правила

- **Серый, белый, dashed-границы** — никаких цветов
- **Текст-плейсхолдеры подписаны** — «Hero заголовок», «3 преимущества», не lorem ipsum
- **Изображения как diamond-pattern квадраты** с подписью
- **CTA кнопка** — обведённый прямоугольник, не залитый
- **Один шрифт на всё** — system sans
- **Блоки разделены 12-24px**, между секциями 32px

## Что вынести в варианты

Хороший набор wireframes — 3 варианта по одной оси:

| Ось | Пример |
|---|---|
| Поток | linear (сверху вниз) vs anchor-nav (sidebar TOC) vs side-by-side |
| Иерархия | hero доминирует vs hero равноправен vs hero крошечный |
| Блоки | 5 секций vs 8 секций vs 12 секций |
| Компоновка | one-column vs split vs grid |

## Стек с design-canvas

Вайрфреймы лучше всего показывать через `design-canvas` — 3 артборда side-by-side с лейблами «A/B/C — что отличается».

## Антипаттерны

- Lorem ipsum вместо описания контента → юзер не видит что внутри
- Цветные блоки в wireframe → читается как готовый дизайн, отвлекает
- Только desktop, забыл mobile → переделка после
- Wireframe в Figma вместо HTML → теряем связь с реализацией
- Сразу hi-fi без шага wireframe → 80% времени переделки на этапе цвета
