#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Юнит-экономика ключа ДО запуска кампании в Яндекс.Директе.

Отвечает на один вопрос: наберётся ли на этой семантике достаточно конверсий,
чтобы автостратегия обучилась — или бюджет уйдёт в никуда.

Цепочка расчёта:

    показы/мес  ->  x доля кликов позиции  ->  клики
                ->  x конверсия лендинга    ->  заявки
                ->  бюджет = клики x CPC,  CPL = бюджет / заявки

Пороги (источник — references/benchmarks.md, курс методология / эксперт):

    обучение автостратегии      >= 10 конверсий В НЕДЕЛЮ на кампанию
    минимальный недельный бюджет = средняя цена конверсии x 10
    выводы по кампании           >= 100 кликов за неделю
    решение по одному запросу    15-20 кликов
    CTR Поиска норма             > 5%

Частотности брать ТОЛЬКО из живого Wordstat, не из головы:
    python ../../seo-machine-ru/scripts/wordstat_client.py batch seeds.txt --out ws.json --region 225

Использование:
    python unit_econ.py phrase "вызвать врача на дом" --freq 9345 --cpc 90 --cr 0.04
    python unit_econ.py from-wordstat ws.json --cpc 90 --cr 0.04 --kpi-cpl 3000
    python unit_econ.py from-wordstat ws.json --cpc 90 --cr 0.04 --children   # считать по вхождениям
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- пороги из references/benchmarks.md -------------------------------------
LEARNING_CONV_PER_WEEK = 10      # минимум конверсий/нед для обучения автостратегии
MIN_WEEKLY_BUDGET_MULT = 10      # мин. недельный бюджет = CPA x 10
CLICKS_FOR_CAMPAIGN_CALL = 100   # минимум кликов/нед для выводов по кампании
CLICKS_FOR_KEYWORD_CALL = 15     # минимум кликов для решения по одному запросу
RULE_X3 = 3                      # потрачено >= 3 x KPI без лидов -> отключать

# Доля кликов, достающаяся объявлению. Не путать с CTR объявления (норма >5%):
# это доля от ВСЕХ показов запроса, которую забирает строка на своей позиции.
POSITION_CLICK_SHARE = {
    "top1": 0.18,    # верх выдачи, оптимистично (в разборе назывался коридор 15-20%)
    "top1-4": 0.10,  # верхний блок в среднем
    "bottom": 0.03,  # нижний блок
}

WEEKS_PER_MONTH = 4.345


def compute(phrase: str, freq: int, cpc: float, cr: float,
            position: str = "top1", waste: float = 0.30) -> dict:
    """Одна фраза -> прогноз. waste — доля нецелевых показов (широкое соответствие)."""
    share = POSITION_CLICK_SHARE.get(position, POSITION_CLICK_SHARE["top1"])

    # Wordstat "popular" считает ВСЕ вхождения, включая нецелевые.
    # Без минусовки часть показов мусорная — срезаем её сразу, а не задним числом.
    effective = freq * (1.0 - waste)

    clicks = effective * share
    leads = clicks * cr
    budget = clicks * cpc
    cpl = (budget / leads) if leads > 0 else None

    return {
        "phrase": phrase,
        "freq_raw": freq,
        "freq_effective": round(effective),
        "clicks_month": round(clicks, 1),
        "clicks_week": round(clicks / WEEKS_PER_MONTH, 1),
        "leads_month": round(leads, 2),
        "leads_week": round(leads / WEEKS_PER_MONTH, 2),
        "budget_month": round(budget),
        "cpl": round(cpl) if cpl else None,
        "keyword_decidable": (clicks / WEEKS_PER_MONTH) >= CLICKS_FOR_KEYWORD_CALL,
    }


