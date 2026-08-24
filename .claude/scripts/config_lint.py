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
  4. OFF-BOOK WEIGHT (added 2026-07-31): everything the 4-component TILE
     misses but that still lands in the startup prompt —
       - MEMORY.md (auto-memory, injected whole)
       - command descriptions (commands/**/*.md frontmatter)
       - plugin skills + plugin commands (enabled plugins only)
       - MCP tool schemas (measured live via stdio handshake, cached)
     MCP is reported in TWO scenarios, because Claude Code >= ~2.1.x defers
     MCP tool schemas behind the ToolSearch tool by default
     (env ENABLE_TOOL_SEARCH: unset/"auto" => deferred; "100" => standard):
       deferred  -> only the tool NAME list is in the prompt
       raw       -> the full JSON schema of every tool is in the prompt
  5. ARGS:
       (no args)              -> full report (MCP from cache if present)
       --probe-mcp            -> spawn every enabled MCP server (stdio),
                                 do initialize+tools/list, cache the schemas,
                                 then print the full report. SLOW (~2-4 min:
                                 npx servers resolve the registry on start).
       --check-select "фраза" -> which skills / routing rows roughly match

Baseline reference (report 30, o200k_base):
  rules total 36427 | routing.md 20702 | skill-listing 28043
  CLAUDE.md 3766 | agent-registry 2525 | auto-load ~70761
