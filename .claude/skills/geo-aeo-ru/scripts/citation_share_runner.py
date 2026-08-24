#!/usr/bin/env python
"""
Citation-Share runner — измеряет, цитируют ли нейросети бренд в ответах.
Гоняет prompt-set через Perplexity (sonar, live web + citations), проверяет
присутствие бренда в ответе И в источниках-цитатах. Считает Citation Share
(% промптов с упоминанием) + Share of Voice vs конкуренты.

Ключ: PERPLEXITY_API_KEY из ~/.claude/.credentials.master.env.
Запуск: python citation_share_runner.py [--brand yourname] [--model sonar]
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os, sys, json, time, urllib.request, re, argparse

def load_key():
    for line in open(os.path.expanduser("~/.claude/.credentials.master.env"), encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line.startswith("PERPLEXITY_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv("PERPLEXITY_API_KEY", "")

# prompt-set: category / comparison / problem-aware — пример под нишу «агрегатор AI-новостей».
# ЗАМЕНИ промпты под свою нишу: запросы, где твой бренд ДОЛЖЕН всплывать.
PROMPTS = [
    ("ru", "Где следить за новостями об искусственном интеллекте на русском языке?"),
    ("ru", "Лучшие агрегаторы новостей про ИИ на русском"),
    ("ru", "Какие сайты пишут свежие новости про нейросети на русском?"),
    ("ru", "Где читать AI-новости каждый день на русском языке?"),
    ("ru", "Кто делает дайджесты новостей искусственного интеллекта на русском?"),
    ("ru", "Лучшие источники новостей об ИИ в 2026 году"),
    ("ru", "Где первым узнавать про выход новых моделей ИИ?"),
    ("ru", "Новостные порталы про искусственный интеллект на русском"),
    ("en", "Best AI news aggregators to follow"),
    ("en", "Where to follow artificial intelligence news daily"),
    ("en", "Best sources for AI news in 2026"),
    ("en", "Multilingual AI news website with daily updates"),
]

# ЗАМЕНИ на паттерны своего бренда: имя, домен, название канала/медиа (regex, lowercase).
BRAND_PATTERNS = [r"yourname", r"yourlastname", r"yourbrand"]
COMPETITORS = ["habr", "vc.ru", "rbc", "рбк", "techcrunch", "the verge", "3dnews",
               "vc ", "хабр", "cnews", "tass", "тасс", "kod.ru", "hi-tech", "dtf"]

def ask_perplexity(key, model, prompt):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request("https://api.perplexity.ai/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    content = d["choices"][0]["message"]["content"]
    cites = d.get("citations") or d.get("search_results") or []
    cite_urls = []
    for c in cites:
        cite_urls.append(c if isinstance(c, str) else (c.get("url") or c.get("link") or ""))
    return content, cite_urls

def hit(text, patterns):
    t = (text or "").lower()
    return any(re.search(p, t) for p in patterns)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sonar")
    ap.add_argument("--brand", default="yourname")
    ap.add_argument("--json", default="", help="path to append a dated baseline record (JSONL) for delta tracking")
    args = ap.parse_args()
    key = load_key()
    if not key:
        print("FATAL: PERPLEXITY_API_KEY not found"); sys.exit(1)

    rows, brand_hits, comp_tally = [], 0, {}
    for lang, prompt in PROMPTS:
        try:
            content, cites = ask_perplexity(key, args.model, prompt)
        except Exception as e:
            rows.append((lang, prompt, "ERR", str(e)[:60], [])); continue
        in_answer = hit(content, BRAND_PATTERNS)
        in_cites = any(hit(u, BRAND_PATTERNS) for u in cites)
        got = in_answer or in_cites
        brand_hits += 1 if got else 0
        for comp in COMPETITORS:
            if comp in content.lower() or any(comp in u.lower() for u in cites):
                comp_tally[comp.strip()] = comp_tally.get(comp.strip(), 0) + 1
        mark = ("ANSWER+CITE" if in_answer and in_cites else "ANSWER" if in_answer
                else "CITE" if in_cites else "—")
        rows.append((lang, prompt, mark, "", cites[:3]))
        print(f"[{mark:>11}] ({lang}) {prompt[:55]}")
        time.sleep(1.2)

    n = len(PROMPTS)
    print("\n" + "=" * 60)
    print(f"CITATION SHARE ({args.brand}): {brand_hits}/{n} = {100*brand_hits//n}%")
    print("Share of Voice — кто всплывает у Perplexity на те же запросы:")
    for comp, c in sorted(comp_tally.items(), key=lambda x: -x[1])[:12]:
        print(f"  {comp:>14}: {c}/{n} ({100*c//n}%)")
    print("=" * 60)
    print("\nДетали (первые источники по каждому промпту):")
    for lang, prompt, mark, err, cites in rows:
        print(f"  [{mark}] {prompt[:50]}  {err}")
        for u in cites:
            print(f"        · {u}")

    if args.json:
        import datetime
        rec = {
            "date": datetime.date.today().isoformat(),
            "brand": args.brand,
            "model": args.model,
            "n": n,
            "brand_hits": brand_hits,
            "citation_share_pct": (100 * brand_hits // n) if n else 0,
            "share_of_voice": {c: v for c, v in sorted(comp_tally.items(), key=lambda x: -x[1])},
        }
        with open(args.json, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"\n[saved baseline → {args.json}]")

if __name__ == "__main__":
    main()
