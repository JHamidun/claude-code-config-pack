---
name: pptx
description: "PowerPoint .pptx на python-pptx: собрать колоду, править чужую, разобрать по слайдам, заметки докладчика, таблицы, картинки, замена текста с сохранением оформления. Триггеры: «pptx», «PowerPoint», «поправь слайд», «заметки докладчика», «собери колоду». НЕ HTML-дек → export-pptx; НЕ дизайн слайдов → manus-slides."
metadata:
  version: 1.0.0
  updated: 2026-08-23
  license: MIT (этот навык написан для пака; сторонний код не вендорится)
---

# PPTX

Навык собственный: рецепты поверх `python-pptx`, вендоренного кода нет.

```bash
pip install python-pptx
```

Единицы измерения в PowerPoint — EMU. Руками их не считают, берут хелперы:

```python
from pptx.util import Inches, Pt, Emu
Inches(1)   # дюйм
Pt(18)      # пункт (кегль и размеры)
```

Слайд 16:9 — 13.333 × 7.5 дюйма; 4:3 — 10 × 7.5.

---

## Разобрать чужую колоду

С этого стоит начинать любую правку: имена макетов и порядок плейсхолдеров у
каждого шаблона свои, угадывать их бесполезно.

```python
from pptx import Presentation

prs = Presentation("deck.pptx")
print("слайдов:", len(prs.slides), "| размер:", prs.slide_width, prs.slide_height)

for i, layout in enumerate(prs.slide_layouts):
    print(i, layout.name)

for n, slide in enumerate(prs.slides, 1):
    print(f"--- слайд {n}  (макет: {slide.slide_layout.name})")
    for sh in slide.shapes:
        kind = sh.shape_type
        text = sh.text_frame.text.replace("\n", " / ")[:70] if sh.has_text_frame else ""
        ph = sh.placeholder_format.idx if sh.is_placeholder else "-"
        print(f"   [{ph}] {sh.name!r:28} {kind}  {text}")
    if slide.has_notes_slide:
        print("   заметки:", slide.notes_slide.notes_text_frame.text[:100])
```

## Собрать колоду

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)   # 16:9

# титул
s = prs.slides.add_slide(prs.slide_layouts[0])
s.shapes.title.text = "Итоги квартала"
s.placeholders[1].text = "Отдел маркетинга · август 2026"

# заголовок + текст
s = prs.slides.add_slide(prs.slide_layouts[1])
s.shapes.title.text = "Что изменилось"
tf = s.placeholders[1].text_frame
tf.text = "Расход вырос на 18%"
for line, lvl in [("CPL упал до 690 ₽", 1), ("Доля Директа — 61%", 1)]:
    p = tf.add_paragraph()
    p.text = line
    p.level = lvl

# пустой слайд со своей надписью
s = prs.slides.add_slide(prs.slide_layouts[6])
box = s.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(2))
p = box.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
run.text = "690 ₽"
run.font.size = Pt(96)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

prs.save("deck.pptx")
```

`slide_layouts[6]` в стандартном шаблоне — «Blank». В чужом шаблоне номер
другой: искать по имени, а не по индексу.

```python
blank = next(l for l in prs.slide_layouts if l.name.lower() in ("blank", "пустой слайд"))
```

## Заметки докладчика

```python
slide.notes_slide.notes_text_frame.text = "Здесь сказать про сезонность, 40 секунд."
```

Обращение к `slide.notes_slide` создаёт страницу заметок, если её не было.
Проверять существование — `slide.has_notes_slide`.

## Картинка

```python
from pptx.util import Inches

pic = slide.shapes.add_picture("chart.png", Inches(1), Inches(1.5), width=Inches(8))
# высота посчитается сама и пропорции сохранятся — если задать ТОЛЬКО одну сторону
```

Задать и `width`, и `height` — значит растянуть картинку; пропорции python-pptx
не бережёт.

## Таблица

```python
rows, cols = 3, 4
tbl = slide.shapes.add_table(rows, cols, Inches(1), Inches(1.5),
                             Inches(11), Inches(0.8 * rows)).table
tbl.columns[0].width = Inches(4)
data = [["Канал", "Расход", "Лиды", "CPL"],
        ["Директ", "42 000", "61", "689"],
        ["VK Ads", "18 500", "24", "771"]]
for r, row in enumerate(data):
    for c, val in enumerate(row):
        cell = tbl.cell(r, c)
        cell.text = val
        cell.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
```

## Замена текста без потери оформления

Присваивание `shape.text_frame.text = "..."` **сносит всё форматирование абзаца**
— размер, цвет, жирность. Чтобы сохранить вид, менять текст надо в каждом
`run` по отдельности:

```python
def replace_everywhere(prs, mapping):
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    for old, new in mapping.items():
                        if old in run.text:
                            run.text = run.text.replace(old, new)

replace_everywhere(prs, {"{{КЛИЕНТ}}": "ООО «Ромашка»", "{{ДАТА}}": "23.08.2026"})
```

Ограничение метода: PowerPoint рвёт текст на `run`-ы произвольно (проверка
орфографии, правки), поэтому плейсхолдер `{{КЛИЕНТ}}` может оказаться разрезан
на `{{КЛИ` и `ЕНТ}}` и не найтись. Надёжный приём — держать в шаблоне
плейсхолдер **одним словом без пробелов и скобок** (`KLIENT`), а перед заменой
проверять, что он нашёлся:

```python
found = sum(run.text.count("KLIENT")
            for sl in prs.slides for sh in sl.shapes if sh.has_text_frame
            for p in sh.text_frame.paragraphs for run in p.runs)
if not found:
    raise SystemExit("плейсхолдер KLIENT не найден — шаблон не тот или текст разрезан на runs")
```

## Удалить и переставить слайды

В python-pptx нет публичного API ни для того, ни для другого — работать
приходится с XML списка слайдов:

```python
def drop_slide(prs, index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    rid = slides[index].get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    prs.part.drop_rel(rid)
    xml_slides.remove(slides[index])

def move_slide(prs, old, new):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[old])
    xml_slides.insert(new, slides[old])
```

Это единственное место навыка, где трогаются приватные атрибуты. Работает,
но при обновлении библиотеки надо перепроверять.

## Экспорт в PDF и картинки

python-pptx рендерить не умеет — только собирает файл. Отрисовка через
LibreOffice:

```bash
soffice --headless --convert-to pdf --outdir out/ deck.pptx
```

Пути к `soffice`, если его нет в `PATH`: macOS
`/Applications/LibreOffice.app/Contents/MacOS/soffice`, Windows
`C:\Program Files\LibreOffice\program\soffice.exe`.

---

## Грабли

- **`text_frame.text = ...` затирает форматирование.** Правка по `run`-ам — выше.
- **Плейсхолдер, разрезанный на runs, не находится** заменой по тексту. Проверять
  число совпадений и падать громко, а не молча сохранять неподменённый файл.
- **Индексы макетов зависят от шаблона.** `slide_layouts[6]` — «Blank» только в
  стандартном; в корпоративном там что угодно. Искать по `layout.name`.
- **Размер слайда задаётся у презентации, а не у слайда**, и до добавления
  слайдов — иначе уже созданные останутся в старой геометрии.
- **`add_picture` с двумя сторонами растягивает картинку.** Задавать одну.
- **Кириллица в консоли Windows** — `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- **Комментарии PowerPoint (не заметки) python-pptx не читает и не пишет.**
  Если задача про них — распаковывать `.pptx` как zip и смотреть
  `ppt/comments/`.
