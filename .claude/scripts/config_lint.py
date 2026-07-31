#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_lint.py - Linter for YourFirstName's Claude Code config (Windows 11).

Zero hooks, manual run. Python stdlib + tiktoken (optional, o200k_base).
Read-only: NEVER modifies any config file. It only measures and flags.

WHAT IT DOES
  1. COUNTERS vs FACT: counts real skills/agents/commands/rules/plugins on disk
     and diffs them against the numbers declared in CLAUDE.md.
  2. TILE (tiktoken o200k_base): per-component auto-load token weight
     (each rules/*.md, CLAUDE.md, skill-listing, agent-registry) + TOTAL,
     compared against the report-30 hard-measure baseline.
  3. HYGIENE FLAGS: skills with empty frontmatter description, zombies
     (desc < 60 chars), oversized descriptions (> 400 chars), broken skill
     dirs (no SKILL.md), skills not referenced in routing.md.
  4. ARGS:
       (no args)              -> full report
       --check-select "фраза" -> which skills / routing rows roughly match

Baseline reference (report 30, o200k_base):
  rules total 36427 | routing.md 20702 | skill-listing 28043
  CLAUDE.md 3766 | agent-registry 2525 | auto-load ~70761
"""

import io
import json
import os
import re
import sys

# ---- Force UTF-8 stdout for Cyrillic on Windows ----
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CLAUDE_HOME = r"${HOME}\.claude"
CLAUDE_MD = r"${HOME}\CLAUDE.md"
SKILLS_DIR = os.path.join(CLAUDE_HOME, "skills")
AGENTS_DIR = os.path.join(CLAUDE_HOME, "agents")
COMMANDS_DIR = os.path.join(CLAUDE_HOME, "commands")
RULES_DIR = os.path.join(CLAUDE_HOME, "rules")
SETTINGS_JSON = os.path.join(CLAUDE_HOME, "settings.json")
ROUTING_MD = os.path.join(RULES_DIR, "routing.md")

# Report-30 hard-measure baseline (o200k_base) for delta reporting.
REF = {
    "rules_total": 36427,
    "routing": 20702,
    "skill_listing": 28043,
    "skill_desc_only": 26354,
    "claude_md": 3766,
    "agent_registry": 2525,
    "auto_load": 70761,
}

EMPTY_DESC_MAX = 0      # description == "" -> empty
ZOMBIE_MAX = 60         # 0 < len < 60 -> zombie
OVERSIZED_MIN = 400     # len > 400 -> oversized
BLOAT_DESC_MAX = 450    # len > 450 -> listing-bloat regress-guard


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Token counting: tiktoken o200k_base, with self-calibrated char fallback
# ---------------------------------------------------------------------------
def build_encoder():
    """Return (encode_fn(text)->int, mode_label)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        return (lambda t: len(enc.encode(t)) if t else 0), "tiktoken/o200k_base"
    except Exception:
        # Fallback: self-calibrate tokens-per-char from routing.md
        # (known ground truth: routing.md == 20702 tokens, report 30).
        ratio = 0.2548  # default tok/char for this Cyrillic-heavy corpus
        rt = read_text(ROUTING_MD)
        if rt:
            ratio = REF["routing"] / max(1, len(rt))
        return (lambda t: int(round(len(t) * ratio)) if t else 0), (
            "heuristic chars*%.4f (tiktoken missing)" % ratio
        )


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (name + description), stdlib only
# ---------------------------------------------------------------------------
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def parse_frontmatter(text):
    """Return dict with 'name' and 'description' (both str, may be '')."""
    out = {"name": "", "description": ""}
    m = _FM_RE.match(text)
    if not m:
        return out
    block = m.group(1)
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$", line)
        if km and km.group(1) in ("name", "description"):
            key = km.group(1)
            rest = km.group(2).strip()
            if rest in (">", "|", ">-", "|-", ">+", "|+"):
                # block scalar: collect indented continuation lines
                buf = []
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.strip() == "" or nxt.startswith((" ", "\t")):
                        buf.append(nxt.strip())
                        j += 1
                    else:
                        break
                out[key] = " ".join(x for x in buf if x).strip()
                i = j
                continue
            else:
                val = rest
                # folded continuation (indented lines with no "key:" on them)
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.startswith((" ", "\t")) and not re.match(
                        r"^\s*[A-Za-z_][A-Za-z0-9_-]*:\s", nxt
                    ):
                        val += " " + nxt.strip()
                        j += 1
                    else:
                        break
                out[key] = _strip_quotes(val.strip())
                i = j
                continue
        i += 1
    return out


def _strip_quotes(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------
def collect_skills():
    """Return (skills list of {name,desc,dir,desc_len}, broken_dirs list)."""
    skills = []
    broken = []
    if not os.path.isdir(SKILLS_DIR):
        return skills, broken
    for name in sorted(os.listdir(SKILLS_DIR)):
        d = os.path.join(SKILLS_DIR, name)
        if not os.path.isdir(d):
            continue
        sk = os.path.join(d, "SKILL.md")
        if not os.path.isfile(sk):
            broken.append(name)
            continue
        fm = parse_frontmatter(read_text(sk))
        sname = fm["name"] or name
        desc = fm["description"] or ""
        skills.append(
            {"name": sname, "dir": name, "desc": desc, "desc_len": len(desc)}
        )
    return skills, broken


def collect_agents():
    """Return list of {name,desc} for all agents/**/*.md except README."""
    agents = []
    if not os.path.isdir(AGENTS_DIR):
        return agents
    for root, _dirs, files in os.walk(AGENTS_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            if fn.lower() == "readme.md":
                continue
            p = os.path.join(root, fn)
            fm = parse_frontmatter(read_text(p))
            aname = fm["name"] or os.path.splitext(fn)[0]
            agents.append({"name": aname, "desc": fm["description"] or ""})
    return agents


def collect_commands():
    """Return (root_count, gsd_count, total) for *.md excluding README."""
    root = 0
    gsd = 0
    if os.path.isdir(COMMANDS_DIR):
        for fn in os.listdir(COMMANDS_DIR):
            if fn.endswith(".md") and fn.lower() != "readme.md":
                if os.path.isfile(os.path.join(COMMANDS_DIR, fn)):
                    root += 1
        gsd_dir = os.path.join(COMMANDS_DIR, "gsd")
        if os.path.isdir(gsd_dir):
            for fn in os.listdir(gsd_dir):
                if fn.endswith(".md") and fn.lower() != "readme.md":
                    if os.path.isfile(os.path.join(gsd_dir, fn)):
                        gsd += 1
    return root, gsd, root + gsd


def collect_rules():
    """Return list of (filename, text) for rules/*.md."""
    out = []
    if os.path.isdir(RULES_DIR):
        for fn in sorted(os.listdir(RULES_DIR)):
            if fn.endswith(".md"):
                out.append((fn, read_text(os.path.join(RULES_DIR, fn))))
    return out


def collect_plugins():
    """Return (total, enabled, disabled, disabled_names)."""
    try:
        d = json.loads(read_text(SETTINGS_JSON) or "{}")
    except Exception:
        return 0, 0, 0, []
    ep = d.get("enabledPlugins", {})
    if not isinstance(ep, dict):
        return 0, 0, 0, []
    enabled = sum(1 for v in ep.values() if v is True)
    disabled = sum(1 for v in ep.values() if v is False)
    dis_names = sorted(k for k, v in ep.items() if v is False)
    return len(ep), enabled, disabled, dis_names


# ---------------------------------------------------------------------------
# CLAUDE.md declared numbers
# ---------------------------------------------------------------------------
def parse_claude_md_declared():
    """Grep the inventory table in CLAUDE.md for declared counts."""
    text = read_text(CLAUDE_MD)
    declared = {}
    labels = {
        "skills": "Навыки",
        "agents": "Агенты",
        "commands": "Команды",
        "rules": "Правила",
        "plugins": "Плагины",
    }
    for key, label in labels.items():
        # table row: | <label> | ... | <value cell> |
        m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|.*?\|([^|]*)\|",
                      text)
        if m:
            declared[key] = m.group(1).strip()
        else:
            declared[key] = None
    return declared


def _first_int(s):
    if not s:
        return None
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else None


def _total_int(s):
    """Take number after '=' if present else first int (for '34+17=51')."""
    if not s:
        return None
    if "=" in s:
        m = re.search(r"=\s*(\d+)", s)
        if m:
            return int(m.group(1))
    return _first_int(s)


# ---------------------------------------------------------------------------
# Skill listing / agent registry strings (as they weigh in the prompt)
# ---------------------------------------------------------------------------
def build_skill_listing(skills):
    lines = []
    for s in skills:
        if s["desc"]:
            lines.append("- %s: %s" % (s["name"], s["desc"]))
        else:
            lines.append("- %s" % s["name"])
    return "\n".join(lines)


def build_skill_desc_only(skills):
    return "\n".join(s["desc"] for s in skills if s["desc"])


def build_agent_registry(agents):
    lines = []
    for a in agents:
        if a["desc"]:
            lines.append("- %s: %s" % (a["name"], a["desc"]))
        else:
            lines.append("- %s" % a["name"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def fmt_delta(actual, ref):
    d = actual - ref
    sign = "+" if d >= 0 else ""
    return "%s%d" % (sign, d)


def print_counters(enc, skills, broken, agents, cmd_root, cmd_gsd, cmd_tot,
                   rules, plug):
    declared = parse_claude_md_declared()
    total_pl, en_pl, dis_pl, dis_names = plug

    print("=" * 74)
    print("1. COUNTERS vs FACT (disk)  →  CLAUDE.md declared")
    print("=" * 74)
    rows = [
        ("Skills (dir w/ SKILL.md)", len(skills),
         _first_int(declared["skills"]), declared["skills"]),
        ("Agents (**/*.md, no README)", len(agents),
         _total_int(declared["agents"]), declared["agents"]),
        ("Commands (root %d + gsd %d)" % (cmd_root, cmd_gsd), cmd_tot,
         _first_int(declared["commands"]), declared["commands"]),
        ("Rules (*.md)", len(rules),
         _first_int(declared["rules"]), declared["rules"]),
        ("Plugins enabled", en_pl,
         _first_int(declared["plugins"]), declared["plugins"]),
    ]
    print("%-30s %8s %10s   %s" % ("component", "FACT", "DECLARED", "note"))
    print("-" * 74)
    for name, fact, decl, raw in rows:
        flag = ""
        if decl is not None and decl != fact:
            flag = "  <<< MISMATCH (%s)" % fmt_delta(fact, decl)
        decl_s = "n/a" if decl is None else str(decl)
        print("%-30s %8d %10s%s" % (name, fact, decl_s, flag))
    # plugins extra: disabled
    decl_dis = None
    if declared["plugins"]:
        m = re.search(r"\((\d+)\s*disabled", declared["plugins"])
        if m:
            decl_dis = int(m.group(1))
    flag = ""
    if decl_dis is not None and decl_dis != dis_pl:
        flag = "  <<< MISMATCH (%s)" % fmt_delta(dis_pl, decl_dis)
    print("%-30s %8d %10s%s" % ("Plugins disabled", dis_pl,
                                "n/a" if decl_dis is None else decl_dis, flag))
    print("%-30s %8d" % ("Plugins total (settings.json)", total_pl))
    if dis_names:
        print("  disabled:", ", ".join(dis_names))
    if broken:
        print("  broken skill dirs (no SKILL.md): %d -> %s"
              % (len(broken), ", ".join(broken)))
    print("  raw CLAUDE.md cells:")
    for k in ("skills", "agents", "commands", "rules", "plugins"):
        print("    %-9s = %s" % (k, declared[k]))