"""

import io
import json
import os
import re
import subprocess
import sys
import threading
import time

# ---- Force UTF-8 stdout for Cyrillic on Windows ----
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Оба пути раньше стояли литералом "${HOME}\..." — Python его не разворачивает
# (на Windows переменной HOME обычно нет вовсе). Инструмент, который CLAUDE.md
# называет источником правды по счётчикам,
# показывал из-за этого ровно нули: каталогов с таким именем не существует, а
# os.walk по несуществующему пути молча возвращает пустоту, без единой ошибки.
# Берём домашний каталог у самой системы; CLAUDE_CONFIG_DIR (штатная переменная
# Claude Code) позволяет посчитать чужую раскладку — например, сам пакет до установки.
HOME_DIR = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME_DIR, ".claude")
# Навигационный хаб — это ПОЛЬЗОВАТЕЛЬСКАЯ память Claude Code, ~/.claude/CLAUDE.md.
# Раньше здесь стоял ~/CLAUDE.md (уровнем выше): это ПРОЕКТНАЯ память, она читается только
# внутри домашнего каталога, и у большинства такого файла нет вовсе — read_text молча
# отдавал пустоту, а отчёт печатал нули по «объявленным числам». Старый адрес оставлен
# запасным: у тех, кто ставил пак прежней версией, хаб всё ещё лежит там.
def _find_claude_md():
    primary = os.path.join(CLAUDE_HOME, "CLAUDE.md")
    if os.path.isfile(primary):
        return primary
    legacy = os.path.join(os.path.dirname(CLAUDE_HOME.rstrip("\\/")) or HOME_DIR,
                          "CLAUDE.md")
    if os.path.isfile(legacy):
        return legacy
    return primary   # предсказуемый путь: отчёт покажет 0, а не упадёт


CLAUDE_MD = _find_claude_md()
SKILLS_DIR = os.path.join(CLAUDE_HOME, "skills")
AGENTS_DIR = os.path.join(CLAUDE_HOME, "agents")
COMMANDS_DIR = os.path.join(CLAUDE_HOME, "commands")
RULES_DIR = os.path.join(CLAUDE_HOME, "rules")
SETTINGS_JSON = os.path.join(CLAUDE_HOME, "settings.json")
ROUTING_MD = os.path.join(RULES_DIR, "routing.md")

# --- off-book components -----------------------------------------------------
# Имя папки памяти Claude Code кодирует из пути проекта, поэтому оно у каждого
# своё (C--Users-<логин>). Литерал-плейсхолдер здесь давал ту же тихую нулевую
# метрику, что и "${HOME}" выше: путь не существует ни у кого, read_text молча
# отдаёт пустоту. Берём папку с самым свежим индексом — это и есть проект, в
# котором работают (тот же приём, что в scripts/memory_fit.py).
def _find_memory_md():
    root = os.path.join(CLAUDE_HOME, "projects")
    best, best_mtime = None, -1.0
    try:
        for name in os.listdir(root):
            cand = os.path.join(root, name, "memory", "MEMORY.md")
            try:
                mtime = os.path.getmtime(cand)
            except OSError:
                continue
            if mtime > best_mtime:
                best, best_mtime = cand, mtime
    except OSError:
        pass
    # Ничего не нашли — вернуть предсказуемый путь, чтобы отчёт показал 0, а не упал.
    return best or os.path.join(root, "default", "memory", "MEMORY.md")


MEMORY_MD = _find_memory_md()
PLUGINS_DIR = os.path.join(CLAUDE_HOME, "plugins")
INSTALLED_PLUGINS = os.path.join(PLUGINS_DIR, "installed_plugins.json")
GLOBAL_CONFIG = os.path.join(os.path.expanduser("~"), ".claude.json")
MCP_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         ".mcp_schema_cache.json")
MCP_PROBE_TIMEOUT = 120  # seconds per server (npx cold start is ~30-40s)

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
# OFF-BOOK collectors: commands with descriptions, plugin skills/commands
# ---------------------------------------------------------------------------
def collect_command_entries():
    """Return list of {name,desc} for commands/**/*.md (README excluded).

    Name mirrors how the slash-command shows up: gsd/next.md -> 'gsd:next'.
    """
    out = []
    if not os.path.isdir(COMMANDS_DIR):
        return out
    for root, _dirs, files in os.walk(COMMANDS_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn.lower() == "readme.md":
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, COMMANDS_DIR).replace(os.sep, "/")
            name = rel[:-3].replace("/", ":")
            fm = parse_frontmatter(read_text(p))
            out.append({"name": name, "desc": fm["description"] or ""})
    return out


def enabled_plugin_roots():
    """Return list of (plugin_key, installPath) for ENABLED plugins only."""
    try:
        st = json.loads(read_text(SETTINGS_JSON) or "{}")
    except Exception:
        return []
    enabled = {k for k, v in (st.get("enabledPlugins") or {}).items()
               if v is True}
    try:
        inst = json.loads(read_text(INSTALLED_PLUGINS) or "{}").get(
            "plugins", {})
    except Exception:
        return []
    roots = []
    for key in sorted(enabled):
        for rec in inst.get(key, []):
            p = rec.get("installPath")
            if p and os.path.isdir(p):
                roots.append((key, p))
    return roots


def collect_plugin_entries(roots):
    """Return (plugin_skills, plugin_commands) as [{name,desc}]."""
    pskills, pcmds = [], []
    for key, root in roots:
        short = key.split("@")[0]
        sdir = os.path.join(root, "skills")
        if os.path.isdir(sdir):
            for d in sorted(os.listdir(sdir)):
                sk = os.path.join(sdir, d, "SKILL.md")
                if os.path.isfile(sk):
                    fm = parse_frontmatter(read_text(sk))
                    pskills.append({"name": "%s:%s" % (short, d),
                                    "desc": fm["description"] or ""})
        cdir = os.path.join(root, "commands")
        if os.path.isdir(cdir):
            for rt, _d, fs in os.walk(cdir):
                for fn in sorted(fs):
                    if not fn.endswith(".md"):
                        continue
                    fm = parse_frontmatter(read_text(os.path.join(rt, fn)))
                    pcmds.append({"name": "%s:%s" % (short,
                                                     os.path.splitext(fn)[0]),
                                  "desc": fm["description"] or ""})
    return pskills, pcmds


# ---------------------------------------------------------------------------
# MCP: config discovery + live stdio handshake (initialize -> tools/list)
# ---------------------------------------------------------------------------
def collect_mcp_configs():
    """Return {server_name: {'cfg':..., 'origin':..., 'prefix':...}}.

    Sources: settings.json mcpServers (user scope), ~/.claude.json
    mcpServers (global), .mcp.json of every ENABLED plugin.
    Servers with "disabled": true are skipped.
    """
    out = {}

    def add(name, cfg, origin, prefix):
        if isinstance(cfg, dict) and cfg.get("disabled"):
            return
        out[name] = {"cfg": cfg, "origin": origin, "prefix": prefix}

    try:
        st = json.loads(read_text(SETTINGS_JSON) or "{}")
    except Exception:
        st = {}
    for name, cfg in (st.get("mcpServers") or {}).items():
        add(name, cfg, "settings.json", name)

    try:
        gc = json.loads(read_text(GLOBAL_CONFIG) or "{}")
    except Exception:
        gc = {}
    for name, cfg in (gc.get("mcpServers") or {}).items():
        add(name, cfg, "~/.claude.json", name)

    for key, root in enabled_plugin_roots():
        short = key.split("@")[0]
        p = os.path.join(root, ".mcp.json")
        blob = {}
        if os.path.isfile(p):
            try:
                blob = json.loads(read_text(p) or "{}")
            except Exception:
                blob = {}
            blob = blob.get("mcpServers", blob)
        pj = os.path.join(root, ".claude-plugin", "plugin.json")
        if not blob and os.path.isfile(pj):
            try:
                blob = (json.loads(read_text(pj) or "{}")
                        .get("mcpServers") or {})
            except Exception:
                blob = {}
        for name, cfg in (blob or {}).items():
            if not isinstance(cfg, dict):
                continue
            cfg = dict(cfg)
            cfg["_plugin_root"] = root
            add("plugin:%s:%s" % (short, name), cfg, "plugin/" + short,
                "plugin_%s_%s" % (short, name))
    return out


def _mcp_handshake(cmd, env, timeout):
    """Spawn a stdio MCP server, return (tools_list, error_str)."""
    try:
        p = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, bufsize=0,
            shell=(os.name == "nt"
                   and os.path.splitext(cmd[0])[1].lower() not in
                   (".exe", ".cmd", ".bat")),
        )
    except Exception as e:
        return None, "spawn failed: %s" % e

    threading.Thread(
        target=lambda: [None for _ in iter(p.stderr.readline, b"")],
        daemon=True).start()

    def send(obj):
        p.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        p.stdin.flush()

    def read_msg(budget):
        box = {}

        def rd():
            while True:
                line = p.stdout.readline()
                if not line:
                    box["r"] = None
                    return
                s = line.decode("utf-8", "replace").strip()
                if s.lower().startswith("content-length:"):
                    n = int(s.split(":")[1].strip())
                    p.stdout.readline()
                    box["r"] = json.loads(p.stdout.read(n).decode("utf-8"))
                    return
                if s.startswith("{"):
                    try:
                        box["r"] = json.loads(s)
                        return
                    except Exception:
                        continue
        t = threading.Thread(target=rd, daemon=True)
        t.start()
        t.join(budget)
        return box.get("r")

    t0 = time.time()
    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "config-lint", "version": "1.0"}}})
        init = None
        for _ in range(6):
            m = read_msg(max(1, timeout - (time.time() - t0)))
            if m is None:
                break
            if m.get("id") == 1:
                init = m
                break
        if init is None:
            return None, "no initialize response (%.0fs)" % (time.time() - t0)
        if "error" in init:
            return None, "initialize error: %s" % str(init["error"])[:120]
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        res = None
        for _ in range(8):
            m = read_msg(max(1, timeout - (time.time() - t0)))
            if m is None:
                break
            if m.get("id") == 2:
                res = m
                break
        if res is None or "result" not in res:
            return None, "no tools/list result (%.0fs)" % (time.time() - t0)
        return res["result"].get("tools", []), None
    except Exception as e:
        return None, "handshake error: %s" % e
    finally:
        try:
            p.kill()
        except Exception:
            pass


def probe_mcp(configs):
    """Probe every stdio server; return {name: {'tools':[...]} | {'error':..}}."""
    out = {}
    for name in sorted(configs):
        rec = configs[name]
        cfg = rec["cfg"]
        kind = cfg.get("type", "stdio")
        if kind != "stdio" or not cfg.get("command"):
            if cfg.get("url"):
                out[name] = {"error": "remote %s server (%s) — needs OAuth/"
                                      "token, not measurable headlessly"
                                      % (kind, cfg.get("url"))}
            else:
                out[name] = {"error": "no stdio command in config"}
            continue
        args = []
        for a in cfg.get("args", []):
            args.append(str(a).replace("${CLAUDE_PLUGIN_ROOT}",
                                       cfg.get("_plugin_root", "")))
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        for k, v in (cfg.get("env") or {}).items():
            if isinstance(v, str) and not re.search(r"\$\{\w+\}", v):
                env[k] = v
        sys.stderr.write("  probing %-34s ... " % name)
        sys.stderr.flush()
        tools, err = _mcp_handshake([cfg["command"]] + args, env,
                                    MCP_PROBE_TIMEOUT)
        if err:
            sys.stderr.write("FAIL (%s)\n" % err)
            out[name] = {"error": err}
        else:
            sys.stderr.write("%d tools\n" % len(tools))
            out[name] = {"tools": tools}
    return out


def mcp_tokens(enc, name, prefix, tools):
    """(raw_schema_tokens, deferred_name_tokens) for one server's tools."""
    api = [{"name": "mcp__%s__%s" % (prefix, t.get("name", "")),
            "description": t.get("description", ""),
            "input_schema": t.get("inputSchema") or t.get("input_schema")
            or {}} for t in tools]
    raw = enc(json.dumps(api, ensure_ascii=False, separators=(",", ":")))
    names = enc("\n".join(x["name"] for x in api))
    return raw, names


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
    return auto


