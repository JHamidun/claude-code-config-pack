"""
Working helpers for driving an AutoCAD-compatible CAD over COM from Python.

Copy the pieces you need into your script; this file is a reference, not a
library to import. Every function here was exercised against AutoCAD 2027
(ProgID AutoCAD.Application.26) on Windows 11.
"""

import ctypes
import math
import time

import pythoncom
import win32com.client
import win32gui
from win32com.client import VARIANT

PROGIDS = [
    "AutoCAD.Application",
    "GstarCAD.Application",
    "ZWCAD.Application",
    "BricscadApp.AcadApplication",
    "nanoCAD.Application",
]

ACAD_UNION, ACAD_INTERSECT, ACAD_SUBTRACT = 0, 1, 2
ZOOM_ABSOLUTE, ZOOM_RELATIVE, ZOOM_PSPACE = 0, 1, 2
SHADE_AS_DISPLAYED, SHADE_WIREFRAME, SHADE_HIDDEN, SHADE_RENDERED = 0, 1, 2, 3


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------

def connect(progids=None):
    """Attach to a running CAD, else start one. Reports why each attempt failed.

    The error text matters: CO_E_CLASSSTRING means the program is not installed,
    MK_E_UNAVAILABLE means it is installed but not running, and
    CO_E_SERVER_EXEC_FAILURE means Windows launched it and the process died.
    """
    pythoncom.CoInitialize()
    failures = []
    candidates = list(progids or PROGIDS)

    # Порядок важен, и раньше он был неверным. Перебор «для каждого CAD сперва
    # GetActiveObject, потом Dispatch» означает, что при незапущенном AutoCAD
    # он ЗАПУСТИТСЯ — медленно и отбирая фокус — прежде чем код вообще
    # попробует подключиться к уже работающему GstarCAD.
    # Сначала обходим все ProgID на предмет РАБОТАЮЩЕГО приложения и только
    # потом, вторым проходом, соглашаемся что-то поднимать.
    for grab in (win32com.client.GetActiveObject, win32com.client.Dispatch):
        for progid in candidates:
            try:
                app = grab(progid)
                try:
                    app.Visible = True
                except pythoncom.com_error:
                    pass
                return app
            except pythoncom.com_error as exc:
                failures.append(f"{progid} / {grab.__name__}: {exc.strerror or exc}")
    raise RuntimeError("no CAD reachable over COM:\n  " + "\n  ".join(failures))


def attach_only(progids=None):
    """Подключиться к уже работающему CAD и НЕ поднимать ничего.

    Нужно, когда запуск приложения недопустим: пакетный прогон, чужая машина,
    сессия по расписанию. Отдельной функцией, потому что у `connect` запуск —
    штатное поведение, и отличить одно от другого флагом легко забыть.
    """
    pythoncom.CoInitialize()
    failures = []
    for progid in progids or PROGIDS:
        try:
            return win32com.client.GetActiveObject(progid)
        except pythoncom.com_error as exc:
            failures.append(f"{progid}: {exc.strerror or exc}")
    raise RuntimeError("нет ЗАПУЩЕННОГО CAD:\n  " + "\n  ".join(failures))


def document(app):
    """Active document, creating one if the CAD is sitting on its Start tab."""
    try:
        return app.ActiveDocument
    except pythoncom.com_error:
        return app.Documents.Add()


# --------------------------------------------------------------------------
# Arguments: COM will not accept plain Python lists
# --------------------------------------------------------------------------

def com_retry(fn, tries=15, delay=1.0):
    """Retry a call the application refused because it was busy.

    "Вызов был отклонен" (RPC_E_CALL_REJECTED) and RPC_E_SERVERCALL_RETRYLATER
    are transient: the CAD is mid-redraw. Everything else is a real error and is
    re-raised immediately.
    """
    last = None
    for _ in range(tries):
        try:
            return fn()
        except pythoncom.com_error as exc:
            if exc.hresult not in (-2147418111, -2147417846):
                raise
            last = exc
            time.sleep(delay)
    raise last


def new_document(app, tries=20):
    """Add a document and wait until it is actually usable.

    Documents.Add() returns before the document is ready; touching ModelSpace
    straight away can raise while the CAD is still setting it up.
    """
    doc = com_retry(lambda: app.Documents.Add())
    for _ in range(tries):
        try:
            _ = doc.ModelSpace
            return doc
        except (AttributeError, pythoncom.com_error):
            time.sleep(0.5)
    raise RuntimeError("new document never became usable")