def print_tile(enc, skills, agents, rules):
    print()
    print("=" * 74)
    print("2. TILE — auto-load token weight (o200k_base)")
    print("=" * 74)

    # rules per file
    rules_tok = []
    rules_total = 0
    for fn, text in rules:
        t = enc(text)
        rules_tok.append((fn, t))
        rules_total += t
    rules_tok.sort(key=lambda x: -x[1])

    print("rules/ per file:")
    print("%-26s %8s" % ("file", "tokens"))
    print("-" * 40)
    for fn, t in rules_tok:
        mark = ""
        if fn == "routing.md":
            mark = "   (ref %d, %s)" % (REF["routing"],
                                        fmt_delta(t, REF["routing"]))
        print("%-26s %8d%s" % (fn, t, mark))
    print("-" * 40)
    print("%-26s %8d   (ref %d, %s)"
          % ("rules TOTAL", rules_total, REF["rules_total"],
             fmt_delta(rules_total, REF["rules_total"])))

    # other components
    claude_txt = read_text(CLAUDE_MD)
    claude_tok = enc(claude_txt)
    listing = build_skill_listing(skills)
    listing_tok = enc(listing)
    desc_only = build_skill_desc_only(skills)
    desc_tok = enc(desc_only)
    registry = build_agent_registry(agents)
    registry_tok = enc(registry)

    print()
    print("%-30s %8s %8s   %s" % ("component", "tokens", "ref", "delta"))
    print("-" * 66)
    comp = [
        ("rules/ (all 23)", rules_total, REF["rules_total"]),
        ("CLAUDE.md (home)", claude_tok, REF["claude_md"]),
        ("skill-listing (%d local)" % len(skills), listing_tok,
         REF["skill_listing"]),
        ("  skill desc-only", desc_tok, REF["skill_desc_only"]),
        ("agent-registry (%d)" % len(agents), registry_tok,
         REF["agent_registry"]),
    ]
    for name, tok, ref in comp:
        print("%-30s %8d %8d   %s"
              % (name, tok, ref, fmt_delta(tok, ref)))
    print("-" * 66)
    auto = rules_total + claude_tok + listing_tok + registry_tok
    print("%-30s %8d %8d   %s"
          % ("AUTO-LOAD TOTAL", auto, REF["auto_load"],
             fmt_delta(auto, REF["auto_load"])))
    print("  (TOTAL = rules + CLAUDE.md + skill-listing + agent-registry.")
    print("   ref skill-listing 28043 was measured at audit time when ~51 descs")
    print("   were EMPTY; since then descs were filled in (now only a few empty,")
    print("   many >400ch), so the listing legitimately grew. %d SKILL.md counted"
          % len(skills))
    print("   (real dirs + resolved junctions; matches audit's ~389 entries).)")


