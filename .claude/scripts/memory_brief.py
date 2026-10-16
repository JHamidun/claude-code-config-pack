"""
memory_brief.py — KNOWN GOTCHAS block for Fable-worker prompts.

Usage:
    python ~/.claude/scripts/memory_brief.py "<тема задачи>"
    python ~/.claude/scripts/memory_brief.py "hermes деплой" --max-tokens 600

Pulls relevant грабли/решения from three memory layers:
  1. ВСЕ заметки памяти — memory_find.py (необязательный: если его нет рядом
     со скриптом, слой пуст), ранжирование по description/заголовку/телу.
     Без этого слоя в бриф не могут попасть заметки, которых нет в MEMORY.md.
  2. MEMORY.md curated index — keyword-scored one-liner lines.

Prints a compact "KNOWN GOTCHAS" markdown block (default cap 600 tokens)
meant to be pasted verbatim into a worker prompt. Read-only; degrades
gracefully: if embedding API is down → FTS-only; if brain import fails →
MEMORY.md only.
"""

import argparse
import re
import sys
from pathlib import Path

BRAIN_DIR = Path.home() / ".brain"


def _memory_md() -> Path:
    """Индекс памяти этого проекта.

    Claude Code кодирует путь проекта в имя папки (C--Users-<логин>), поэтому
    оно у каждого своё и захардкодить его нельзя: несуществующий путь тут не
    падает, а тихо отдаёт пустой блок гоч. Берём папку с самым свежим
    MEMORY.md — это и есть проект, в котором работают.
    """
    root = Path.home() / ".claude" / "projects"
    cands = sorted(root.glob("*/memory/MEMORY.md"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else root / "default" / "memory" / "MEMORY.md"


MEMORY_MD = _memory_md()

STOPWORDS = {
    "как", "что", "для", "при", "это", "или", "его", "все", "чем", "быть",
    "the", "and", "for", "with", "какие", "какой", "куда", "где", "когда",
    "почему", "нужно", "надо", "есть",
}


def _count_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        # RU in cl100k ≈ 1.7 chars/token; conservative 1.5
        return int(len(text) / 1.5)


def _keywords(topic: str) -> list[str]:
    words = re.findall(r"[\w-]+", topic.lower())
    kws = []
    for w in words:
        if len(w) < 3 or w in STOPWORDS:
            continue
        # crude RU stemming: keep first 5 chars for morphology tolerance
        kws.append(w[:5] if len(w) > 5 else w)
    return kws


def _one_liner(text: str, max_chars: int = 180) -> str:
    line = " ".join(text.split())
    if len(line) > max_chars:
        cut = line[:max_chars]
        # try not to cut mid-word
        if " " in cut[-20:]:
            cut = cut[:cut.rfind(" ")]
        line = cut + "…"
    return line


def search_memory_md(topic: str, limit: int = 6) -> list[str]:
    """Score MEMORY.md one-liner index lines by keyword overlap."""
    if not MEMORY_MD.exists():
        return []
    kws = _keywords(topic)
    if not kws:
        return []
    scored = []
    for raw in MEMORY_MD.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("- ["):
            continue
        low = line.lower()
        score = sum(1 for kw in kws if kw in low)
        if score > 0:
            # strip markdown link target, keep the human title
            clean = re.sub(r"\]\([^)]+\)", "]", line[2:])
            scored.append((score, clean))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:limit]]


def search_notes(topic: str, limit: int = 4) -> list[str]:
    """Ранжированный поиск по ВСЕМ заметкам памяти (memory_find.py)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import memory_find as mf
    except Exception:
        return []
    try:
        top = mf.search(topic, n=limit, paths_only=False, quiet=True)
    except Exception:
        return []
    out = []
    for _score, note, _matched, _key in top:
        desc = _one_liner(note.get("desc") or note.get("title") or "", 160)
        if not desc:
            continue
        out.append(f"[{note['date']} · {note['file']}] {desc}")
    return out


def _with_timeout(fn, secs, default):
    """Слой Second Brain (векторный путь LanceDB) умеет висеть минутами —
    измерено 2026-08-19. Бриф обязан вернуться в любом случае, поэтому
    считаем зависший слой пустым, а не ждём его."""
    import threading
    box = [default]

    def run():
        try:
            box[0] = fn()
        except Exception:
            box[0] = default

    th = threading.Thread(target=run, daemon=True)
    th.start()
    th.join(secs)
    return box[0]


# Таймаут 20 с срезал ПЕРВЫЙ за сессию вызов: холодная загрузка эмбеддера
# занимает 15-27 с, прогретый — 4 с. То есть слой Second Brain молча
# выпадал ровно тогда, когда бриф собирают в начале работы.
def search_brain(topic: str, limit: int = 8, timeout: float = 35.0) -> list[str]:
    return _with_timeout(lambda: _search_brain_inner(topic, limit), timeout, [])


def _search_brain_inner(topic: str, limit: int = 8) -> list[str]:
    """Second Brain hybrid search → one-liner distillates."""
    sys.path.insert(0, str(BRAIN_DIR))
    try:
        from brain_db import hybrid_search
    except Exception:
        return []

    query_vector = None
    try:
        from brain_embedder import embed_query
        query_vector = embed_query(topic)
    except Exception:
        pass  # FTS-only fallback

    try:
        results = hybrid_search(topic, query_vector=query_vector, limit=limit)
    except Exception:
        return []

    lines = []
    seen = set()
    for r in results:
        text = r.snippet.replace(">>>", "").replace("<<<", "") if r.snippet else r.text
        line = _one_liner(text)
        key = line[:60]
        if key in seen or len(line) < 25:
            continue
        seen.add(key)
        date = (r.date or "")[:10]
        tag = f"{r.source}{' ' + date if date else ''}"
        lines.append(f"[{tag}] {line}")
    return lines


def build_brief(topic: str, max_tokens: int = 600) -> str:
    note_lines = search_notes(topic)
    mem_lines = search_memory_md(topic)
    brain_lines = search_brain(topic)

    header = f"## KNOWN GOTCHAS: {topic}\n"
    footer = ("\n(из памяти прошлых сессий; применяй как собственный опыт, "
              "не цитируй источник)")
    if not note_lines and not mem_lines and not brain_lines:
        return header + "- (в памяти релевантного не найдено)\n"

    # заметки (точный ранжированный слой) → curated MEMORY.md → сырые чанки
    seen = set()
    candidates = []
    for line in note_lines + mem_lines + brain_lines:
        key = re.sub(r"[^\wа-яё]+", "", line.lower())[:70]
        if key in seen:
            continue
        seen.add(key)
        candidates.append(f"- {line}")

    out = [header]
    budget = max_tokens - _count_tokens(header) - _count_tokens(footer)
    for c in candidates:
        cost = _count_tokens(c) + 1
        if cost > budget:
            break
        out.append(c)
        budget -= cost
    out.append(footer)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="KNOWN GOTCHAS brief for worker prompts")
    ap.add_argument("topic", help="тема задачи, напр. 'hermes деплой'")
    ap.add_argument("--max-tokens", type=int, default=600)
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(build_brief(args.topic, max_tokens=args.max_tokens))


if __name__ == "__main__":
    main()
