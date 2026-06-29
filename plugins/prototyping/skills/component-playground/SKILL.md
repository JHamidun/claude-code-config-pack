---
name: component-playground
description: Storybook-подобная страница со всеми вариантами всех компонентов из дизайн-системы. Контролы для пропсов.
when_to_use: Есть дизайн-система или набор компонентов. Нужно показать всё в одном месте, проверить покрытие.
---

# Component playground

Одна HTML-страница, на которой каждый компонент отрендерён во всех вариантах. С контролами «слева список → клик → справа сцена с компонентом + рычажки для пропсов».

## Структура

```
playground/
  index.html            ← главный
  components/           ← по файлу на компонент
    button.html
    input.html
    card.html
  data.json             ← список компонентов и их вариантов
```

## Шаблон index.html

```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Component playground</title>
  <link rel="stylesheet" href="../tokens.css">
  <style>
    body { display: grid; grid-template-columns: 240px 1fr; height: 100vh; margin: 0; font-family: ui-monospace, monospace; }
    nav { background: #f4f4f4; border-right: 1px solid #ddd; overflow: auto; padding: 16px 0; }
    nav h2 { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #888; padding: 0 16px; margin: 16px 0 8px; }
    nav a { display: block; padding: 6px 16px; color: #333; text-decoration: none; font-size: 13px; }
    nav a:hover { background: #e8e8e8; }
    nav a.active { background: #111; color: #fff; }
    main { display: grid; grid-template-rows: 1fr 200px; height: 100vh; }
    .stage { padding: 32px; overflow: auto; background: #fff; }
    .stage iframe { width: 100%; height: 100%; border: 0; }
    .controls { background: #fafafa; border-top: 1px solid #ddd; padding: 16px; overflow: auto; font-size: 12px; }
    .controls label { display: grid; grid-template-columns: 120px 1fr; gap: 8px; align-items: center; margin-bottom: 8px; }
  </style>
</head>
<body>
  <nav id="nav"></nav>
  <main>
    <div class="stage"><iframe id="frame"></iframe></div>
    <div class="controls" id="controls"></div>
  </main>

<script type="module">
  const data = await fetch('data.json').then(r => r.json());
  const nav = document.getElementById('nav');
  const frame = document.getElementById('frame');
  const ctl = document.getElementById('controls');

  for (const [group, items] of Object.entries(data.groups)) {
    const h = document.createElement('h2'); h.textContent = group; nav.append(h);
    for (const it of items) {
      const a = document.createElement('a');
      a.href = '#' + it.id; a.textContent = it.name;
      a.onclick = e => { e.preventDefault(); load(it); };
      nav.append(a);
    }
  }

  function load(it) {
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    document.querySelector(`nav a[href="#${it.id}"]`).classList.add('active');
    frame.src = 'components/' + it.file;
    ctl.innerHTML = '';
    if (it.props) for (const [name, spec] of Object.entries(it.props)) {
      const lab = document.createElement('label');
      lab.append(document.createTextNode(name));
      let input;
      if (spec.type === 'select') {
        input = document.createElement('select');
        for (const o of spec.options) input.append(new Option(o));
      } else if (spec.type === 'bool') {
        input = document.createElement('input'); input.type = 'checkbox';
      } else {
        input = document.createElement('input'); input.value = spec.default || '';
      }
      input.oninput = () => {
        frame.contentWindow.postMessage({ prop: name, value: input.type==='checkbox' ? input.checked : input.value }, '*');
      };
      lab.append(input); ctl.append(lab);
    }
  }
  if (location.hash) {
    const id = location.hash.slice(1);
    for (const items of Object.values(data.groups)) {
      const it = items.find(x => x.id === id); if (it) { load(it); break; }
    }
  }
</script>
</body>
</html>
```

## data.json

```json
{
  "groups": {
    "Foundation": [
      { "id": "tokens", "name": "Tokens", "file": "tokens.html" },
      { "id": "type",   "name": "Typography", "file": "type.html" }
    ],
    "Inputs": [
      { "id": "button", "name": "Button", "file": "button.html",
        "props": {
          "variant": { "type": "select", "options": ["primary","secondary","ghost"] },
          "size":    { "type": "select", "options": ["sm","md","lg"] },
          "loading": { "type": "bool" },
          "label":   { "type": "text", "default": "Click me" }
        }
      }
    ]
  }
}
```

## Компонент-страница (button.html)

```html
<!doctype html>
<style>
  body { display: grid; gap: 16px; padding: 24px; align-content: start; }
  body button { /* реальные стили из системы */ }
</style>
<button id="btn">Click me</button>
<script>
  const btn = document.getElementById('btn');
  window.addEventListener('message', e => {
    const { prop, value } = e.data;
    if (prop === 'label') btn.textContent = value;
    else if (prop === 'loading') btn.dataset.loading = value;
    else btn.dataset[prop] = value;
  });
</script>
```

## Что показывать обязательно

- Все варианты × размеры × состояния.
- Пустое / disabled / loading / error состояния (см. `states-checklist`).
- В тёмной теме (если есть).
- На мобилке (через rezizer).

## Антипаттерны

- ❌ Один gigantic html-файл со всеми компонентами. Невозможно навигировать.
- ❌ Только default-вариант. Покрытие должно быть полным.
- ❌ Без контролов — нельзя проверить интерактивные стейты.