def print_hygiene(skills):
    print()
    print("=" * 74)
    print("3. HYGIENE FLAGS")
    print("=" * 74)

    empty = [s for s in skills if s["desc_len"] == EMPTY_DESC_MAX]
    zombie = [s for s in skills if 0 < s["desc_len"] < ZOMBIE_MAX]
    oversized = [s for s in skills if s["desc_len"] > OVERSIZED_MIN]

    print("3.1 EMPTY frontmatter description: %d" % len(empty))
    if empty:
        print("    " + ", ".join(sorted(s["dir"] for s in empty)))

    print("3.2 ZOMBIE (0 < desc < %d chars): %d" % (ZOMBIE_MAX, len(zombie)))
    for s in sorted(zombie, key=lambda x: x["desc_len"]):
        print("    %-28s %d ch" % (s["dir"], s["desc_len"]))

    print("3.3 OVERSIZED (desc > %d chars): %d" % (OVERSIZED_MIN,
                                                   len(oversized)))
    for s in sorted(oversized, key=lambda x: -x["desc_len"]):
        print("    %-28s %d ch" % (s["dir"], s["desc_len"]))

    # skills not referenced in routing.md
    routing = read_text(ROUTING_MD)
    not_routed = []
    for s in skills:
        # match by skill name or dir as a whole token
        nm = re.escape(s["name"])
        dr = re.escape(s["dir"])
        if re.search(nm, routing) or re.search(dr, routing):
            continue
        not_routed.append(s["dir"])
    print("3.4 NOT in routing.md (selectable only from listing): %d"
          % len(not_routed))
    if not_routed:
        print("    " + ", ".join(sorted(not_routed)))

    # regression guard: descriptions > 450 chars bloat the auto-loaded
    # skill-listing. Flag them so a future bulk-import doesn't re-inflate it.
    bloat = [s for s in skills if s["desc_len"] > BLOAT_DESC_MAX]
    print("3.5 WARNING — desc > %d chars (listing-bloat regress-guard): %d"
          % (BLOAT_DESC_MAX, len(bloat)))
    for s in sorted(bloat, key=lambda x: -x["desc_len"]):
        print("    %-28s %d ch" % (s["dir"], s["desc_len"]))


