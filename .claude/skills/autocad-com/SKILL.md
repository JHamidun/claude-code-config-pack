---
name: autocad-com
description: "AutoCAD/GstarCAD/ZWCAD/BricsCAD/nanoCAD из Python через COM: чертежи, размеры, 3D-тела, листы. Симптомы: «RPC недоступен», размер без текста. Только Windows."
---

# AutoCAD over COM

## Что нужно до начала

**Только Windows.** COM/ActiveX — механизм Windows; на macOS и Linux этот навык
неприменим целиком, а не частично.

```bash
pip install pywin32 pillow
```

`pywin32` даёт `win32com`, `pythoncom` и `win32gui`; `pillow` нужен только для
снятия скриншота окна. CAD должен быть **установлен и запущен** — навык
подключается к работающему приложению, а не поднимает его с нуля.

Проверить связку одной строкой, не открывая редактор:

```bash
python -c "import win32com.client as c; print(c.GetActiveObject('AutoCAD.Application').Name)"
```

Ошибка здесь читается по тексту — таблица в разделе «Connecting» разбирает три
разных случая, которые выглядят одинаково.

## Overview

Any CAD with the AutoCAD-compatible ActiveX object model is driven the same way
from Python: `win32com.client` talks to a **running** application, and the drawing
is built by calling methods on `ModelSpace`. Nothing is installed into the CAD,
nothing is compiled, and `SECURELOAD` / `TRUSTEDPATHS` never enter the picture
because no code is loaded inside the application.

**Core principle:** the COM layer lies quietly. Calls return success, variables
read back the value you set, and the drawing is still wrong. Verify geometry by
measuring it (`GetBoundingBox`, `Volume`, entity counts), never by reading back
the setting you just wrote.

## When to Use

- Drawing or editing entities, layers, blocks, dimensions, hatches, 3D solids
- Building paper-space sheets and viewports
- Reading a drawing's contents or measuring what is in it
- Diagnosing why a CAD will not accept an external connection

**Do not use for:** AutoCAD LT — it is not an ActiveX server and cannot be reached
from another process at all. Its only automation surface is AutoLISP text plus
`.scr` scripts. Nothing in this skill applies to it.

## Connecting

```python
import pythoncom, win32com.client
pythoncom.CoInitialize()
app = win32com.client.GetActiveObject("AutoCAD.Application")   # already running
```

`GetActiveObject` attaches to a running instance; `Dispatch` launches one, slowly
and with focus stealing. Prefer the former, fall back to the latter.

Read the COM error text — it distinguishes three different situations:

| Error text | Meaning |
|---|---|
| `Недопустимая строка с указанием класса` (CO_E_CLASSSTRING) | ProgID not registered — the program is not installed |
| `Операция недоступна` (MK_E_UNAVAILABLE) | Registered, but no instance running |
| `Ошибка при выполнении приложения-сервера` (CO_E_SERVER_EXEC_FAILURE) | Windows tried to launch it and the process died |

ProgIDs: `AutoCAD.Application` (also versioned, `.26` = 2027), `GstarCAD.Application`,
`ZWCAD.Application`, `BricscadApp.AcadApplication`, `nanoCAD.Application`.

On the Start tab no document exists — `app.ActiveDocument` raises, so catch it and
call `app.Documents.Add()`.

## Points and arrays

Every point argument is a VARIANT array of doubles, never a Python list:

```python
from win32com.client import VARIANT

def pt(x, y, z=0.0):
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), float(z)])
```

Polylines take one flat array `[x1, y1, x2, y2, ...]`. Object arrays (hatch
boundaries) take `VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [...])`.

## Quick reference — the failures that cost real time

