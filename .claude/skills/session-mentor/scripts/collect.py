#!/usr/bin/env python3
"""session-mentor · collect.py
Parse local Claude Code (and Codex) session transcripts into a compact stats bundle.
Data never leaves the machine. Output = JSON to stdout (or --out file).

Usage:
  python collect.py --days 30 --agent both --out stats.json
  python collect.py --days 7 --agent claude
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse, json, os, sys, glob
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# --- transcript locations (per agent) ---
HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude", "projects")
CODEX_DIR  = os.path.join(HOME, ".codex")   # sessions/rollouts if present

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
FILE_ARG_KEYS = ("file_path", "path", "notebook_path")


def _iter_jsonl(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
    except (OSError, IOError):
        return


def _parse_ts(s):
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def collect_file(path, cutoff, agent_label):
    """Return a per-session dict, or None if empty/out-of-window."""
    n_user = n_assistant = out_tokens = 0
    tools = Counter()
    files_touched = set()
    days = set()
    first_prompt = ""
    ts_min = ts_max = None
    any_in_window = False

    for o in _iter_jsonl(path):
        t = o.get("type")
        ts = _parse_ts(o.get("timestamp"))
        if ts:
            if cutoff and ts < cutoff:
                continue  # older than window — skip this line
            any_in_window = True
            d = ts.date().isoformat()
            days.add(d)
            ts_min = ts if ts_min is None or ts < ts_min else ts_min
            ts_max = ts if ts_max is None or ts > ts_max else ts_max

        msg = o.get("message") if isinstance(o.get("message"), dict) else None
        if t in ("last-prompt",) and not first_prompt:
            first_prompt = (o.get("prompt") or o.get("text") or "")[:200]
        if not msg:
            continue
        role = msg.get("role")
        if role == "user":
            n_user += 1
            if not first_prompt:
                c = msg.get("content")
                if isinstance(c, str):
                    first_prompt = c[:200]
                elif isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "text":
                            first_prompt = (b.get("text") or "")[:200]
                            break
        elif role == "assistant":
            n_assistant += 1
        u = msg.get("usage") or {}
        if isinstance(u, dict):
            out_tokens += int(u.get("output_tokens", 0) or 0)
        c = msg.get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    name = b.get("name", "?")
                    tools[name] += 1
                    inp = b.get("input") or {}
                    if isinstance(inp, dict):
                        for k in FILE_ARG_KEYS:
                            v = inp.get(k)
                            if isinstance(v, str) and v:
                                files_touched.add(v)

    if not any_in_window and cutoff:
        return None
    if n_user == 0 and n_assistant == 0 and not tools:
        return None

    project = os.path.basename(os.path.dirname(path))
    return {
        "agent": agent_label,
        "session_id": os.path.splitext(os.path.basename(path))[0],
        "project": project,
        "messages_user": n_user,
        "messages_assistant": n_assistant,
        "tool_calls": dict(tools),
        "edits": sum(tools[t] for t in EDIT_TOOLS),
        "reads": tools.get("Read", 0),
        "bash": tools.get("Bash", 0),
        "files_touched": len(files_touched),
        "out_tokens": out_tokens,
        "days": sorted(days),
        "created": ts_min.isoformat() if ts_min else None,
        "modified": ts_max.isoformat() if ts_max else None,
        "first_prompt": first_prompt.strip(),
    }


def gather(agent, days):
    cutoff = None
    if days and days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    files = []
    if agent in ("claude", "both") and os.path.isdir(CLAUDE_DIR):
        files += [("claude", p) for p in glob.glob(os.path.join(CLAUDE_DIR, "*", "*.jsonl"))]
    if agent in ("codex", "both") and os.path.isdir(CODEX_DIR):
        files += [("codex", p) for p in glob.glob(os.path.join(CODEX_DIR, "**", "*.jsonl"), recursive=True)]

    # window pre-filter by file mtime (cheap) to avoid parsing the whole 49k-file history
    if cutoff:
        cut_ts = cutoff.timestamp()
        files = [(a, p) for (a, p) in files if _safe_mtime(p) >= cut_ts - 86400]

    sessions = []
    for a, p in files:
        s = collect_file(p, cutoff, a)
        if s:
            sessions.append(s)
    return sessions


def _safe_mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0.0


def aggregate(sessions, days):
    tool_mix = Counter()
    per_project = Counter()
    per_day = Counter()
    per_agent = Counter()
    tokens_total = edits_total = reads_total = bash_total = files_total = 0
    msgs_user = msgs_assistant = 0
    for s in sessions:
        for k, v in s["tool_calls"].items():
            tool_mix[k] += v
        per_project[s["project"]] += s["messages_user"] + s["messages_assistant"]
        per_agent[s["agent"]] += 1
        for d in s["days"]:
            per_day[d] += 1
        tokens_total += s["out_tokens"]
        edits_total += s["edits"]
        reads_total += s["reads"]
        bash_total += s["bash"]
        files_total += s["files_touched"]
        msgs_user += s["messages_user"]
        msgs_assistant += s["messages_assistant"]

    themes = [s["first_prompt"] for s in sessions if s["first_prompt"]]
    return {
        "generated_window_days": days,
        "totals": {
            "sessions": len(sessions),
            "messages": msgs_user + msgs_assistant,
            "messages_user": msgs_user,
            "messages_assistant": msgs_assistant,
            "tool_calls": sum(tool_mix.values()),
            "edits": edits_total,
            "reads": reads_total,
            "bash": bash_total,
            "files_touched": files_total,
            "out_tokens": tokens_total,
        },
        "tool_mix": dict(tool_mix.most_common()),
        "per_project": dict(per_project.most_common(25)),
        "per_agent": dict(per_agent),
        "activity_by_day": dict(sorted(per_day.items())),
        "session_themes": themes[:120],   # first prompts — for the model to cluster
        "top_sessions_by_tokens": sorted(
            ({"project": s["project"], "tokens": s["out_tokens"],
              "prompt": s["first_prompt"][:120]} for s in sessions),
            key=lambda x: x["tokens"], reverse=True)[:15],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--agent", choices=["claude", "codex", "both"], default="both")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sessions = gather(args.agent, args.days)
    bundle = aggregate(sessions, args.days)
    out = json.dumps(bundle, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        sys.stderr.write(f"wrote {args.out} — {bundle['totals']['sessions']} sessions, "
                         f"{bundle['totals']['tool_calls']} tool calls\n")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
