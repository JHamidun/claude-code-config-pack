---
name: forms-a11y
description: Формы, которые работают со скрин-ридерами и клавиатурой. Label, описания, ошибки, focus-management.
when_to_use: Любая форма в production-продукте. Не для прототипа на 5 минут.
---

# Forms a11y

Формы — самая нарушаемая часть accessibility. Делай правильно с первого раза.

## Каждый input — с label

```html
<!-- ✅ Правильно -->
<label for="email">Email</label>
<input id="email" type="email" name="email">

<!-- ✅ Альтернатива (label оборачивает) -->
<label>
  Email
  <input type="email" name="email">
</label>

<!-- ❌ Неправильно — placeholder вместо label -->
<input type="email" placeholder="Email">

<!-- ❌ Неправильно — visually-hidden span ≠ label -->
<input type="email" name="email">
<span class="sr-only">Email</span>
```

## Visually-hidden label (если в дизайне нет места)

```html
<label for="search" class="sr-only">Поиск</label>
<input id="search" type="search" placeholder="Поиск...">
```

```css
.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}
```

## Описание (helper text)

```html
<label for="pwd">Пароль</label>
<input id="pwd" type="password" aria-describedby="pwd-help">
<p id="pwd-help" class="helper">Не меньше 8 символов, цифра и буква.</p>
```

`aria-describedby` ID элемента, прочитается скрин-ридером после label.

## Ошибки

```html
<label for="email">Email</label>
<input id="email" type="email" aria-invalid="true" aria-describedby="email-err">
<p id="email-err" class="error" role="alert">Введите корректный email — например, ivan@example.com.</p>
```

- `aria-invalid="true"` — статус.
- `aria-describedby` — связывает с текстом.
- `role="alert"` — скрин-ридер прочитает сразу.
- **Текст ошибки конкретный.** «Неверно» не годится. Что не так + что сделать.

## Required

```html
<label for="name">Имя <span aria-hidden="true">*</span></label>
<input id="name" required aria-required="true">
```

`*` визуальная — `aria-hidden`. `required` + `aria-required` для скрин-ридера и валидации.

## Группы (radio/checkbox)

```html
<fieldset>
  <legend>Способ оплаты</legend>
  <label><input type="radio" name="pay" value="card"> Карта</label>
  <label><input type="radio" name="pay" value="cash"> Наличные</label>
</fieldset>
```

`<fieldset>` + `<legend>` — обязательны для группы radio/checkbox. Без них скрин-ридер не понимает, к чему относятся опции.

## autocomplete

```html
<input type="text" autocomplete="given-name" name="firstName">
<input type="text" autocomplete="family-name" name="lastName">
<input type="email" autocomplete="email" name="email">
<input type="password" autocomplete="current-password">
<input type="password" autocomplete="new-password">
<input type="tel" autocomplete="tel">
<input type="text" autocomplete="postal-code">
<input type="text" autocomplete="cc-number" inputmode="numeric">
```

Полный список — на developer.mozilla.org/autocomplete.

`inputmode="numeric"` — показывает цифровую клавиатуру на мобильных.

## Focus management

После сабмита формы — переведи фокус:
- На сообщение об успехе.
- На первое поле с ошибкой.

```js
form.addEventListener('submit', async e => {
  e.preventDefault();
  const result = await validate(form);
  if (result.errors.length) {
    const firstErrEl = form.querySelector(`[name=${result.errors[0].field}]`);
    firstErrEl.focus();
  } else {
    successEl.tabIndex = -1;
    successEl.focus();
  }
});
```

## Кнопка submit

```html
<button type="submit">Создать аккаунт</button>
```

- Текст — действие, не «Отправить» / «OK».
- `type="submit"` — иначе Enter не сработает.

## Loading state

```html
<button type="submit" aria-busy="true" disabled>
  <span class="spinner" aria-hidden="true"></span>
  <span>Создаём…</span>
</button>
```

`aria-busy` + текст «Создаём…» — понятно скрин-ридеру.

## Floating labels (если хочется)

Visual-only паттерн. Нужен label под капотом. Никогда не заменяй placeholder'ом.

```html
<div class="float">
  <input id="email" type="email" placeholder=" ">
  <label for="email">Email</label>
</div>
```

```css
.float { position: relative; }
.float input { padding: 24px 12px 8px; }
.float label {
  position: absolute; left: 12px; top: 16px;
  pointer-events: none; transition: all .15s ease;
  color: #888;
}
.float input:focus + label, .float input:not(:placeholder-shown) + label {
  top: 4px; font-size: 11px; color: #555;
}
```

## Чек-лист

Для каждого поля:
- ✅ `<label>` или `aria-label`
- ✅ Описательный текст связан через `aria-describedby` (где нужно)
- ✅ Ошибка с `role="alert"` и `aria-invalid`
- ✅ `autocomplete` для известных полей
- ✅ `type` соответствует данным (email, tel, url, number)
- ✅ `inputmode` на мобильных
- ✅ Фокус управляется после сабмита

Для формы:
- ✅ `<fieldset>` для групп radio/checkbox
- ✅ Submit-кнопка с конкретным текстом
- ✅ Можно сабмитить Enter'ом
- ✅ Tab проходит через поля в логичном порядке

## Что НЕ делать

- ❌ Placeholder вместо label. Когда введено — пропадает.
- ❌ Скрытые labels через `display: none` — скрин-ридеры пропустят.
- ❌ Кнопка-`<div onclick>`. Только `<button>` или `<a>`.
- ❌ `tabindex` на не-интерактивных элементах.
- ❌ `outline: none` без замены focus-кольца.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-forms-a11y.md`. Секции там: Минимум на каждое поле, Полная таблица типов, Группировка через fieldset, Error UX, Focus rings, Disabled vs read-only, Mobile keyboards, Required indicator, Validation на стороне клиента vs сервера, Антипаттерны.
