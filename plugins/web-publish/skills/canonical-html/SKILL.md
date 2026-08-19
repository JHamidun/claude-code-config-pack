---
name: canonical-html
description: "Канонический HTML: закрытые теги, double-quotes, без implied-close — для предсказуемых правок инструментами. Триггеры: «почини разметку», «закрой теги»."
---

# Canonical HTML

Цель — чтобы любая дальнейшая инструментальная правка (find-replace, AST, форматтеры, патчи через WebSocket в `visual-edit`) работала предсказуемо.

## Правила

### 1. Закрывай каждый non-void тег явно
```html
<!-- плохо -->
<p>Привет
<p>Мир

<!-- хорошо -->
<p>Привет</p>
<p>Мир</p>
```

`<p>`, `<li>`, `<dt>`, `<dd>`, `<option>`, `<thead>`, `<tbody>`, `<tr>`, `<td>` — у всех implied-close. Закрывай все вручную.

### 2. Double-quote атрибуты
```html
<!-- плохо -->
<input type=text required>
<a href=/foo class=link>foo</a>

<!-- хорошо -->
<input type="text" required>
<a href="/foo" class="link">foo</a>
```

Boolean-атрибуты без значения — OK (`required`, `disabled`, `hidden`).

### 3. Не self-close non-void
```html
<!-- плохо -->
<div class="card" />
<span/>

<!-- хорошо -->
<div class="card"></div>
<span></span>
```

Self-closing валиден только в SVG/MathML и для void-элементов (`<br>`, `<hr>`, `<img>`, `<input>`, `<meta>`, `<link>`, `<source>`, `<area>`, `<col>`, `<embed>`, `<wbr>`).

### 4. Атрибуты в стабильном порядке
Не обязательно, но удобно. Рекомендую:
1. `id`
2. `class`
3. `data-*`
4. `aria-*`
5. role
6. остальное

### 5. Никаких `<style>`/`<script>` без `</style>`/`</script>`
Даже если пустой.

### 6. Мета-теги — full open/close не нужны (void)
```html
<meta charset="utf-8">
<link rel="stylesheet" href="...">
```

## Список void-элементов (самозакрывающихся БЕЗ слеша)

`area`, `base`, `br`, `col`, `embed`, `hr`, `img`, `input`, `link`, `meta`, `source`, `track`, `wbr`.

Всё остальное — открывать и закрывать парой.

## Почему это важно

- Регэкспы вида `</p>` начинают находить настоящие пары, а не воздух.
- AST-парсеры (cheerio, jsdom, htmlparser2) одинаково видят дерево, как браузер.
- Find-replace в редакторе не превращается в лотерею.
- `visual-edit` и `tweaks-persist` могут патчить файл без неожиданностей.

## Антипаттерны

- ❌ `<p>` перед `<div>` без `</p>` — браузер закроет `p` за тебя, но AST не всегда.
- ❌ `<img />` — лишний слеш. Просто `<img>`.
- ❌ Mixed quotes: `class='card' id="hero"` — выбери один стиль.
- ❌ Attribute-value в одинарных кавычках: `<a href='...'>` — работает, но непоследовательно с большинством стилей.

## Чек-перед-сдачей

```bash
npx html-validate <file>     # отловит implied-close и пр.
npx prettier --check <file>  # форматирование
```
