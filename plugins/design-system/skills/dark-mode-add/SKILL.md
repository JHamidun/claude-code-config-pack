---
name: dark-mode-add
version: 1.0.0
description: "Добавить dark mode к light-дизайну: продуманные dark-токены, не инверт. Триггеры: «тёмная тема к дизайну», «dark theme tokens»."
---

# Dark mode add

Не «инверт всех цветов». Хороший dark mode — это **отдельная тема** с продуманными токенами.

## Чек-лист

### 1. Токены, не значения

Если в коде `color: #111` или `background: #fff` — переделай на CSS-переменные:

```css
:root {
  --bg: #FAF9F6;
  --fg: #111;
  --muted: #6B6B6B;
  --rule: rgba(0,0,0,.08);
}
[data-theme="dark"] {
  --bg: #0d0d0d;
  --fg: #e8e6e1;
  --muted: #888;
  --rule: rgba(255,255,255,.1);
}
```

### 2. Не белый, не чёрный

- `--bg` в dark — **не #000**, а #0d0d0d / #111 / #161616. Чистый чёрный выглядит как «выключенный экран».
- `--fg` в dark — **не #fff**, а #e8e6e1 / #f5f5f3. Чистый белый режет глаза.

### 3. Тени → контраст бордеров

Тени в dark почти не видно. Замени их на тонкие светлые бордеры:

```css
.card { box-shadow: var(--shadow-md); }
[data-theme="dark"] .card {
  box-shadow: none;
  border: 1px solid var(--rule);
}
```

### 4. Градиенты ослабь

Розово-фиолетовый градиент в light часто выглядит свежо. В dark — кислотно. Ослабь intensity:

```css
[data-theme="dark"] .hero-gradient {
  filter: saturate(0.7) brightness(0.9);
}
```

### 5. Картинки

- Фотографии — оставь как есть.
- Логотипы — нужны два варианта (тёмный логотип на светлом, светлый на тёмном), либо один монохромный с `currentColor`.
- Иллюстрации SVG — тоже через `currentColor` или две версии.

### 6. Картинки на тёмном фоне

Добавь лёгкий outline вокруг картинок, чтобы они не «висели в пустоте»:

```css
[data-theme="dark"] img {
  border: 1px solid var(--rule);
  border-radius: 8px;
}
```

(Только не для иконок, очевидно.)

### 7. Состояния

Hover/active в dark должны **светлеть**, а не темнеть. В light — наоборот.

```css
button { background: var(--primary); }
button:hover { background: oklch(from var(--primary) calc(l - 0.05) c h); }
[data-theme="dark"] button:hover {
  background: oklch(from var(--primary) calc(l + 0.05) c h);
}
```

### 8. Toggle

Минимальный, без анимаций-аттракционов:

```html
<button id="theme-toggle" aria-label="Toggle theme">🌓</button>
<script>
const root = document.documentElement;
const stored = localStorage.getItem('theme');
const sysDark = matchMedia('(prefers-color-scheme: dark)').matches;
root.dataset.theme = stored || (sysDark ? 'dark' : 'light');
document.getElementById('theme-toggle').onclick = () => {
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  localStorage.setItem('theme', next);
};
</script>
```

### 9. `prefers-color-scheme`

Уважай системный preference:

```css
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --bg: #0d0d0d;
    --fg: #e8e6e1;
    /* ... */
  }
}
```

### 10. Контраст

После переключения проверь `a11y-audit` — некоторые сочетания могут не пройти WCAG, нужно подкрутить.

## Антипаттерны

- ❌ `filter: invert(1)` на body. Ломает картинки и оттенки.
- ❌ Один и тот же акцентный цвет для light и dark — в dark он будет блёклым. Используй -400 в dark, -500 в light.
- ❌ Toggle с анимацией на 1+ секунду. Должно переключиться мгновенно.
- ❌ Игнорировать систему — пользователю с dark OS неприятно увидеть светлую страницу.
