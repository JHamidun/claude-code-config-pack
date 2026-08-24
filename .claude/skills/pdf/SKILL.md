---
name: pdf
description: "Работа с PDF на pypdf/pdfplumber: вытащить текст и таблицы, склеить, разрезать, повернуть, снять пароль, заполнить форму, отрисовать страницы в PNG. Триггеры: «пдф», «вытащи текст из pdf», «merge PDF», «split PDF», «заполни форму pdf», «pdf в картинки». НЕ печать HTML в PDF → export-pdf; НЕ битый OCR → ocr-restore."
metadata:
  version: 1.0.0
  updated: 2026-08-23
  license: MIT (этот навык написан для пака; сторонний код не вендорится)
---

# PDF

Навык собственный: здесь нет вендоренного кода, только рецепты поверх обычных
пакетов PyPI. Ставится всё одной строкой:

```bash
pip install pypdf pdfplumber pdf2image
```

`pdf2image` дополнительно требует бинарники **poppler** на `PATH`
(`pdftoppm`, `pdftocairo`):

| ОС | Как поставить |
|---|---|
| Windows | `winget install oschwartz10612.Poppler` либо архив poppler-windows, затем добавить `…\poppler\bin` в `PATH` |
| macOS | `brew install poppler` |
| Debian/Ubuntu | `sudo apt install poppler-utils` |

Проверка одной командой — `pdftoppm -v`. Если её нет, всё, что ниже помечено
«нужен poppler», работать не будет; остальное будет.

---

## Что чем делать

| Задача | Инструмент |
|---|---|
| Текст страницы, метаданные, склейка, разрезание, поворот, пароль | `pypdf` |
| Таблицы, координаты слов, разметка страницы | `pdfplumber` |
| Страница → PNG/JPEG | `pdf2image` (нужен poppler) |
| HTML-макет → PDF | навык `export-pdf` (Playwright), не этот |
| Скан без текстового слоя | сначала OCR, потом сюда; чистка распознанного — навык `ocr-restore` |

---

## Извлечь текст

```python
from pypdf import PdfReader

reader = PdfReader("doc.pdf")
print(len(reader.pages), "страниц")
text = "\n".join((page.extract_text() or "") for page in reader.pages)
```

`extract_text()` возвращает `None` для страницы без текстового слоя — отсюда
`or ""`. **Пустая строка на выходе почти всегда означает скан, а не пустой файл.**
Проверить это надо явно, иначе дальше по конвейеру поедет пустота:

```python
if not text.strip():
    raise SystemExit("PDF без текстового слоя (скан?) — нужен OCR, extract_text() бесполезен")
```

Точнее и с раскладкой — `pdfplumber`:

```python
import pdfplumber

with pdfplumber.open("doc.pdf") as pdf:
    page = pdf.pages[0]
    print(page.extract_text(layout=True))      # сохранить колонки
    for w in page.extract_words()[:5]:
        print(w["text"], w["x0"], w["top"])    # координаты в пунктах, начало отсчёта сверху
```

## Таблицы

```python
import pdfplumber

with pdfplumber.open("report.pdf") as pdf:
    for i, page in enumerate(pdf.pages, 1):
        for t, table in enumerate(page.extract_tables(), 1):
            print(f"--- стр. {i}, таблица {t}: {len(table)} строк")
            for row in table:
                print(" | ".join("" if c is None else c.replace("\n", " ") for c in row))
```

Таблица без линий (разделение только пробелами) по умолчанию не находится —
надо переключить стратегию:

```python
settings = {"vertical_strategy": "text", "horizontal_strategy": "text"}
tables = page.extract_tables(settings)
```

## Склеить, разрезать, повернуть

```python
from pypdf import PdfReader, PdfWriter

# склейка
w = PdfWriter()
for f in ["a.pdf", "b.pdf"]:
    for page in PdfReader(f).pages:
        w.add_page(page)
w.write("merged.pdf")

# страницы 3–7 (человеческая нумерация) в отдельный файл
r = PdfReader("in.pdf")
w = PdfWriter()
for page in r.pages[2:7]:
    w.add_page(page)
w.write("part.pdf")

# повернуть все страницы на 90° по часовой
r = PdfReader("in.pdf"); w = PdfWriter()
for page in r.pages:
    page.rotate(90)
    w.add_page(page)
w.write("rotated.pdf")
```

