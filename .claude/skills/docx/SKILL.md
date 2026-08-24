---
name: docx
description: "Word .docx на python-docx: собрать документ, править существующий, стили и нумерация, таблицы, картинки, колонтитулы, разбор чужого файла, чтение правок и комментариев через XML. Триггеры: «docx», «word», «документ Word», «сделай ворд», «tracked changes», «правки в документе». НЕ конвертация форматов → file-converter; НЕ вёрстка отчёта под клиента → kp-deck-factory."
metadata:
  version: 1.0.0
  updated: 2026-08-23
  license: MIT (этот навык написан для пака; сторонний код не вендорится)
---

# DOCX

Навык собственный: рецепты поверх `python-docx`, вендоренного кода нет.

```bash
pip install python-docx        # импортируется как `docx`, не как `python_docx`
```

Готовый рабочий пример на 300 строк, который собирает отчёт с обложкой,
нативными стилями Word и таблицами, уже лежит в паке:
`.claude/skills/seo-machine-ru/scripts/build_report_docx.py` — его удобно брать
за скелет.

---

## Собрать документ

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK

doc = Document()

# базовый шрифт всего документа
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

doc.add_heading("Отчёт за квартал", level=0)      # level=0 — Title
doc.add_heading("Что изменилось", level=1)

p = doc.add_paragraph("Расход вырос на ")
r = p.add_run("18%")
r.bold = True
r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
p.add_run(" при падении CPL.")

doc.add_paragraph("CPL упал до 690 ₽", style="List Bullet")
doc.add_paragraph("Доля Директа — 61%", style="List Bullet")
doc.add_paragraph("Первый шаг", style="List Number")

doc.add_page_break()
doc.save("report.docx")
```

Имена встроенных стилей — английские (`List Bullet`, `List Number`, `Quote`,
`Intense Quote`, `Caption`), даже в русском Word. Русское имя даст
`KeyError: no style with name 'Маркированный список'`.

## Разобрать чужой документ

```python
from docx import Document

doc = Document("in.docx")
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f"{i:3} [{p.style.name}] {p.text[:90]}")

for t, table in enumerate(doc.tables, 1):
    print(f"--- таблица {t}: {len(table.rows)}×{len(table.columns)}")
    for row in table.rows:
        print(" | ".join(c.text.strip() for c in row.cells))
```

**`doc.paragraphs` не содержит текст из таблиц, колонтитулов, сносок и
надписей.** Поэтому «в документе ничего нет» при непустом файле — обычная
ситуация: текст лежит в таблице. Полный обход в порядке документа:

```python
from docx.document import Document as _Doc
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

def iter_blocks(parent):
    el = parent.element.body if isinstance(parent, _Doc) else parent._tc
    for child in el.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

for block in iter_blocks(doc):
    if isinstance(block, Paragraph):
        print(block.text)
    else:
        for row in block.rows:
            for cell in row.cells:
                for b in iter_blocks(cell):
                    if isinstance(b, Paragraph):
                        print("  ", b.text)
```

## Править существующий

```python
doc = Document("in.docx")
for p in doc.paragraphs:
    for run in p.runs:
        if "{{ДАТА}}" in run.text:
            run.text = run.text.replace("{{ДАТА}}", "23.08.2026")
doc.save("out.docx")
```

Как и в PowerPoint, Word рвёт абзац на `run`-ы произвольно, и плейсхолдер может
оказаться разрезан. Проверять число замен и падать громко:

```python
hits = sum(r.text.count("PLACEHOLDER") for p in doc.paragraphs for r in p.runs)
if not hits:
    raise SystemExit("плейсхолдер не найден — либо шаблон не тот, либо текст разрезан на runs")
```

Присваивание `paragraph.text = "..."` уничтожает всё форматирование абзаца —
менять только внутри `run`.

## Таблица

```python
from docx.shared import Cm

data = [["Канал", "Расход", "Лиды"],
        ["Директ", "42 000", "61"],
        ["VK Ads", "18 500", "24"]]

table = doc.add_table(rows=0, cols=3)
table.style = "Light Grid Accent 1"
for r, row in enumerate(data):
    cells = table.add_row().cells
    for c, val in enumerate(row):
        cells[c].text = val
        if r == 0:
            cells[c].paragraphs[0].runs[0].bold = True
table.columns[0].width = Cm(6)
```

Ширина колонки в Word задаётся у **каждой ячейки**, а не у колонки — установка
`columns[i].width` часто не действует. Надёжно:

```python
for row in table.rows:
    row.cells[0].width = Cm(6)
```

## Картинка, ориентация, колонтитулы

```python
from docx.shared import Cm
from docx.enum.section import WD_ORIENT

doc.add_picture("chart.png", width=Cm(16))       # высота посчитается сама

sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width   # обязательно вручную
sec.left_margin = sec.right_margin = Cm(2)

sec.header.paragraphs[0].text = "ООО «Ромашка» · внутренний документ"
sec.footer.paragraphs[0].text = "23.08.2026"
```

Смена `orientation` **не меняет размеры страницы** — их надо переставить самому,
иначе альбомный документ останется по ширине книжного.

## Правки и комментарии (tracked changes)

python-docx этого не умеет: ни принять правку, ни оставить комментарий, ни
прочитать их штатно. Всё это лежит в XML внутри zip-архива:

```python
import zipfile
from defusedxml import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
with zipfile.ZipFile("in.docx") as z:
    body = z.read("word/document.xml").decode("utf-8")
    root = ET.fromstring(body)
    ins = root.findall(".//w:ins", NS)      # вставки
    dele = root.findall(".//w:del", NS)     # удаления
    print("вставок:", len(ins), "удалений:", len(dele))
    if "word/comments.xml" in z.namelist():
        croot = ET.fromstring(z.read("word/comments.xml").decode("utf-8"))
        for c in croot.findall("w:comment", NS):
            author = c.get("{%s}author" % NS["w"])
            text = "".join(t.text or "" for t in c.findall(".//w:t", NS))
            print(f"[{author}] {text}")
```

`defusedxml` вместо `xml.etree` — потому что документ пришёл извне, а разбор
чужого XML стандартным парсером открывает XXE. Пакет уже в `requirements.txt`.

**Принять или отклонить правки программно надёжнее всего не питоном, а
LibreOffice**, и это же единственный способ конвертировать в PDF:

```bash
soffice --headless --convert-to pdf --outdir out/ in.docx
```

---

## Грабли

- **Пакет ставится как `python-docx`, а импортируется как `docx`.**
  `pip install docx` поставит чужой заброшенный пакет 2014 года, и импорт
  сломается непонятным образом.
- **`doc.paragraphs` не видит таблицы, колонтитулы и надписи.** «Документ пустой»
  чаще всего означает «текст в таблице» — полный обход выше.
- **`paragraph.text = ...` стирает форматирование**; правка по `run`-ам.
- **Плейсхолдер, разрезанный на runs, не находится.** Считать число замен.
- **Русские имена стилей не работают** — только английские.
- **Смена ориентации не меняет размер страницы** — переставлять `page_width`
  и `page_height` руками.
- **Ширина колонки задаётся по ячейкам**, не по `table.columns`.
- **Нумерация списков продолжается сквозь документ.** Начать заново python-docx
  штатно не умеет — либо править XML `numbering.xml`, либо готовить шаблон в
  Word и подставлять текст.
- **Кириллица в консоли Windows** — `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
