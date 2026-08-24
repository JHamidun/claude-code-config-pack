---
name: document-import
description: "Извлечь текст и картинки из PDF/DOCX/PPTX/скетча для прототипа или дека. Триггеры: «из PDF в слайды», «DOCX в лендинг». НЕ переверстать дек 1-в-1→pptx-import."
---

# Document import

Все документы — это zip-архивы с XML или текстом. Открыть и извлечь можно без специальных SDK.

## DOCX

`.docx` = zip. Текст лежит в `word/document.xml`. Картинки в `word/media/`.

```bash
unzip -o file.docx -d docx-out
# Текст: docx-out/word/document.xml — выдерни <w:t> элементы
# Картинки: docx-out/word/media/*.{png,jpg}
```

> **`unzip` есть не везде.** На Windows его нет ни в системе, ни в Git Bash (там
> только `tar.exe`, а в PowerShell — `Expand-Archive`). Python в паке обязателен, и
> его `zipfile` делает то же самое на всех трёх ОС — им и распаковывай, если `unzip`
> не нашёлся:
>
> ```bash
> python -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" file.docx docx-out
> ```
>
> Готовая обёртка с фолбэком — `templates/extract-doc.sh` (см. «Команды-обёртки» ниже).

Извлечь текст:

```js
import fs from 'node:fs/promises';
import { XMLParser } from 'fast-xml-parser';
const xml = await fs.readFile('docx-out/word/document.xml', 'utf8');
const j = new XMLParser({ ignoreAttributes: false }).parse(xml);
function collect(n, out = []) {
  if (!n) return out;
  if (typeof n === 'string') { out.push(n); return out; }
  for (const k of Object.keys(n)) {
    if (k === 'w:t') {
      const v = n[k];
      if (typeof v === 'string') out.push(v);
      else if (Array.isArray(v)) v.forEach(x => out.push(x['#text'] || x));
      else out.push(v['#text'] || '');
    } else if (typeof n[k] === 'object') {
      Array.isArray(n[k]) ? n[k].forEach(c => collect(c, out)) : collect(n[k], out);
    }
  }
  return out;
}
console.log(collect(j).join(' '));
```

## PPTX

`.pptx` = zip. Каждый слайд — `ppt/slides/slide1.xml`, `slide2.xml`, …
Текст — в `<a:t>` тегах. Картинки в `ppt/media/`.

```bash
unzip -o file.pptx -d pptx-out
# нет unzip (Windows, Git Bash) — тем же Python:
# python -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" file.pptx pptx-out
ls pptx-out/ppt/slides/   # slide1.xml slide2.xml ...
ls pptx-out/ppt/media/    # image1.png image2.jpeg ...
```

Тот же подход что для docx, только другой XML-namespace.

## PDF

Без бинарных тулов сложно. Варианты:

1. **pdf-parse** (Node, чистый JS) — текст:
   ```bash
   npm i pdf-parse
   ```
   ```js
   import fs from 'node:fs/promises';
   import pdf from 'pdf-parse';
   const buf = await fs.readFile('brief.pdf');
   const data = await pdf(buf);
   console.log(data.text);
   ```

2. **pdftotext** (poppler-utils, через CLI) — лучше качество:
   ```bash
   pdftotext -layout brief.pdf brief.txt
   ```

3. **pdfimages** — извлечь картинки:
   ```bash
   pdfimages -all brief.pdf out/img
   ```

## Скетч / фото доски / .napkin

Если пользователь кинул фото маркерной доски или скетч от руки — это просто картинка. Не пытайся «распознать» руками. Действия:

1. Открой картинку, прочитай глазами (через свой visual capability).
2. Опиши вслух: «вижу 3 экрана, на первом форма входа, на втором лента, на третьем настройки».
3. Спроси у пользователя, всё ли правильно понял.
4. Дальше — обычный flow.

Если файл `.napkin` — это рисовалка с JSON-данными внутри. Картинка-превью обычно лежит рядом — её и читай.

## Что использовать после импорта

- **Тексты PRD/брифа** → как контент слайдов или основу копирайта прототипа.
- **Картинки из PPTX** → если это диаграммы / скрины из старого дека, можно повторно использовать как ассеты.
- **Картинки из PDF** → обычно low-res, годятся как референс, не как финальные ассеты.
- **Скетч-фото** → референс структуры экранов, не финальная разметка.

## Команды-обёртки

`templates/extract-doc.sh` — распаковывает docx / pptx / sketch и вынимает текст из PDF:

```bash
bash templates/extract-doc.sh file.docx [out-dir]
```

Скрипт сам ищет, чем распаковать: сперва `unzip`, если его нет — `python3`/`python`
и стандартный `zipfile`. Имя интерпретатора тоже проверяется в обе стороны
(`python3` нет на Windows, `python` нет на macOS 12.3+ и голой Ubuntu). Если нет ни
того ни другого — печатает, чего именно не хватает, и выходит с ненулевым кодом,
а не создаёт пустую папку и «✓».

Для PDF нужен `pdftotext` (пакет poppler); без него скрипт скажет это явно и
продолжит с остальным, а не отчитается об успехе.

Полный текст — в самом файле `templates/extract-doc.sh`; здесь он намеренно не
дублируется: копия в документации уже успела разойтись с оригиналом.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-document-import.md`. Секции там: PDF, DOCX, PPTX, Sketch (legacy), Структурирование вывода, Извлечение по типам, Качество текста, Изображения из документов, Антипаттерны.