def print_full_picture(enc, lint_total, mcp_cache):
    """Section 2b: everything the 4-component TILE does not count."""
    print()
    print("=" * 74)
    print("2b. OFF-BOOK WEIGHT — what the TILE above does NOT count")
    print("=" * 74)

    mem_tok = enc(read_text(MEMORY_MD))
    cmds = collect_command_entries()
    cmd_tok = enc(build_agent_registry(cmds))          # same "- name: desc"
    roots = enabled_plugin_roots()
    pskills, pcmds = collect_plugin_entries(roots)
    psk_tok = enc(build_agent_registry(pskills))
    pcm_tok = enc(build_agent_registry(pcmds))

    configs = collect_mcp_configs()
    raw_total = 0
    def_total = 0
    rows = []
    failed = []
    for name in sorted(configs):
        rec = mcp_cache.get(name)
        if not rec or "tools" not in rec:
            reason = (rec or {}).get("error", "not probed — run --probe-mcp")
            failed.append((name, reason))
            continue
        raw, nm = mcp_tokens(enc, name, configs[name]["prefix"], rec["tools"])
        rows.append((name, len(rec["tools"]), raw, nm))
        raw_total += raw
        def_total += nm
    rows.sort(key=lambda x: -x[2])

    print("%-34s %7s %10s %10s" % ("MCP server (enabled)", "tools",
                                   "raw sch.", "names only"))
    print("-" * 66)
    for name, n, raw, nm in rows:
        print("%-34s %7d %10d %10d" % (name[:34], n, raw, nm))
    print("-" * 66)
    print("%-34s %7s %10d %10d" % ("MCP TOTAL (measured)", "", raw_total,
                                   def_total))
    if failed:
        print("  not measured (%d):" % len(failed))
        for name, why in failed:
            print("    %-30s %s" % (name[:30], why[:70]))

    ts_env = os.environ.get("ENABLE_TOOL_SEARCH")
    deferred = ts_env is None or ts_env == "auto" or ts_env.startswith("auto:")
    print()
    print("  ENABLE_TOOL_SEARCH=%s -> MCP schemas are %s"
          % (ts_env if ts_env else "(unset, default)",
             "DEFERRED behind ToolSearch (names only in prompt)" if deferred
             else "sent RAW in the prompt"))

    mcp_eff = def_total if deferred else raw_total
    comps = [
        ("counted by TILE (rules+CLAUDE.md+skills+agents)", lint_total),
        ("MEMORY.md (auto-memory)", mem_tok),
        ("commands listing (%d)" % len(cmds), cmd_tok),
        ("plugin skills listing (%d)" % len(pskills), psk_tok),
        ("plugin commands listing (%d)" % len(pcmds), pcm_tok),
        ("MCP tool schemas (%s)" % ("deferred names" if deferred else "raw"),
         mcp_eff),
    ]
    total = sum(c[1] for c in comps)
    print()
    print("%-48s %8s %7s" % ("component", "tokens", "% total"))
    print("-" * 66)
    for name, tok in comps:
        print("%-48s %8d %6.1f%%" % (name, tok, 100.0 * tok / max(1, total)))
    print("-" * 66)
    print("%-48s %8d" % ("REAL AUTO-LOAD TOTAL", total))
    print("  off-book share: %d tok (%.1f%% of the real total)"
          % (total - lint_total,
             100.0 * (total - lint_total) / max(1, total)))
    if deferred:
        print("  if tool search were OFF (ENABLE_TOOL_SEARCH=100): %d tok"
              % (total - def_total + raw_total))
    return total


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


