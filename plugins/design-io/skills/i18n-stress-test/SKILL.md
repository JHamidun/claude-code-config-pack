---
name: i18n-stress-test
description: Стресс-тест UI на i18n — длинные слова (немецкий), RTL (арабский, иврит), CJK (японский, китайский), emoji в тексте. Чтобы кнопка не разъехалась когда «Submit» = «Senden in den Warenkorb».
when_to_use: Артефакт пойдёт в i18n / multilingual продукт. Перед dev-handoff. Особенно если текущий язык — английский (текст самый короткий), всё может выглядеть нормально, а на немецком/русском всё разъедется.
---

# i18n stress test

UI который ОК на английском часто разваливается на других языках. Стресс-тест предотвращает это.

## 4 категории риска

### 1. Длинные слова / фразы
- **Немецкий:** «Geschwindigkeitsbegrenzung» (ограничение скорости) = 1 слово
- **Финский / венгерский:** аналогично
- **Русский:** до +30% длины относительно английского
- **Французский:** +20-25%

```
EN: "Submit"           (6 символов)
DE: "Absenden"         (8)
RU: "Отправить"        (9)
FR: "Soumettre"        (9)
HU: "Beküldés"         (8)
```

### 2. CJK (китайский / японский / корейский)
- **Короче по символам**, но каждый символ = слово
- Нет word-break как в латинице
- Шрифт с CJK glyphs обязателен (Noto Sans CJK)
- Vertical text bonus (`writing-mode: vertical-rl`) для японского

### 3. RTL (арабский, иврит, фарси)
- Весь layout зеркалится
- Иконки тоже зеркалятся (стрелки, прогресс-бары)
- Числа остаются LTR (123 пишутся слева направо даже в RTL-text)
- `dir="rtl"` на `<html>` или нужном контейнере

### 4. Emoji в тексте
- 👨👩👧👦 = 7 codepoints, 1 «character» — длина строки разная в JS vs визуально
- Variation selectors: ❤️ = 2 codepoints
- Скайн-тоны: 👋🏽 = 2 codepoints
- Нужно `Intl.Segmenter` для правильного counting

## Test fixtures

```js
const fixtures = {
  en: { hello: "Hello", submit: "Submit", error_required: "This field is required" },
  ru: { hello: "Здравствуйте", submit: "Отправить", error_required: "Это поле обязательно" },
  de: { hello: "Hallo", submit: "Geschwindigkeitsbegrenzung", error_required: "Dieses Feld muss ausgefüllt werden" },
  zh: { hello: "你好", submit: "提交", error_required: "此栏必填" },
  ja: { hello: "こんにちは", submit: "送信する", error_required: "この欄は必須です" },
  ar: { hello: "مرحبا", submit: "إرسال", error_required: "هذا الحقل إلزامي", dir: "rtl" },
  he: { hello: "שלום", submit: "שלח", error_required: "שדה זה חובה", dir: "rtl" },
  hi: { hello: "नमस्ते", submit: "सबमिट करें" },
  emoji: { hello: "Hello 👋🏽", submit: "Submit ➡️", name: "👨👩👧👦 Family" },
};
```

## Stress-test mode

В прототипе: добавь `?lang=de` URL-параметр и переключай fixtures:

```jsx
const lang = new URL(location).searchParams.get('lang') || 'en';
const t = fixtures[lang];

document.documentElement.lang = lang;
document.documentElement.dir = t.dir || 'ltr';

return (
  <button>{t.submit}</button>
);
```

Прогон: открыть прототип с `?lang=de`, `?lang=ja`, `?lang=ar`, `?lang=emoji`. Что сломалось?

## Чек-лист

| Что проверить | Признак сломанности |
|---|---|
| Кнопки вмещают текст | Текст обрезан / button разъехалась на 2 строки |
| Заголовки на 2 строки | Hero h1 стал 4 строки |
| Lables форм не overlap | Label наезжает на input или соседнее поле |
| Меню navbar не переполнено | Items не помещаются, нет overflow handling |
| Modal не разъехалась | Title из 4 слов на немецком переполнил |
| Иконки + RTL | Стрелки направлены не туда |
| CJK glyphs показываются | Вместо них квадраты ☐☐☐ — нет шрифта |
| Эмодзи colored | На некоторых платформах monochrome — игнорируй |

## Решения проблем

### Длинные слова разъезжают layout
```css
.button { word-break: keep-all; }   /* плохо для DE/HU */
.button { hyphens: auto; }          /* OK с lang attr */
.button { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }  /* radical */
```

Лучше: **flexible buttons + min/max widths**, текст занимает столько места сколько нужно.

### RTL зеркалирует ВСЕ
```css
[dir="rtl"] .arrow-icon { transform: scaleX(-1); }
[dir="rtl"] .progress { direction: ltr; }   /* ← кроме number-rich UI */
```

В CSS используй logical properties:
```css
/* Плохо */
.card { padding-left: 16px; margin-right: 12px; }

/* Хорошо */
.card { padding-inline-start: 16px; margin-inline-end: 12px; }
```

### CJK font fallback
```css
body { font-family: 'Inter', 'Noto Sans CJK JP', 'Noto Sans CJK KR', system-ui, sans-serif; }
```

Или подгружай CJK font только когда `lang=ja|zh|ko`.

### Emoji counting
```js
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
const count = [...segmenter.segment('👨👩👧')].length;  // 1, не 5
```

## Антипаттерны

- Тестировать только на английском → всё разъедется на немецком в prod
- Жёсткие `width: 200px` на кнопках → длинные translations не помещаются
- Полагаться на `string.length` для проверки длины → CJK / emoji нет
- Игнорировать RTL потому что «у нас не Ближний Восток» → жёсткие `padding-left` потом ломаются если решат
- Использовать `&nbsp;` чтобы не break слово → ломается i18n
- Машинный перевод как final → пропадают культурные нюансы (формат дат, валюта, имена-формы)
