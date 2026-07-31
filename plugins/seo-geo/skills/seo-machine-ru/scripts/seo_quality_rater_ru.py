#!/usr/bin/env python3
"""Оценка on-page SEO статьи 0-100 против RU-гайдлайнов (Яндекс/Google).

Проверяет: объём, заголовки H2/H3, мета (title 50-60 / description 120-160),
внутренние/внешние ссылки, плотность главного ключа, читаемость, наличие
прямого ответа в начале (для AEO), списки/таблицы. Чистый stdlib.

CLI:
    python seo_quality_rater_ru.py <file.md> --kw "главный ключ" [--json]

Markdown-вход. Мета берём из YAML-frontmatter (title/description) если есть.
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
import readability_ru  # сосед по scripts/  # noqa: E402
import keyword_analyzer_ru  # noqa: E402


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = {}
    body = text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = text[m.end():]
    return meta, body


def score(text, keyword=None):
    meta, body = parse_frontmatter(text)
    words = re.findall(r"[А-Яа-яЁёA-Za-z]+", body)
    wc = len(words)
    h2 = len(re.findall(r"^##\s+", body, re.M))
    h3 = len(re.findall(r"^###\s+", body, re.M))
    links_int = len(re.findall(r"\]\((?!https?://)[^)]+\)", body))
    links_ext = len(re.findall(r"\]\(https?://[^)]+\)", body))
    lists = len(re.findall(r"^\s*[-*]\s+", body, re.M))
    tables = body.count("|---")
    title = meta.get("title", "")
    desc = meta.get("description", meta.get("descr", ""))

    checks = []  # (название, балл, макс, заметка)

    # Объём
    if wc >= 1500: checks.append(("Объём", 15, 15, f"{wc} слов"))
    elif wc >= 800: checks.append(("Объём", 10, 15, f"{wc} слов — норм, можно глубже"))
    else: checks.append(("Объём", 4, 15, f"{wc} слов — тонко"))

    # Структура заголовков
    s = 15 if h2 >= 3 else (8 if h2 >= 1 else 0)
    checks.append(("Заголовки H2/H3", s, 15, f"H2={h2}, H3={h3}"))

    # Мета title
    if 45 <= len(title) <= 60: checks.append(("Title", 10, 10, f"{len(title)} симв."))
    elif title: checks.append(("Title", 5, 10, f"{len(title)} симв. — не в 45-60"))
    else: checks.append(("Title", 0, 10, "нет title"))

    # Мета description
    if 110 <= len(desc) <= 160: checks.append(("Description", 10, 10, f"{len(desc)} симв."))
    elif desc: checks.append(("Description", 5, 10, f"{len(desc)} симв. — не в 110-160"))
    else: checks.append(("Description", 0, 10, "нет description"))

    # Ссылки
    ls = (8 if links_int >= 2 else links_int * 3) + (4 if links_ext >= 1 else 0)
    checks.append(("Ссылки", min(12, ls), 12, f"внутр={links_int}, внеш={links_ext}"))

    # Списки/таблицы (сканируемость + AEO)
    checks.append(("Списки/таблицы", 8 if (lists + tables) >= 2 else 3, 8, f"списки={lists}, таблиц={tables}"))

    # Плотность ключа
    if keyword:
        ka = keyword_analyzer_ru.analyze(body, [keyword])["keywords"][0]
        if ka["verdict"] == "ок": ks = 12
        elif ka["verdict"] in ("выше нормы", "мало"): ks = 7
        elif ka["verdict"] == "переспам — риск": ks = 3
        else: ks = 0
        checks.append(("Плотность ключа", ks, 12, f"{ka['density_pct']}% — {ka['verdict']}"))
    else:
        checks.append(("Плотность ключа", 6, 12, "ключ не задан"))

    # Читаемость
    fo = readability_ru.flesch_oborneva(body)
    rs = 10 if fo >= 50 else (6 if fo >= 35 else 2)
    checks.append(("Читаемость", rs, 10, f"Флеш-Оборнева={fo}"))

    # Прямой ответ в начале (AEO)
    first = " ".join(body.split()[:60])
    aeo = 8 if (keyword and any(k in first.lower() for k in keyword.lower().split())) else 3
    checks.append(("Прямой ответ в intro (AEO)", aeo, 8, "ключ в первых 60 словах" if aeo == 8 else "нет прямого ответа сверху"))

    total = sum(c[1] for c in checks)
    maxt = sum(c[2] for c in checks)
    pct = round(100 * total / maxt)
    return {
        "score": pct,
        "verdict": "готово к публикации" if pct >= 75 else ("доработать" if pct >= 55 else "переписать"),
        "checks": [{"name": n, "score": sc, "max": mx, "note": note} for n, sc, mx, note in checks],
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
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"SEO-оценка: {res['score']}/100 — {res['verdict']}\n")
        for c in res["checks"]:
            print(f"  [{c['score']}/{c['max']}] {c['name']}: {c['note']}")


if __name__ == "__main__":
    main()
