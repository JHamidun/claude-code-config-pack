---
name: xlsx
description: "Excel .xlsx на openpyxl: создать книгу, править существующую без потери формул, форматирование, ширины, заморозка, автофильтр, диаграммы, чтение посчитанных значений. Триггеры: «эксель», «xlsx», «таблица Excel», «запиши в таблицу», «формулы в экселе». НЕ анализ данных и графики → csv-analysis; НЕ Google Sheets → google-workspace."
metadata:
  version: 1.0.0
  updated: 2026-08-23
  license: MIT (этот навык написан для пака; сторонний код не вендорится)
---

# XLSX

Навык собственный: рецепты поверх `openpyxl`, вендоренного кода нет.

```bash
pip install openpyxl
```

---

## Главное про openpyxl, из-за чего чаще всего теряют данные

`openpyxl` **не считает формулы**. В книге живут две вещи: сама формула
(`=SUM(A1:A9)`) и последнее значение, которое посчитал Excel. Режим чтения
выбирает, что вернётся:

```python
from openpyxl import load_workbook

wb_f = load_workbook("book.xlsx")                  # data_only=False — формулы
wb_v = load_workbook("book.xlsx", data_only=True)  # значения, посчитанные Excel'ем
```

Из этого следуют два правила, которые надо держать в голове одновременно:

1. **Читать значения — `data_only=True`.** Иначе в ячейке окажется строка
   `"=SUM(A1:A9)"`, и она молча уедет в отчёт как текст.
2. **Сохранять после `data_only=True` — нельзя.** Такое сохранение записывает
   значения на место формул: файл откроется, цифры будут те же, а формулы
   исчезнут навсегда. Правку делать только на книге, открытой без `data_only`.

И третье, менее очевидное: если книгу создала не Excel, а скрипт, посчитанных
значений в ней нет вообще — `data_only=True` вернёт `None` у каждой формулы.
Файл, собранный `openpyxl`, обязан быть хоть раз открыт и сохранён Excel'ем
(или LibreOffice), прежде чем из него можно будет прочитать результаты.

Проверять это надо явно, иначе получите отчёт из `None`:

```python
vals = [c.value for c in wb_v["Лист1"]["D2:D10"][0]]
if all(v is None for v in vals):
    raise SystemExit("в книге нет посчитанных значений — её ни разу не открывал Excel")
```

---

## Создать книгу

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Отчёт"

headers = ["Дата", "Канал", "Расход", "Лиды", "CPL"]
ws.append(headers)

rows = [
    ("2026-08-01", "Директ", 42000, 61, "=C2/D2"),
    ("2026-08-01", "VK Ads", 18500, 24, "=C3/D3"),
]
for r in rows:
    ws.append(r)

# шапка
head_fill = PatternFill("solid", fgColor="1F3864")
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = head_fill
    c.alignment = Alignment(horizontal="center", vertical="center")

# форматы чисел
for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
    for c in row:
        c.number_format = '# ##0\\ ₽'
for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
    for c in row:
        c.number_format = '# ##0.00'

ws.freeze_panes = "A2"                       # шапка не уезжает при прокрутке
ws.auto_filter.ref = ws.dimensions           # автофильтр на всю таблицу

# ширины по содержимому
for i, _ in enumerate(headers, 1):
    letter = get_column_letter(i)
    width = max(len(str(c.value or "")) for c in ws[letter]) + 2
    ws.column_dimensions[letter].width = min(width, 50)

wb.save("report.xlsx")
```

## Править существующую книгу

```python
from openpyxl import load_workbook

wb = load_workbook("book.xlsx")          # без data_only — формулы уцелеют
ws = wb["Данные"]

ws["B2"] = 12345
ws.cell(row=3, column=2, value="=B2*1.2")

if "Свод" not in wb.sheetnames:
    wb.create_sheet("Свод")

wb.save("book.xlsx")
```

Записать в открытый в Excel файл нельзя — `PermissionError`. Это единственная
причина этой ошибки на практике; закрыть файл и повторить.

## Большие файлы

```python
# чтение построчно, память не растёт
wb = load_workbook("big.xlsx", read_only=True, data_only=True)
for row in wb["Лист1"].iter_rows(values_only=True):
    ...
wb.close()          # read_only держит открытый дескриптор — закрывать обязательно

# запись потоком
from openpyxl import Workbook
wb = Workbook(write_only=True)
ws = wb.create_sheet("Данные")
ws.append(["id", "значение"])
for i in range(1_000_000):
    ws.append([i, i * 3])
wb.save("big-out.xlsx")
```

В `write_only` нельзя обращаться к ячейкам по адресу и нельзя вернуться к
записанной строке — только `append` вперёд.

## Диаграмма

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.title = "Расход по каналам"
data = Reference(ws, min_col=3, min_row=1, max_row=ws.max_row)
cats = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.height, chart.width = 8, 16
ws.add_chart(chart, "G2")
```

## CSV → XLSX и обратно

```python
import csv
from openpyxl import Workbook, load_workbook

wb = Workbook(); ws = wb.active
with open("in.csv", encoding="utf-8-sig", newline="") as f:
    for row in csv.reader(f, delimiter=";"):
        ws.append(row)
wb.save("out.xlsx")

wb = load_workbook("out.xlsx", data_only=True)
with open("back.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    for row in wb.active.iter_rows(values_only=True):
        w.writerow(["" if v is None else v for v in row])
```

`utf-8-sig` — не украшение: без BOM русский Excel открывает CSV в `cp1251` и
показывает кракозябры, а с BOM определяет UTF-8 сам.

---

## Грабли

- **Сохранение книги, открытой с `data_only=True`, стирает все формулы.** Самая
  дорогая ошибка в этом навыке.
- **`data_only=True` даёт `None`, если книгу не открывал Excel.** Файл, собранный
  скриптом, посчитанных значений не содержит.
- **Формула пишется строкой и всегда с латинскими именами функций** —
  `=SUM(...)`, не `=СУММ(...)`. Русские имена Excel показывает сам, но в файле
  они хранятся по-английски; `=СУММ` уедет в ячейку как текст.
- **Разделитель аргументов в файле — запятая**, независимо от региональных
  настроек: `=IF(A1>0,1,0)`.
- **Формат числа — не значение.** `number_format = '0.00'` меняет отображение;
  само значение остаётся полным.
- **`ws.max_row` считает и пустые строки с форматированием**, поэтому «последняя
  строка» иногда оказывается на сотни ниже данных. Надёжнее искать последнюю
  непустую самому.
- **Ширины столбцов openpyxl не считает** — `auto_size` в формате не существует,
  ширину задаёт скрипт (рецепт выше).
- **Файлы `.xls` (старый формат) openpyxl не открывает вообще.** Их надо сначала
  пересохранить в `.xlsx` — навык `file-converter` (LibreOffice) это умеет.
