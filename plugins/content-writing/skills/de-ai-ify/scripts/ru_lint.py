#!/usr/bin/env python3
"""Local lint for Russian text: chatbot traces plus structure and punctuation signals.

Offline and read-only: no network, files are only read. Prints
`path:line: LEVEL rule - description`; the text of chatbot traces is never printed
(a match can sit inside a URL that carries a token).

Profiles:
  user  (default) the owner's voice. Dashes are allowed. Only chatbot copy-paste
          traces are errors; every other signal is a warning: one hit is not proof,
          a cluster is (see SKILL.md, "Не переусердствуй").
  strict  adds the hard bans of the source linter as errors: any long or medium
          dash, math signs, negative parallelism, chopped drama, a `---` rule in
          the body. Only on request: on the owner's own replies it fails most texts.

Usage:
    python ru_lint.py FILE [FILE ...] [--profile user|strict] [-v]
    python ru_lint.py -                 # text from stdin
Exit codes: 0 no errors (warnings are fine), 1 errors found, 2 unreadable input.
-v also prints NOTE lines: weak signals that are normal in the owner's voice.

Thresholds of the positional checks follow references/structure-level.md ("Как
посчитать без модели"); the shapes come from the lint of snjrusmn/jev-humanizer@1ec645f
(MIT), see ../references/ORIGIN.md. Chatbot traces are delegated to artifact_scan.py.
"""
import argparse
import os
import re
import sys
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import artifact_scan  # noqa: E402  (same folder)

PROFILES = ("user", "strict")
Finding = namedtuple("Finding", "level line rule detail")

URL = re.compile(r"https?://\S+")
NOT_PROSE = re.compile(r"^\s*(#|\||[-*+]\s|\d+[.)]\s|>)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
HR_LINE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
BOLD_SPAN = re.compile(r"\*\*[^*\n]+\*\*")
QUOTED = re.compile(r"«[^»\n]*»|“[^”\n]*”|„[^“”\n]*[“”]|\"[^\"\n]*\"")
DASH_ANY = re.compile(r"[—–]|(?<=\s)-(?=\s)")
DASH_LONG = re.compile(r"[—–]")
MATH_SIGNS = re.compile(r"[≈≥≤≠±⇒←→]|\s[=><&+]\s|\d\+(?!\d)|\bvs\.?\b")
# Negative parallelism: a full contrast figure, not any "не только". The second member
# must exist and be non-empty, otherwise it is a cut-off clause and not the pattern.
NEG_PARALLEL = re.compile(
    r"[Нн]е только\b[^.!?\n]{1,80}?\b(?:но|а)\s+\S"
    r"|[Нн]е просто (?!так\b)[^.!?\n]{1,80}?(?:,\s*(?:а|но)\s+\S|(?:,|--?|—|–)\s*это\s+\S)"
    r"|[Нн]е просто (?!так\b)[^.!?\n]{1,40}[.!?]\s+Это\s+\S"
    r"|[Рр]ечь идёт не только"
    r"|[Нн]ет [^,.!?\n]{1,40}, нет "
    r"|[Дд]ело не в [^.!?\n]{1,50}, (?:а\s+в\b|дело в\b)"
    r"|[Вв]опрос не в том[^.!?\n]{1,60}, а в том"
    r"|\b[Ээ]то не [^.!?\n]{1,50}, это\s+\S")
CHOPPED_DRAMA = re.compile(r"(?:Без|Ноль) [^.!?\n]{1,35}[.!] (?:Без|Ноль) ")
# Heuristic verb stems by suffix; no morphology. A signal only: repeating the same
# verb for different subjects is the pattern, repeating it for rhythm is not.
VERB_SUFFIX = re.compile(r"(ует|яет|ает|еет|ит|ат|ят|ют|ал|ял|ил|ел|ся|сь|ть)$")
MIN_WORDS_FOR_VERB_REPEAT = 6   # shorter pairs are anaphora: «Звонил. Звонил каждый день.»


def _words(s):
    return len(s.split())


def _prose(lines):
    """[(first_line_no, text)] paragraphs of prose: headings, tables, lists, quotes excluded."""
    paras, cur, start = [], [], 0
    for no, line in lines:
        if not line.strip() or NOT_PROSE.match(line):
            if cur:
                paras.append((start, " ".join(cur)))
                cur = []
            continue
        if not cur:
            start = no
        cur.append(line.strip())
    if cur:
        paras.append((start, " ".join(cur)))
    return paras


def _sentences(paragraphs):
    """[(line_no, sentence)] over all prose paragraphs; line_no = start of the paragraph."""
    out = []
    for no, para in paragraphs:
        para = re.sub(r"\*\*|«|»", "", para)
        out.extend((no, s.strip()) for s in re.split(r"(?<=[.!?…])\s+", para) if s.strip())
    return out


def verb_stems(sentence):
    stems = set()
    for w in re.findall(r"[а-яё]{5,}", sentence.lower()):
        if VERB_SUFFIX.search(w):
            stems.add(VERB_SUFFIX.sub("", w)[:6])
    return {s for s in stems if len(s) >= 4}


def _front_matter_end(lines):
    """Number of the last line of a leading `---` block, or 0."""
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 40)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def _excerpt(s, n=50):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1] + "…"


