# -*- coding: utf-8 -*-
"""
Общий холст листа для всех модулей альбома: SVG (Sheet) и DXF (DxfCanvas) с ОДНИМ API,
чтобы любая функция компоновки рисовала оба выхода без изменений.

Содержит всё «ГОСТовское», что повторяется на 40 листах:
  форматы (ГОСТ 2.301) · рамка с графами левого поля · штамп ГОСТ 21.101 форма 3 (185×55)
  и малый штамп продолжения (форма 6, 185×15) · размерные цепочки с засечками 45°
  · таблицы · выноски-полки · штриховки · цветовой словарь эталона · View (мм мира → мм листа).

Координаты страницы — мм, начало в левом верхнем углу, Y вниз (как в SVG).
View переводит мировые координаты плана (Y вверх) в страничные.
"""

import math
import re

# ------------------------------------------------------------ форматы ГОСТ 2.301 --
# (ширина, высота) в мм, альбомная ориентация; «P» — портрет. Подпись — как под рамкой эталона.
FORMATS = {
    "A4":   (210, 297, "А4"),      # портрет (спецификации)
    "A4L":  (297, 210, "А4"),
    "A3":   (420, 297, "А3"),
    "A3P":  (297, 420, "А3"),      # портрет (спецификации в эталоне — А3 вертикальный)
    "A2":   (594, 420, "А2"),
    "A3x3": (891, 420, "А3х3"),    # все планы эталона
    "A4x3": (630, 297, "А4х3"),
    "A4x4": (841, 297, "А4х4"),
    "A4x5": (1051, 297, "А4х5"),
    "A4x6": (1261, 297, "А4х6"),
}
MARGIN_LEFT, MARGIN = 20, 5          # рамка: слева 20 (подшивка), остальные 5
STAMP_W, STAMP_H, STAMP_SMALL_H = 185, 55, 15

# ------------------------------------------------------------ цветовой словарь эталона --
INK = "#111111"
COLOR = {
    "ink": INK,
    "grey": "#6f6f6f",         # существующие стены (заливка/контур)
    "grey_fill": "#c9c9c9",
    "grey_light": "#e6e6e6",
    "blue": "#1c4fb0",         # всё новое: ГСП, размеры к ним, розетки, выключатели
    "orange": "#e07b1a",       # кирпич/пеноблок закладки
    "red": "#c1272d",          # стояки, демонтаж, шторы, тёплый пол, свет, выводы
    "green": "#2e8b3c",        # остекление лоджий
    "cyan": "#1aa3b8",         # сантехника, стекло
    "magenta": "#b83fb8",
    "beige": "#d9c7a5",
    "brown": "#8b6a3e",
    "veneer": "#c6bcb0",       # штриховка шпон (мебель)
    "glass": "#e4e4e4",
    "enamel": "#ececec",
    "plan_fill": "#e3e3e3",
    "dark_red": "#8a1c20",
    "cut_mark": "#535353",
}
# слои DXF → цвет ACI
DXF_LAYERS = {
    "0": 7, "FRAME": 7, "STAMP": 7, "TEXT": 7, "DIMS": 7, "TABLE": 7, "LEGEND": 7,
    "WALLS_EXIST": 8, "WALLS_NEW": 5, "DEMOLITION": 1, "DOORS": 7, "WINDOWS": 7, "GLASS": 4,
    "FURNITURE": 8, "FLOOR": 7, "CEILING": 7, "LIGHT": 1, "POWER": 5, "OUTPUTS": 1,
    "HATCH": 8, "RISERS": 1, "LOGGIA": 3, "TILE": 5, "FINISH": 7, "SANITARY": 4,
}
FONT = ("'ISOCPEUR', 'GOST type B', 'GOST Type BU', 'PT Sans Narrow', "
        "'Arial Narrow', Arial, Helvetica, sans-serif")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def fmt_coord(v):
    return f"{v:.2f}"


# ======================================================================= Sheet (SVG) ==

