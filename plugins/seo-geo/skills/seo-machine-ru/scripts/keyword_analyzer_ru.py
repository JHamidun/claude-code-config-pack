#!/usr/bin/env python3
"""Анализ ключевых слов для русского текста с учётом словоформ.

Русский флективный — «нейросеть/нейросети/нейросетью» = одно ключевое.
Если установлен pymorphy3 (или pymorphy2 на Python<3.11) — лемматизируем; иначе грубая нормализация
по общему корню (отрезаем типовые окончания). Считаем плотность,
распределение по тексту, риск переспама.

CLI:
    python keyword_analyzer_ru.py <file.md> --kw "нейросети" "ai-агрегатор"
    python keyword_analyzer_ru.py <file.md> --kw-file keywords.txt --json
"""
import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import pymorphy3 as _pymorphy
    _MORPH = _pymorphy.MorphAnalyzer()
except Exception:
    try:
        import pymorphy2 as _pymorphy  # legacy; broken on Python >= 3.11 (inspect.getargspec)
        _MORPH = _pymorphy.MorphAnalyzer()
    except Exception:
        _MORPH = None

_ENDINGS = ("ами", "ями", "ого", "его", "ому", "ему", "ыми", "ими",
            "ах", "ях", "ам", "ям", "ом", "ем", "ой", "ей", "ую", "юю",
            "ов", "ев", "ы", "и", "а", "я", "о", "е", "у", "ю", "й", "ь")


def normalize(word: str) -> str:
    w = word.lower().replace("ё", "е")
    if _MORPH:
        try:
            return _MORPH.parse(w)[0].normal_form.replace("ё", "е")
        except Exception:
            pass
    for end in _ENDINGS:
        if len(w) - len(end) >= 4 and w.endswith(end):
            return w[: -len(end)]
    return w


def tokens(text: str):
    return [normalize(t) for t in re.findall(r"[А-Яа-яЁёA-Za-z]+", text)]


def norm_phrase(kw: str):
    return tuple(normalize(t) for t in re.findall(r"[А-Яа-яЁёA-Za-z]+", kw))


def count_phrase(toks, phrase):
    n = len(phrase)
    if n == 0:
        return 0
    return sum(1 for i in range(len(toks) - n + 1) if tuple(toks[i:i + n]) == phrase)


def distribution(text: str, phrase, parts: int = 4):
    """В каких четвертях текста встречается ключ (равномерность)."""
    chunks = _split_chunks(text, parts)
    return [count_phrase(tokens(c), phrase) for c in chunks]


def _split_chunks(text, parts):
    words = re.findall(r"\S+\s*", text)
    size = max(1, len(words) // parts)
    return ["".join(words[i:i + size]) for i in range(0, len(words), size)][:parts] or [text]


def analyze(text: str, keywords):
    toks = tokens(text)
    total = max(1, len(toks))
    out = []
    for kw in keywords:
        phrase = norm_phrase(kw)
        cnt = count_phrase(toks, phrase)
        density = round(100 * cnt * len(phrase) / total, 2)
        dist = distribution(text, phrase)
        # для однословных ключей целевая плотность 1-2%, фраз — 0.5-1%
        target = (1.0, 2.0) if len(phrase) == 1 else (0.3, 1.0)
        if density == 0:
            verdict = "отсутствует"
        elif density < target[0]:
            verdict = "мало"
        elif density > target[1] + 1.5:
            verdict = "переспам — риск"
        elif density > target[1]:
            verdict = "выше нормы"
        else:
            verdict = "ок"
        out.append({
            "keyword": kw,
            "count": cnt,
            "density_pct": density,
            "target_pct": list(target),
            "verdict": verdict,
            "distribution_quarters": dist,
            "even": all(d > 0 for d in dist) if cnt else False,
        })
    return {"total_words": total, "lemmatizer": _pymorphy.__name__ if _MORPH else "fallback", "keywords": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--kw", nargs="*", default=[])
    ap.add_argument("--kw-file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    kws = list(args.kw)
    if args.kw_file:
        with open(args.kw_file, encoding="utf-8") as f:
            kws += [l.strip() for l in f if l.strip()]
    if not kws:
        ap.error("укажи --kw или --kw-file")
    with open(args.file, encoding="utf-8") as f:
        text = f.read()
    res = analyze(text, kws)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"Всего слов: {res['total_words']} | лемматизатор: {res['lemmatizer']}\n")
        for k in res["keywords"]:
            print(f"  {k['keyword']!r}: {k['count']}× | {k['density_pct']}% | {k['verdict']} | распр. {k['distribution_quarters']}")


if __name__ == "__main__":
    main()
