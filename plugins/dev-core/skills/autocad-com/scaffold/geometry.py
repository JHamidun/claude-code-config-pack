# -*- coding: utf-8 -*-
"""
Плоская геометрия квартиры: площади полигонов, обход стен по часовой от двери,
привязка проёмов и перегородок к рёбрам помещения. Всё в мм, Y вверх (север сверху).

Полигоны — списки [x, y] без повтора первой точки. Внутренняя сторона помещения —
по внутренним граням стен; перегородки заданы осевой линией (a, b) и толщиной t.
"""

import math

TOL = 5.0            # допуск совпадения координат, мм


def area(poly):
    """Площадь многоугольника (формула шнурков), мм². Всегда положительная."""
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def area_m2(poly):
    return area(poly) / 1e6


def is_ccw(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s > 0


def ensure_ccw(poly):
    return list(poly) if is_ccw(poly) else list(reversed(poly))


def edges(poly):
    n = len(poly)
    return [(tuple(poly[i]), tuple(poly[(i + 1) % n])) for i in range(n)]


def length(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def perimeter(poly):
    return sum(length(a, b) for a, b in edges(poly))


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def centroid(poly):
    """Центроид площади (для подписи помещения)."""
    n = len(poly)
    a = 0.0
    cx = cy = 0.0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(a) < 1e-9:
        x0, y0, x1, y1 = bbox(poly)
        return (x0 + x1) / 2, (y0 + y1) / 2
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)


def point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xint = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xint:
                inside = not inside
    return inside


def unit(a, b):
    L = length(a, b)
    if L < 1e-9:
        return (0.0, 0.0)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def normal_right(a, b):
    """Правая нормаль к направлению a→b (для обхода по часовой — смотрит внутрь помещения)."""
    ux, uy = unit(a, b)
    return (uy, -ux)


def dist_point_line(p, a, b):
    """Расстояние от точки до прямой (a, b) со знаком (левая сторона > 0)."""
    ux, uy = unit(a, b)
    return (p[0] - a[0]) * uy - (p[1] - a[1]) * ux


def project_t(p, a, b):
    """Параметр проекции точки на отрезок a→b в мм от a."""
    ux, uy = unit(a, b)
    return (p[0] - a[0]) * ux + (p[1] - a[1]) * uy


def parallel(a1, b1, a2, b2, tol_deg=1.0):
    u1, u2 = unit(a1, b1), unit(a2, b2)
    cross = abs(u1[0] * u2[1] - u1[1] * u2[0])
    return cross < math.sin(math.radians(tol_deg))


def overlap_1d(lo1, hi1, lo2, hi2):
    lo, hi = max(lo1, lo2), min(hi1, hi2)
    return (lo, hi) if hi - lo > TOL else None


def segment_on_edge(seg_a, seg_b, edge_a, edge_b, max_dist):
    """Лежит ли отрезок (seg) вдоль ребра (edge) на расстоянии ≤ max_dist с перекрытием.
    Возвращает (t0, t1) — интервал в мм от начала ребра, либо None."""
    if not parallel(seg_a, seg_b, edge_a, edge_b):
        return None
    d0 = abs(dist_point_line(seg_a, edge_a, edge_b))
    d1 = abs(dist_point_line(seg_b, edge_a, edge_b))
    if max(d0, d1) > max_dist:
        return None
    t0, t1 = sorted((project_t(seg_a, edge_a, edge_b), project_t(seg_b, edge_a, edge_b)))
    return overlap_1d(0.0, length(edge_a, edge_b), t0, t1)


DOOR_MATCH_DIST = 250      # проём задан на ОСЕВОЙ стены: до грани помещения t/2 (60…200 мм)


def walls_clockwise(poly, door_seg=None, door_last=True, max_dist=DOOR_MATCH_DIST):
    """Рёбра помещения в порядке обхода по часовой стрелке (интерьер справа по ходу).

    door_seg — отрезок дверного проёма (a, b) в координатах плана; ребро, на котором он
    лежит, ставится ПОСЛЕДНИМ (как в эталоне: стена с дверью замыкает обход, стена 1 —
    следующая по часовой). Если door_last=False — дверная стена первая.
    Возвращает список dict: {no, a, b, length}.
    """
    p = ensure_ccw(poly)
    cw = list(reversed(p))                       # обход по часовой
    ring = edges(cw)
    start = 0
    if door_seg is not None:
        for i, (a, b) in enumerate(ring):
            if segment_on_edge(door_seg[0], door_seg[1], a, b, max_dist=max_dist) is not None:
                start = (i + 1) % len(ring) if door_last else i
                break
    ordered = ring[start:] + ring[:start]
    return [dict(no=i + 1, a=a, b=b, length=round(length(a, b)))
            for i, (a, b) in enumerate(ordered)]


def wall_band(a, b, t):
    """Полигон полосы стены толщиной t вокруг осевой a→b (для заливки/штриховки)."""
    ux, uy = unit(a, b)
    nx, ny = -uy * t / 2, ux * t / 2
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
            (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def subtract_intervals(L, cuts):
    """[0, L] минус список интервалов (t0, t1) → сохранённые отрезки.
    Вырезы обрезаются по [0, L]; пустые и обратные (после нормализации) отбрасываются —
    вырез за пределами отрезка НЕ удлиняет его (находка ревью: (1500,1600) при L=1000 давал [(0,1500)])."""
    norm = []
    for c0, c1 in cuts:
        lo, hi = max(min(c0, c1), 0.0), min(max(c0, c1), L)
        if hi - lo > 1e-9:
            norm.append((lo, hi))
    segs, pos = [], 0.0
    for c0, c1 in sorted(norm):
        if c1 <= pos:
            continue
        if c0 > pos:
            segs.append((pos, c0))
        pos = max(pos, c1)
    if pos < L - 1e-9:
        segs.append((pos, L))
    return segs


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segments_cross(p1, p2, p3, p4, eps=1e-6):
    """Собственное пересечение отрезков (во внутренних точках обоих); касание концами и наложение — нет."""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    return ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
           ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps))


