#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanitize_config_secrets.py — move real credential VALUES from config/*.md into
.credentials.master.env and replace them in-file with `<see ENV_VAR>` references.

RULE (owner): value -> .credentials.master.env FIRST (if not already there),
THEN replace in source with a reference. Values moved 1:1 (rotation is a SEPARATE step).

Default = DRY-RUN (reads only, prints REDACTED plan). --apply performs the moves.
Only CREDENTIAL types are touched; operational PII (emails, project names, own-server
IPs) is left in place (separate depersonalization concern, not for local config).
"""
import re, os, sys, io

BASE = r"${HOME}/.claude"
ENV  = os.path.join(BASE, ".credentials.master.env")
TARGETS = [
    os.path.join(BASE, "config/projects-registry.md"),
    os.path.join(BASE, "config/server-secondary.md"),
]
APPLY = "--apply" in sys.argv

PLACEHOLDER = re.compile(r"(<[^>]*>|\$\{|see\s+ENV|REDACT|ROTATED|example|your-|xxx+|changeme|placeholder|\.\.\.)", re.I)
SENS_NEAR   = re.compile(r"(pass|pwd|secret|token|api[_\- ]?key|api[_\- ]?hash|bearer|client_secret|webhook|jwt|access[_\- ]?key)", re.I)

# value-level detectors: (name, regex_capturing_value, needs_sensitive_context)
DETECTORS = [
    ("tg_bot_token", re.compile(r"\b(\d{8,10}:AA[A-Za-z0-9_-]{33})\b"), False),
    ("openai_key",   re.compile(r"\b(sk-[A-Za-z0-9]{20,})\b"), False),
    ("google_api",   re.compile(r"\b(AIza[0-9A-Za-z_-]{35})\b"), False),
    ("github_pat",   re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{30,})\b"), False),
    ("slack_token",  re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b"), False),
    ("perplexity",   re.compile(r"\b(pplx-[A-Za-z0-9]{40,})\b"), False),
    ("hf_token",     re.compile(r"\b(hf_[A-Za-z0-9]{30,})\b"), False),
    ("aws_akid",     re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), False),
    ("jwt",          re.compile(r"\b(eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+)"), False),
    ("hex64",        re.compile(r"\b([0-9a-fA-F]{64})\b"), True),
    ("hex32",        re.compile(r"\b([0-9a-fA-F]{32})\b"), True),
    # generic key: value / key = value (value 6+ chars, no spaces/pipes/quotes)
    ("kv_secret",    re.compile(r"(?i)(?:pass(?:word)?|pwd|secret|token|api[_\- ]?key|api[_\- ]?hash|bearer|client_secret|access[_\- ]?key)\s*[:=]\s*[`'\"]?([^\s`'\"|<>]{6,})[`'\"]?"), False),
    # markdown table password cells: `pw:value` or `password value`
    ("backtick_secret", re.compile(r"`([A-Za-z0-9][A-Za-z0-9!@#$%^&*_\-]{7,})`"), True),
]

def slug(s, n=28):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return (s[:n] or "SEC")

def load_env_values():
    vals, names = set(), set()
    if os.path.exists(ENV):
        for l in io.open(ENV, encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z0-9_]{3,})\s*=\s*(.*)$", l)
            if m:
                names.add(m.group(1)); vals.add(m.group(2).strip().strip('"\''))
    return vals, names

def redact(v):
    if len(v) <= 8: return v[:2] + "***"
    return v[:4] + "***" + v[-2:] + f"(len{len(v)})"

def main():
    env_vals, env_names = load_env_values()
    found = []   # (file, lineno, typ, value, env_name, in_env, section, label)
    seen_values = {}
    for path in TARGETS:
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
        section = ""
        for i, ln in enumerate(lines, 1):
            if ln.lstrip().startswith("#"):
                section = ln.strip("# ").strip()[:30]
            for typ, rx, need_ctx in DETECTORS:
                for m in rx.finditer(ln):
                    val = m.group(1)
                    if PLACEHOLDER.search(val):        continue
                    if val.lower() in ("password","secret","token","true","false","null","none"): continue
                    if need_ctx and not SENS_NEAR.search(ln): continue
                    if val.startswith(("http://","https://")): continue
                    # label = nearest sensitive word or first cell
                    lm = SENS_NEAR.search(ln)
                    label = lm.group(1) if lm else (ln.split("|")[1].strip() if "|" in ln else "")
                    key = val
                    if key in seen_values:
                        env_name = seen_values[key]
                        in_env = key in env_vals
                    else:
                        base = slug(f"{section}_{label}_{typ}")
                        env_name = base
                        k = 1
                        while env_name in env_names or env_name in seen_values.values():
                            k += 1; env_name = f"{base}_{k}"
                        seen_values[key] = env_name
                        in_env = key in env_vals
                    found.append([path, i, typ, val, env_name, in_env, section, label])
    # dedup identical (file,line,value)
    uniq = []
    seenfl = set()
    for r in found:
        k = (r[0], r[1], r[3])
        if k in seenfl: continue
        seenfl.add(k); uniq.append(r)
    # report (redacted)
    rep = os.path.join(BASE, "scratchpad/config-audit-2026-07-17/_p0_sanitize_plan.md")
    os.makedirs(os.path.dirname(rep), exist_ok=True)
    uv = {r[3] for r in uniq}
    with io.open(rep, "w", encoding="utf-8") as f:
        f.write(f"# P0.2 sanitize plan (DRY-RUN, values REDACTED)\n\n")
        f.write(f"Secret occurrences: {len(uniq)} | unique values: {len(uv)} | already in env: {sum(1 for r in uniq if r[5])}\n\n")
        f.write("| file | line | type | env_name | in_env | value |\n|---|---|---|---|---|---|\n")
        for p,i,typ,val,en,ie,sec,lab in uniq:
            f.write(f"| {os.path.basename(p)} | {i} | {typ} | {en} | {'Y' if ie else ''} | {redact(val)} |\n")
    print(f"DRY-RUN: {len(uniq)} secret occurrences, {len(uv)} unique, {sum(1 for r in uniq if r[5])} already-in-env. Plan -> {rep}")
    if not APPLY:
        print("Review the plan. Re-run with --apply to move values to env + replace with <see ENV>.")
        return
    # APPLY
    # 1) append missing values to env
    to_add = {}
    for p,i,typ,val,en,ie,sec,lab in uniq:
        if val not in env_vals and val not in to_add:
            to_add[val] = en
    if to_add:
        with io.open(ENV, "a", encoding="utf-8") as f:
            f.write(f"\n# --- moved from config/*.md by sanitize_config_secrets.py 2026-07-17 (rotate these) ---\n")
            for val, en in to_add.items():
                f.write(f"{en}={val}\n")
    # 2) replace values in files (longest-first to avoid partial overlap)
    per_file = {}
    for r in uniq: per_file.setdefault(r[0], []).append(r)
    changed = {}
    for path, rows in per_file.items():
        txt = io.open(path, encoding="utf-8").read()
        for r in sorted(rows, key=lambda x: -len(x[3])):
            val, en = r[3], r[4]
            if val in txt:
                txt = txt.replace(val, f"<see {en}>")
        io.open(path, "w", encoding="utf-8", newline="").write(txt)
        changed[path] = len(rows)
    print(f"APPLIED: added {len(to_add)} new env vars; replaced in files: " + ", ".join(f"{os.path.basename(k)}:{v}" for k,v in changed.items()))
    print(f"Rotation list (new env vars): {', '.join(to_add.values())}")

if __name__ == "__main__":
    main()
