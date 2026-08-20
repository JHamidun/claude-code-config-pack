---
name: comment-injector
version: 1.0.0
description: "Overlay в HTML: Alt+Click по элементу кладёт в clipboard CSS-селектор и outerHTML — правки без скриншотов. Триггеры: «ревью прототипа в браузере». НЕ правка мышкой→visual-edit."
---

# Comment injector

Добавь `<script src="comment-injector.js"></script>` в страницу или дёрни `?cc=1` через query-параметр (snippet ниже).

При нажатии **Alt+Click** на элемент — копирует в clipboard:

```
SELECTOR: .product-card .title
OUTER_HTML: <h3 class="title">Apex Pro</h3>
```

Пользователь вставляет это в чат → ты сразу знаешь, что править.

## Snippet

`templates/comment-injector.js`:

```js
(function () {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.body.removeAttribute('data-cc-on');
  });
  document.addEventListener('click', (e) => {
    if (!e.altKey) return;
    e.preventDefault(); e.stopPropagation();
    const el = e.target;
    const sel = cssPath(el);
    const text = `SELECTOR: ${sel}\nOUTER_HTML: ${el.outerHTML.slice(0, 400)}`;
    navigator.clipboard.writeText(text);
    flash(el);
  }, true);

  function cssPath(el) {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.tagName.toLowerCase();
      if (el.id) { part += '#' + el.id; parts.unshift(part); break; }
      if (el.className) part += '.' + [...el.classList].slice(0, 2).join('.');
      const sib = [...el.parentNode.children].filter(c => c.tagName === el.tagName);
      if (sib.length > 1) part += `:nth-of-type(${sib.indexOf(el) + 1})`;
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  function flash(el) {
    const o = el.style.outline;
    el.style.outline = '2px solid #ff3b30';
    setTimeout(() => { el.style.outline = o; }, 600);
  }
})();
```

## Auto-inject через live-preview

В `live.mjs` добавь `?cc=1` логику или просто включи всегда — много места не занимает.

## Антипаттерны

- Не используй в production-сборке. Это инструмент работы.
- Не объединяй с обычным `click` — будет конфликтовать. Только `alt+click`.
