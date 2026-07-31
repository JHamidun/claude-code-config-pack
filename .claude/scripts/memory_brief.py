"""
memory_brief.py — KNOWN GOTCHAS block for Fable-worker prompts.

Usage:
    python ~/.claude/scripts/memory_brief.py "<тема задачи>"
    python ~/.claude/scripts/memory_brief.py "hermes деплой" --max-tokens 600

Pulls relevant грабли/решения from two memory layers:
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
MEMORY_MD = (Path.home() / ".claude" / "projects" / "C--Users-youruser"
             / "memory" / "MEMORY.md")

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


def search_brain(topic: str, limit: int = 8) -> list[str]:
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
    mem_lines = search_memory_md(topic)
    brain_lines = search_brain(topic)

    header = f"## KNOWN GOTCHAS: {topic}\n"
    footer = ("\n(из памяти прошлых сессий; применяй как собственный опыт, "
              "не цитируй источник)")
    if not mem_lines and not brain_lines:
        return header + "- (в памяти релевантного не найдено)\n"

    # curated MEMORY.md first (distilled, high trust), then brain chunks
    candidates = [f"- {l}" for l in mem_lines] + [f"- {l}" for l in brain_lines]

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
