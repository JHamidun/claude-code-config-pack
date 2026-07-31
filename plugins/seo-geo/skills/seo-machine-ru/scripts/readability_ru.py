#!/usr/bin/env python3
"""Читаемость русского текста.

textstat/Flesch заточены под английский и врут на русском. Здесь:
- индекс удобочитаемости Флеша–Оборневой (адаптация Флеша для русского),
- метрики «водности» в духе Главреда (стоп-слова/канцелярит),
- структурные метрики (длина предложений/абзацев, пассив).

Зависимостей нет (чистый stdlib). Слоги считаем по гласным.

CLI:  python readability_ru.py <file.md> [--json]
"""
import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"

# Канцелярит / водность (фрагмент списка Главреда — расширяемо)
STOP_WORDS = [
    "является", "осуществляется", "представляет собой", "в настоящее время",
    "в связи с тем что", "необходимо отметить", "следует отметить",
    "данный", "данная", "данные", "вышеуказанный", "вышеперечисленный",
    "в рамках", "в целях", "в части", "по причине", "в случае если",
    "имеет место", "на сегодняшний день", "в результате того что",
    "достаточно", "весьма", "крайне", "очень", "довольно", "просто",
    "по сути", "как правило", "в принципе", "собственно",
]

PASSIVE_PAT = re.compile(r"\b\w+(ется|ются|тся|ался|илась|ировалось|ировался)\b", re.I)


def sentences(text: str):
    text = re.sub(r"\s+", " ", text)
    return [s for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]


def words(text: str):
    return re.findall(r"[А-Яа-яЁёA-Za-z]+", text)


def syllables(word: str) -> int:
    return max(1, sum(1 for ch in word if ch in VOWELS))


def flesch_oborneva(text: str) -> float:
    sents = sentences(text)
    wds = words(text)
    if not sents or not wds:
        return 0.0
    asl = len(wds) / len(sents)            # средняя длина предложения (слов)
    asw = sum(syllables(w) for w in wds) / len(wds)  # слогов на слово
    # Флеш–Оборнева: 206.835 − 1.3·ASL − 60.1·ASW
    return round(206.835 - 1.3 * asl - 60.1 * asw, 1)


def grade_label(score: float) -> str:
    if score >= 80: return "очень легко (5-6 класс)"
    if score >= 60: return "легко (7-9 класс)"
    if score >= 40: return "средне (10-11 класс)"
    if score >= 20: return "сложно (вуз)"
    return "очень сложно (научный)"


def water_score(text: str) -> dict:
    wds = words(text)
    total = max(1, len(wds))
    low = text.lower()
    stop_hits = sum(low.count(sw) for sw in STOP_WORDS)
    water_pct = round(100 * stop_hits / total, 1)
    return {"stop_word_hits": stop_hits, "water_pct": water_pct}


def analyze(text: str) -> dict:
    sents = sentences(text)
    wds = words(text)
    paras = [p for p in text.split("\n\n") if p.strip()]
    long_sents = [s for s in sents if len(words(s)) > 30]
    passive = len(PASSIVE_PAT.findall(text))
    fo = flesch_oborneva(text)
    res = {
        "flesch_oborneva": fo,
        "readability_label": grade_label(fo),
        "words": len(wds),
        "sentences": len(sents),
        "paragraphs": len(paras),
        "avg_sentence_words": round(len(wds) / max(1, len(sents)), 1),
        "long_sentences_over_30w": len(long_sents),
        "passive_constructions": passive,
        **water_score(text),
    }
    # рекомендации
    rec = []
    if fo < 40: rec.append("слишком сложно — короче предложения, проще слова")
    if res["avg_sentence_words"] > 20: rec.append("средняя длина предложения >20 слов — дроби")
    if res["water_pct"] > 5: rec.append("много канцелярита/воды — чисти стоп-слова")
    if res["long_sentences_over_30w"] > 0: rec.append(f"{len(long_sents)} предложений >30 слов — разбей")
    res["recommendations"] = rec
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    res = analyze(text)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for k, v in res.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