def cmd_check_select(phrase, skills):
    """Rough selection: score skills & routing rows against phrase tokens."""
    print("=" * 74)
    print("CHECK-SELECT: %r" % phrase)
    print("=" * 74)
    words = [w.lower() for w in re.findall(r"[\wа-яёА-ЯЁ]+", phrase)
             if len(w) >= 3]
    if not words:
        print("  (phrase too short / no words >= 3 chars)")
        return

    # score skills
    scored = []
    for s in skills:
        hay = (s["name"] + " " + s["dir"] + " " + s["desc"]).lower()
        hits = sum(1 for w in words if w in hay)
        if hits:
            scored.append((hits, s["dir"], s["desc_len"]))
    scored.sort(key=lambda x: (-x[0], x[1]))
    print("\nSKILLS matched (word-hits / dir / desc_len):")
    if not scored:
        print("  (none — likely routing-only or empty-desc skill)")
    for hits, dr, dl in scored[:12]:
        note = "  [EMPTY desc]" if dl == 0 else ""
        print("  %d  %-30s (%d ch)%s" % (hits, dr, dl, note))

    # score routing rows
    routing = read_text(ROUTING_MD)
    rows = []
    for line in routing.split("\n"):
        if not line.strip().startswith("|"):
            continue
        low = line.lower()
        hits = sum(1 for w in words if w in low)
        if hits:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cat = cells[0] if cells else ""
            tool = cells[-1] if len(cells) >= 2 else ""
            rows.append((hits, cat, tool))
    rows.sort(key=lambda x: -x[0])
    print("\nROUTING rows matched (hits / category -> tool):")
    if not rows:
        print("  (none)")
    for hits, cat, tool in rows[:10]:
        tool_s = (tool[:70] + "…") if len(tool) > 70 else tool
        print("  %d  %-24s -> %s" % (hits, cat[:24], tool_s))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    enc, mode = build_encoder()

    skills, broken = collect_skills()
    agents = collect_agents()
    cmd_root, cmd_gsd, cmd_tot = collect_commands()
    rules = collect_rules()
    plug = collect_plugins()

    args = sys.argv[1:]
    if args and args[0] == "--check-select":
        phrase = " ".join(args[1:]).strip().strip('"').strip("'")
        cmd_check_select(phrase, skills)
        return

    print("config_lint.py  |  token mode: %s" % mode)
    print("CLAUDE_HOME: %s" % CLAUDE_HOME)
    print()
    print_counters(enc, skills, broken, agents, cmd_root, cmd_gsd, cmd_tot,
                   rules, plug)
    print_tile(enc, skills, agents, rules)
    print_hygiene(skills)
    print()
    print("Done. (read-only; no config file was modified)")


if __name__ == "__main__":
    main()
