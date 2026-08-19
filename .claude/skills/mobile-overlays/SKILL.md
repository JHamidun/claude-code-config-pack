---
name: mobile-overlays
description: "Мобильные оверлеи поверх device-frames: iOS-клавиатура, bottom sheet, тосты. Триггеры: «action sheet», «toast», «mobile UI overlay»."
---

# Mobile overlays

Добавки к `device-frames`. Каждый — самодостаточный snippet HTML+CSS+JS.

## iOS keyboard

`templates/ios-keyboard.html` — пиксель-точная QWERTY-клавиатура iOS. Слайдится снизу, нажатия добавляют буквы в `input`.

Использование:
```html
<input id="ios-input" type="text">
<div id="ios-keyboard" class="ios-keyboard"></div>
```

Высота клавиатуры — 291px (стандартная для iPhone). Учти: контент над ней должен скроллиться, не сжиматься.

## Bottom sheet

```html
<div class="bs-backdrop" data-open="true"></div>
<div class="bs-sheet" data-open="true">
  <div class="bs-grabber"></div>
  <h3>Sheet title</h3>
  <p>Content</p>
</div>
```

```css
.bs-sheet {
  position: absolute; left: 0; right: 0; bottom: 0;
  background: #fff; border-radius: 16px 16px 0 0;
  padding: 24px; padding-bottom: 50px;
  transform: translateY(100%);
  transition: transform 300ms cubic-bezier(0.32, 0.72, 0, 1);
  box-shadow: 0 -10px 40px rgba(0,0,0,.15);
}
.bs-sheet[data-open="true"] { transform: translateY(0); }
.bs-grabber {
  width: 36px; height: 5px; background: #d4d4d4;
  border-radius: 3px; margin: -8px auto 16px;
}
.bs-backdrop {
  position: absolute; inset: 0; background: rgba(0,0,0,.4);
  opacity: 0; pointer-events: none;
  transition: opacity 300ms;
}
.bs-backdrop[data-open="true"] { opacity: 1; pointer-events: auto; }
```

## Toast

```html
<div class="toast" data-show="true">
  <span class="toast-text">Файл сохранён</span>
</div>
```

```css
.toast {
  position: absolute; top: 64px; left: 50%; transform: translate(-50%, -20px);
  background: rgba(0,0,0,.85); color: #fff;
  padding: 12px 16px; border-radius: 999px;
  font-size: 14px; font-weight: 500;
  opacity: 0; transition: all 200ms ease-out;
  z-index: 100; backdrop-filter: blur(10px);
}
.toast[data-show="true"] {
  transform: translate(-50%, 0); opacity: 1;
}
```

JS-хелпер:
```js
function showToast(text, ms = 2000) {
  const el = document.querySelector('.toast');
  el.querySelector('.toast-text').textContent = text;
  el.dataset.show = 'true';
  setTimeout(() => el.dataset.show = 'false', ms);
}
```

## Action sheet (iOS)

```html
<div class="action-sheet" data-open="true">
  <div class="as-card">
    <button>Поделиться</button>
    <button>Скопировать ссылку</button>
    <button class="destructive">Удалить</button>
  </div>
  <button class="as-cancel">Отмена</button>
</div>
```

```css
.action-sheet {
  position: absolute; left: 12px; right: 12px; bottom: 12px;
  display: grid; gap: 8px;
  transform: translateY(100%); transition: transform 300ms cubic-bezier(0.32, 0.72, 0, 1);
  z-index: 50;
}
.action-sheet[data-open="true"] { transform: translateY(0); }
.action-sheet button {
  background: rgba(255,255,255,.9); backdrop-filter: blur(20px);
  border: 0; border-radius: 14px; padding: 18px;
  font-size: 17px; color: #007AFF;
}
.action-sheet button.destructive { color: #FF3B30; }
.as-card { display: grid; }
.as-card button + button { border-top: 0.5px solid rgba(0,0,0,.1); border-radius: 0; }
.as-card button:first-child { border-radius: 14px 14px 0 0; }
.as-card button:last-child  { border-radius: 0 0 14px 14px; }
.as-cancel { font-weight: 600; }
```

## Когда использовать

- Клавиатура — только когда показываешь экран ввода (форма, чат, поиск). На прочих скрывай.
- Bottom sheet — для второстепенных действий, фильтров, share-меню.
- Toast — только для подтверждения действия. Не для ошибок (для них inline-сообщения).
- Action sheet — iOS-специфика, не используй на Android (там dialog или bottom sheet с button-list).

## Что НЕ делать

- ❌ Imitating клавиатуру через одну картинку. Делай настоящую сетку клавиш — реалистичнее и редактируемо.
- ❌ Двигать клавиатуру через top/bottom вместо transform — лагает.
- ❌ Тосты в центре экрана — это alert-паттерн, не toast.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-mobile-overlays.md`. Секции там: Состав, iOS Keyboard (упрощённая), Bottom sheet, Toast, Стек, Антипаттерны.
