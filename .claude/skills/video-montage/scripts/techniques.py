#!/usr/bin/env python3
"""Каталог монтажных и съёмочных приёмов: найти приём под задачу.

Зачем. Приёмы разбросаны по десятку скиллов и по чужим разобранным движкам, и всякий
раз их приходится вспоминать. Здесь они сведены в одну таблицу, где у каждого приёма
записано главное: КОГДА он уместен, КАКИМИ числами задаётся и ЧЕМ исполняется у нас.

У каждого приёма проставлен статус доказательности, и это не украшение: половина
ходовых «правил» интернета первоисточника не имеет, и смешивать их с официальными
данными площадок — верный способ построить пайплайн на выдумке.

    подтверждено  официальный источник площадки или рецензируемое исследование
    практика      сходятся независимые практики, контролируемых сравнений нет
    наше          проверено на своём материале в этой мастерской

    python techniques.py list                      # всё
    python techniques.py list --cat cut            # по разделу
    python techniques.py find "не держится внимание"
    python techniques.py show hook_in_medias
    python techniques.py for-block крючок          # что уместно в этом блоке плана
    python techniques.py stats
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
DB = HERE / "techniques.json"

CATS = {
    "structure": "строение ролика",
    "hook": "крючок, первые секунды",
    "pacing": "темп и плотность событий",
    "cut": "склейка и переход",
    "camera": "камера, крупность, движение",
    "light": "свет и цвет",
    "look": "фактура кадра: грейд, зерно, свечение",
    "text": "текст и титры в кадре",
    "audio": "звук, музыка, голос",
    "prompt": "промпт генерации",
    "qa": "проверка перед выпуском",
}


def load() -> list[dict]:
    if not DB.exists():
        raise SystemExit(f"каталога нет: {DB}")
    return json.loads(DB.read_text(encoding="utf-8"))


def show_one(t: dict, full: bool = True) -> str:
    L = [f"  {t['id']}   [{CATS.get(t['category'], t['category'])}]  ·  {t['evidence']}",
         f"  {t['name']}"]
    if full:
        L.append(f"\n  когда:    {t['when']}")
        L.append(f"  как:      {t['how']}")
        if t.get("params"):
            L.append(f"  числа:    {t['params']}")
        if t.get("tool"):
            L.append(f"  чем:      {t['tool']}")
        if t.get("fail"):
            L.append(f"  ошибка:   {t['fail']}")
        if t.get("source"):
            L.append(f"  источник: {t['source']}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="перечислить приёмы")
    p.add_argument("--cat", choices=sorted(CATS))
    p.add_argument("--evidence", choices=["подтверждено", "практика", "наше"])
    p.add_argument("--full", action="store_true")

    p = sub.add_parser("find", help="поиск по смыслу задачи")
    p.add_argument("query")

    p = sub.add_parser("show", help="карточка приёма")
    p.add_argument("tid")

    p = sub.add_parser("for-block", help="что уместно в блоке плана")
    p.add_argument("block", help="крючок | перехват | тело | выдача | петля")

    sub.add_parser("stats", help="сводка каталога")
    a = ap.parse_args()

    T = load()

    if a.cmd == "stats":
        print(f"  приёмов: {len(T)}")
        for c, name in CATS.items():
            n = sum(t["category"] == c for t in T)
            if n:
                print(f"    {c:10s} {n:3d}   {name}")
        print()
        for e in ("подтверждено", "практика", "наше"):
            print(f"    {e:14s} {sum(t['evidence'] == e for t in T):3d}")
        return 0

    if a.cmd == "list":
        pool = [t for t in T
                if (not a.cat or t["category"] == a.cat)
                and (not a.evidence or t["evidence"] == a.evidence)]
        for t in pool:
            print(show_one(t, full=a.full))
            print()
        print(f"  всего: {len(pool)}")
        return 0

    if a.cmd == "show":
        for t in T:
            if t["id"] == a.tid:
                print(show_one(t))
                return 0
        raise SystemExit(f"нет такого приёма: {a.tid}")

    if a.cmd == "for-block":
        pool = [t for t in T if a.block in (t.get("blocks") or [])]
        if not pool:
            raise SystemExit(f"для блока «{a.block}» ничего не помечено")
        for t in pool:
            print(show_one(t))
            print()
        print(f"  уместно в блоке «{a.block}»: {len(pool)}")
        return 0

    if a.cmd == "find":
        # Поиск по всем полям, слова запроса — по отдельности: спрашивают своими словами,
        # а не терминами каталога, поэтому совпадение по одному слову уже полезно.
        words = [w for w in re.split(r"\W+", a.query.lower()) if len(w) > 2]
        scored = []
        for t in T:
            blob = " ".join(str(v) for v in t.values()).lower()
            hits = sum(blob.count(w) for w in words)
            if hits:
                scored.append((hits, t))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            print("  ничего не нашлось — попробуй другими словами")
            return 1
        for hits, t in scored[:8]:
            print(show_one(t))
            print()
        print(f"  найдено: {len(scored)}, показано {min(8, len(scored))}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
