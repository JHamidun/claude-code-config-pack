<!-- LEGACY: полное тело скилла 'visual-edit' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: visual-edit
description: Drag/resize handles в браузере → patch обратно в файл. Юзер двигает мышью элемент в превью, скилл записывает изменения в исходный JSX/CSS. Подделка direct-manipulation editor'а внутри Claude Code.
when_to_use: Юзер итерирует layout вручную («чуть левее», «больше отступ»), быстрее показать пальцем чем словами. Внутри live-preview или standalone HTML.
---

# Visual edit

Браузер становится подобием Figma на коротком цикле — drag-и-resize-handle'ы поверх элементов, изменения patch'ятся в JSX/CSS.

## Architectural overview

```
Browser (with overlay)              Claude Code (file editor)
     |                                       |
     | Юзер тащит элемент                    |
     |─────── WebSocket ───────────────────► |
     |  { selector, prop, oldValue, newVal } |
     |                                       | Парсит файл, находит правило
     |                                       | Apply Edit() с новым значением
     |                                       |
     |  ◄─────── reload signal ──────────────|
     | Браузер re-render с новым value       |
```

## Overlay script (browser side)

`templates/visual-edit.js`:
```js
(function() {
  // Включается при ?edit=1 в URL
  if (!new URL(location).searchParams.get('edit')) return;

  const ws = new WebSocket('ws://localhost:8081/visual-edit');
  let selected = null;

  // Hover highlight
  document.addEventListener('mousemove', (e) => {
    if (!e.altKey) return;
    const el = e.target;
    document.querySelectorAll('.ve-hl').forEach(x => x.classList.remove('ve-hl'));
    el.classList.add('ve-hl');
  });

  // Click → select
  document.addEventListener('click', (e) => {
    if (!e.altKey) return;
    e.preventDefault();
    selected = e.target;
    addHandles(selected);
    document.querySelectorAll('.ve-selected').forEach(x => x.classList.remove('ve-selected'));
    selected.classList.add('ve-selected');
  }, true);

  function addHandles(el) {
    document.querySelectorAll('.ve-handle').forEach(x => x.remove());
    const r = el.getBoundingClientRect();
    ['nw','n','ne','e','se','s','sw','w'].forEach(pos => {
      const h = document.createElement('div');
      h.className = `ve-handle ve-handle-${pos}`;
      Object.assign(h.style, {
        position: 'fixed', width: '10px', height: '10px',
        background: '#1e90ff', border: '1px solid #fff',
        borderRadius: '50%', zIndex: 99999, cursor: `${pos}-resize`,
      });
      // Position handle at corner/edge
      // ... (вычисление top/left по pos)
      document.body.appendChild(h);
      h.addEventListener('mousedown', (e) => startDrag(e, el, pos));
    });
  }

  function startDrag(start, el, pos) {
    const r0 = el.getBoundingClientRect();
    const onMove = (e) => {
      const dx = e.clientX - start.clientX;
      const dy = e.clientY - start.clientY;
      // Apply visual change
      if (pos === 'e' || pos === 'ne' || pos === 'se') {
        el.style.width = (r0.width + dx) + 'px';
      }
      // ... other directions
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      // Send to backend
      ws.send(JSON.stringify({
        op: 'resize',
        selector: cssPath(el),
        width: el.style.width,
        height: el.style.height,
      }));
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }

  function cssPath(el) {
    const parts = [];
    while (el && el.tagName && parts.length < 6) {
      let p = el.tagName.toLowerCase();
      if (el.id) { p += '#' + el.id; parts.unshift(p); break; }
      if (el.className) p += '.' + [...el.classList].slice(0, 2).join('.');
      const sib = [...el.parentElement?.children || []].filter(c => c.tagName === el.tagName);
      if (sib.length > 1) p += `:nth-of-type(${sib.indexOf(el)+1})`;
      parts.unshift(p);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }

  // Inject CSS for highlights
  const s = document.createElement('style');
  s.textContent = `
    .ve-hl { outline: 2px dashed #ffd400 !important; outline-offset: 2px; }
    .ve-selected { outline: 2px solid #1e90ff !important; outline-offset: 2px; }
  `;
  document.head.appendChild(s);
})();
```

## Server side (Claude Code patches)

WebSocket server слушает изменения, parses target file и применяет:

```js
const { WebSocketServer } = require('ws');
const fs = require('fs');

const wss = new WebSocketServer({ port: 8081 });
wss.on('connection', (ws) => {
  ws.on('message', async (raw) => {
    const msg = JSON.parse(raw);

    if (msg.op === 'resize') {
      // Найти `width: ...px` для этого селектора в стилях
      // Или inline `style={{ width: ...}}` в JSX
      // Применить Edit (вызов Claude Edit tool)
      console.log(`patch ${msg.selector} → width:${msg.width}`);
      // ... здесь логика парсинга и patch
    }
  });
});
```

В реальной интеграции Claude Code: WebSocket принимает событие → Claude получает prompt «измени width у X на Y» → Edit tool применяется.

## Ограничения

| Что работает | Что нет |
|---|---|
| Inline `style={{ width: 200 }}` | Tailwind classes (нужен класс-mapping) |
| `.class { width: 200px }` | CSS-in-JS (styled-components) |
| Single rule per element | Cascading с !important |
| `position`, `width`, `height` | `display: grid` / flex layout (multiple deps) |

## Альтернативы

- **GoyaWeb / Pinegrow** — visual editors из мира IDE
- **Webflow Designer** — production-grade visual edit
- **Plasmic** — codegen + visual edit

Visual-edit skill — лёгкая поделка для Claude Code, не замена.

## Когда НЕ использовать

- Сложный layout с grid/flex breakpoints → визуальные изменения сломают responsive
- Production code → visual-edit для prototype, ручной control для prod
- Большой проект с CSS-in-JS → парсинг сложнее value

## Stack

- `live-preview` — обязательно (для browser refresh)
- `version-snapshots` — каждое изменение save в snapshot, можно откатить
- `tweaks-persist` — для сохранения tweaks в файл

## Антипаттерны

- Применять каждое drag-движение → 50 patches на одно изменение, файл фрагментируется. Только финальная позиция на mouseup.
- Editing prod code visually → потеряешь важную semantic logic
- Не поддерживать undo → один кривой drag = ручное возвращение
- Не использовать debounce → файл write spam
- Не selectors-стабильность (drag меняет structure → следующий patch к новому selector'у) → каскад поломок