class Sheet:
    """SVG-лист. Все методы принимают мм страницы."""

    def __init__(self, fmt="A3"):
        if fmt not in FORMATS:
            raise KeyError(f"неизвестный формат {fmt!r}; есть {list(FORMATS)}")
        self.fmt = fmt
        self.W, self.H, self.fmt_label = FORMATS[fmt]
        self.e = []
        self.defs = {}
        self.current_layer = "0"
        self.frame = (MARGIN_LEFT, MARGIN, self.W - MARGIN, self.H - MARGIN)   # x0, y0, x1, y1

    # ---------------------------------------------------------------- слои / служебное --
    def set_layer(self, name):
        self.current_layer = str(name).upper()

    def _la(self):
        return f' data-layer="{esc(self.current_layer)}"'

    def raw(self, svg_fragment):
        self.e.append(svg_fragment)

    def view(self, scale, ox, oy):
        return View(self, scale, ox, oy)

    # ---------------------------------------------------------------- примитивы --
    def line(self, x1, y1, x2, y2, w=0.18, dash=None, color=INK):
        if abs(x2 - x1) < 1e-9 and abs(y2 - y1) < 1e-9:
            return
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                      f'stroke="{color}" stroke-width="{w}"{d} stroke-linecap="round"{self._la()}/>')

    def rect(self, x, y, w, h, sw=0.18, fill="none", color=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                      f'fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}{self._la()}/>')

    def frect(self, x, y, w, h, fill=INK):
        self.e.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                      f'fill="{fill}" stroke="none"{self._la()}/>')

    def circle(self, cx, cy, r, sw=0.2, fill="none", color=INK, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}" '
                      f'stroke="{color}" stroke-width="{sw}"{d}{self._la()}/>')

    def ellipse(self, cx, cy, rx, ry, sw=0.15, fill="none", color=INK):
        self.e.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                      f'fill="{fill}" stroke="{color}" stroke-width="{sw}"{self._la()}/>')

    def dot(self, cx, cy, r=0.5, color=INK):
        self.e.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{color}"{self._la()}/>')

    def path(self, d, w=0.18, fill="none", color=INK, dash=None):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{w}"{ds} '
                      f'stroke-linecap="round" stroke-linejoin="round"{self._la()}/>')

    def poly(self, pts, w=0.18, fill="none", color=INK, dash=None):
        """Незамкнутая ломаная."""
        if len(pts) < 2:
            return
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<polyline points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}"{ds} '
                      f'stroke-linecap="round" stroke-linejoin="round"{self._la()}/>')

    def polygon(self, pts, w=0.18, fill="none", color=INK, dash=None):
        """Замкнутый многоугольник; fill может быть url(#pattern)."""
        if len(pts) < 3:
            return
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.e.append(f'<polygon points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}"{ds} '
                      f'stroke-linejoin="round"{self._la()}/>')

    def arc(self, cx, cy, r, a0, a1, w=0.18, color=INK, dash=None):
        """Дуга от угла a0 до a1 (градусы, против часовой в мировых координатах → на странице Y вниз)."""
        x0, y0 = cx + r * math.cos(math.radians(a0)), cy - r * math.sin(math.radians(a0))
        x1, y1 = cx + r * math.cos(math.radians(a1)), cy - r * math.sin(math.radians(a1))
        large = 1 if abs(a1 - a0) > 180 else 0
        sweep = 0 if a1 > a0 else 1
        self.path(f"M {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 {large} {sweep} {x1:.2f} {y1:.2f}",
                  w=w, color=color, dash=dash)

    def text(self, x, y, s, size=2.5, anchor="middle", bold=False, italic=True, rot=None,
             color=INK, underline=False, family=None):
        st = []
        if bold:
            st.append('font-weight="bold"')
        if italic:
            st.append('font-style="italic"')
        if underline:
            st.append('text-decoration="underline"')
        if family:
            st.append(f'font-family="{family}"')
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        self.e.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" '
                      f'fill="{color}" {" ".join(st)}{tr}{self._la()}>{esc(s)}</text>')

    def text_lines(self, x, y, lines, size=2.5, lh=None, anchor="start", **kw):
        lh = lh or size * 1.45
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size, anchor=anchor, **kw)
        return y + len(lines) * lh

    def tick(self, x, y, r=1.0, w=0.35):
        """Засечка размерной линии 45° (ГОСТ 2.307)."""
        self.line(x - r, y + r, x + r, y - r, w)

    def hatch(self, name, color=INK, spacing=1.5, angle=45, w=0.12, bg=None):
        """Регистрирует штриховку и возвращает fill='url(#name)'. Шаг — мм на бумаге."""
        if name not in self.defs:
            s = spacing
            bgr = f'<rect width="{s}" height="{s}" fill="{bg}"/>' if bg else ""
            self.defs[name] = (
                f'<pattern id="{name}" patternUnits="userSpaceOnUse" width="{s}" height="{s}" '
                f'patternTransform="rotate({angle})">{bgr}'
                f'<line x1="0" y1="0" x2="0" y2="{s}" stroke="{color}" stroke-width="{w}"/></pattern>')
        return f"url(#{name})"

    def cross_hatch(self, name, color=INK, spacing=1.5, w=0.12, bg=None):
        if name not in self.defs:
            s = spacing
            bgr = f'<rect width="{s}" height="{s}" fill="{bg}"/>' if bg else ""
            self.defs[name] = (
                f'<pattern id="{name}" patternUnits="userSpaceOnUse" width="{s}" height="{s}" '
                f'patternTransform="rotate(45)">{bgr}'
                f'<line x1="0" y1="0" x2="0" y2="{s}" stroke="{color}" stroke-width="{w}"/>'
                f'<line x1="0" y1="0" x2="{s}" y2="0" stroke="{color}" stroke-width="{w}"/></pattern>')
        return f"url(#{name})"

    def dots_pattern(self, name, color=INK, spacing=1.2, r=0.15):
        if name not in self.defs:
            s = spacing
            self.defs[name] = (f'<pattern id="{name}" patternUnits="userSpaceOnUse" width="{s}" height="{s}">'
                               f'<circle cx="{s/2}" cy="{s/2}" r="{r}" fill="{color}"/></pattern>')
        return f"url(#{name})"

    def image(self, x, y, w, h, href):
        """Растровая картинка (фото светильника в спецификации): href — data:URI или путь."""
        self.e.append(f'<image x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                      f'href="{esc(href)}" preserveAspectRatio="xMidYMid meet"{self._la()}/>')

    # ---------------------------------------------------------------- вывод --
    def svg(self, font_face_css=""):
        defs = "".join(self.defs.values())
        style = f"<style>{font_face_css}</style>" if font_face_css else ""
        body = "\n".join(self.e)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}mm" height="{self.H}mm" '
                f'viewBox="0 0 {self.W} {self.H}" font-family="{FONT}">\n{style}<defs>{defs}</defs>\n'
                f'<rect x="0" y="0" width="{self.W}" height="{self.H}" fill="white"/>\n{body}\n</svg>')


# ======================================================================= View ==

class View:
    """Мировые мм (Y вверх) → мм страницы. X = ox + x/scale, Y = oy − y/scale.
    ox, oy — страничные координаты мировой точки (0, 0)."""

    def __init__(self, sh, scale, ox, oy):
        self.sh, self.scale, self.ox, self.oy = sh, float(scale), ox, oy

    def X(self, x):
        return self.ox + x / self.scale

    def Y(self, y):
        return self.oy - y / self.scale

    def P(self, pt):
        return (self.X(pt[0]), self.Y(pt[1]))

    def L(self, mm):
        """Длина мира → длина на бумаге."""
        return mm / self.scale

    def pts(self, poly):
        return [self.P(p) for p in poly]

    def line(self, a, b, **kw):
        self.sh.line(self.X(a[0]), self.Y(a[1]), self.X(b[0]), self.Y(b[1]), **kw)

    def poly(self, poly, **kw):
        self.sh.poly(self.pts(poly), **kw)

    def polygon(self, poly, **kw):
        self.sh.polygon(self.pts(poly), **kw)

    def rect(self, x0, y0, x1, y1, **kw):
        """Прямоугольник мира по двум углам."""
        self.sh.rect(self.X(min(x0, x1)), self.Y(max(y0, y1)), abs(x1 - x0) / self.scale,
                     abs(y1 - y0) / self.scale, **kw)

    def frect(self, x0, y0, x1, y1, fill=INK):
        self.sh.frect(self.X(min(x0, x1)), self.Y(max(y0, y1)), abs(x1 - x0) / self.scale,
                      abs(y1 - y0) / self.scale, fill=fill)

    def circle(self, c, r_mm, **kw):
        self.sh.circle(self.X(c[0]), self.Y(c[1]), r_mm / self.scale, **kw)

    def text(self, pt, s, size=2.5, **kw):
        self.sh.text(self.X(pt[0]), self.Y(pt[1]), s, size, **kw)

    def dot(self, pt, r=0.5, **kw):
        self.sh.dot(self.X(pt[0]), self.Y(pt[1]), r, **kw)

    def arc(self, c, r_mm, a0, a1, **kw):
        self.sh.arc(self.X(c[0]), self.Y(c[1]), r_mm / self.scale, a0, a1, **kw)


