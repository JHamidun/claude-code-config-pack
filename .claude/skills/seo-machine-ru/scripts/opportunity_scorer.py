#!/usr/bin/env python3
"""Скоринг SEO-возможностей (перекалибровано под Яндекс).

Считает приоритет ключа/страницы по 8 факторам. Кривая CTR взята под
выдачу Яндекса (а не Google). Вход — список словарей с метриками из
Wordstat/Вебмастера (скилл `yandex`), выход — отсортированный список.

CTR Яндекса по позициям (десктоп+моб, усреднённо, %):
  1:28, 2:15, 3:10, 4:7, 5:5, 6:4, 7:3, 8:2.5, 9:2, 10:1.8

CLI:  python opportunity_scorer.py keywords.json [--json]
  где keywords.json = [{"keyword","volume","position","intent","competition"}...]
"""
import argparse
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

YANDEX_CTR = {1: 28, 2: 15, 3: 10, 4: 7, 5: 5, 6: 4, 7: 3, 8: 2.5, 9: 2, 10: 1.8}

INTENT_WEIGHT = {  # коммерческость намерения
    "transactional": 1.0, "commercial": 0.85, "informational": 0.5, "navigational": 0.3,
    "транзакционный": 1.0, "коммерческий": 0.85, "информационный": 0.5, "навигационный": 0.3,
}

WEIGHTS = {  # сумма = 1.0
    "volume": 0.25, "position": 0.20, "intent": 0.20,
    "competition": 0.15, "cluster": 0.10, "ctr_gap": 0.10,
}


def expected_ctr(pos):
    if not pos:
        return 0.0
    pos = int(round(pos))
    if pos <= 10:
        return YANDEX_CTR.get(pos, 1.5)
    if pos <= 20:
        return 0.8
    return 0.2


def score_one(kw):
    vol = float(kw.get("volume", 0) or 0)
    pos = float(kw.get("position", 0) or 0)
    intent = INTENT_WEIGHT.get(str(kw.get("intent", "informational")).lower(), 0.5)
    comp = float(kw.get("competition", 0.5) or 0.5)  # 0..1, выше = сложнее
    cluster = float(kw.get("cluster_size", 0) or 0)  # сколько связанных ключей

    # нормализации (логарифм объёма, инверсия конкуренции)
    import math
    vol_n = min(1.0, math.log10(vol + 1) / 5)          # 100k -> ~1.0
    pos_n = (1 - min(pos, 30) / 30) if pos else 0.3     # ближе к топу = выше потенциал улучшения
    comp_n = 1 - comp
    cluster_n = min(1.0, cluster / 20)
    # CTR-gap: разница между потенциальным (топ-3) и текущим CTR
    ctr_gap = max(0, expected_ctr(3) - expected_ctr(pos)) / expected_ctr(1)

    raw = (
        vol_n * WEIGHTS["volume"]
        + pos_n * WEIGHTS["position"]
        + intent * WEIGHTS["intent"]
        + comp_n * WEIGHTS["competition"]
        + cluster_n * WEIGHTS["cluster"]
        + ctr_gap * WEIGHTS["ctr_gap"]
    )
    return round(raw * 100, 1)


def rank(keywords):
    scored = []
    for kw in keywords:
        s = score_one(kw)
        scored.append({**kw, "opportunity_score": s,
                       "tier": "quick-win" if (kw.get("position") and 11 <= kw["position"] <= 20)
                       else ("high" if s >= 60 else "medium" if s >= 40 else "low")})
    return sorted(scored, key=lambda x: x["opportunity_score"], reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="JSON-массив ключей с метриками")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    with open(args.file, encoding="utf-8") as f:
        kws = json.load(f)
    ranked = rank(kws)
    if args.json:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))
    else:
        for k in ranked[:20]:
            print(f"  {k['opportunity_score']:5} [{k['tier']:9}] {k.get('keyword','')}")


if __name__ == "__main__":
    main()
