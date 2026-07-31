#!/usr/bin/env python3
"""Композитная оценка качества контента (RU), порог публикации 70.

5 измерений (веса как в исходном seomachine, перекалибровано под RU):
  humanity 30 / specificity 25 / structure 20 / seo 15 / readability 10.
humanity штрафует за AI-клише и канцелярит (RU-список), хвалит за живость.
Выдаёт JSON со scores/composite/priority_fixes — формат совместим с
авто-ревайз-циклом /write.

CLI:  python content_scorer.py <file.md> [--kw "ключ"] [--json]
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import readability_ru  # noqa: E402
import seo_quality_rater_ru  # noqa: E402

# AI-клише и маркетинговый шум на русском (анти-AI-tells)
AI_CLICHES = [
    "в современном мире", "в эпоху цифровизации", "не секрет что", "стоит отметить",
    "важно понимать", "давайте разберёмся", "давайте разберемся", "в данной статье",
    "в этой статье мы", "подводя итог", "в заключение хочется", "является ключевым",
    "играет важную роль", "трудно переоценить", "на сегодняшний день",
    "революционный", "уникальный", "инновационный", "не имеет аналогов",
    "вывод на новый уровень", "меняет правила игры", "в мире где",
    "погрузимся в", "раскроем секреты", "всё что нужно знать",
]
MARKETING_HYPE = ["лучший", "идеальный", "потрясающий", "невероятный", "удивительный"]


def humanity(text):
    low = text.lower()
    cliche = sum(low.count(c) for c in AI_CLICHES)
    hype = sum(low.count(h) for h in MARKETING_HYPE)
    # живость: вопросы, первое лицо, прямая речь
    first_person = len(re.findall(r"\b(я|мы|меня|нам|нас|мой|наш)\b", low))
    questions = text.count("?")
    base = 100
    base -= min(50, cliche * 8)
    base -= min(20, hype * 4)
    base += min(15, first_person // 3)
    base += min(10, questions * 2)
    fixes = []
    if cliche: fixes.append(f"убрать {cliche} AI-клише")
    if hype: fixes.append(f"убрать {hype} оценочных эпитетов без доказательств")
    if first_person == 0: fixes.append("добавить первое лицо / личный опыт")
    return max(0, min(100, base)), fixes


def specificity(text):
    words = max(1, len(re.findall(r"[А-Яа-яЁёA-Za-z]+", text)))
    numbers = len(re.findall(r"\b\d[\d %₽$.,]*\b", text))
    proper = len(re.findall(r"\b[А-ЯA-Z][а-яa-z]{2,}\b", text))
    density = (numbers + proper * 0.3) / words * 100
    score = min(100, round(density * 12))
    fixes = []
    if numbers < words / 150: fixes.append("мало цифр/фактов — добавить конкретику")
    return score, fixes


def structure(text):
    h2 = len(re.findall(r"^##\s+", text, re.M))
    paras = [p for p in text.split("\n\n") if p.strip()]
    long_paras = [p for p in paras if len(p.split()) > 80]
    lists = len(re.findall(r"^\s*[-*]\s+", text, re.M))
    score = 100
    if h2 < 3: score -= 25
    if long_paras: score -= min(30, len(long_paras) * 10)
    if lists == 0: score -= 15
    fixes = []
    if h2 < 3: fixes.append("добавить подзаголовки H2 (минимум 3)")
    if long_paras: fixes.append(f"{len(long_paras)} абзацев >80 слов — разбить")
    return max(0, score), fixes


def score(text, keyword=None):
    h, hf = humanity(text)
    sp, spf = specificity(text)
    st, stf = structure(text)
    seo = seo_quality_rater_ru.score(text, keyword)["score"]
    fo = readability_ru.flesch_oborneva(text)
    read = max(0, min(100, round(fo + 30)))  # сдвиг шкалы: 50 FO ≈ 80
    composite = round(h * .30 + sp * .25 + st * .20 + seo * .15 + read * .10)
    fixes = (hf + spf + stf)[:5]
    return {
        "scores": {"humanity": h, "specificity": sp, "structure": st, "seo": seo, "readability": read},
        "composite": composite,
        "pass": composite >= 70,
        "priority_fixes": fixes,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--kw")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    res = score(text, args.kw)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