# ---------------------------------------------------------------------------
# Model IDs
# ---------------------------------------------------------------------------
# Псевдонимы, которые Claude Code разрешает сам в актуальную модель.
MODEL_ALIASES = {"opus", "fable", "sonnet", "haiku", "inherit", "default"}
# Прибитый ID вида claude-opus-4-5-20251101.
PINNED_MODEL_RE = re.compile(r"^claude-[a-z]+[\w.-]*-[\w.-]+$", re.I)
TEMPLATES_DIR = os.path.join(CLAUDE_HOME, "templates")
MODELS_MD = os.path.join(CLAUDE_HOME, "config", "models.md")


def collect_model_pins():
    """Файлы, где `model:` прибит датированным ID вместо алиаса.

    Устаревший ID не падает — он молча отдаёт вчерашнюю модель, и по поведению
    это не отличить. Значит, единственный способ это заметить — вот такая
    проверка. Смотрим agents/**.md и templates/**.yaml|yml.
    """
    pins = []
    targets = []
    for base, exts in ((AGENTS_DIR, (".md",)), (TEMPLATES_DIR, (".yaml", ".yml"))):
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in sorted(files):
                if fn.endswith(exts) and fn.lower() != "readme.md":
                    targets.append(os.path.join(root, fn))

    for p in targets:
        text = read_text(p)
        m = re.search(r"^model:[ \t]*(.+?)[ \t]*$", text, re.M)
        if not m:
            continue
        val = _strip_quotes(m.group(1).split("#")[0].strip())
        if not val or val.lower() in MODEL_ALIASES:
            continue
        if PINNED_MODEL_RE.match(val):
            pins.append((os.path.relpath(p, CLAUDE_HOME), val))
    return pins