def lint(text, profile="user"):
    """Return a list of Finding(level, line, rule, detail); line 0 = whole text.

    level: ERROR (gate), WARN (cluster signal), NOTE (weak, normal in the owner's voice).
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; use one of: {', '.join(PROFILES)}")
    strict = profile == "strict"
    if text.startswith(""):
        text = text[1:]
    out = []

    # 1. chatbot traces and invisible characters: delegated, never echoed
    for no, kind, count in artifact_scan.scan_text(text):
        times = f" x{count}" if count > 1 else ""
        level = "WARN" if kind == "zero-width" else "ERROR"   # CMS and mailers add zero-width
        out.append(Finding(level, no, kind, artifact_scan.TITLES[kind] + times))

    raw_lines = artifact_scan._split_lines(text)
    fm_end = _front_matter_end(raw_lines)
    masked = []
    for no, line in artifact_scan._mask_code(raw_lines):
        masked.append((no, "" if no <= fm_end else URL.sub(" ", line)))

    # 2. per line: punctuation and figures
    for no, line in masked:
        if not line.strip():
            continue
        scan = re.sub(r"^\s*[>+*]\s", "  ", line)       # markdown markers are not prose signs
        in_voice = QUOTED.sub(" ", scan)                  # quoted text is someone else's voice
        if strict and HR_LINE.match(line):
            out.append(Finding("ERROR", no, "hr-in-body", "строка-разделитель в теле"))
            continue
        for rule, rx, title in (("negative-parallelism", NEG_PARALLEL, "негативный параллелизм"),
                                ("chopped-drama", CHOPPED_DRAMA, "рубленый драматизм")):
            for m in rx.finditer(in_voice):
                out.append(Finding("ERROR" if strict else "WARN", no, rule,
                                   f"{title}: «{_excerpt(m.group(0), 40)}»"))
        if strict:
            for m in DASH_LONG.finditer(in_voice):
                out.append(Finding("ERROR", no, "dash", "длинное или среднее тире"))
            for m in MATH_SIGNS.finditer(in_voice):
                out.append(Finding("ERROR", no, "math-sign", "математический знак в прозе"))

    paragraphs = _prose(masked)
    plain = [(no, re.sub(r"\*\*", "", p)) for no, p in paragraphs]

    # 3. dashes in the owner's voice: a weak signal only (NOTE, shown with -v)
    if not strict:
        for no, para in plain:
            n = len(DASH_ANY.findall(QUOTED.sub(" ", para)))
            if n >= 3:
                out.append(Finding("NOTE", no, "dash-density",
                                   f"{n} тире в одном абзаце: смотри, если так густо везде"))

    # 4. sentence level
    sents = _sentences(paragraphs)
    lengths = [_words(s) for _, s in sents]
    for (no_a, a), (no_b, b) in zip(sents, sents[1:]):
        if _words(a) < MIN_WORDS_FOR_VERB_REPEAT or _words(b) < MIN_WORDS_FOR_VERB_REPEAT:
            continue
        common = verb_stems(a) & verb_stems(b)
        if common:
            out.append(Finding("WARN", no_b, "verb-repeat",
                               f"основа «{sorted(common)[0]}…» в соседних предложениях"))
    if len(lengths) >= 8:
        diffs = [abs(x - y) for x, y in zip(lengths, lengths[1:])]
        mean_diff = sum(diffs) / len(diffs)
        if all(15 <= n <= 22 for n in lengths) or mean_diff < 4:
            out.append(Finding("WARN", 0, "even-rhythm",
                               f"ровный ритм: средняя разница соседних предложений {mean_diff:.1f} слова"))
    if len(lengths) >= 10 and not any(n < 8 for n in lengths):
        out.append(Finding("WARN", 0, "no-short-sentences", "ни одного предложения короче 8 слов"))

    # 5. paragraph and list level
    plens = [_words(p) for _, p in plain if _words(p) >= 5]
    if len(plens) >= 5:
        mean = sum(plens) / len(plens)
        cv = (sum((x - mean) ** 2 for x in plens) / len(plens)) ** 0.5 / mean
        if cv < 0.25:
            out.append(Finding("WARN", 0, "uniform-paragraphs",
                               f"абзацы под копирку: разброс длин {cv:.0%} от средней"))
    sizes, size = [], 0
    for _, line in masked:
        if LIST_ITEM.match(line):
            size += 1
        else:
            if size:
                sizes.append(size)
            size = 0
    if size:
        sizes.append(size)
    if len(sizes) >= 2 and all(n == 3 for n in sizes):
        out.append(Finding("WARN", 0, "lists-of-three", f"{len(sizes)} списка, все ровно из трёх пунктов"))
    for no, para in paragraphs:
        n = len(BOLD_SPAN.findall(para))
        if n > 2:
            out.append(Finding("WARN", no, "bold-overuse", f"{n} жирных выделений в одном абзаце"))

    return sorted(out, key=lambda f: (f.line, f.rule))


def has_errors(findings):
    return any(f.level == "ERROR" for f in findings)


def format_finding(name, f):
    where = f"{name}:{f.line}:" if f.line else f"{name}:"
    return f"{where} {f.level} {f.rule} - {f.detail}"


def _read(path):
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Local lint for Russian text (offline, read-only).")
    ap.add_argument("files", nargs="+", help="files to check, or - for stdin")
    ap.add_argument("--profile", choices=PROFILES, default="user")
    ap.add_argument("-v", "--verbose", action="store_true", help="also print NOTE lines")
    a = ap.parse_args(argv)

    status, errors, warns = 0, 0, 0
    for path in a.files:
        name = "<stdin>" if path == "-" else path
        if path != "-" and os.path.isdir(path):
            print(f"{name}: это папка, передай файлы", file=sys.stderr)
            status = 2
            continue
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError) as exc:
            hint = " (файл не в UTF-8?)" if isinstance(exc, UnicodeDecodeError) else ""
            print(f"{name}: не прочитан, {type(exc).__name__}{hint}", file=sys.stderr)
            status = 2
            continue
        for f in lint(text, a.profile):
            if f.level == "NOTE" and not a.verbose:
                continue
            print(format_finding(name, f))
            errors += f.level == "ERROR"
            warns += f.level == "WARN"
    sys.stdout.flush()
    print(f"ru_lint: профиль {a.profile}; ошибок {errors}, предупреждений {warns}, файлов {len(a.files)}",
          file=sys.stderr)
    if status == 2:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
