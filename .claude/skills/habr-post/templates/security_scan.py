#!/usr/bin/env python3
"""Security scan for habr-post pipeline - catches personal data leaks before publication.

Built-in patterns (generic, work out of the box for anyone):
- Telegram numeric IDs (9-11 digit numbers, with year-whitelist)
- Bot handles (@something_bot or @somethingBot)
- CPF (Brazilian tax ID)
- Phone numbers (E.164 fragments)
- Emails (any; put your public ones in the whitelist)
- Private IPv4 ranges (10.x, 172.16-31.x, 192.168.x)
- Home directory paths (C:/Users/<user>, /home/<user>, /Users/<user>)
- API tokens and keys (sk-, ghp_, AIza, xox[bap]-, Bearer, PRIVATE KEY)

Site-specific things - YOUR public email and handles, YOUR server IP, YOUR
production paths - do not belong in this file: it ships with the skill and is
shared. Put them in patterns.local.json next to this script (see
patterns.local.example.json).

Usage:
    python security_scan.py FINAL.md
    # Exit 0 = clean, exit 1 = leaks found

    python security_scan.py FINAL.md --json    # JSON output for pipeline
    python security_scan.py FINAL.md --patterns /path/to/patterns.local.json
    python security_scan.py FINAL.md --whitelist whitelist.txt
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Force UTF-8 on Windows consoles (cp1251 chokes on arrows etc.)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Emails / handles you intentionally publish. Empty on purpose: which addresses are
# "public" differs per author, and a shipped default would either leak someone's
# address or silently un-flag yours. Fill patterns.local.json instead.
DEFAULT_PUBLIC_WHITELIST: set = set()

# Where the local (personal) config is looked up, in order. First hit wins.
LOCAL_CONFIG_CANDIDATES = [
    Path(__file__).with_name("patterns.local.json"),
    Path.home() / ".claude" / "habr-patterns.local.json",
]

PATTERNS = [
    # name, regex, severity, hint
    ("tg_numeric_id", r"\b\d{9,11}\b", "high",
     "Похоже на Telegram numeric user_id. Замените на placeholder."),
    ("bot_handle", r"@[A-Za-z][A-Za-z0-9_]*[Bb]ot\b", "high",
     "Telegram bot handle. Замените на @<your_bot> или удалите."),
    ("cpf", r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "critical",
     "CPF (Brazilian tax ID). Удалить."),
    ("phone_e164", r"\+\d{1,3}\s?\(?\d{2,4}\)?\s?\d{3}-?\d{2}-?\d{2}", "critical",
     "Phone number. Удалить или обобщить."),
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "medium",
     "Email address. Проверьте whitelist."),
    ("private_ipv4",
     r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
     r"|192\.168\.\d{1,3}\.\d{1,3})\b", "medium",
     "Private/internal IP. Замените на <server_ip> или уберите."),
    ("home_path_win", r"[A-Za-z]:[/\\]Users[/\\][^\s\)\]/\\]+[/\\][^\s\)\]]*", "medium",
     "Абсолютный путь с именем пользователя. Замените на относительный или ~/."),
    ("home_path_nix", r"/(?:home|Users)/[^\s\)\]/]+/[^\s\)\]]*", "medium",
     "Абсолютный путь с именем пользователя. Замените на относительный или ~/."),
    ("api_token",
     r"(?:sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{20,}"
     r"|xox[bapr]-[A-Za-z0-9\-]{10,}|Bearer\s+[A-Za-z0-9._\-]{20,}"
     r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)", "critical",
     "Похоже на живой ключ или токен. Убрать и отозвать."),
]

# Site-specific regexes (your server IP, your production paths, your internal
# hostnames) live outside this file. Format of patterns.local.json:
#   {"public_whitelist": ["me@example.com", "@my_bot"],
#    "extra_patterns": [
#       {"name": "my_server_ip", "regex": "\\b203\\.0\\.113\\.\\d{1,3}\\b",
#        "severity": "high", "hint": "Server IP. Replace with <server_ip>."}]}


def load_local_config(explicit):
    """Returns (whitelist_entries, extra_patterns). A missing file is not an error."""
    path = explicit
    if path is None:
        path = next((p for p in LOCAL_CONFIG_CANDIDATES if p.exists()), None)
    if path is None or not Path(path).exists():
        return set(), []
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # Loud, not silent: a broken personal config means the scan is weaker than
        # the author thinks, and that is exactly how a leak gets through.
        print(f"WARNING: cannot read {path}: {exc}", file=sys.stderr)
        return set(), []
    wl = set(data.get("public_whitelist", []))
    extra = []
    for p in data.get("extra_patterns", []):
        try:
            re.compile(p["regex"])
        except (re.error, KeyError, TypeError) as exc:
            print(f"WARNING: bad pattern in {path}: {exc}", file=sys.stderr)
            continue
        extra.append((p["name"], p["regex"],
                      p.get("severity", "medium"),
                      p.get("hint", "Site-specific pattern from patterns.local.json.")))
    return wl, extra

# Year-like 4-digit substring inside numeric_id should not flag (1900–2100)
YEAR_RE = re.compile(r"\b(19[0-9]{2}|20[0-9]{2}|21[0-9]{2})\b")


def is_year(token: str) -> bool:
    return bool(YEAR_RE.fullmatch(token))


def scan_text(text: str, whitelist: set, extra_patterns=()) -> List[Tuple[int, str, str, str, str]]:
    """Returns list of (line_number, name, match, severity, hint)."""
    patterns = list(PATTERNS) + list(extra_patterns)
    findings = []
    lines = text.splitlines()

    # Build a set of code-block line ranges to optionally skip strict-pattern matches
    in_code = False
    code_lines = set()
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            code_lines.add(idx)
            continue
        if in_code:
            code_lines.add(idx)

    for idx, line in enumerate(lines, 1):
        for name, pattern, severity, hint in patterns:
            for m in re.finditer(pattern, line):
                token = m.group(0)
                # Skip year-like 4-digit numbers when matched as tg_numeric_id
                if name == "tg_numeric_id" and len(token) == 4 and is_year(token):
                    continue
                # Skip 9-digit numbers like phone-without-prefix only inside known code contexts
                # (heuristic: if line contains 'port' or 'redis' near the number, skip)
                if name == "tg_numeric_id" and idx in code_lines:
                    if any(kw in line.lower() for kw in (
                            "port", "redis", "uid", "size", "bytes", "lines",
                            "rows", "stars", "version", "timestamp")):
                        continue
                # Whitelist emails
                if name == "email" and token.lower() in {w.lower() for w in whitelist}:
                    continue
                # Whitelist bot handles (e.g. official public ones)
                if name == "bot_handle" and token in whitelist:
                    continue
                findings.append((idx, name, token, severity, hint))
    return findings


def main():
    parser = argparse.ArgumentParser(description="Security scan for FINAL.md")
    parser.add_argument("file", type=Path, help="Markdown file to scan")
    parser.add_argument("--whitelist", type=Path,
                        help="File with one whitelist entry per line")
    parser.add_argument("--patterns", type=Path,
                        help="patterns.local.json with your public whitelist and "
                             "site-specific regexes (default: alongside this script, "
                             "then ~/.claude/habr-patterns.local.json)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--write-report", type=Path,
                        help="Write SECURITY-SCAN.md report")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    local_whitelist, extra_patterns = load_local_config(args.patterns)
    whitelist = set(DEFAULT_PUBLIC_WHITELIST) | local_whitelist
    if args.whitelist and args.whitelist.exists():
        for ln in args.whitelist.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                whitelist.add(ln)

    text = args.file.read_text(encoding="utf-8")
    findings = scan_text(text, whitelist, extra_patterns)

    if args.json:
        print(json.dumps([
            {"line": i, "name": n, "match": m, "severity": s, "hint": h}
            for i, n, m, s, h in findings
        ], ensure_ascii=False, indent=2))
    else:
        if not findings:
            print(f"PASS: 0 leaks found in {args.file.name}")
        else:
            print(f"BLOCK: {len(findings)} potential leaks in {args.file.name}")
            for i, n, m, s, h in findings:
                print(f"  [{s.upper():8}] line {i:4d}  {n:18s}  {m!r}")
                print(f"             → {h}")

    if args.write_report:
        report = ["# Security scan report", "",
                  f"**File:** `{args.file.name}`",
                  f"**Findings:** {len(findings)}",
                  ""]
        if not findings:
            report.append("**Verdict:** ✅ PASS — no leaks detected.")
        else:
            report.append("**Verdict:** 🛑 BLOCK — fix before publication.")
            report.append("")
            report.append("| Line | Pattern | Match | Severity | Hint |")
            report.append("|------|---------|-------|----------|------|")
            for i, n, m, s, h in findings:
                escaped = m.replace("|", "\\|")
                report.append(f"| {i} | {n} | `{escaped}` | {s} | {h} |")
        args.write_report.write_text("\n".join(report) + "\n", encoding="utf-8")
        print(f"Report written: {args.write_report}")

    sys.exit(0 if not findings else 1)


if __name__ == "__main__":
    main()
