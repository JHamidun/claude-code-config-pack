#!/usr/bin/env python3
"""Find chatbot copy-paste traces in text files.

Looks for chatbot citation markers (oaicite, turn0search...), chatbot utm tags
in links, think-tag remnants, unreplaced placeholders and invisible characters.

Read-only. Prints `path:line: kind - description` and never the matched text:
a match can sit inside a URL that carries a token, or next to a pasted secret.

Usage:
    python artifact_scan.py FILE [FILE ...]
    python artifact_scan.py -              # text from stdin
Exit codes: 0 nothing found, 1 traces found, 2 a file could not be read.

Pattern shapes follow the copy-paste registry of humanizer-ru as vendored in
snjrusmn/jev-humanizer@1ec645f (MIT); see ../references/ORIGIN.md.
"""
import os
import re
import sys

# Text traces. Skipped inside inline code and fenced blocks: an artifact
# wrapped in backticks is being quoted on purpose, not leaked by copy-paste.
TEXT_KINDS = [
    ("oaicite", "сноска ChatGPT",
     re.compile(r":contentReference\[oaicite:\d+\]|oai_citation:\d+‡|\boaicite:\d+")),
    ("turn-marker", "метка поиска ChatGPT",
     re.compile(r"\bturn\d+[a-z]+\d+|citeturn")),
    ("chatbot-utm", "метка чат-бота в ссылке",
     re.compile(r"utm_source=(?:chatgpt\.com|copilot\.com|openai)\b|referrer=grok\.com")),
    ("grok-card", "разметка карточки Grok",
     re.compile(r"grok_card://|grok_render_citation_card_json|<grok-card\b")),
    ("gemini-cite", "разметка цитаты Gemini",
     re.compile(r"vertexaisearch\S*grounding-api-redirect|\[cite_start\]|\[cite:\s*\d+|\[span_\d+\]")),
    ("internal-footnote", "внутренняя сноска чат-бота",
     re.compile(r"【\d+†[^】\n]*】|\]\(sandbox:/mnt/data/")),
    ("think-tag", "остаток рассуждений модели",
     re.compile(r"</?think(?:ing)?>")),
    ("perplexity-upload", "ссылка на загрузку файла в Perplexity",
     re.compile(r"ppl-ai-file-upload")),
    ("placeholder", "незаменённая заглушка",
     re.compile(r"INSERT_SOURCE_URL|PASTE_\w+_URL_HERE|\bURL_HERE\b|\b20\d\d-XX-XX\b"
                r"|\[(?:ваш[аеи]?|вставьте|укажите|опишите|добавьте|введите|имя|название|дата)\b"
                r"[^\]\n]{0,60}\](?!\()",
                re.IGNORECASE)),
]

# Invisible characters. Checked everywhere, code included: nobody quotes an
# invisible character on purpose, and inside code it breaks the code.
# A zero width joiner between two emoji glues a sequence (family, profession)
# and is normal; anywhere else it is junk.
EMOJI_CH = r"[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]"
INVISIBLE_KINDS = [
    ("zero-width", "невидимый символ нулевой ширины",
     re.compile(r"[⁠]|(?<!%s)|(?!%s)" % (EMOJI_CH, EMOJI_CH))),
    ("pua-marker", "служебный символ чат-бота из частной зоны Unicode",
     re.compile(r"[-]")),
]

TITLES = {kind: title for kind, title, _ in TEXT_KINDS + INVISIBLE_KINDS}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`\n]+`")


def _split_lines(text):
    # Split on line breaks only: str.splitlines() also breaks on U+2028 and
    # friends, which would shift line numbers against the editor.
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _mask_code(lines):
    """Yield (line_no, line) with fenced blocks and inline code blanked out."""
    fence = None
    for no, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            yield no, ""
            continue
        if m:
            fence = m.group(1)
            yield no, ""
            continue
        yield no, INLINE_CODE.sub(lambda c: " " * len(c.group(0)), line)


def scan_text(text):
    """Return findings as a sorted list of (line_no, kind, count)."""
    if text.startswith(""):  # a BOM at the very start is file encoding, not text
        text = text[1:]
    lines = _split_lines(text)
    hits = {}

    def add(no, kind, count):
        if count:
            hits[(no, kind)] = hits.get((no, kind), 0) + count

    for no, line in enumerate(lines, 1):
        for kind, _, rx in INVISIBLE_KINDS:
            add(no, kind, len(rx.findall(line)))
    for no, line in _mask_code(lines):
        if line:
            for kind, _, rx in TEXT_KINDS:
                add(no, kind, len(rx.findall(line)))
    return sorted((no, kind, count) for (no, kind), count in hits.items())


def _read(path):
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig")


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if args else 2

    status, total, files_with_hits = 0, 0, 0
    for path in args:
        name = "<stdin>" if path == "-" else path
        if path != "-" and os.path.isdir(path):
            print(f"{name}: это папка, передай файлы", file=sys.stderr)
            status = 2
            continue
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError) as exc:
            # Only the exception class: its message may quote bytes of the file.
            hint = " (файл не в UTF-8?)" if isinstance(exc, UnicodeDecodeError) else ""
            print(f"{name}: не прочитан, {type(exc).__name__}{hint}", file=sys.stderr)
            status = 2
            continue
        findings = scan_text(text)
        for no, kind, count in findings:
            times = f" x{count}" if count > 1 else ""
            print(f"{name}:{no}: {kind}{times} - {TITLES[kind]}")
        if findings:
            files_with_hits += 1
            total += len(findings)

    sys.stdout.flush()  # keep the summary after the findings when both streams share a file
    print(f"artifact_scan: находок {total}, файлов с находками {files_with_hits} из {len(args)}",
          file=sys.stderr)
    if status == 2:
        return 2
    return 1 if total else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
