#!/usr/bin/env python3
"""Mechanical acceptance of an edit: what must survive a cleanup of a text.

Compares the original with the edited text and rejects the edit when it
  - lost, added or changed a number, a {PLACEHOLDER}, a link or a quotation (two words or more),
  - changed the HTML tags or their order,
  - is shorter than 60% or longer than 105% of the original (--micro drops the lower bound:
    buttons, pushes, SMS and tooltips are meant to get shorter),
  - brought in a cliché that the original did not have, or still has an ERROR of the ru_lint
    profile (chatbot traces; in strict also dashes and the other hard bans).
Clichés that were already in the original and stayed are only reported (NOTE); --no-leftovers
turns them into a rejection. An edit that changed nothing is accepted: for a clean text that is
the right answer; --require-change rejects it.

The check does not judge the style of the new text, only what an edit must never break.

Usage:
    python accept.py OLD NEW [--profile user|strict] [--micro] [--no-leftovers] [--require-change]
    (OLD or NEW may be - for stdin, not both)
Exit codes: 0 accepted, 1 rejected (reasons printed, never the text itself), 2 unreadable input.

Acceptance rules follow the owner's earlier cleanup pipeline (numbers, placeholders, tags, length)
and SKILL.md ("Не короче 60% оригинала", "всё внутри кавычек не трогать").
"""
import argparse
import html
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import artifact_scan  # noqa: E402  (same folder)
import ru_lint  # noqa: E402

MIN_RATIO, MAX_RATIO = 0.60, 1.05
URL = re.compile(r"https?://[^\s<>\"')\]]+")
TAG = re.compile(r"<[^>]+>")
PLACEHOLDER = re.compile(r"\{\{?[A-Za-z_][\w.\-]{0,39}\}?\}|%\([A-Za-z_]\w*\)s|<<[^<>\n]{1,40}>>")
NUMBER = re.compile(r"\d+(?:[   ]\d{3})*(?:[.,]\d+)?")
QUOTED = re.compile(r"«([^»\n]+)»|“([^”\n]+)”|\"([^\"\n]+)\"")

# Clichés and signposting from the table in SKILL.md; each is a stem or phrase, case-insensitive.
CLICHES = [
    r"\bявляется\b", r"\bосуществля\w+", r"\bпредставляет собой\b", r"\bв рамках\b",
    r"\bданн(?:ый|ая|ое|ого|ому|ым|ой|ую)\b", r"\bв современном мире\b",
    r"\bна сегодняшний день\b", r"\bважно отметить\b", r"\bстоит отметить\b",
    r"\bдавайте (?:разберёмся|разберемся|начистоту|признаем|погрузимся)\b",
    r"\bбесшовн\w+", r"\bкомплексный подход\b",
]
CLICHE_RX = [re.compile(p, re.IGNORECASE) for p in CLICHES]


def plain(s):
    """Text without tags, entities decoded, whitespace folded."""
    return " ".join(html.unescape(TAG.sub(" ", s)).split())


def _numbers(s):
    s = plain(s)
    for _, _, rx in artifact_scan.TEXT_KINDS:   # digits inside a chatbot trace are not numbers
        s = rx.sub(" ", s)
    s = URL.sub(" ", s)
    return Counter(re.sub(r"[   ]", "", m).replace(",", ".") for m in NUMBER.findall(s))


def _urls(s):
    return Counter(u.rstrip(".,;:!?)") for u in URL.findall(html.unescape(s)))


def _quotes(s):
    spans = []
    for m in QUOTED.finditer(plain(s)):
        body = next(g for g in m.groups() if g)
        if len(body.split()) >= 2:
            spans.append(body)
    return spans


def _cliches(s):
    text = QUOTED.sub(" ", plain(s))
    return {rx.pattern for rx in CLICHE_RX if rx.search(text)}


def _diff(a, b):
    """(lost, added) counts between two Counters."""
    return sum((a - b).values()), sum((b - a).values())


def check(old, new, profile="user", min_ratio=MIN_RATIO, max_ratio=MAX_RATIO,
          no_leftovers=False, require_change=False):
    """Return (reasons, notes). No reasons = accepted."""
    reasons, notes = [], []
    if not plain(old):
        return ["исходный текст пуст"], notes
    if not plain(new):
        return ["правка пуста"], notes

    lost, added = _diff(_numbers(old), _numbers(new))
    if lost or added:
        reasons.append(f"числа разошлись (пропало {lost}, добавилось {added})")
    lost, added = _diff(Counter(PLACEHOLDER.findall(old)), Counter(PLACEHOLDER.findall(new)))
    if lost or added:
        reasons.append(f"плейсхолдеры разошлись (пропало {lost}, добавилось {added})")
    if TAG.findall(old) != TAG.findall(new):
        reasons.append("html-теги изменились или идут в другом порядке")
    lost, added = _diff(_urls(old), _urls(new))
    if lost or added:
        reasons.append(f"ссылки разошлись (пропало {lost}, добавилось {added})")
    new_plain = plain(new)
    broken = sum(1 for q in _quotes(old) if q not in new_plain)
    if broken:
        reasons.append(f"цитаты изменены или пропали: {broken}")

    ratio = len(plain(new)) / len(plain(old))
    if ratio > max_ratio:
        reasons.append(f"длина {ratio:.0%} от исходной, предел {max_ratio:.0%}")
    if ratio < min_ratio:
        reasons.append(f"длина {ratio:.0%} от исходной, нижний предел {min_ratio:.0%}")

    old_c, new_c = _cliches(old), _cliches(new)
    if new_c - old_c:
        reasons.append(f"добавлены штампы: {len(new_c - old_c)}")
    if new_c & old_c:
        (reasons if no_leftovers else notes).append(f"остались штампы из исходника: {len(new_c & old_c)}")
    errors = sorted({f.rule for f in ru_lint.lint(new, profile) if f.level == "ERROR"})
    if errors:   # a cleanup has to remove these, so they count even if the original had them
        reasons.append("ошибки линтера в правке: " + ", ".join(errors))
    if plain(old) == plain(new):
        (reasons if require_change else notes).append("без изменений")
    return reasons, notes


def _read(path):
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mechanical acceptance of an edit.")
    ap.add_argument("old", help="original file, or - for stdin")
    ap.add_argument("new", help="edited file, or - for stdin")
    ap.add_argument("--profile", choices=ru_lint.PROFILES, default="user")
    ap.add_argument("--micro", action="store_true", help="microcopy: no lower bound on length")
    ap.add_argument("--no-leftovers", action="store_true", help="reject clichés that stayed from the original")
    ap.add_argument("--require-change", action="store_true", help="reject an edit that changed nothing")
    a = ap.parse_args(argv)
    if a.old == "-" and a.new == "-":
        print("accept: stdin можно передать только один раз", file=sys.stderr)
        return 2
    texts = []
    for path in (a.old, a.new):
        try:
            texts.append(_read(path))
        except (OSError, UnicodeDecodeError) as exc:
            name = "<stdin>" if path == "-" else path
            print(f"{name}: не прочитан, {type(exc).__name__}", file=sys.stderr)
            return 2
    reasons, notes = check(texts[0], texts[1], a.profile, 0.0 if a.micro else MIN_RATIO, MAX_RATIO,
                           a.no_leftovers, a.require_change)
    for n in notes:
        print(f"NOTE {n}")
    for r in reasons:
        print(f"REJECT {r}")
    print("accept: " + ("отклонено" if reasons else "принято"), file=sys.stderr)
    return 1 if reasons else 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