| Symptom | Cause | Fix |
|---|---|---|
| Dimension lines drawn, no text or arrows | `SetVariable("DIMSCALE", n)` does not reach entities created through ActiveX | `dim.ScaleFactor = n` on the object, then `doc.Regen(1)` |
| Mass/filter by colour misses the biggest parts | Boolean resets the result to ByLayer (256) | Identify parts by volume or layer, never by colour after a Boolean |
| `Сервер RPC недоступен`, AutoCAD gone | Deleted every object in a layout, including its last viewport | Delete only `ObjectName != "AcDbViewport"`; reuse existing viewports |
| `Ошибка при установке текущего видового экрана` | `ActivePViewport` set before entering model space | `doc.MSpace = True` first, then assign |
| `PlotToFile` returns True, no file or a 2 KB stub | `BACKGROUNDPLOT` defaults to 2 | Set it to 0; prefer building the PDF outside the CAD |
| `Недопустимый аргумент type в ZoomScaled` | Wrong enum | 0 absolute, 1 relative, 2 relative-to-paper |
| `Неоднородное масштабирование невозможно` | Solids accept uniform scaling only — a sphere cannot be squashed into an ellipsoid | Build oval bodies from an elliptical profile: `AddEllipse` → `AddRegion` → `AddExtrudedSolid` |
| `Неверный ввод` from `AddRegion` | `AddPolyline` makes a 3D polyline, and a region needs a planar curve | Draw the profile as a lightweight polyline in XY, then `Rotate3D` it upright |
| Drawing extents far larger than the model | `AddRegion`, `AddExtrudedSolid` and `AddRevolvedSolid` do not consume their input | Delete the source curve and the region after creating the solid |
| `Вызов был отклонен` (RPC_E_CALL_REJECTED) | The application is busy redrawing | Retry the call after a second; it is transient, not an error in the code |
| Every property suddenly fails with `<unknown>.Name`, `<unknown>.Count` | An unterminated `SendCommand` left the CAD waiting at the command line, which blocks the whole ActiveX interface. It looks exactly like a corrupt pywin32 cache and is not — clearing `gen_py` changes nothing | Send ESC to the window (`WScript.Shell.SendKeys("{ESC}")`), then set visual styles through system variables instead: `VSFACESTYLE=1`, `VSEDGES=2`. Guard with `doc.GetVariable("CMDACTIVE")` |
| `Вызванный объект был отключен от клиентов` | Read a property of a document after `Close()` | Capture `.Name` before closing |
| A newly added document has no `ModelSpace` | `Documents.Add()` returns before the document is usable | Retry for a few seconds |
| Module list shows only `ntdll` + `wow64*` | 64-bit tooling cannot enumerate a 32-bit process | Use `C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe` |
| Window screenshots land ~300 px off | Display scaling above 100 % | `ctypes.windll.user32.SetProcessDPIAware()` before `GetWindowRect` |
| Screenshot grab fails, or the window "is not found" | Matched windows by title and size; a minimised frame reports a tiny rect and tooltips share the title | Match by owning process id, `ShowWindow(RESTORE)` then `MAXIMIZE`, poll until the rect is big |
| A property tooltip sits in the middle of the capture | The cursor is hovering over a solid | `SetCursorPos` to a corner before grabbing |

## Verify by measuring

```python
mn, mx = solid.GetBoundingBox()          # returns two 3-tuples
print(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
print(solid.Volume / 1e6, "litres")
```

Cross-check the volume against a hand calculation before trusting a model. A shell
built as outer-box minus cavity minus opening must equal the sum of its equivalent
plates; if it does not, the geometry is wrong regardless of how it looks on screen.

## Commands and language

`SendCommand` is asynchronous and returns nothing — anything that depends on its
result must wait, and a following `ZoomExtents` will otherwise run first. Prefix
commands with `.` and options with `_` so they survive a localised build:
`doc.SendCommand("._VSCURRENT\n_E\n")`.

## Implementation

`cookbook.py` in this directory holds working helpers: connection with fallback,
point and object arrays, 3D solid construction with Booleans, cylinders on the X
and Y axes, dimension creation that is actually visible, paper-space sheets, and
window capture. Copy what is needed rather than importing it.

Отдельно стоит знать про четыре из них — они закрывают ровно те ловушки, что
описаны выше, и без них таблица симптомов остаётся теорией:

| Помощник | Закрывает |
|---|---|
| `attach_only()` | подключиться, но **не запускать** CAD: пакетный прогон, чужая машина, работа по расписанию. У `connect()` запуск — штатное поведение |
| `send_command()` | асинхронность `SendCommand`: ждёт по `CMDACTIVE`, пока команда действительно завершится, и снимает зависшую через ESC |
| `visual_style()` | то же, что `._VSCURRENT`, но системными переменными — не трогает командную строку и потому не может её подвесить |
| `cad_window()` | поиск окна по идентификатору процесса с разворачиванием и ожиданием настоящего размера, вместо совпадения по заголовку |

## Common mistakes

- **Trusting a system variable read-back.** `DIMSCALE` reads 50 while entities
  render at 2.5. Measure the entity, not the variable.
- **Screenshotting a shaded view on a white background.** Colour 7 is white on
  dark and black on light; a plan on a white figure can look completely empty
  while every entity is present. Count entities before concluding anything.
- **Assuming a colour survives editing.** Only Booleans reset it, which is exactly
  when it matters most.
- **Plotting from the CAD.** The PDF drivers plot in the background and fail
  silently. Generating the sheet with matplotlib from the same data is faster and
  actually verifiable.