def close_documents(app, keep=()):
    """Close documents by name. Read every name BEFORE closing anything: once
    Close() runs, the COM object is disconnected and even .Name raises."""
    for doc, name in [(d, d.Name) for d in app.Documents]:
        if name in keep:
            continue
        try:
            com_retry(lambda d=doc: d.Close(False))
        except pythoncom.com_error:
            pass


def pt(x, y, z=0.0):
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(x), float(y), float(z)])


def doubles(values):
    """Flat array, e.g. a polyline as [x1, y1, x2, y2, ...]."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for v in values])


def objects(items):
    """Object array, e.g. hatch boundary loops."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, list(items))


# --------------------------------------------------------------------------
# 2D
# --------------------------------------------------------------------------

def rectangle(msp, x, y, w, h, layer=None):
    poly = msp.AddLightWeightPolyline(
        doubles([x, y, x + w, y, x + w, y + h, x, y + h])
    )
    poly.Closed = True
    if layer:
        poly.Layer = layer
    return poly


def ring_hatch(msp, outer, inner, pattern="ANSI31", scale=40.0, layer=None):
    """Hatch the band between two closed polylines — a wall body, for instance."""
    hatch = msp.AddHatch(0, pattern, True)          # 0 = predefined pattern
    hatch.AppendOuterLoop(objects([outer]))
    hatch.AppendInnerLoop(objects([inner]))
    hatch.PatternScale = scale
    hatch.Evaluate()
    if layer:
        hatch.Layer = layer
    return hatch


def linear_dim(msp, p1, p2, text_pos, scale, vertical=False, layer=None):
    """A dimension that is actually visible.

    Setting the DIMSCALE system variable does NOT reach entities created through
    ActiveX: the drawing gets dimension lines with 2.5-unit text, invisible on
    anything measured in millimetres. ScaleFactor on the object does work.
    """
    dim = msp.AddDimRotated(
        pt(*p1), pt(*p2), pt(*text_pos), math.pi / 2 if vertical else 0.0
    )
    dim.ScaleFactor = float(scale)
    if layer:
        dim.Layer = layer
    return dim


# --------------------------------------------------------------------------
# 3D solids
# --------------------------------------------------------------------------

def box(msp, x0, y0, z0, dx, dy, dz, color=None):
    """AddBox takes the CENTRE, which is rarely what you have."""
    solid = msp.AddBox(
        pt(x0 + dx / 2, y0 + dy / 2, z0 + dz / 2), float(dx), float(dy), float(dz)
    )
    if color is not None:
        solid.color = color
    return solid


def cylinder_z(msp, x, y, z0, radius, height, color=None):
    solid = msp.AddCylinder(pt(x, y, z0 + height / 2), float(radius), float(height))
    if color is not None:
        solid.color = color
    return solid


def cylinder_along(msp, axis, x, y, z, radius, length, color=None):
    """Cylinder on the X or Y axis: build on Z, tip it over, then move it."""
    solid = cylinder_z(msp, 0, 0, -length / 2, radius, length, color)
    if axis == "y":
        solid.Rotate3D(pt(0, 0, 0), pt(1, 0, 0), math.pi / 2)
    elif axis == "x":
        solid.Rotate3D(pt(0, 0, 0), pt(0, 1, 0), math.pi / 2)
    solid.Move(pt(0, 0, 0), pt(x, y, z))
    return solid


def oval_frustum(msp, cx, cy, z_top, semi_x, semi_y, height, taper_deg, color=None):
    """Oval tapered body — a seat shell, a lampshade, a planter.

    A sphere scaled unevenly would be the obvious route to an oval body, but
    AutoCAD refuses it: "Неоднородное масштабирование невозможно". Solids scale
    uniformly only, so the oval has to come from an elliptical PROFILE.
    Extrude with a negative height to grow downwards from the rim.
    """
    ell = msp.AddEllipse(pt(cx, cy, z_top), pt(semi_x, 0, 0), semi_y / semi_x)
    region = msp.AddRegion(objects([ell]))[0]
    solid = msp.AddExtrudedSolid(region, -float(height), math.radians(taper_deg))
    region.Delete()          # neither call consumes its input; both linger
    ell.Delete()             # in the drawing and inflate the extents
    if color is not None:
        solid.color = color
    return solid


