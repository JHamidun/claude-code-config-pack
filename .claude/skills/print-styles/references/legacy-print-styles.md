<!-- LEGACY: полное тело скилла 'print-styles' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: print-styles
description: CSS @media print стили чтобы артефакт нормально печатался / экспортировался в PDF. Скрывает navigation, ставит правильные page breaks, переключает шрифты под печать, выключает hover.
when_to_use: Перед export-pdf если артефакт длинный (лендинг, multi-page документ). Не нужен для slides (там размеры уже фиксированные).
---

# Print styles

Web и print — два разных медиума. Без `@media print` всё печатается криво — обрезанные блоки, лишние элементы, бледный текст на чёрно-белой.

## Базовый print stylesheet

```css
@media print {
  /* 1. Скрыть всё что не для печати */
  nav, header.sticky, footer.dynamic, .toolbar,
  .cookie-banner, .modal, .toast, .live-chat,
  button[type="button"]:not(.print-keep),
  .scroll-to-top, .share-buttons {
    display: none !important;
  }

  /* 2. Body на всю ширину, без max-width */
  body { margin: 0; padding: 0; max-width: none; }

  /* 3. Чёрный текст на белом фоне (в больших объёмах) */
  body { background: white !important; color: black !important; }

  /* 4. Переключить шрифты на serif для длинного чтения */
  body { font-family: Georgia, "Times New Roman", serif; font-size: 11pt; line-height: 1.5; }

  /* 5. Ссылки без подчёркивания (с URL рядом если важно) */
  a { color: black !important; text-decoration: none; }
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 9pt; color: #666;
  }
  /* НО: не показывать URL для anchor links и mailto */
  a[href^="#"]::after, a[href^="mailto:"]::after { content: ""; }

  /* 6. Page breaks */
  h1, h2, h3 { page-break-after: avoid; }
  p, li { orphans: 3; widows: 3; }
  pre, blockquote, table, figure { page-break-inside: avoid; }
  section, .chapter { page-break-before: auto; }
  .new-page { page-break-before: always; }

  /* 7. Не печатать background-images (по умолчанию выключено в большинстве браузеров) */
  * { background: transparent !important; box-shadow: none !important; }
  /* Но если фон важен (брендинг): */
  .keep-bg { background: var(--bg) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }

  /* 8. Картинки уменьшать */
  img { max-width: 100% !important; height: auto !important; page-break-inside: avoid; }

  /* 9. Скрыть @media:hover styles */
  .hover-effect:hover { transform: none !important; }
}

/* @page правила (вне @media print) */
@page {
  size: A4 portrait;
  margin: 20mm 15mm;

  @top-center { content: "ExampleProduct — Pitch Deck"; font-size: 9pt; color: #888; }
  @bottom-right { content: counter(page) " / " counter(pages); font-size: 9pt; }
}
@page :first {
  margin-top: 30mm;
  @top-center { content: ""; }    /* без headers на cover */
}
```

## Для slides (отдельная стратегия)

Slides уже фиксированы 1920×1080. Print-styles делают:
1. Активируют все слайды (по дефолту видим только current)
2. Ставят `page-break-after: always`
3. Размер страницы = размер слайда

```css
@media print {
  body { background: white; }

  /* Все слайды visible */
  .slide { opacity: 1 !important; pointer-events: auto !important;
           position: static !important; transform: none !important;
           page-break-after: always; break-after: page; }

  .slide:last-child { page-break-after: auto; }
}

@page {
  size: 1920px 1080px;     /* пропорция совпадает со slide */
  margin: 0;
}
```

## Для лендингов

Длинный документ → continuous page-flow:

```css
@media print {
  /* Hero — на первой странице */
  .hero { min-height: auto; padding: 40mm 0; }

  /* Большие секции — break перед */
  section[id="pricing"], section[id="about"], section[id="faq"] {
    page-break-before: always;
  }

  /* Но компактные секции — потоком */
  section[id="features"], section[id="testimonials"] {
    page-break-before: auto;
  }
}
```

## Footnotes / endnotes для академических

```html
<p>Текст со сноской<sup class="fn">1</sup></p>
<p class="footnote" data-num="1">Это сноска</p>
```

```css
@media print {
  .footnote {
    counter-increment: footnote;
    font-size: 9pt; line-height: 1.3;
    padding-left: 1em; text-indent: -1em;
  }
  .footnote::before { content: counter(footnote) ". "; }
  sup.fn { font-size: 7pt; vertical-align: super; }
}
```

## Watermark

```css
@media print {
  body::before {
    content: "DRAFT";
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-size: 120pt; color: rgba(0,0,0,0.05);
    z-index: -1;
  }
}
```

## Тест в браузере

В Chrome DevTools: Console → Cmd+Shift+P → «Show rendering» → «Emulate CSS media → print».

Все @media print применяются, видишь как в PDF. Не нужно реально печатать.

Или Cmd+P → preview.

## Когда не нужны print-styles

- Чистый prototype для browser only
- Артефакт уже фиксирован под export (slides 1920×1080)
- Single-page card (постер, обложка) — там нет page breaks

## Антипаттерны

- Не скрывать navigation → print с nav-bar в шапке
- `display: none` для всего сразу → нет понимания что должно остаться
- Полагаться на CSS variables в print → некоторые браузеры не resolve'ят
- Огромные шрифты (40pt+) для печати → каждый параграф на новой странице
- Не использовать `orphans` / `widows` → вдова на новой странице
- Hardcoded `width: 1200px` в layout → не помещается в A4
- Печатать с тёмным фоном без `print-color-adjust: exact` → текст на чёрном становится белым на белом → невидим
