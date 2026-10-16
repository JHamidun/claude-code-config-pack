# -*- coding: utf-8 -*-
"""Каркас проверок по нормам: статусы, форма записи, потерянные требования.

Переносится между областями (здания, электросети, дороги) потому, что это НЕ
предметная логика, а способ отчитаться. Сами проверки пишутся под область.

Четыре статуса, и разница между двумя средними содержательная:

    PASS  — требование выполнено;
    FAIL  — норма НАРУШЕНА, результат отдавать нельзя;
    WARN  — проверено ПРИКИДКОЙ, точный расчёт относится к другой стадии;
    INFO  — справочно, решения не требует.

`WARN` существует ради честности. Ток короткого замыкания, посчитанный
приближённо, обязан быть `WARN` со ссылкой «точный ТКЗ по ГОСТ 28249 на стадии
РД», а не зелёным `PASS`: приближение, выданное за проверку, — тот же выдуманный
ответ, только с ореолом строгости.
"""
from __future__ import annotations

from typing import Any, Iterable

MARK = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "WARN": "⚠️ WARN", "INFO": "ℹ️ INFO"}


def rule(code: str, requirement: str, ok: bool | None, detail: str = "",
         fix: str = "", approximate: bool = False) -> dict[str, Any]:
    """Одна запись проверки.

    code        — номер пункта: «СП 379.1325800.2020, п. 6.1.23», «ПУЭ гл.3.1».
                  Без номера предъявить заказчику нечего — это не проверка,
                  а обещание.
    requirement — что именно требуется, человеческим языком и с числом.
    ok          — True/False; None = справочно (INFO).
    fix         — конкретное действие при провале: «поднять номинал до ≥N А».
    approximate — True, если считали прикидкой: тогда успех даёт WARN, не PASS.
    """
    if ok is None:
        status = "INFO"
    elif not ok:
        status = "FAIL"
    else:
        status = "WARN" if approximate else "PASS"
    rec = {"rule": code, "requirement": requirement, "status": status, "detail": detail}
    if status == "FAIL" and fix:
        rec["fix"] = fix
    return rec


def lost(requirement: str, why: str) -> dict[str, Any]:
    """Требование заказчика, которое проверить НЕЧЕМ.

    Молчание о непроверенном хуже отказа: заказчик считает, что учли.
    """
    return {"rule": "—", "requirement": requirement, "status": "INFO",
            "detail": f"НЕ ПРОВЕРЕНО: {why}"}


def verdict(rules: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Свод: можно ли отдавать результат.

    Отдавать нельзя при любом FAIL. WARN не блокирует, но обязан быть
    произнесён вслух вместе с ценой и чертежом.
    """
    rules = list(rules)
    by = {s: [r for r in rules if r["status"] == s] for s in MARK}
    return {
        "ok": not by["FAIL"],
        "counts": {s: len(v) for s, v in by.items()},
        "fails": by["FAIL"],
        "warns": by["WARN"],
        "unchecked": [r for r in by["INFO"] if r["detail"].startswith("НЕ ПРОВЕРЕНО")],
        "hint": ("Есть нарушения норм — результат НЕ отдавать, перечислить FAIL "
                 "и предложить варианты." if by["FAIL"] else
                 "Нарушений нет. WARN и непроверенное произнести вслух вместе "
                 "с результатом, не умалчивать."),
    }


def render(rules: Iterable[dict[str, Any]]) -> str:
    """Текст для человека."""
    out = []
    for r in rules:
        out.append(f"{MARK[r['status']]}  {r['rule']} — {r['requirement']}")
        if r.get("detail"):
            out.append(f"        {r['detail']}")
        if r.get("fix"):
            out.append(f"        как исправить: {r['fix']}")
    return "\n".join(out)
