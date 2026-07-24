<!-- LEGACY: полное тело скилла 'forms-a11y' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: forms-a11y
description: Доступные формы — лейблы, error-сообщения, autocomplete, fieldset для группировки, focus-rings, validation на blur не на change. Чтобы скринридер читал, клавиатура работала, ошибки понимались.
when_to_use: В прототипе/интерфейсе есть form-fields — input, select, textarea, checkbox, radio, file-upload. Перед states-checklist (т.к. формы дают много состояний).
---

# Forms a11y

Форма без accessibility — провал по 4 фронтам: screen readers, клавиатура, мобильная клавиатура, error UX. Учти все.

## Минимум на каждое поле

```html
<div class="field">
  <label for="email">Email</label>
  <input
    id="email"
    name="email"
    type="email"
    autocomplete="email"
    inputmode="email"
    required
    aria-describedby="email-error"
    aria-invalid="false"
  />
  <div id="email-error" class="error" hidden></div>
</div>
```

**Все 8 атрибутов важны:**
- `id`+`for` — связка label↔input для screen reader
- `name` — для form submission
- `type` — нативная валидация + правильная клавиатура mobile
- `autocomplete` — браузер подсказывает сохранённые значения
- `inputmode` — клавиатура mobile (email, numeric, tel, url, search)
- `required` — нативная валидация
- `aria-describedby` — связка с error message
- `aria-invalid` — toggleв JS при ошибке

## Полная таблица типов

| Type | Inputmode | Autocomplete | Mobile keyboard |
|---|---|---|---|
| email | email | email | with `@` |
| tel | tel | tel | digits + `+` |
| url | url | url | with `.com`, `/` |
| number | numeric | one-time-code если SMS | numbers |
| password | text | new-password / current-password | letters |
| search | search | (none) | with «search» button |
| date | (none) | bday / cc-exp | native picker |

## Группировка через fieldset

```html
<fieldset>
  <legend>Способ оплаты</legend>
  <label><input type="radio" name="payment" value="card"> Карта</label>
  <label><input type="radio" name="payment" value="sbp"> СБП</label>
  <label><input type="radio" name="payment" value="invoice"> Счёт</label>
</fieldset>
```

Без fieldset screen reader читает radios как несвязанные. С fieldset → читает «Способ оплаты, 3 варианта».

## Error UX

### Когда показывать
- ❌ На `oninput` (каждое нажатие) — раздражает
- ✅ На `onblur` (когда юзер ушёл с поля) — даёт закончить ввод
- ✅ На `onsubmit` (всегда) — последняя проверка

### Что писать
- ❌ «Неверный формат» → не понятно что не так
- ✅ «Email должен содержать @» → конкретно
- ❌ «Required» → ОК для разработчика, не для юзера
- ✅ «Это поле обязательно» → понятно
- ✅ «Пароль: минимум 8 символов, одна цифра, одна заглавная» → разъясняется требование

### Куда ставить
- Под полем, не над (юзер уже посмотрел поле)
- Цвет красный + иконка ⚠ — не только цвет (а11y для дальтоников)
- Связь через `aria-describedby` чтобы screen reader прочитал ошибку

```jsx
function Field({ label, type, error, ...props }) {
  const id = useId();
  const errId = `${id}-err`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} type={type} aria-invalid={!!error}
        aria-describedby={error ? errId : undefined} {...props} />
      {error && <div id={errId} className="error" role="alert">
        <Icon name="warn" /> {error}
      </div>}
    </div>
  );
}
```

## Focus rings

Никогда не убирай:
```css
input:focus { outline: none; }  /* ❌ не делай так */
```

Делай так:
```css
input:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

`:focus-visible` показывает ring только при keyboard navigation, не при click — лучшее из двух миров.

## Disabled vs read-only

| disabled | read-only |
|---|---|
| Не submit'ится | Submit'ится |
| Не focus'ится | Focus'ится |
| Скринридер: «недоступно» | Скринридер: читает значение |
| ⚠ Юзер не понимает почему grey | ✅ Видно что нельзя редактировать |

Используй `read-only` если поле fixed но contextual. `disabled` только если действительно недоступно (нужно сначала купить план).

## Mobile keyboards

```html
<!-- 6-digit OTP -->
<input type="text" inputmode="numeric" autocomplete="one-time-code" pattern="\d{6}" maxlength="6">

<!-- Phone -->
<input type="tel" inputmode="tel" autocomplete="tel" placeholder="+7">

<!-- Money -->
<input type="text" inputmode="decimal" pattern="[0-9.]*">
```

`inputmode` — главный override клавиатуры. `type` — fallback.

## Required indicator

- ❌ Помечать только обязательные → юзер не уверен
- ✅ Помечать необязательные (`Email (необязательно)`) → меньше пометок
- ✅ Если все поля обязательные — пиши вверху «Все поля обязательные»

## Validation на стороне клиента vs сервера

Клиент:
- Format (email regex, phone digits)
- Length (min/max)
- Required

Сервер (всегда):
- Уникальность (email уже занят)
- Бизнес-логика (промокод действителен)
- Безопасность

**Никогда не доверяй только клиенту** — но клиентская валидация даёт мгновенный feedback и снижает нагрузку на сервер.

## Антипаттерны

- Placeholder вместо label → исчезает при вводе, скринридеру не понятно
- Все поля required без пометки → юзер бросает после первой ошибки
- Error на каждом keystroke → раздражает
- Form submit без disabled-state на кнопке → двойная отправка
- Captcha без a11y альтернативы → блочит users with disabilities
- Validation regex `^[a-z]+$` для имени → ломаются Your Name, José, 王伟
- Пароль input без `autocomplete="new-password"` → менеджер паролей не сохраняет
- 30+ полей в одной форме → разбивай на шаги (multistep wizard)