def dist_point_segment(p, a, b):
    L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    if L2 < 1e-12:
        return length(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / L2))
    return length(p, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))


def point_strictly_inside(pt, poly, margin=TOL):
    """Точка внутри полигона и дальше margin от его границы."""
    if not point_in_polygon(pt, poly):
        return False
    return all(dist_point_segment(pt, a, b) > margin for a, b in edges(poly))


def point_inside_or_on(pt, poly, tol=TOL):
    return point_in_polygon(pt, poly) or any(dist_point_segment(pt, a, b) <= tol for a, b in edges(poly))


def polygons_overlap(A, B, margin=TOL):
    """Пересекаются ли ВНУТРЕННОСТИ полигонов (общая граница/касание — не пересечение):
    вершина одного строго внутри другого либо собственное пересечение рёбер."""
    if any(point_strictly_inside(p, B, margin) for p in A):
        return True
    if any(point_strictly_inside(p, A, margin) for p in B):
        return True
    for a1, a2 in edges(A):
        for b1, b2 in edges(B):
            if segments_cross(a1, a2, b1, b2):
                return True
    return False


def polygon_contains(outer, inner, tol=TOL):
    """inner целиком внутри outer (с допуском по границе): все вершины внутри/на границе и рёбра не пересекаются."""
    if not all(point_inside_or_on(p, outer, tol) for p in inner):
        return False
    for a1, a2 in edges(inner):
        for b1, b2 in edges(outer):
            if segments_cross(a1, a2, b1, b2):
                return False
    # центр тоже внутри — отсекает вогнутые случаи, где все вершины на границе, а тело снаружи
    return point_inside_or_on(centroid(inner), outer, tol)


def chain_breaks(L, openings):
    """Разбивка нижней размерной цепочки стены: [простенок, проём, простенок, …]."""
    pts = [0.0]
    for op in sorted(openings, key=lambda o: o["at"]):
        pts += [op["at"], op["at"] + op["w"]]
    pts.append(L)
    out = []
    for i in range(len(pts) - 1):
        d = pts[i + 1] - pts[i]
        if d > TOL:
            out.append(round(d))
    return out


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def poly_intersects_rect(poly, x0, y0, x1, y1):
    bx0, by0, bx1, by1 = bbox(poly)
    return not (bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1)