def verdict(rows: list, cr: float, kpi_cpl: float | None) -> dict:
    """Агрегат по всей семантике + проверка порогов обучения."""
    live = [r for r in rows if r["freq_raw"] > 0]
    clicks_month = sum(r["clicks_month"] for r in live)
    leads_month = sum(r["leads_month"] for r in live)
    budget_month = sum(r["budget_month"] for r in live)
    # недельные — делением месячных, иначе итог расходится с колонкой на округлениях
    clicks_week = clicks_month / WEEKS_PER_MONTH
    leads_week = leads_month / WEEKS_PER_MONTH
    cpl = round(budget_month / leads_month) if leads_month > 0 else None

    learning_ok = leads_week >= LEARNING_CONV_PER_WEEK
    min_weekly_budget = round(cpl * MIN_WEEKLY_BUDGET_MULT) if cpl else None

    # Сколько конверсий не хватает и во сколько раз надо больше спроса
    gap_mult = round(LEARNING_CONV_PER_WEEK / leads_week, 1) if 0 < leads_week < LEARNING_CONV_PER_WEEK else None

    lines = []
    if not live:
        lines.append("Ни одной фразы с ненулевой частотностью. Рекламировать нечего.")
    elif not learning_ok:
        lines.append(
            f"Автостратегия НЕ обучится: {leads_week:.1f} конверсий/нед против порога "
            f"{LEARNING_CONV_PER_WEEK}. Нужно в {gap_mult}x больше спроса, "
            f"либо конверсия лендинга выше {cr:.1%}, либо оптимизация на микроцель."
        )
    else:
        lines.append(f"Порог обучения проходит: {leads_week:.1f} конверсий/нед (нужно {LEARNING_CONV_PER_WEEK}).")

    if clicks_week < CLICKS_FOR_CAMPAIGN_CALL and live:
        lines.append(
            f"Кликов {clicks_week:.0f}/нед — меньше {CLICKS_FOR_CAMPAIGN_CALL}, "
            "решения по кампании будут статистически необоснованными."
        )
    if kpi_cpl and cpl:
        # При непройденном пороге обучения CPL считается на долях конверсии в неделю —
        # число арифметически верное, но статистически пустое. Молча показывать его
        # рядом с зелёным «укладывается в KPI» = зелёный отчёт при поломке.
        if not learning_ok:
            lines.append(
                f"CPL {cpl} ₽ против KPI {kpi_cpl:.0f} ₽ приведён СПРАВОЧНО и решением не является: "
                f"при {leads_week:.1f} конверсиях/нед он посчитан на долях лида."
            )
        elif cpl > kpi_cpl:
            lines.append(f"Прогнозный CPL {cpl} ₽ выше KPI {kpi_cpl:.0f} ₽ — экономика не сходится уже на бумаге.")
        else:
            lines.append(f"Прогнозный CPL {cpl} ₽ укладывается в KPI {kpi_cpl:.0f} ₽.")
        lines.append(f"Правило X3: отключать связку, потратившую {RULE_X3 * kpi_cpl:.0f} ₽ без лидов.")

    return {
        "phrases_live": len(live),
        "phrases_dead": len(rows) - len(live),
        "clicks_month": round(clicks_month, 1),
        "clicks_week": round(clicks_week, 1),
        "leads_week": round(leads_week, 2),
        "leads_month": round(leads_month, 1),
        "budget_month": budget_month,
        "cpl": cpl,
        "learning_feasible": learning_ok,
        "min_weekly_budget": min_weekly_budget,
        "notes": lines,
    }


