#!/usr/bin/env python3
"""student-defaults guard (TRACKED FILE — must not be gitignored) — keeps a learner's first sessions quiet.

WHY THIS FILE EXISTS
--------------------
The pack's `.claude/` tree is periodically re-synced wholesale from a live
personal config (README, "Keeping the free-by-default promise"). The
maintainer's machine is not a learner's machine: it has tokens, logins and a
real `python3`, so noise that every learner sees never shows up there. A sync
copies whole files, so a fix made only inside a synced file dies with the next
sync. `.claude/hooks/gsd-statusline.js` was byte-identical to the live copy
when the skull below was removed: the next sync would have brought it back.

So these defaults are owned HERE and re-applied on top of every sync:

    sync .claude/  ->  python guard_free_by_default.py --apply
                   ->  python guard_student_defaults.py --apply
                   ->  python _build_plugins.py

What it owns. Each item is something learners hit in support dialogs
(2026-07..10, codes from the installer issue review):

  B02  Plugins that need a personal token or login are OFF. Enabled, they greet
       every learner with "N MCP servers need authentication" or a failed
       server in /mcp, or with skills that stop at "log in first".
  B04  No permission rule that Claude Code warns about at every start:
       - a path rule for Write/MultiEdit/NotebookEdit/Glob. File access is
         checked against Edit(path) and Read(path) only, so such a rule is never
         consulted (docs: permissions#read-and-edit). It becomes its Edit()/Read()
         twin, or is dropped when the twin is already listed, so the effective
         permissions do not change. `Tool(*)` means the bare tool and is left;
       - a Bash rule mixing `*` with the legacy trailing `:*`: matched as a
         literal prefix, it "will likely never match". In deny/ask it becomes the
         form Claude Code itself suggests (`:*` -> `*`), so it finally blocks.
       Both mirror the rule validator of claude.exe 2.1.283: an unauthenticated
       `claude -p --debug` printed exactly these warnings for the old file.
  B06  hookify is OFF. It runs `python3` on every PreToolUse, PostToolUse, Stop
       and UserPromptSubmit. Without a working python3 (on Windows `python3` is
       the Microsoft Store stub, "Python was not found") every answer carries a
       "hook error" line. The maintainer's own config has it off too.
  B08  CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1 — the documented off switch for the
       "How is Claude doing this session?" survey and its transcript-share
       follow-up. `feedbackSurveyRate` is only the sampling alternative, so it is
       not set as well.
  B17  The status line shows a plain hint instead of a skull when the context
       is nearly full.

USAGE
-----
    python guard_student_defaults.py            # same as --check
    python guard_student_defaults.py --check    # verify; exit 1 if a default eroded
    python guard_student_defaults.py --dry-run  # show exactly what --apply would change
    python guard_student_defaults.py --apply    # restore everything (idempotent), then check
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SETTINGS = ".claude/settings.json"
STATUSLINE = ".claude/hooks/gsd-statusline.js"

# --- B02 + B06: plugins that must ship disabled ----------------------------
PLUGINS_OFF = {
    "greptile@claude-plugins-official":
        "B02 MCP server api.greptile.com needs a Greptile login",
    "sourcegraph@claude-plugins-official":
        "B02 MCP URL is ${SOURCEGRAPH_ENDPOINT} + access token, both empty on a fresh machine",
    "coderabbit@claude-plugins-official":
        "B02 every skill needs the CodeRabbit CLI and `coderabbit auth login`",
    "github@claude-plugins-official":
        "B02 MCP server needs a GitHub token (off since 51a58b6)",
    "linear@claude-plugins-official":
        "B02 MCP server needs a Linear login (off since 8ea2a60)",
    "notion@claude-plugins-official":
        "B02 MCP server needs a Notion login (off since 8ea2a60)",
    "telegram@claude-plugins-official":
        "B02 channel server needs a bot token (off since 8ea2a60)",
    "hookify@claude-plugins-official":
        "B06 runs python3 on every tool call and prompt; no python3 = 'hook error' in every answer",
}

# --- B04: rules Claude Code warns about at every start ------------------------
PATH_RULE_TWIN = {"Write": "Edit", "MultiEdit": "Edit", "NotebookEdit": "Edit", "Glob": "Read"}
PATH_RULE = re.compile(r"^(Write|MultiEdit|NotebookEdit|Glob)\((.*)\)$", re.S)
BASH_RULE = re.compile(r"^Bash\((.*)\)$", re.S)
RULE_LISTS = ("allow", "deny", "ask")
MANUAL = "MANUAL"

# --- B08: environment defaults -----------------------------------------------
ENV_DEFAULTS = {
    "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
}

# --- B17: status line --------------------------------------------------------
# Exact-string surgery, same shape as the installer fixes in guard_free_by_default.py.
# The colour logic stays as it was (red, blinking at >= 80% of usable context);
# only the glyph becomes words. "когда Claude закончит": learners who typed
# /compact while Claude was busy saw it reach the model as a plain message.
SKULL = "\U0001F480"
STATUSLINE_OLD = r"ctx = ` \x1b[5;31m" + SKULL + r" ${bar} ${used}%\x1b[0m`;"
STATUSLINE_NEW = (r"ctx = ` \x1b[5;31m${bar} контекст ${used}% — "
                  r"введи /compact, когда Claude закончит\x1b[0m`;")


# ---------------------------------------------------------------------------
def path(rel):
    return os.path.join(ROOT, rel)


def read(rel):
    with open(path(rel), encoding="utf-8") as fh:
        return fh.read()


def write(rel, text):
    with open(path(rel), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_settings():
    """(data, raw text) or (None, reason) — a broken file must never pass."""
    if not os.path.isfile(path(SETTINGS)):
        return None, "file missing"
    raw = read(SETTINGS)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return None, "not valid JSON: %s" % exc
    if not isinstance(data, dict):
        return None, "top level is not an object"
    return data, raw


def dump_settings(data, raw):
    # Same layout the file already has: 2-space indent, UTF-8 as is, and the
    # trailing newline only if it was there. Unchanged keys stay byte-identical.
    text = json.dumps(data, indent=2, ensure_ascii=False)
    return text + "\n" if raw.endswith("\n") else text


def warned_rule(rule, list_name):
    """(replacement, why) for a rule Claude Code warns about at start, else None.

    replacement is MANUAL when no mechanical fix keeps the author's intent.
    """
    if not isinstance(rule, str):
        return None
    m = PATH_RULE.match(rule)
    # Tool(*) is the bare tool rule, and the validator skips ':*' content.
    if m and m.group(2) != "*" and ":*" not in m.group(2):
        return ("%s(%s)" % (PATH_RULE_TWIN[m.group(1)], m.group(2)),
                "a %s path rule is never consulted" % m.group(1))
    m = BASH_RULE.match(rule)
    if m and m.group(1).endswith(":*"):
        prefix = m.group(1)[:-2].rstrip()
        if "*" in prefix:
            why = "mixes * with the trailing :*, matched as a literal prefix, never matches"
            if list_name == "allow":
                return MANUAL, why            # Claude Code: "replace that * with the exact value"
            return "Bash(%s*)" % prefix, why
    return None


def fix_rules(rules, list_name):
    """Rewrite one permissions list. Returns (new list, [(old, new-or-None)])."""
    present = set(r for r in rules if isinstance(r, str))
    out, changes = [], []
    for rule in rules:
        hit = warned_rule(rule, list_name)
        if hit is None or hit[0] == MANUAL:
            out.append(rule)
        elif hit[0] in present or hit[0] in out:
            changes.append((rule, None))       # twin already listed: drop
        else:
            out.append(hit[0])                 # replace in place
            changes.append((rule, hit[0]))
    return out, changes


def settings_problems(data):
    problems = []
    plugins = data.get("enabledPlugins") or {}
    for pid, why in PLUGINS_OFF.items():
        if plugins.get(pid) is True:
            problems.append("enabledPlugins: %s is on — %s" % (pid, why))
    perms = data.get("permissions") or {}
    for name in RULE_LISTS:
        for rule in perms.get(name) or []:
            hit = warned_rule(rule, name)
            if hit:
                fix = ("fix by hand" if hit[0] == MANUAL else "use " + hit[0])
                problems.append("permissions.%s: %s — %s; warns at every start (B04), %s"
                                % (name, rule, hit[1], fix))
    env = data.get("env") or {}
    for key, want in ENV_DEFAULTS.items():
        if env.get(key) != want:
            problems.append('env: %s must be "%s" (B08), found %r' % (key, want, env.get(key)))
    return problems


def statusline_problems():
    if not os.path.isfile(path(STATUSLINE)):
        return ["%s missing (the status line in settings.json points at it)" % STATUSLINE]
    if SKULL in read(STATUSLINE):
        return ["%s still draws a skull at high context (B17)" % STATUSLINE]
    return []


def check(verbose=True):
    data, raw = load_settings()
    if data is None:
        problems = ["%s: %s" % (SETTINGS, raw)]
    else:
        problems = settings_problems(data)
    problems += statusline_problems()

    if verbose:
        print("=== STUDENT-DEFAULTS GUARD ===")
        if problems:
            print("FAIL — %d problem(s):" % len(problems))
            for p in problems:
                print("  x " + p)
            print("\nFix: python guard_student_defaults.py --apply")
        else:
            print("OK — no token-only plugins, no rules that warn at start, survey off, "
                  "no python3 hooks, no skull in the status line.")
    return problems


def apply(dry=False):
    changes = []

    data, raw = load_settings()
    if data is None:
        changes.append(("CANNOT FIX", SETTINGS, raw))
    else:
        plugins = data.get("enabledPlugins")
        if isinstance(plugins, dict):
            for pid in PLUGINS_OFF:
                if plugins.get(pid) is True:
                    plugins[pid] = False
                    changes.append(("plugin off", SETTINGS, pid))

        perms = data.get("permissions")
        if isinstance(perms, dict):
            for name in RULE_LISTS:
                if not isinstance(perms.get(name), list):
                    continue
                perms[name], done = fix_rules(perms[name], name)
                for old, new in done:
                    changes.append(("permissions.%s" % name, SETTINGS,
                                    "%s -> %s" % (old, new) if new
                                    else "%s dropped (twin already listed)" % old))
                for rule in perms[name]:
                    hit = warned_rule(rule, name)
                    if hit and hit[0] == MANUAL:
                        changes.append(("MANUAL — permissions.%s" % name, SETTINGS, rule))

        env = data.setdefault("env", {})
        for key, want in ENV_DEFAULTS.items():
            if env.get(key) != want:
                env[key] = want
                changes.append(("env", SETTINGS, "%s=%s" % (key, want)))

        new_raw = dump_settings(data, raw)
        if new_raw != raw and not dry:
            write(SETTINGS, new_raw)

    if os.path.isfile(path(STATUSLINE)):
        text = read(STATUSLINE)
        if STATUSLINE_OLD in text:
            changes.append(("status line hint", STATUSLINE, "skull -> words"))
            if not dry:
                write(STATUSLINE, text.replace(STATUSLINE_OLD, STATUSLINE_NEW))
        elif SKULL in text:
            changes.append(("MANUAL — status line drifted", STATUSLINE,
                            "skull present but the expected line is not"))

    verb = "WOULD CHANGE" if dry else "CHANGED"
    print("=== %s (%d) ===" % (verb, len(changes)))
    for what, rel, detail in changes:
        print("  %-28s %s (%s)" % (what, rel, detail))
    if not changes:
        print("  nothing to do — student defaults already intact")
    return changes


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if arg == "--apply":
        apply(dry=False)
        sys.exit(1 if check() else 0)
    elif arg == "--dry-run":
        apply(dry=True)
        sys.exit(0)
    elif arg in ("--check", "-c"):
        sys.exit(1 if check() else 0)
    else:
        print(__doc__)
        sys.exit(0 if arg in ("-h", "--help") else 2)