def print_model_pins():
    pins = collect_model_pins()
    print()
    print("3.6 PINNED model IDs in agents/ and templates/: %d" % len(pins))
    if not pins:
        print("    (все на алиасах opus/fable/haiku — так и надо)")
        return
    known = read_text(MODELS_MD)
    for rel, val in sorted(pins):
        mark = "" if (known and val in known) else "  <- нет даже в config/models.md"
        print("    %-46s %s%s" % (rel, val, mark))
    print("    ! Прибитый ID НЕ падает, когда устаревает — он молча отдаёт")
    print("      вчерашнюю модель. Замени на алиас (opus / fable / haiku);")
    print("      точное соответствие алиас -> ID держится в config/models.md.")


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
    if sys.argv[1:] and sys.argv[1] in ("-h", "--help"):
        print("Usage: python config_lint.py [--check-select \"phrase\"] [--probe-mcp]")
        print("Read-only lint of ~/.claude config: counters, token weights (TILE), hygiene.")
        print("  --check-select \"phrase\"  which skills a phrase would match")
        print("  --probe-mcp              re-probe MCP servers (slow stdio handshake)")
        return

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

    mcp_cache = {}
    if "--probe-mcp" in args:
        sys.stderr.write("probing MCP servers (stdio handshake, slow)...\n")
        mcp_cache = probe_mcp(collect_mcp_configs())
        try:
            with io.open(MCP_CACHE, "w", encoding="utf-8") as f:
                f.write(json.dumps({"ts": int(time.time()),
                                    "servers": mcp_cache}, ensure_ascii=False))
        except Exception as e:
            sys.stderr.write("cache write failed: %s\n" % e)
    else:
        try:
            mcp_cache = json.loads(read_text(MCP_CACHE) or "{}").get(
                "servers", {})
        except Exception:
            mcp_cache = {}

    print("config_lint.py  |  token mode: %s" % mode)
    print("CLAUDE_HOME: %s" % CLAUDE_HOME)
    if mcp_cache and "--probe-mcp" not in args:
        try:
            ts = json.loads(read_text(MCP_CACHE) or "{}").get("ts", 0)
            print("MCP schema cache: %s (re-probe with --probe-mcp)"
                  % time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)))
        except Exception:
            pass
    print()
    print_counters(enc, skills, broken, agents, cmd_root, cmd_gsd, cmd_tot,
                   rules, plug)
    lint_total = print_tile(enc, skills, agents, rules)
    print_full_picture(enc, lint_total, mcp_cache)
    print_hygiene(skills)
    print_model_pins()
    print()
    print("Done. (read-only; no config file was modified)")


if __name__ == "__main__":
    main()