## Пароль

```python
from pypdf import PdfReader, PdfWriter

r = PdfReader("locked.pdf")
if r.is_encrypted:
    if not r.decrypt("пароль"):          # 0 = пароль не подошёл
        raise SystemExit("пароль не подошёл")
w = PdfWriter()
for page in r.pages:
    w.add_page(page)
w.write("open.pdf")

# поставить пароль
w = PdfWriter(clone_from="open.pdf")
w.encrypt("новый-пароль", algorithm="AES-256")
w.write("locked2.pdf")
```

## Формы AcroForm

Сначала посмотреть, какие поля вообще есть — угадывать имена бесполезно:

```python
from pypdf import PdfReader

fields = PdfReader("form.pdf").get_fields() or {}
for name, f in fields.items():
    print(repr(name), f.get("/FT"), "=", f.get("/V"))
```

`/FT` — тип поля: `/Tx` текст, `/Btn` галочка или радиокнопка, `/Ch` выпадающий
список. Пустой словарь означает, что формы в файле нет: поля нарисованы,
заполнять их программно нечем — тогда либо печатать текст поверх, либо просить
исходник с формой.

```python
from pypdf import PdfReader, PdfWriter

r = PdfReader("form.pdf")
w = PdfWriter(clone_from=r)
w.update_page_form_field_values(
    w.pages[0],
    {"ФИО": "Иванов Иван", "Дата": "23.08.2026"},
    auto_regenerate=False,
)
w.set_need_appearances_writer(True)   # иначе часть читалок покажет поле пустым
w.write("filled.pdf")
```

`set_need_appearances_writer(True)` — та самая строчка, без которой заполненная
форма открывается пустой в Acrobat, хотя значения в файле лежат. Проверять
результат надо чтением обратно, а не тем, что скрипт не упал:

```python
back = PdfReader("filled.pdf").get_fields()
assert back["ФИО"].get("/V") == "Иванов Иван", back["ФИО"].get("/V")
```

Галочка ставится не `True`, а именем состояния из самого файла (обычно `/Yes`,
но бывает `/On`, `/1`):

```python
states = fields["Согласен"]["/_States_"]     # что реально принимает поле
w.update_page_form_field_values(w.pages[0], {"Согласен": states[0]})
```

## Страницы в картинки (нужен poppler)

```python
from pdf2image import convert_from_path

pages = convert_from_path("doc.pdf", dpi=200, first_page=1, last_page=3)
for i, img in enumerate(pages, 1):
    img.save(f"page-{i:03d}.png", "PNG")
```

Если poppler не установлен, вызов падает с `PDFInfoNotInstalledError` — это
понятная ошибка, не глушить её `try/except`.

## Метаданные

```python
from pypdf import PdfReader, PdfWriter

print(PdfReader("doc.pdf").metadata)         # /Title, /Author, /CreationDate…

w = PdfWriter(clone_from="doc.pdf")
w.add_metadata({"/Title": "Отчёт", "/Author": "—"})
w.write("doc-clean.pdf")
```

Метаданные — частый канал утечки: там остаются имя автора, название организации
и путь к исходнику. Перед отправкой файла наружу их стоит перезаписать.

---

## Грабли

- **Пустой текст ≠ пустой PDF.** Скан не имеет текстового слоя; `extract_text()`
  честно вернёт пустоту, а конвейер поедет дальше. Проверять явно (см. выше).
- **Кириллица в консоли Windows.** Печать извлечённого текста падает
  `UnicodeEncodeError` в `cp1251`. В начале скрипта:
  `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- **`PdfWriter()` без `clone_from` теряет формы, закладки и вложения** — при
  правке существующего файла всегда `PdfWriter(clone_from=...)`.
- **Координаты `pdfplumber` считаются от верха страницы** (`top`), а внутри
  PDF-модели — от низа (`y0`). Смешивать их нельзя.
- **`pypdf` не растеризует.** «Сделать из PDF картинку» — только через poppler
  либо через `pdftoppm` напрямую.
