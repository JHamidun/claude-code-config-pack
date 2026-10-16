# -*- coding: utf-8 -*-
"""Форматирование чисел единообразно на весь альбом (десятичная запятая, один форматтер)."""


def fmt_num(v, digits=1):
    """13.24 → '13,2' (digits=1); 404.4 → '404,4'. Целые без хвоста при digits=0."""
    if v is None:
        return ""
    s = f"{float(v):.{digits}f}"
    return s.replace(".", ",")


def fmt_area(m2):
    return fmt_num(m2, 1)


def fmt_int(v):
    return str(int(round(v)))


def fmt_m(mm, digits=2):
    """мм → метры строкой: 2930 → '2,93'."""
    return fmt_num(mm / 1000.0, digits)


def rng(a, b):
    """Диапазон стен '1–14'."""
    return f"{a}–{b}" if a != b else str(a)