def revolve_profile(msp, points, color=None):
    """Revolve a (radius, height) profile a full turn about Z.

    AddRegion needs a PLANAR curve, and AddPolyline produces a 3D polyline that
    it rejects with "Неверный ввод". So draw the profile as a lightweight
    polyline in the XY plane — X reads as radius, Y as height — then stand it
    upright into XZ before revolving.
    """
    flat = []
    for r, z in points:
        flat += [float(r), float(z)]
    poly = msp.AddLightWeightPolyline(
        VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
    )
    poly.Closed = True
    region = msp.AddRegion(objects([poly]))[0]
    region.Rotate3D(pt(0, 0, 0), pt(1, 0, 0), math.pi / 2)
    solid = msp.AddRevolvedSolid(region, pt(0, 0, 0), pt(0, 0, 1), 2 * math.pi)
    region.Delete()
    poly.Delete()
    if color is not None:
        solid.color = color
    return solid


def tube_between(msp, p1, p2, radius, color=None):
    """Cylinder spanning two arbitrary points: build on Z, aim it, move it."""
    dx, dy, dz = (p2[i] - p1[i] for i in range(3))
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    tube = msp.AddCylinder(pt(0, 0, 0), float(radius), length)
    horizontal = math.hypot(dx, dy)
    if horizontal > 1e-9:                       # already aligned if purely vertical
        tube.Rotate3D(pt(0, 0, 0), pt(-dy, dx, 0), math.atan2(horizontal, dz))
    tube.Move(pt(0, 0, 0),
              pt((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2))
    if color is not None:
        tube.color = color
    return tube


def dish_radius(chord, depth):
    """Radius of the sphere that scoops a depression of the given chord and
    depth. Cutting with anything smaller turns a seat into a funnel."""
    return (chord ** 2 / 4 + depth ** 2) / (2 * depth)


def hollow(msp, outer, inner):
    """outer.Boolean(SUBTRACT, inner) consumes inner and returns nothing.

    The result keeps outer's identity but its colour is reset to ByLayer (256).
    Never identify parts by colour after this — use volume or layer.
    """
    outer.Boolean(ACAD_SUBTRACT, inner)
    return outer


def measure(entity):
    """Prove the geometry rather than eyeballing it."""
    mn, mx = entity.GetBoundingBox()
    size = tuple(mx[i] - mn[i] for i in range(3))
    try:
        volume = entity.Volume
    except pythoncom.com_error:
        volume = None
    return size, volume


# --------------------------------------------------------------------------
# Командная строка CAD
# --------------------------------------------------------------------------

def command_active(doc):
    """Ждёт ли CAD ввода в командной строке.

    Пока ждёт, ActiveX не отвечает НИ НА ЧТО: падает и `.Name`, и `.Count`, и
    любое свойство. Симптом один в один как у испорченного кэша pywin32, и
    чистка `gen_py` не помогает, потому что дело не в ней.
    """
    try:
        return int(doc.GetVariable("CMDACTIVE")) != 0
    except pythoncom.com_error:
        return True          # не смогли даже спросить — считаем, что занят


def send_escape(title_fragment="AutoCAD"):
    """Выдать ESC в окно CAD, чтобы снять зависшую команду."""
    shell = win32com.client.Dispatch("WScript.Shell")
    if shell.AppActivate(title_fragment):
        time.sleep(0.3)
        shell.SendKeys("{ESC}")
        shell.SendKeys("{ESC}")
        time.sleep(0.3)
        return True
    return False


def send_command(doc, text, title_fragment="AutoCAD", settle=0.4, tries=8):
    """`SendCommand` с проверкой, что команда ЗАВЕРШИЛАСЬ.

    Сам вызов асинхронный и ничего не возвращает: следующая строка кода
    выполнится, пока CAD ещё думает. Хуже, если команда осталась недописанной —
    тогда приложение замирает на вводе и блокирует весь интерфейс.

    Точки и подчёркивания в начале обязательны (`._VSCURRENT`, `_E`): без них
    команда не переживёт локализованную сборку.
    """
    if command_active(doc):                       # чужая команда уже висит
        send_escape(title_fragment)
    doc.SendCommand(text)
    for _ in range(tries):
        time.sleep(settle)
        if not command_active(doc):
            return True
    send_escape(title_fragment)                   # не завершилась — снимаем сами
    raise RuntimeError(
        f"команда не завершилась и оставила CAD ждать ввода: {text!r}. "
        f"ESC отправлен. Проверь, что все аргументы переданы и строка "
        f"заканчивается переводом строки.")


def visual_style(doc, face=1, edges=2):
    """Стиль отображения БЕЗ SendCommand.

    `._VSCURRENT` требует диалога с командной строкой и потому легко оставляет
    её висеть. Системные переменные делают то же самое и ничего не блокируют.
    """
    doc.SetVariable("VSFACESTYLE", int(face))
    doc.SetVariable("VSEDGES", int(edges))
    doc.Regen(1)


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------

def set_view(app, doc, direction, zoom_out=0.9):
    """direction points from the target towards the viewer."""
    vp = doc.ActiveViewport
    vp.direction = pt(*direction)
    doc.ActiveViewport = vp
    app.ZoomExtents()
    if zoom_out:
        app.ZoomScaled(zoom_out, ZOOM_RELATIVE)


# --------------------------------------------------------------------------
# Paper space
# --------------------------------------------------------------------------

def prepare_layout(doc, layout_name, device="DWG To PDF.pc3", media=None):
    lay = doc.Layouts.Item(layout_name)
    doc.ActiveLayout = lay
    doc.MSpace = False
    lay.ConfigName = device
    lay.RefreshPlotDeviceInfo()
    if media:
        lay.CanonicalMediaName = media
    lay.PlotType = 5                       # 5 = acLayout, the sheet at 1:1
    return lay


def clear_sheet(doc):
    """Strip a layout without killing AutoCAD.

    Deleting every object in a layout deletes its last viewport too, and the
    application goes down with "RPC server unavailable". Keep the viewports and
    hand them back for reuse.
    """
    ps = doc.PaperSpace
    spare = []
    for obj in list(ps):
        try:
            if obj.ObjectName == "AcDbViewport":
                spare.append(obj)
            else:
                obj.Delete()
        except pythoncom.com_error:
            pass
    return ps, spare


def fit_viewport(app, doc, vp):
    """Zoom a viewport to its contents. MSpace must be on BEFORE assigning."""
    doc.MSpace = True
    doc.ActivePViewport = vp
    app.ZoomExtents()
    app.ZoomScaled(0.85, ZOOM_RELATIVE)
    doc.MSpace = False


# --------------------------------------------------------------------------
# Screen capture
# --------------------------------------------------------------------------

SW_RESTORE, SW_MAXIMIZE = 9, 3


def cad_window(pid=None, title_fragment=None, min_side=400, tries=20):
    """Найти ГЛАВНОЕ окно CAD, а не первое совпавшее по заголовку.

    Совпадение по заголовку ненадёжно сразу по двум причинам, и обе описаны в
    SKILL.md: всплывающая подсказка носит тот же заголовок, что и окно, а
    свёрнутое окно отдаёт крошечный прямоугольник — снимок получается пустым
    или обрезанным. Поэтому окно ищется по идентификатору ПРОЦЕССА, затем
    разворачивается, и код ждёт, пока прямоугольник не станет настоящим.
    """
    import win32process

    found = []

    def visit(h, _):
        if not win32gui.IsWindowVisible(h):
            return
        if pid is not None:
            _, wpid = win32process.GetWindowThreadProcessId(h)
            if wpid != pid:
                return
        elif title_fragment and title_fragment not in win32gui.GetWindowText(h):
            return
        l, t, r, b = win32gui.GetWindowRect(h)
        found.append((h, (r - l) * (b - t)))

    win32gui.EnumWindows(visit, None)
    if not found:
        raise RuntimeError(
            f"окна не нашлось (pid={pid}, заголовок={title_fragment!r})")

    hwnd = max(found, key=lambda x: x[1])[0]      # главное окно — самое большое
    win32gui.ShowWindow(hwnd, SW_RESTORE)
    win32gui.ShowWindow(hwnd, SW_MAXIMIZE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass                                       # Windows иногда запрещает, не критично

    for _ in range(tries):                         # ждём, пока окно развернётся
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        if (r - l) >= min_side and (b - t) >= min_side:
            return hwnd
        time.sleep(0.25)
    raise RuntimeError("окно так и не развернулось до нормального размера")


def capture(title_fragment=None, pid=None, crop=(12, 245, 12, 105),
            park_cursor=True):
    """Снимок окна CAD. crop = (слева, сверху, справа, снизу) в пикселях.

    `SetProcessDPIAware` обязателен первым: без него `GetWindowRect` отдаёт
    логические пиксели, и на экране с масштабом снимок уезжает на сотни точек.

    Курсор отводится в угол: если он висит над телом, CAD рисует всплывающую
    подсказку со свойствами прямо посреди кадра.
    """
    from PIL import ImageGrab

    ctypes.windll.user32.SetProcessDPIAware()
    hwnd = cad_window(pid=pid, title_fragment=title_fragment)

    if park_cursor:
        ctypes.windll.user32.SetCursorPos(5, 5)
    time.sleep(1.2)

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return ImageGrab.grab(
        bbox=(left + crop[0], top + crop[1], right - crop[2], bottom - crop[3]),
        all_screens=True,
    )