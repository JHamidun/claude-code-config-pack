#!/usr/bin/env python3
"""Удержать индекс памяти в пределах, за которыми он молча обрезается.

MEMORY.md загружается в начало каждой сессии, и всё, что выходит за лимит, просто не
доезжает — без ошибки и без предупреждения. Обнаруживается это случайно: однажды
оказалось, что из индекса выпали целые разделы, включая указатель на архив.

Лимита два, и нарушается обычно второй: 200 строк И 25 килобайт. Строк почти всегда
меньше нормы, а байты набегают из пояснений — к каждой ссылке дописывается пересказ
того, что и так лежит внутри самой заметки.

Скрипт ужимает индекс до безопасного размера тремя приёмами по очереди, от самого
безобидного: сначала режет длинные пояснения у старых записей, потом выносит старые
операции в отдельный файл-архив, и только в крайнем случае сообщает, что нужна
ручная чистка.

    python memory_fit.py                 # проверить и ужать, если нужно
    python memory_fit.py --check         # только проверить, ничего не менять
    python memory_fit.py --limit 24      # свой запас в килобайтах
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

def _memory_dir() -> pathlib.Path:
    """Где лежит память этого проекта.

    Claude Code кодирует путь проекта в имя папки, поэтому оно у каждого своё.
    Берём папку с самым свежим индексом — это и есть проект, в котором работают.
    """
    root = pathlib.Path.home() / ".claude" / "projects"
    cands = sorted(root.glob("*/memory/MEMORY.md"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if cands:
        return cands[0].parent
    return root / "default" / "memory"


MEM = _memory_dir()
INDEX = MEM / "MEMORY.md"
HARD_KB = 25          # за этим байтом хвост отбрасывается
HARD_LINES = 200


def size_kb(t: str) -> float:
    return len(t.encode("utf-8")) / 1024


def age_marks(lines: list[str], keep_fresh: int = 6) -> tuple[list[str], int]:
    """Снять пометку «свежее» со всех записей, кроме последних добавленных.

    Пометка защищает запись от ужатия — это правильно, пока запись действительно
    свежая. Но за день их набирается два десятка, и защищённой оказывается половина
    индекса: ужимать становится нечего, а лимит уже нарушен. Поэтому пометка стареет
    сама, оставаясь только у последних записей.
    """
    idx = [i for i, l in enumerate(lines) if "⭐ NEW" in l]
    stale = idx[:-keep_fresh] if len(idx) > keep_fresh else []
    out = list(lines)
    for i in stale:
        out[i] = out[i].replace(" ⭐ NEW", "").replace("⭐ NEW ", "").replace("⭐ NEW", "")
    return out, len(stale)


def trim_tails(lines: list[str], keep: int = 78) -> tuple[list[str], int]:
    """Укоротить пояснения у записей, кроме свежих.

    Свежие пометки трогать нельзя: их читают чаще всего, и обрезанная мысль там
    дороже сэкономленных байтов.
    """
    out, saved = list(lines), 0
    for i, l in enumerate(out):
        if not l.startswith("- ") or "⭐ NEW" in l:
            continue
        idx = l.rfind(")")
        if idx < 0:
            continue
        head, tail = l[:idx + 1], l[idx + 1:]
        if len(tail.encode()) <= keep + 40:
            continue
        cut = tail[:keep].rsplit(" ", 1)[0].rstrip(",;—-·")
        saved += len(tail.encode()) - len(cut.encode())
        out[i] = head + cut + "…"
    return out, saved


def archive_old(lines: list[str], months_keep: int = 2) -> tuple[list[str], int]:
    """Вынести старые операции в отдельный файл, оставив один указатель.

    Записи прошлых месяцев нужны редко, а место в окне занимают каждую сессию.
    Они не удаляются — переезжают в файл рядом и остаются доступны по ссылке.
    """
    from datetime import date
    cur = date.today()
    old_marks = set()
    for back in range(months_keep, months_keep + 10):
        m = cur.month - back
        y = cur.year + (m - 1) // 12
        old_marks.add(f"{y}-{((m - 1) % 12) + 1:02d}-")

    kept, moved, in_ops = [], [], False
    for l in lines:
        if l.startswith("## "):
            in_ops = "ACTIVE OPS" in l
        m = re.match(r"^- (?:\d{2}-\d{2}: )?\[.*?\]\((.+?\.md)\)", l)
        if in_ops and m and any(k in m.group(1) for k in old_marks):
            moved.append(l)
            continue
        kept.append(l)

    if moved:
        arch = MEM / "_ops-archive-older.md"
        prev = arch.read_text(encoding="utf-8") if arch.exists() else "# Операции прошлых месяцев\n\n"
        arch.write_text(prev.rstrip() + "\n" + "\n".join(moved) + "\n", encoding="utf-8")
        for i, l in enumerate(kept):
            if "ACTIVE OPS" in l:
                kept.insert(i + 1, f"\n- 📦 [Операции прошлых месяцев]({arch.name}) — {len(moved)} записей")
                break
    return kept, len(moved)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="только проверить")
    ap.add_argument("--limit", type=float, default=24.2,
                    help="целевой размер в КБ (с запасом до жёстких 25)")
    a = ap.parse_args()

    if not INDEX.exists():
        raise SystemExit(f"нет файла: {INDEX}")
    t = INDEX.read_text(encoding="utf-8")
    kb, ln = size_kb(t), t.count("\n") + 1
    over_kb, over_ln = kb > HARD_KB, ln > HARD_LINES
    print(f"  сейчас: {kb:.1f} КБ из {HARD_KB}, {ln} строк из {HARD_LINES}"
          f"{'  ← ХВОСТ ТЕРЯЕТСЯ' if over_kb or over_ln else '  — в пределах'}")

    if a.check or (kb <= a.limit and not over_ln):
        return 0

    lines = t.splitlines()
    lines, aged = age_marks(lines)
    if aged:
        print(f"  снята пометка «свежее» с {aged} записей — они перестали защищать от ужатия")
    lines, saved = trim_tails(lines)
    t2 = "\n".join(lines) + "\n"
    print(f"  укорочены пояснения: −{saved / 1024:.1f} КБ → {size_kb(t2):.1f} КБ")

    if size_kb(t2) > a.limit:
        lines, moved = archive_old(lines)
        t2 = "\n".join(lines) + "\n"
        print(f"  вынесено в архив записей: {moved} → {size_kb(t2):.1f} КБ")

    INDEX.write_text(t2, encoding="utf-8")
    final = size_kb(t2)
    print(f"  итог: {final:.1f} КБ, {t2.count(chr(10)) + 1} строк "
          f"{'✓' if final <= HARD_KB else '← всё ещё много, нужна ручная чистка'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