# ======================================================================= DxfCanvas ==

def _san(s):
    cleaned = re.sub(r"\s+", " ", str(s).replace("\r", " ").replace("\n", " ")).strip()
    return (cleaned.replace("≤", "<=").replace("≥", ">=").replace("×", "x").replace("Δ", "D")
            .replace("—", "-").replace("–", "-").replace("·", "-").replace("²", "2")
            .replace("°", "гр.").replace("₽", "руб").replace("…", "...").replace("Ø", "D"))


def _hatch_lines(poly, spacing, angle_deg):
    """Линии штриховки внутри полигона (для DXF): поворот → горизонтальные сканлайны → обратно."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(-a), math.sin(-a)
    rot = [(x * ca - y * sa, x * sa + y * ca) for x, y in poly]
    ys = [p[1] for p in rot]
    y = math.floor(min(ys) / spacing) * spacing
    out = []
    n = len(rot)
    while y <= max(ys):
        xs = []
        for i in range(n):
            x1, y1 = rot[i]
            x2, y2 = rot[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            ca2, sa2 = math.cos(a), math.sin(a)
            p = (xs[j] * ca2 - y * sa2, xs[j] * sa2 + y * ca2)
            q = (xs[j + 1] * ca2 - y * sa2, xs[j + 1] * sa2 + y * ca2)
            out.append((p, q))
        y += spacing
    return out


_ACI_PALETTE = {1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 160, 0), 4: (0, 200, 220), 5: (0, 0, 255),
                6: (200, 0, 200), 7: (0, 0, 0), 8: (128, 128, 128), 9: (200, 200, 200), 30: (255, 127, 0),
                41: (200, 160, 100), 33: (150, 100, 50)}


def aci_color(color):
    """SVG-цвет (#rrggbb) → ближайший индекс ACI. INK/None → 256 (по слою)."""
    if not color or color == INK or color == "none":
        return None
    s = str(color).lstrip("#")
    if len(s) != 6:
        return None
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    if max(r, g, b) < 40:
        return None                                      # чёрный — цвет слоя
    best = min(_ACI_PALETTE.items(), key=lambda kv: (kv[1][0] - r) ** 2 + (kv[1][1] - g) ** 2 + (kv[1][2] - b) ** 2)
    return best[0]


def _svg_arc_points(p0, rx, ry, phi_deg, large, sweep, p1, n=16):
    """Дуга SVG (endpoint-параметризация) → точки; по W3C SVG 1.1 §F.6.5."""
    x1, y1 = p0
    x2, y2 = p1
    if rx == 0 or ry == 0:
        return [p0, p1]
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    out = []
    for k in range(n + 1):
        t = t1 + dt * k / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        out.append((cp * ex - sp * ey + cx, sp * ex + cp * ey + cy))
    return out


class DxfCanvas:
    """Тот же API, что у Sheet; копит DXF R12. Y инвертируется (DXF — Y вверх). cp1251 при записи.
    Цвет примитива передаётся кодом 62 (ближайший ACI), иначе — цвет слоя."""

    def __init__(self, fmt="A3"):
        self.fmt = fmt
        self.W, self.H, self.fmt_label = FORMATS[fmt]
        self.ents = []
        self.defs = {}
        self.current_layer = "0"
        self.frame = (MARGIN_LEFT, MARGIN, self.W - MARGIN, self.H - MARGIN)
        self._pattern_meta = {}

    def set_layer(self, name):
        name = str(name).upper()
        self.current_layer = name if name in DXF_LAYERS else "0"

    def raw(self, _):
        pass

    def view(self, scale, ox, oy):
        return View(self, scale, ox, oy)

    def _y(self, y):
        return self.H - y

    @staticmethod
    def _col(color):
        a = aci_color(color)
        return f"62\n{a}\n" if a else ""

    def _line(self, x1, y1, x2, y2, dash=None, layer=None, color=None):
        if abs(x2 - x1) < 1e-9 and abs(y2 - y1) < 1e-9:
            return
        layer = layer or self.current_layer
        self.ents.append(f"0\nLINE\n8\n{layer}\n{self._col(color)}6\n{'DASHED' if dash else 'CONTINUOUS'}\n"
                         f"10\n{x1:.3f}\n20\n{self._y(y1):.3f}\n30\n0.000\n"
                         f"11\n{x2:.3f}\n21\n{self._y(y2):.3f}\n31\n0.000\n")

    def _polyline(self, pts, width=0.0, closed=False, dash=None, color=None):
        if len(pts) < 2:
            return
        layer = self.current_layer
        body = (f"0\nPOLYLINE\n8\n{layer}\n{self._col(color)}6\n{'DASHED' if dash else 'CONTINUOUS'}\n66\n1\n"
                f"70\n{1 if closed else 0}\n10\n0.000\n20\n0.000\n30\n0.000\n40\n{width:.3f}\n41\n{width:.3f}\n")
        for x, y in pts:
            body += f"0\nYOUR_SERVER\n8\n{layer}\n10\n{x:.3f}\n20\n{self._y(y):.3f}\n30\n0.000\n"
        body += f"0\nSEQEND\n8\n{layer}\n"
        self.ents.append(body)

    def line(self, x1, y1, x2, y2, w=0.18, dash=None, color=None):
        if w >= 0.6:
            self._polyline([(x1, y1), (x2, y2)], width=w, dash=dash, color=color)
        else:
            self._line(x1, y1, x2, y2, dash=dash, color=color)

    def rect(self, x, y, w, h, sw=0.18, fill="none", color=None, dash=None):
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self._polyline(pts, closed=True, dash=dash, color=color)
        self._fill(pts, fill)

    def frect(self, x, y, w, h, fill=None):
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self._polyline(pts, closed=True, color=fill if str(fill).startswith("#") else None)
        self._fill(pts, fill)

    def _fill(self, pts, fill):
        """Штриховка-паттерн → примитивы в слое HATCH с цветом узора. Сплошная заливка в DXF R12 не передаётся
        (нет SOLID-масок): модули обязаны не полагаться на «белые маски», а вырезать геометрию."""
        if not fill or fill == "none" or not str(fill).startswith("url(#"):
            return
        meta = self._pattern_meta.get(fill[5:-1])
        if not meta:
            return
        kind, spacing, angle, color = meta
        if kind == "hatch":
            # SVG: вертикальная линия узора, повёрнутая на angle (по часовой, Y вниз) → на странице это угол 90+angle
            for p, q in _hatch_lines(pts, spacing, 90 + angle):
                self._line(p[0], p[1], q[0], q[1], layer="HATCH", color=color)
        elif kind == "cross":
            for a in (135, 45):
                for p, q in _hatch_lines(pts, spacing, a):
                    self._line(p[0], p[1], q[0], q[1], layer="HATCH", color=color)
        elif kind == "dots":
            x0, y0, x1, y1 = min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)
            n = len(pts)
            y = y0 + spacing / 2
            while y < y1:
                x = x0 + spacing / 2
                while x < x1:
                    # точка внутри полигона (чёт-нечет)
                    inside = False
                    for i in range(n):
                        ax, ay = pts[i]
                        bx, by = pts[(i + 1) % n]
                        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                            inside = not inside
                    if inside:
                        self.ents.append(f"0\nCIRCLE\n8\nHATCH\n{self._col(color)}10\n{x:.3f}\n20\n{self._y(y):.3f}\n"
                                         f"30\n0.000\n40\n{spacing * 0.12:.3f}\n")
                    x += spacing
                y += spacing

    def circle(self, cx, cy, r, sw=0.2, fill="none", color=None, dash=None):
        self.ents.append(f"0\nCIRCLE\n8\n{self.current_layer}\n{self._col(color)}6\n{'DASHED' if dash else 'CONTINUOUS'}\n"
                         f"10\n{cx:.3f}\n20\n{self._y(cy):.3f}\n30\n0.000\n40\n{r:.3f}\n")

    def ellipse(self, cx, cy, rx, ry, sw=0.15, fill="none", color=None):
        pts = [(cx + rx * math.cos(t * math.pi / 18), cy + ry * math.sin(t * math.pi / 18)) for t in range(36)]
        self._polyline(pts, closed=True, color=color)

    def dot(self, cx, cy, r=0.5, color=None):
        self.circle(cx, cy, max(r, 0.3), color=color)

    def poly(self, pts, w=0.18, fill="none", color=None, dash=None):
        self._polyline(list(pts), width=w if w >= 0.6 else 0.0, dash=dash, color=color)

    def polygon(self, pts, w=0.18, fill="none", color=None, dash=None):
        self._polyline(list(pts), closed=True, dash=dash, color=color)
        self._fill(list(pts), fill)

    def arc(self, cx, cy, r, a0, a1, w=0.18, color=None, dash=None):
        lo, hi = (a0, a1) if a1 > a0 else (a1, a0)
        self.ents.append(f"0\nARC\n8\n{self.current_layer}\n{self._col(color)}10\n{cx:.3f}\n20\n{self._y(cy):.3f}\n30\n0.000\n"
                         f"40\n{r:.3f}\n50\n{lo:.2f}\n51\n{hi:.2f}\n")

    def path(self, d, w=0.18, fill="none", color=None, dash=None):
        """M/L/H/V/Q/A/Z (абсолютные и относительные) → полилинии; Q сплющивается, A — по параметризации SVG."""
        toks = re.findall(r"[MLHVQAZmlhvqaz]|-?\d*\.?\d+(?:e-?\d+)?", d)
        pts, cur, start, i = [], None, None, 0

        def flush():
            if len(pts) > 1:
                self.poly(pts, w=w, dash=dash, color=color)

        def num(k):
            return float(toks[i + k])
        while i < len(toks):
            t = toks[i]
            if t in "Mm":
                x, y = num(1), num(2)
                if t == "m" and cur:
                    x, y = cur[0] + x, cur[1] + y
                flush()
                pts, start = [], (x, y)
                cur = (x, y)
                pts.append(cur)
                i += 3
            elif t in "Ll":
                x, y = num(1), num(2)
                if t == "l" and cur:
                    x, y = cur[0] + x, cur[1] + y
                cur = (x, y)
                pts.append(cur)
                i += 3
            elif t in "Hh":
                x = num(1) + (cur[0] if t == "h" and cur else 0)
                cur = (x, cur[1] if cur else 0)
                pts.append(cur)
                i += 2
            elif t in "Vv":
                y = num(1) + (cur[1] if t == "v" and cur else 0)
                cur = (cur[0] if cur else 0, y)
                pts.append(cur)
                i += 2
            elif t in "Qq":
                c = (num(1), num(2))
                p1 = (num(3), num(4))
                if t == "q" and cur:
                    c = (cur[0] + c[0], cur[1] + c[1])
                    p1 = (cur[0] + p1[0], cur[1] + p1[1])
                p0 = cur or c
                for k in range(1, 9):
                    s = k / 8
                    pts.append(((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * c[0] + s ** 2 * p1[0],
                                (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * c[1] + s ** 2 * p1[1]))
                cur = p1
                i += 5
            elif t in "Aa":
                rx, ry, phi, large, sweep = num(1), num(2), num(3), int(num(4)), int(num(5))
                p1 = (num(6), num(7))
                if t == "a" and cur:
                    p1 = (cur[0] + p1[0], cur[1] + p1[1])
                if cur:
                    pts.extend(_svg_arc_points(cur, rx, ry, phi, large, sweep, p1)[1:])
                else:
                    pts.append(p1)
                cur = p1
                i += 8
            elif t in "zZ":
                if start:
                    pts.append(start)
                i += 1
            else:
                i += 1
        flush()

    def text(self, x, y, s, size=2.5, anchor="middle", bold=False, italic=True, rot=None,
             color=None, underline=False, family=None):
        s = _san(s)
        if not s:
            return
        h = size * 0.72
        halign = {"start": 0, "middle": 1, "end": 2}.get(anchor, 1)
        rotation = (-(rot or 0)) % 360
        layer = self.current_layer if self.current_layer in ("STAMP", "TABLE", "DIMS") else "TEXT"
        e = (f"0\nTEXT\n8\n{layer}\n{self._col(color)}10\n{x:.3f}\n20\n{self._y(y):.3f}\n30\n0.000\n40\n{h:.3f}\n"
             f"1\n{s}\n50\n{rotation:.1f}\n7\n{'GOSTI' if italic else 'GOST'}\n")
        if halign:
            e += f"72\n{halign}\n11\n{x:.3f}\n21\n{self._y(y):.3f}\n31\n0.000\n"
        self.ents.append(e)

    def text_lines(self, x, y, lines, size=2.5, lh=None, anchor="start", **kw):
        lh = lh or size * 1.45
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, size, anchor=anchor, **kw)
        return y + len(lines) * lh

    def tick(self, x, y, r=1.0, w=0.35):
        self._line(x - r, y + r, x + r, y - r)

    def hatch(self, name, color=None, spacing=1.5, angle=45, w=0.12, bg=None):
        self._pattern_meta[name] = ("hatch", spacing, angle, color)
        return f"url(#{name})"

    def cross_hatch(self, name, color=None, spacing=1.5, w=0.12, bg=None):
        self._pattern_meta[name] = ("cross", spacing, 45, color)
        return f"url(#{name})"

    def dots_pattern(self, name, color=None, spacing=1.2, r=0.15):
        self._pattern_meta[name] = ("dots", spacing, 0, color)
        return f"url(#{name})"

    def image(self, x, y, w, h, href):
        self.rect(x, y, w, h)

    def dxf(self):
        header = ("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$DWGCODEPAGE\n3\nANSI_1251\n"
                  "9\n$INSBASE\n10\n0.0\n20\n0.0\n30\n0.0\n9\n$EXTMIN\n10\n0.0\n20\n0.0\n30\n0.0\n"
                  f"9\n$EXTMAX\n10\n{self.W:.1f}\n20\n{self.H:.1f}\n30\n0.0\n0\nENDSEC\n")
        layers = "".join(f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in DXF_LAYERS.items())
        tables = ("0\nSECTION\n2\nTABLES\n"
                  "0\nTABLE\n2\nLTYPE\n70\n2\n"
                  "0\nLTYPE\n2\nCONTINUOUS\n70\n0\n3\nSolid line\n72\n65\n73\n0\n40\n0.0\n"
                  "0\nLTYPE\n2\nDASHED\n70\n0\n3\nDashed line\n72\n65\n73\n2\n40\n3.0\n49\n2.0\n74\n0\n49\n-1.0\n74\n0\n"
                  "0\nENDTAB\n"
                  f"0\nTABLE\n2\nLAYER\n70\n{len(DXF_LAYERS)}\n{layers}0\nENDTAB\n"
                  "0\nTABLE\n2\nSTYLE\n70\n2\n"
                  "0\nSTYLE\n2\nGOST\n70\n0\n40\n0.0\n41\n1.0\n50\n0.0\n71\n0\n42\n2.5\n3\nisocpeur.ttf\n4\n\n"
                  "0\nSTYLE\n2\nGOSTI\n70\n0\n40\n0.0\n41\n1.0\n50\n15.0\n71\n0\n42\n2.5\n3\nisocpeur.ttf\n4\n\n"
                  "0\nENDTAB\n0\nENDSEC\n")
        ents = "0\nSECTION\n2\nENTITIES\n" + "".join(self.ents) + "0\nENDSEC\n"
        return header + tables + ents + "0\nEOF\n"

    def write(self, path):
        with open(path, "w", encoding="cp1251", errors="replace", newline="\r\n") as f:
            f.write(self.dxf())
        return path


# ======================================================================= ГОСТ-оформление ==

def draw_frame(sh, with_agreed=True):
    """Рамка ГОСТ 21.101: внешняя граница, внутренняя рамка 20/5/5/5, графы левого поля
    (снизу вверх: Инв. № подл. 25 · Подп. и дата 35 · Взам. инв. № 25 · блок «Согласовано»),
    под рамкой — «Копировал» и формат."""
    x0, y0, x1, y1 = sh.frame
    sh.set_layer("FRAME")
    sh.rect(0.25, 0.25, sh.W - 0.5, sh.H - 0.5, 0.1)
    sh.rect(x0, y0, x1 - x0, y1 - y0, 0.6)
    gx = x0 - 7.0
    yb = y1
    for label, h in (("Инв. № подл.", 25), ("Подп. и дата", 35), ("Взам. инв. №", 25)):
        sh.rect(gx, yb - h, 7.0, h, 0.25)
        sh.text(gx + 4.6, yb - h / 2, label, 2.0, rot=-90, italic=False)
        yb -= h
    if with_agreed and yb - 60 > y0:
        # блок «Согласовано»: 4 ячейки по 15 мм, вертикальная подпись слева
        top = yb - 60
        sh.rect(gx, top, 7.0, 60, 0.25)
        for i in range(1, 4):
            sh.line(gx, top + i * 15, gx + 7, top + i * 15, 0.13)
        sh.text(gx + 4.6, top + 30, "Согласовано", 2.0, rot=-90, italic=False)
    # под рамкой
    sh.text(x1 - STAMP_W + 45, sh.H - 1.3, "Копировал", 2.2, anchor="start", italic=False)
    sh.text(x1 - 12, sh.H - 1.3, f"Формат {sh.fmt_label}", 2.2, anchor="end", italic=False)


def stamp_data(project, sheet_title, sheet_no, sheets_total, format_label=None, scale=None):
    """Единый источник данных штампа для ЛЮБОГО листа: адрес и название комплекта — из project.meta,
    поэтому «чужой адрес в штампе» (артефакт эталона) структурно невозможен."""
    m = project["meta"]
    title = list(sheet_title) if isinstance(sheet_title, (list, tuple)) else [sheet_title]
    if scale and title and "М 1:" not in title[-1]:
        title[-1] = f"{title[-1]} М 1:{scale}"
    return dict(object=m["object"], set_name=m["set_name"], sheet_title=title, stage=m.get("stage", "АИ"),
                sheet_no=sheet_no, sheets_total=sheets_total, roles=list(m.get("roles", ["Дизайнер", "Архитектор"])),
                org=m.get("designer_org", ""))


def draw_stamp(sh, st):
    """Основная надпись ГОСТ 21.101 форма 3 (185×55) в правом нижнем углу рамки.
    st — dict из stamp_data(). Роли — параметр (в эталоне «Дизайнер»/«Архитектор» без фамилий).
    «Листов» заполняется всегда (в эталоне пусто на всех 59 листах)."""
    fx0, fy0, fx1, fy1 = sh.frame
    x0, y0 = fx1 - STAMP_W, fy1 - STAMP_H
    x1, y1 = fx1, fy1
    sh.set_layer("STAMP")
    sh.rect(x0, y0, STAMP_W, STAMP_H, 0.6)
    # ---- левый блок 65 мм: колонки 10/10/10/10/15/10, 11 строк по 5
    xr = x0 + 65
    cols = [x0, x0 + 10, x0 + 20, x0 + 30, x0 + 40, x0 + 55, xr]
    for i in range(1, 11):
        sh.line(x0, y0 + 5 * i, xr, y0 + 5 * i, 0.13 if i != 6 else 0.35)
    for c in cols[1:-1]:
        sh.line(c, y0, c, y1, 0.13)
    sh.line(xr, y0, xr, y1, 0.6)
    hdr = ["Изм.", "Кол.уч.", "Лист", "№ док.", "Подп.", "Дата"]
    for i, t in enumerate(hdr):
        sh.text((cols[i] + cols[i + 1]) / 2, y0 + 25 + 3.6, t, 1.8, italic=False)
    for i, role in enumerate(st.get("roles", [])[:5]):
        sh.text(x0 + 1.0, y0 + 30 + 5 * i + 3.6, role, 2.0, anchor="start", italic=False)
    # ---- правый блок 120 мм: 15 (обозначение) / 15 (объект) / 15 (комплект + стадия/лист/листов) / 10
    sh.line(xr, y0 + 15, x1, y0 + 15, 0.6)
    sh.line(xr, y0 + 30, x1, y0 + 30, 0.6)
    sh.line(xr, y0 + 45, x1, y0 + 45, 0.6)
    cx = (xr + x1) / 2
    sh.text(cx, y0 + 15 + 9.8, st["object"], 4.4, italic=True)
    xm = x1 - 50                                        # стадия/лист/листов = 15+15+20
    sh.line(xm, y0 + 30, xm, y1, 0.6)
    sh.text((xr + xm) / 2, y0 + 30 + 9.6, st["set_name"], 3.2, italic=True)
    sc = [xm, xm + 15, xm + 30, x1]
    sh.line(xm, y0 + 35, x1, y0 + 35, 0.13)
    for c in sc[1:-1]:
        sh.line(c, y0 + 30, c, y0 + 45, 0.13)
    for i, t in enumerate(["Стадия", "Лист", "Листов"]):
        sh.text((sc[i] + sc[i + 1]) / 2, y0 + 33.8, t, 1.8, italic=False)
    for i, t in enumerate([st["stage"], str(st["sheet_no"]), str(st.get("sheets_total") or "")]):
        sh.text((sc[i] + sc[i + 1]) / 2, y0 + 42.4, t, 3.2, italic=True)
    # наименование листа (1–2 строки) + ячейка организации
    lines = st["sheet_title"][:2]
    if len(lines) == 1:
        sh.text((xr + xm) / 2, y0 + 45 + 6.6, lines[0], 2.8, italic=True)
    else:
        sh.text((xr + xm) / 2, y0 + 45 + 4.2, lines[0], 2.6, italic=True)
        sh.text((xr + xm) / 2, y0 + 45 + 8.4, lines[1], 2.4, italic=True)
    if st.get("org"):
        sh.text((xm + x1) / 2, y0 + 45 + 6.4, st["org"], 2.2, italic=False)


def draw_stamp_small(sh, sheet_no, doc_code=""):
    """Малый штамп продолжения (ГОСТ 21.101 форма 6, 185×15): на листах «продолжение/окончание»."""
    fx0, fy0, fx1, fy1 = sh.frame
    x0, y0 = fx1 - STAMP_W, fy1 - STAMP_SMALL_H
    sh.set_layer("STAMP")
    sh.rect(x0, y0, STAMP_W, STAMP_SMALL_H, 0.6)
    cols = [x0, x0 + 10, x0 + 20, x0 + 30, x0 + 40, x0 + 55, x0 + 65]
    for c in cols[1:]:
        sh.line(c, y0, c, y0 + 15, 0.13 if c != x0 + 65 else 0.6)
    for i in (1, 2):
        sh.line(x0, y0 + 5 * i, x0 + 65, y0 + 5 * i, 0.13)
    hdr = ["Изм.", "Кол.уч.", "Лист", "№ док.", "Подп.", "Дата"]
    for i, t in enumerate(hdr):
        sh.text((cols[i] + cols[i + 1]) / 2, y0 + 10 + 3.6, t, 1.8, italic=False)
    xl = fx1 - 10
    sh.line(xl, y0, xl, y0 + 15, 0.6)
    sh.text((x0 + 65 + xl) / 2, y0 + 9.8, doc_code, 3.0, italic=True)
    sh.line(xl, y0 + 5, fx1, y0 + 5, 0.13)
    sh.text((xl + fx1) / 2, y0 + 3.8, "Лист", 1.8, italic=False)
    sh.text((xl + fx1) / 2, y0 + 12.4, str(sheet_no), 3.0, italic=True)


def sheet_header(sh, title, size=5.0, y=None):
    """Заголовок листа сверху по центру рабочего поля (как в эталоне; масштаб — только в штампе)."""
    x0, y0, x1, y1 = sh.frame
    sh.set_layer("TEXT")
    sh.text((x0 + x1) / 2, (y or y0 + 12), title, size, italic=True)


# ------------------------------------------------------------------ размеры --

def dim_h(sh, x0, x1, y, label, size=2.4, ext_from=None, w=0.15, color=INK, tick_w=0.35):
    """Горизонтальная размерная линия между x0 и x1 на высоте y; выносные от ext_from (y точек)."""
    sh.set_layer("DIMS")
    if ext_from is not None:
        for x in (x0, x1):
            a, b = sorted((ext_from, y))
            sh.line(x, a, x, b + (1.5 if y > ext_from else 0) - (1.5 if y < ext_from else 0), 0.1, color=color)
    sh.line(min(x0, x1) - 1.5, y, max(x0, x1) + 1.5, y, w, color=color)
    sh.tick(x0, y, w=tick_w)
    sh.tick(x1, y, w=tick_w)
    if label is not None:
        sh.text((x0 + x1) / 2, y - 0.7, str(label), size, color=color)


def dim_v(sh, y0, y1, x, label, size=2.4, ext_from=None, w=0.15, color=INK, tick_w=0.35, side="left"):
    """Вертикальная размерная линия; текст повёрнут на −90°, читается снизу вверх."""
    sh.set_layer("DIMS")
    if ext_from is not None:
        for y in (y0, y1):
            a, b = sorted((ext_from, x))
            sh.line(a, y, b, y, 0.1, color=color)
    sh.line(x, min(y0, y1) - 1.5, x, max(y0, y1) + 1.5, w, color=color)
    sh.tick(x, y0, w=tick_w)
    sh.tick(x, y1, w=tick_w)
    if label is not None:
        dx = -0.7 if side == "left" else 0.7 + size * 0.8
        sh.text(x + dx, (y0 + y1) / 2, str(label), size, rot=-90, color=color)


def dim_chain_h(sh, xs, y, labels=None, size=2.4, ext_from=None, color=INK):
    """Цепочка по X: точки xs (страничные мм), подписи между ними (по умолчанию — не ставятся,
    считать в мире должен вызывающий: labels — уже строки)."""
    sh.set_layer("DIMS")
    if ext_from is not None:
        for x in xs:
            a, b = sorted((ext_from, y))
            sh.line(x, a, x, b, 0.1, color=color)
    sh.line(xs[0] - 1.5, y, xs[-1] + 1.5, y, 0.15, color=color)
    for x in xs:
        sh.tick(x, y)
    if labels:
        for i, lab in enumerate(labels):
            if lab is None:
                continue
            xm = (xs[i] + xs[i + 1]) / 2
            if abs(xs[i + 1] - xs[i]) < size * 0.6 * len(str(lab)) * 0.9:
                # узкий интервал — подпись над линией со сдвигом (как на эталоне у коротких простенков)
                sh.text(xm, y - 0.7 - size * 1.1, str(lab), size * 0.9, color=color)
            else:
                sh.text(xm, y - 0.7, str(lab), size, color=color)


def dim_chain_v(sh, ys, x, labels=None, size=2.4, ext_from=None, color=INK, side="left"):
    sh.set_layer("DIMS")
    if ext_from is not None:
        for y in ys:
            a, b = sorted((ext_from, x))
            sh.line(a, y, b, y, 0.1, color=color)
    sh.line(x, min(ys) - 1.5, x, max(ys) + 1.5, 0.15, color=color)
    for y in ys:
        sh.tick(x, y)
    if labels:
        dx = -0.7 if side == "left" else 0.7 + size * 0.8
        for i, lab in enumerate(labels):
            if lab is None:
                continue
            sh.text(x + dx, (ys[i] + ys[i + 1]) / 2, str(lab), size, rot=-90, color=color)


def dim_along(sh, p0, p1, offset, label, size=2.4, color=INK):
    """Размер вдоль произвольного направления p0→p1 со смещением offset (мм) по правой нормали."""
    sh.set_layer("DIMS")
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    ux, uy = dx / L, dy / L
    nx, ny = uy, -ux
    a = (p0[0] + nx * offset, p0[1] + ny * offset)
    b = (p1[0] + nx * offset, p1[1] + ny * offset)
    sh.line(p0[0], p0[1], a[0] + nx * 1.5, a[1] + ny * 1.5, 0.1, color=color)
    sh.line(p1[0], p1[1], b[0] + nx * 1.5, b[1] + ny * 1.5, 0.1, color=color)
    sh.line(a[0] - ux * 1.5, a[1] - uy * 1.5, b[0] + ux * 1.5, b[1] + uy * 1.5, 0.15, color=color)
    ang = math.degrees(math.atan2(dy, dx))
    for p in (a, b):
        # засечка 45° к направлению
        r = 1.0
        c, s = math.cos(math.radians(ang + 45)), math.sin(math.radians(ang + 45))
        sh.line(p[0] - r * c, p[1] - r * s, p[0] + r * c, p[1] + r * s, 0.35, color=color)
    mx, my = (a[0] + b[0]) / 2 - nx * 0.7, (a[1] + b[1]) / 2 - ny * 0.7
    rot = ang if -90 < ang <= 90 else ang + 180
    sh.text(mx, my, str(label), size, rot=rot if abs(rot) > 0.5 else None, color=color)


# ------------------------------------------------------------------ выноски, метки --

def leader(sh, x0, y0, x1, y1, lines, size=2.3, shelf=None, underline=True, color=INK, dot=False):
    """Выноска: линия от (x0,y0) к (x1,y1), полка вправо (или влево, если shelf<0), текст над полкой."""
    sh.set_layer("TEXT")
    if dot:
        sh.dot(x0, y0, 0.45, color=color)
    sh.line(x0, y0, x1, y1, 0.13, color=color)
    lines = list(lines)
    width = max(len(s) for s in lines) * size * 0.5 + 1.5
    shelf = width if shelf is None else shelf
    x2 = x1 + shelf
    sh.line(x1, y1, x2, y1, 0.13, color=color)
    xa, anchor = (min(x1, x2) + 0.6, "start")
    lh = size * 1.35
    for i, s in enumerate(lines):
        yy = y1 - 0.6 - (len(lines) - 1 - i) * lh
        sh.text(xa, yy, s, size, anchor=anchor, underline=(underline and i == len(lines) - 1), color=color)
    return x2, y1


def room_mark(sh, x, y, no, area_text=None, r=3.0, size=3.0, extra=None):
    """Маркер помещения: кружок с номером, под ним подчёркнутая площадь (как на планах эталона)."""
    sh.set_layer("TEXT")
    sh.circle(x, y, r, 0.25)
    sh.text(x, y + size * 0.36, str(no), size, italic=True)
    if area_text:
        sh.text(x, y + r + size * 1.05, area_text, size * 0.85, italic=True, underline=True)
    if extra:
        sh.text(x + r + 1.0, y + size * 0.36, extra, size * 1.2, anchor="start", italic=True)


def section_mark(sh, x, y, label, direction="right", size=3.5):
    """Метка разреза/вида «А» со стрелкой (жирный штрих + стрелка), как на чертежах мебели."""
    sh.set_layer("TEXT")
    d = 1 if direction == "right" else -1
    sh.line(x, y - 4, x, y + 4, 0.7, color=COLOR["cut_mark"])
    sh.line(x, y, x + d * 4, y, 0.35, color=COLOR["cut_mark"])
    sh.path(f"M {x + d*4:.2f} {y:.2f} l {-d*1.6:.2f} -0.9 l 0 1.8 z", 0.2, fill=COLOR["cut_mark"], color=COLOR["cut_mark"])
    sh.text(x + d * 5.5, y + size * 0.36, label, size, anchor="start" if d > 0 else "end", italic=True)


# ------------------------------------------------------------------ таблицы --

def draw_table(sh, x, y, widths, rows, header=None, row_h=6.0, header_h=None, size=2.4,
               title=None, title_size=3.2, aligns=None, line_w=0.13, border_w=0.5, max_y=None,
               header_size=None):
    """Таблица ГОСТ-вида. rows — список строк; строка = список ячеек (str) или dict:
       {"cells":[...]} / {"span": "текст", "align": "start|middle", "bold": bool} (объединённая строка)
       / {"text": ..., "underline": True} внутри ячейки допустим dict {"text", "bold", "align", "color"}.
    header — список строк шапки (каждая — список подписей колонок; можно многострочно: подпись = список строк).
    Возвращает y конца таблицы. Если max_y задан и строка не влезает — возвращает (y, остаток_rows)."""
    sh.set_layer("TABLE")
    cols = [x]
    for w in widths:
        cols.append(cols[-1] + w)
    xN = cols[-1]
    aligns = aligns or ["middle"] * len(widths)
    header_size = header_size or size
    yy = y
    if title:
        sh.text((x + xN) / 2, yy - 2.2, title, title_size, italic=True)
    y_top = yy
    if header:
        hh = header_h or (row_h * 1.6)
        sh.rect(x, yy, xN - x, hh, border_w)
        for c in cols[1:-1]:
            sh.line(c, yy, c, yy + hh, line_w)
        for i, cell in enumerate(header):
            lines = cell if isinstance(cell, (list, tuple)) else [cell]
            lh = header_size * 1.25
            y0 = yy + hh / 2 - (len(lines) - 1) * lh / 2 + header_size * 0.36
            for k, ln in enumerate(lines):
                sh.text((cols[i] + cols[i + 1]) / 2, y0 + k * lh, ln, header_size, italic=False)
        yy += hh
    rest = None
    for ri, row in enumerate(rows):
        if max_y is not None and yy + row_h > max_y:
            rest = rows[ri:]
            break
        if isinstance(row, dict) and "span" in row:
            al = row.get("align", "start")
            tx = x + 1.5 if al == "start" else (x + xN) / 2
            sh.text(tx, yy + row_h / 2 + size * 0.36, row["span"], size, anchor=al,
                    bold=row.get("bold", False), italic=True, underline=row.get("underline", False))
        else:
            cells = row["cells"] if isinstance(row, dict) else row
            for i, cell in enumerate(cells):
                if cell is None or cell == "":
                    continue
                if isinstance(cell, dict):
                    txt, al = cell.get("text", ""), cell.get("align", aligns[i])
                    bold, und, col = cell.get("bold", False), cell.get("underline", False), cell.get("color", INK)
                    csize = cell.get("size", size)
                else:
                    txt, al, bold, und, col, csize = str(cell), aligns[i], False, False, INK, size
                lines = txt.split("\n")
                lh = csize * 1.2
                y0 = yy + row_h / 2 - (len(lines) - 1) * lh / 2 + csize * 0.36
                tx = {"start": cols[i] + 1.2, "end": cols[i + 1] - 1.2}.get(al, (cols[i] + cols[i + 1]) / 2)
                for k, ln in enumerate(lines):
                    sh.text(tx, y0 + k * lh, ln, csize, anchor=al, bold=bold, underline=und, color=col, italic=True)
            for c in cols[1:-1]:
                sh.line(c, yy, c, yy + row_h, line_w)
        sh.line(x, yy + row_h, xN, yy + row_h, line_w)
        yy += row_h
    sh.rect(x, y_top, xN - x, yy - y_top, border_w)
    return (yy, rest) if max_y is not None else yy


def notes_block(sh, x, y, lines, title="Примечание:", size=2.4, lh=None, title_size=2.7, indent=3.5,
                underline_title=True):
    """Нумерованные примечания под заголовком; продолжение пункта — с отступом."""
    sh.set_layer("TEXT")
    lh = lh or size * 1.5
    if title:
        sh.text(x, y, title, title_size, anchor="start", italic=True, underline=underline_title)
        y += lh + 0.6
    for ln in lines:
        ind = 0 if re.match(r"^\s*(\d+[\.\)]|\*|-)", ln) else indent
        sh.text(x + ind, y, ln, size, anchor="start", italic=True)
        y += lh
    return y


def wrap_text(s, max_chars):
    """Простой перенос по словам для примечаний (ширина в символах)."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ шаблон листа --

def new_sheet(fmt="A3", canvas="svg"):
    return Sheet(fmt) if canvas == "svg" else DxfCanvas(fmt)


def finish_sheet(sh, project, sheet_title, sheet_no, sheets_total, scale=None, small=False, header=None):
    """Рамка + штамп (полный или малый) + заголовок листа. Общая точка входа для всех модулей."""
    draw_frame(sh)
    if small:
        draw_stamp_small(sh, sheet_no, doc_code=project["meta"].get("doc_code", ""))
    else:
        draw_stamp(sh, stamp_data(project, sheet_title, sheet_no, sheets_total, scale=scale))
    if header:
        sheet_header(sh, header)


def stamp_box(sh):
    """Прямоугольник штампа (x0, y0, x1, y1) — чтобы содержимое не заезжало на него."""
    fx0, fy0, fx1, fy1 = sh.frame
    return (fx1 - STAMP_W, fy1 - STAMP_H, fx1, fy1)
