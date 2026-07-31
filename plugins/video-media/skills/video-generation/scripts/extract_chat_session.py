"""Generalized JSONL session extractor — mine past Claude Code chats for skill enrichment.

Streams a Claude Code session JSONL file (≈100 MB-class) and classifies each
message into one or more topics via regex. Writes per-topic chunked Markdown
files (≤400 KB each) ready to feed to parallel subagent workflows.

Originally built to mine Terra + Chronicles-of-Amber + ConferenceX sessions for the
unified video skill. Generic enough to reuse for any future "extract knowledge
from a giant past chat" task.

CLI:
    # Default: use built-in video-pipeline topic regex
    python extract_chat_session.py <session.jsonl> --out extracts/

    # Custom topics from JSON file
    python extract_chat_session.py <session.jsonl> --out extracts/ --topics my_topics.json

my_topics.json schema:
    {
      "myproject": "regex pattern (case-insensitive)",
      "deploy": "deploy|kubectl|helm",
      ...
    }
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Default topic regex for video-pipeline mining
DEFAULT_TOPICS = {
    "amber":     r"хроник|амбер|amber|гоствел",
    "terra":     r"\bterra\b|терр[аеуы]\b|company\.?дет|sample author|sample author",
    "runway":    r"runway|RW_TOKEN_PLACEHOLDER|RunwayClient|your-team-slug",
    "seedance":  r"seedance|seedance_2|moderation_category|CHARACTER",
    "veo":       r"\bveo\b|veo-3|veo_3",
    "kling_gen4":r"kling|gen-?4|gen_4_5",
    "audio":     r"elevenlabs|lyria|саундтрек|музык|закадр|voiceover|tts",
    "ffmpeg":    r"ffmpeg|acrossfade|sidechain|amix|concat|overlay",
    "yandex":    r"yadi\.sk|яндекс\.?диск|yandex.disk",
    "pipeline":  r"пайплайн|pipeline|раскадров|storyboard|keyframe|шаг \d|step \d",
    "gotcha":    r"грабл|gotcha|подвох|ошибк|не работа|fail|safety|reject|400|401|403|429|500",
}

NOISE_PATTERNS = re.compile(
    r"(<system-reminder>|tool_use_id|input_tokens|cache_creation|cache_read|"
    r"usage.+input_tokens)",
    re.I,
)


def extract_text(message: dict) -> str:
    """Pull readable text from message: text parts + tool_use input + tool_result."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for c in content:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "text":
            parts.append(c.get("text", ""))
        elif c.get("type") == "tool_use":
            name = c.get("name", "?")
            inp = c.get("input", {})
            if isinstance(inp, dict):
                if "command" in inp:
                    parts.append(f"[TOOL {name}] $ {inp.get('command','')[:1200]}")
                elif "file_path" in inp:
                    cnt = (inp.get("content") or inp.get("new_string") or "")[:800]
                    parts.append(f"[TOOL {name}] -> {inp['file_path']}\n{cnt}")
                elif "prompt" in inp:
                    parts.append(f"[TOOL {name}] prompt: {inp.get('prompt','')[:1500]}")
                elif "url" in inp:
                    parts.append(f"[TOOL {name}] url: {inp['url']}")
                else:
                    parts.append(f"[TOOL {name}] {json.dumps(inp, ensure_ascii=False)[:600]}")
        elif c.get("type") == "tool_result":
            r = c.get("content", "")
            if isinstance(r, list):
                r = " ".join(
                    (rr.get("text", "") if isinstance(rr, dict) else str(rr))
                    for rr in r
                )
            if r:
                parts.append(f"[TOOL_RESULT] {str(r)[:600]}")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_jsonl", help="Path to session JSONL file")
    ap.add_argument("--out", default="extracts", help="Output directory")
    ap.add_argument("--topics", default=None,
                    help="JSON file with custom topic regex mapping (overrides defaults)")
    ap.add_argument("--chunk-limit", type=int, default=400_000,
                    help="Max bytes per output chunk (default 400 KB)")
    ap.add_argument("--min-message-length", type=int, default=30,
                    help="Skip messages shorter than this (chars)")
    args = ap.parse_args()

    if args.topics:
        topic_map = json.loads(Path(args.topics).read_text(encoding="utf-8"))
    else:
        topic_map = DEFAULT_TOPICS

    topics = {name: re.compile(pat, re.I) for name, pat in topic_map.items()}

    session = Path(args.session_jsonl)
    if not session.exists():
        print(f"FATAL: {session} not found")
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    buckets: dict[str, list[str]] = {t: [] for t in topics}
    stats = {"total": 0, "kept": 0, "noise": 0,
             "by_topic": {t: 0 for t in topics}}

    print(f"[..] streaming {session.stat().st_size//1_048_576} MB JSONL")
    with session.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            stats["total"] += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("type") not in ("user", "assistant"):
                continue
            msg = rec.get("message", {})
            if not isinstance(msg, dict):
                continue

            text = extract_text(msg)
            if not text or len(text) < args.min_message_length:
                continue
            if NOISE_PATTERNS.search(text):
                stats["noise"] += 1
                continue

            matched = [t for t, rx in topics.items() if rx.search(text)]
            if not matched:
                continue

            ts = rec.get("timestamp", "")
            role = rec.get("type", "?")
            block = (f"\n--- [{i}] {role} | {ts} | "
                     f"topics: {','.join(matched)} ---\n{text}\n")

            for t in matched:
                buckets[t].append(block)
                stats["by_topic"][t] += 1
            stats["kept"] += 1

    # Write topic buckets in chunks
    for topic, blocks in buckets.items():
        if not blocks:
            continue
        chunk_idx = 0
        buf: list[str] = []
        buf_size = 0

        def flush(idx: int, buf: list[str]) -> None:
            if not buf:
                return
            out = out_dir / f"{topic}_{idx:02d}.md"
            out.write_text("".join(buf), encoding="utf-8")
            print(f"  {out.name}: {out.stat().st_size//1024} KB ({len(buf)} blocks)")

        for b in blocks:
            if buf_size + len(b) > args.chunk_limit and buf:
                flush(chunk_idx, buf)
                chunk_idx += 1
                buf = []
                buf_size = 0
            buf.append(b)
            buf_size += len(b)
        flush(chunk_idx, buf)

    print("\n=== STATS ===")
    print(f"Total records:  {stats['total']}")
    print(f"Kept messages:  {stats['kept']}")
    print(f"Noise skipped:  {stats['noise']}")
    for t, n in stats["by_topic"].items():
        if n:
            print(f"  {t:12s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