def render(rows: list, agg: dict, params: dict) -> None:
    print(f"\nДОПУЩЕНИЯ: CPC {params['cpc']} ₽ · конверсия лендинга {params['cr']:.1%} · "
          f"позиция {params['position']} (доля кликов {POSITION_CLICK_SHARE[params['position']]:.0%}) · "
          f"нецелевых показов {params['waste']:.0%}")
    print("Частотности — из живого Wordstat. Остальное — оценки, помечены как допущения.\n")

    print(f"{'фраза':<44}{'показы':>9}{'клики/м':>9}{'заявки/м':>10}{'бюджет/м':>11}{'CPL':>8}")
    print("-" * 91)
    for r in sorted(rows, key=lambda x: -x["freq_raw"]):
        mark = "" if r["freq_raw"] > 0 else "  (мертва)"
        cpl = f"{r['cpl']}" if r["cpl"] else "—"
        print(f"{r['phrase'][:43]:<44}{r['freq_raw']:>9}{r['clicks_month']:>9.0f}"
              f"{r['leads_month']:>10.2f}{r['budget_month']:>11}{cpl:>8}{mark}")

    print("-" * 91)
    print(f"{'ИТОГО живых: ' + str(agg['phrases_live']) + ', мёртвых: ' + str(agg['phrases_dead']):<44}"
          f"{'':>9}{agg['clicks_month']:>9.0f}{agg['leads_month']:>10.1f}"
          f"{agg['budget_month']:>11}{agg['cpl'] or '—':>8}")

    print(f"\nВ НЕДЕЛЮ: {agg['clicks_week']:.0f} кликов, {agg['leads_week']:.1f} заявок")
    if agg["min_weekly_budget"]:
        print(f"Минимальный недельный бюджет для обучения: {agg['min_weekly_budget']} ₽ (CPL x {MIN_WEEKLY_BUDGET_MULT})")

    print("\nВЕРДИКТ:")
    for n in agg["notes"]:
        print(f"  · {n}")
    print()


def load_wordstat(path: Path, use_children: bool) -> list:
    """Разобрать вывод wordstat_client.py batch."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for seed, payload in data.items():
        if not isinstance(payload, dict) or "error" in payload:
            out.append((seed, 0))
            continue
        inc = payload.get("including") or []
        if use_children:
            for row in inc:
                out.append((row["phrase"], row["freq"]))
        else:
            # частотность самой маски = точное совпадение среди вхождений,
            # иначе самое частотное вхождение как верхняя оценка кластера
            exact = next((r["freq"] for r in inc if r["phrase"].strip().lower() == seed.strip().lower()), None)
            out.append((seed, exact if exact is not None else (inc[0]["freq"] if inc else 0)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Юнит-экономика ключа до запуска Директа")
    ap.add_argument("--cpc", type=float, default=80.0, help="оценка цены клика, ₽ (допущение)")
    ap.add_argument("--cr", type=float, default=0.04, help="конверсия лендинга долей, напр. 0.04 = 4%%")
    ap.add_argument("--position", default="top1", choices=list(POSITION_CLICK_SHARE))
    ap.add_argument("--waste", type=float, default=0.30, help="доля нецелевых показов до минусовки")
    ap.add_argument("--kpi-cpl", type=float, default=None, help="целевая цена лида, ₽")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("phrase", help="одна фраза с известной частотностью")
    p1.add_argument("text")
    p1.add_argument("--freq", type=int, required=True, help="показов/мес из живого Wordstat")

    p2 = sub.add_parser("from-wordstat", help="json от wordstat_client.py batch")
    p2.add_argument("file")
    p2.add_argument("--children", action="store_true", help="считать по вхождениям, а не по маскам")

    a = ap.parse_args()
    params = {"cpc": a.cpc, "cr": a.cr, "position": a.position, "waste": a.waste}

    if a.cmd == "phrase":
        pairs = [(a.text, a.freq)]
    else:
        path = Path(a.file)
        if not path.exists():
            print(f"нет файла {path}", file=sys.stderr)
            return 2
        pairs = load_wordstat(path, a.children)

    rows = [compute(p, f, a.cpc, a.cr, a.position, a.waste) for p, f in pairs]
    agg = verdict(rows, a.cr, a.kpi_cpl)
    render(rows, agg, params)
    return 0 if agg["learning_feasible"] else 1


if __name__ == "__main__":
    sys.exit(main())
