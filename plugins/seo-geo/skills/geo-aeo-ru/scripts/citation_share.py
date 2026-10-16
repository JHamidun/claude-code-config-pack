# -*- coding: utf-8 -*-
"""Замер Citation Share: как часто бренд появляется в ответах AI-движков.

Зачем этот файл лежит в скилле, а не во временной папке. Первый замер сделали
13.08.2026 — получили 16,7%. Скрипт и набор промптов остались в scratchpad и
были утрачены. Через две недели после исправления разметки сравнивать оказалось
не с чем: базовая цифра есть, а воспроизвести замер нечем. Инструмент измерения
обязан жить под версионным контролем рядом со скиллом.

ВАЖНО ПРО РАСХОДЫ: скрипт обращается к платным API. Без --run он ничего не
вызывает — только показывает, что будет спрошено. Запускать осознанно.

    python citation_share.py                  # показать prompt-set, ничего не тратить
    python citation_share.py --run            # выполнить замер (ПЛАТНО)
    python citation_share.py --run --out r.json
    python citation_share.py --compare a.json b.json   # сравнить два замера

Методология (из skills/geo-aeo-ru): промпты делятся на типы, и это важнее общей
цифры. Попадание в brand-direct («расскажи про X») почти ничего не значит — имя
названо в самом вопросе. Ценность имеют category, problem-aware и comparison:
там бренд должен всплыть сам.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

CREDS = Path.home() / ".claude" / ".credentials.master.env"

# Бренд и то, чем его можно спутать/с чем сравнить.
BRAND_PATTERNS = [
    r"yourname",
    r"yourlastname",
    r"yourfirstname",
    r"вайбкодинг[- ]?интенсив",
]

COMPETITORS = [
    "skillbox", "скиллбокс",
    "яндекс практикум", "practicum",
    "нетология", "netology",
    "geekbrains", "гикбрейнс",
    "stepik", "степик",
    "otus", "отус",
]

# Prompt-set. Тип важнее формулировки — см. методологию выше.
PROMPTS = [
    # --- brand-direct: имя названо в вопросе. Попадание тут почти ничего не доказывает
    ("brand-direct", "Что такое вайбкодинг-интенсив YourName и для кого он?"),
    ("brand-direct", "Кто такой Your Name и чем он занимается в области ИИ?"),
    # --- category: бренд должен всплыть сам
    ("category", "Какие есть курсы по вайбкодингу на русском языке?"),
    ("category", "Где научиться работать с Claude Code на русском?"),
    ("category", "Лучшие обучающие программы по ИИ-агентам для предпринимателей в России"),
    ("category", "Курсы, где учат собирать продукты с помощью ИИ без программирования"),
    # --- problem-aware: описана боль, бренда в вопросе нет. Самый сильный сигнал
    ("problem-aware", "Как предпринимателю научиться делать сайты и ботов с помощью ИИ, не умея программировать?"),
    ("problem-aware", "Хочу собрать своего ИИ-агента под задачу бизнеса, с чего начать обучение?"),
    ("problem-aware", "Как установить и начать пользоваться Claude Code, если я из России?"),
    ("problem-aware", "Что почитать или пройти, чтобы перестать зависеть от подрядчиков в разработке?"),
    # --- comparison: сравнение с конкурентами
    ("comparison", "Сравни курсы по ИИ-разработке: Skillbox, Яндекс Практикум и авторские интенсивы"),
    ("comparison", "Что лучше для обучения вайбкодингу — большие онлайн-школы или авторские программы?"),
]


def env(key: str) -> str:
    if not CREDS.exists():
        return os.environ.get(key, "")
    for line in CREDS.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(key, "")


def find_mentions(text: str) -> dict:
    low = (text or "").lower()
    brand = any(re.search(p, low) for p in BRAND_PATTERNS)
    comps = sorted({c for c in COMPETITORS if c in low})
    return {"бренд": brand, "конкуренты": comps}


def ask_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    import urllib.request
    key = env("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("нет OPENAI_API_KEY")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


def ask_perplexity(prompt: str, model: str = "sonar") -> str:
    import urllib.request
    key = env("PERPLEXITY_API_KEY")
    if not key:
        raise RuntimeError("нет PERPLEXITY_API_KEY")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


ENGINES = {"openai": ask_openai, "perplexity": ask_perplexity}


def run(engines: list[str], out: str | None) -> int:
    results = []
    for kind, prompt in PROMPTS:
        for eng in engines:
            try:
                answer = ENGINES[eng](prompt)
                err = None
            except Exception as e:  # noqa: BLE001
                # Ошибку не проглатываем: замер с молча выпавшим движком врёт
                answer, err = "", str(e)[:160]
            row = {"тип": kind, "движок": eng, "промпт": prompt, "ошибка": err}
            row.update(find_mentions(answer))
            results.append(row)
            print(f"  [{eng}] {kind:14} {'+' if row.get('бренд') else '-'} {prompt[:52]}"
                  + (f"  ОШИБКА: {err}" if err else ""))
            time.sleep(1.2)

    ok = [r for r in results if not r["ошибка"]]
    hits = [r for r in ok if r["бренд"]]
    by_kind = {}
    for r in ok:
        d = by_kind.setdefault(r["тип"], {"всего": 0, "попаданий": 0})
        d["всего"] += 1
        d["попаданий"] += 1 if r["бренд"] else 0

    share = round(100 * len(hits) / len(ok), 1) if ok else 0.0
    summary = {
        "дата": time.strftime("%Y-%m-%d %H:%M"),
        "ответов_учтено": len(ok),
        "ошибок": len(results) - len(ok),
        "citation_share_%": share,
        "по_типам": by_kind,
        "база_13_08_2026": 16.7,
    }
    print("\n=== ИТОГ ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\nЧитать так: попадания в brand-direct почти ничего не значат — имя названо")
    print("в самом вопросе. Смотри category, problem-aware и comparison.")

    if out:
        Path(out).write_text(
            json.dumps({"сводка": summary, "ответы": results}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nсохранено: {out}")
    return 0


def compare(a: str, b: str) -> int:
    da = json.loads(Path(a).read_text(encoding="utf-8"))
    db = json.loads(Path(b).read_text(encoding="utf-8"))
    sa, sb = da["сводка"], db["сводка"]
    print(f"{sa['дата']}: {sa['citation_share_%']}%   →   {sb['дата']}: {sb['citation_share_%']}%")
    delta = round(sb["citation_share_%"] - sa["citation_share_%"], 1)
    print(f"изменение: {delta:+}%")
    print("\nпо типам:")
    for kind in sorted(set(sa["по_типам"]) | set(sb["по_типам"])):
        pa = sa["по_типам"].get(kind, {})
        pb = sb["по_типам"].get(kind, {})
        print(f"  {kind:14} {pa.get('попаданий',0)}/{pa.get('всего',0)}"
              f"  →  {pb.get('попаданий',0)}/{pb.get('всего',0)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="выполнить замер (ПЛАТНЫЕ вызовы)")
    ap.add_argument("--engines", default="openai,perplexity")
    ap.add_argument("--out", default=None)
    ap.add_argument("--compare", nargs=2, metavar=("СТАРЫЙ", "НОВЫЙ"))
    a = ap.parse_args()

    if a.compare:
        return compare(*a.compare)

    if not a.run:
        print("PROMPT-SET (замер НЕ запущен — платные вызовы делаются только с --run)\n")
        by = {}
        for kind, p in PROMPTS:
            by.setdefault(kind, []).append(p)
        for kind, items in by.items():
            print(f"--- {kind} ({len(items)}) ---")
            for p in items:
                print("   ", p)
            print()
        print(f"всего промптов: {len(PROMPTS)} · движков по умолчанию: openai, perplexity")
        print(f"вызовов при запуске: {len(PROMPTS) * 2}")
        print("\nбаза для сравнения: 16,7% (13.08.2026)")
        return 0

    return run([e.strip() for e in a.engines.split(",") if e.strip()], a.out)


if __name__ == "__main__":
    sys.exit(main())
