#!/usr/bin/env python3
"""Changelog generator: git log -> Keep a Changelog markdown.

Part of the changelog-generator skill (~/.claude/skills/changelog-generator/).
Conventional Commits are grouped into Keep a Changelog sections;
breaking changes (feat!: / BREAKING CHANGE) get their own section.

Usage:
  python changelog.py --version 1.2.0                 # since last tag (or all history)
  python changelog.py --version 1.2.0 --since v1.1.0  # since a specific tag/ref
  python changelog.py --version 1.2.0 --repo path/to/repo
  python changelog.py --version 1.2.0 --dry-run       # preview with stats to stderr
  python changelog.py --version 1.2.0 >> CHANGELOG.md
"""

import argparse
import re
import subprocess
import sys
from datetime import date

SEP = "\x1f"  # unit separator: safe field delimiter (commit subjects may contain '|')
REC = "\x1e"  # record separator: commit bodies may contain newlines

TYPE_MAPPING = {
    "feat": "added",
    "fix": "fixed",
    "perf": "changed",
    "refactor": "changed",
    "security": "security",
    "deprecate": "deprecated",
    "remove": "removed",
}

SECTION_NAMES = [
    ("breaking", "### ⚠️ Breaking Changes"),
    ("added", "### Added"),
    ("changed", "### Changed"),
    ("deprecated", "### Deprecated"),
    ("removed", "### Removed"),
    ("fixed", "### Fixed"),
    ("security", "### Security"),
]


def run_git(args: list, repo: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo] + args, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def get_last_tag(repo: str) -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], repo).strip() or None
    except RuntimeError:
        return None  # no tags in repo


def get_commits(repo: str, since: str | None) -> list:
    rev_range = [f"{since}..HEAD"] if since else []
    fmt = f"%H{SEP}%s{SEP}%b{REC}"
    out = run_git(["log", *rev_range, f"--pretty=format:{fmt}", "--no-merges"], repo)
    commits = []
    for record in out.split(REC):
        record = record.strip("\n")
        if SEP not in record:
            continue
        parts = record.split(SEP, 2)
        commits.append(
            {
                "hash": parts[0][:7],
                "subject": parts[1].strip(),
                "body": parts[2] if len(parts) > 2 else "",
            }
        )
    return commits


def parse_conventional_commit(subject: str) -> dict:
    match = re.match(r"^(\w+)(\([\w./-]+\))?(!)?:\s*(.+)$", subject)
    if match:
        return {
            "type": match.group(1).lower(),
            "scope": match.group(2)[1:-1] if match.group(2) else None,
            "breaking": bool(match.group(3)),
            "description": match.group(4),
        }
    return {"type": "other", "scope": None, "breaking": False, "description": subject}


def categorize_commits(commits: list) -> dict:
    categories = {key: [] for key, _ in SECTION_NAMES}
    for commit in commits:
        parsed = parse_conventional_commit(commit["subject"])
        if parsed["breaking"] or "BREAKING CHANGE" in commit.get("body", ""):
            categories["breaking"].append(commit)
            continue
        category = TYPE_MAPPING.get(parsed["type"])
        if category:
            categories[category].append(commit)
    return categories


def generate_changelog(version: str, categories: dict, show_hash: bool = False) -> str:
    lines = [f"## [{version}] - {date.today().isoformat()}"]
    for key, title in SECTION_NAMES:
        if not categories.get(key):
            continue
        lines.append(f"\n{title}\n")
        for commit in categories[key]:
            parsed = parse_conventional_commit(commit["subject"])
            scope = f"**{parsed['scope']}**: " if parsed["scope"] else ""
            suffix = f" ({commit['hash']})" if show_hash else ""
            lines.append(f"- {scope}{parsed['description']}{suffix}")
    if len(lines) == 1:
        lines.append("\n_No user-facing changes (no conventional commits found)._")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Keep a Changelog section from git log")
    parser.add_argument("--version", required=True, help="Version for the heading, e.g. 1.2.0")
    parser.add_argument("--since", help="Tag/ref to start from (default: last tag, else all history)")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: cwd)")
    parser.add_argument("--hashes", action="store_true", help="Append short commit hash to each entry")
    parser.add_argument("--dry-run", action="store_true", help="Preview: changelog to stdout, stats to stderr")
    args = parser.parse_args()

    since = args.since or get_last_tag(args.repo)
    try:
        commits = get_commits(args.repo, since)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    categories = categorize_commits(commits)
    changelog = generate_changelog(args.version, categories, show_hash=args.hashes)

    if args.dry_run:
        total = sum(len(v) for v in categories.values())
        rng = f"{since}..HEAD" if since else "entire history"
        print(f"[dry-run] range: {rng}; commits scanned: {len(commits)}; matched: {total}", file=sys.stderr)
        for key, _ in SECTION_NAMES:
            if categories[key]:
                print(f"[dry-run]   {key}: {len(categories[key])}", file=sys.stderr)
    print(changelog, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
