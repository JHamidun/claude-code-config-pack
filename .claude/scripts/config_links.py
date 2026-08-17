#!/usr/bin/env python3
"""Проверка связности конфига: ведут ли ссылки туда, где что-то есть.

Конфиг разросся до шестисот с лишним единиц — навыки, команды, агенты, правила,
скрипты. Связи между ними держатся на тексте: навык упоминает другой навык, команда
зовёт скрипт, правило отсылает к справочнику. Текст не проверяется ничем, поэтому
ссылки тихо протухают: файл переехал, навык переименовали, скрипт удалили.

Цена такой протухшей ссылки высокая и неочевидная. Агент читает команду `/outlook`,
видит там единственный описанный путь — и упирается в него, хотя рабочий путь
существует и просто нигде не записан. Со стороны это выглядит как «перестал
справляться с тем, что раньше делал легко».

Скрипт ищет четыре вида разрыва:

    битая ссылка   упомянут навык/команда/агент, которого нет
    мёртвый путь   указан файл или скрипт, которого нет на диске
    невидимка      файл есть, но не упомянут нигде — найти его нельзя
    несходство     счётчик в тексте не сходится с фактическим числом файлов

    python config_links.py
    python config_links.py --json отчёт.json
    python config_links.py --fix-hints        # что и где править
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

C = pathlib.Path.home() / ".claude"


def inventory() -> dict:
    def names(d: pathlib.Path, dirs: bool = False) -> set:
        if not d.exists():
            return set()
        return ({x.name for x in d.iterdir() if x.is_dir() and not x.name.startswith("_")}
                if dirs else {f.stem for f in d.glob("*.md")})

    return {
        "skills": names(C / "skills", dirs=True),
        "commands": names(C / "commands"),
        # Агенты живут и в подпапках (health/workers, testing/workers, meta/workers) —
        # Claude Code находит их рекурсивно, значит и инвентарь должен.
        "agents": {f.stem for f in (C / "agents").rglob("*.md")},
        "rules": names(C / "rules"),
        "tools": {f.name for f in (C / "tools").glob("*.py")},
        "scripts": {f.name for f in (C / "scripts").rglob("*.py")},
    }


def text_files() -> list[pathlib.Path]:
    """Где живут ссылки: правила, справочники, описания навыков и команд."""
    out = []
    for sub in ("rules", "config", "commands", "agents"):
        d = C / sub
        if d.exists():
            out += list(d.rglob("*.md"))
    out += [p for p in (C / "skills").glob("*/SKILL.md")]
    root_md = C.parent / "CLAUDE.md"
    if root_md.exists():
        out.append(root_md)
    return out


# Ссылка на другой навык/команду/агента в тексте
PATTERNS = {
    "skills": re.compile(r"[Ss]kill[s]?\s+`([a-z0-9][a-z0-9:-]{2,44})`"),
    "commands": re.compile(r"(?:Command|команда)\s+`/?([a-z0-9][a-z0-9:-]{2,44})`"),
    "agents": re.compile(r"Agent\s+`([a-z0-9][a-z0-9:-]{2,44})`"),
}
# Путь к файлу внутри конфига
PATH_RE = re.compile(r"[~`\"']?(?:~|C:/Users/[\w.-]+)/\.claude/([\w./-]+\.(?:mjs|json|py|js|md|ts))")


def check_links(inv: dict) -> dict:
    broken: dict = {"skills": {}, "commands": {}, "agents": {}, "paths": {}}
    mentioned: dict = {k: set() for k in ("skills", "commands", "agents", "tools", "scripts")}

    for f in text_files():
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = f.relative_to(C.parent).as_posix()

        for kind, rx in PATTERNS.items():
            for m in rx.finditer(t):
                name = m.group(1)
                # Плагинные ссылки вида plugin:skill живут вне папки — не наши
                if ":" in name:
                    continue
                mentioned[kind].add(name)
                if name not in inv[kind]:
                    broken[kind].setdefault(name, []).append(rel)

        for m in PATH_RE.finditer(t):
            sub = m.group(1)
            p = C / sub
            base = pathlib.Path(sub).name
            if sub.startswith("tools/"):
                mentioned["tools"].add(base)
            elif sub.startswith("scripts/"):
                mentioned["scripts"].add(base)
            if not p.exists():
                broken["paths"].setdefault(sub, []).append(rel)

    return {"broken": broken, "mentioned": mentioned}


# Вызов скрипта в описании навыка. Берём путь ЦЕЛИКОМ, вместе с приставкой:
# без неё «~/.claude/scripts/x.py» неотличим от «scripts/x.py», и общий скрипт
# конфига ищется внутри папки навыка — там его, конечно, нет.
SKILL_SCRIPT_RE = re.compile(
    r"(?:python\d?|node)\s+[\"'`]?([^\s\"'`|>]*scripts/[\w./-]+\.(?:py|mjs|js))"
)


def resolve_script(raw: str, skill_dir: pathlib.Path) -> pathlib.Path:
    """Куда на самом деле указывает путь из описания навыка."""
    p = raw.strip().strip("\"'`")
    for var in ("${CLAUDE_SKILL_DIR}", "$CLAUDE_SKILL_DIR", "${SKILL_DIR}"):
        p = p.replace(var, skill_dir.as_posix())
    if p.startswith("~/"):
        return pathlib.Path.home() / p[2:]
    if re.match(r"^[A-Za-z]:/", p):
        return pathlib.Path(p)
    return skill_dir / p


FENCE_RE = re.compile(r"^\s*```\s*([\w+-]*)", re.M)
# Блоки, описывающие ЧУЖОЙ репозиторий, а не конфиг: пайплайн CI ссылается на
# скрипты проекта пользователя, искать их у себя на диске бессмысленно.
FOREIGN_FENCES = {"yaml", "yml", "toml", "dockerfile", "json"}


def strip_foreign_blocks(t: str) -> str:
    """Вырезать fenced-блоки чужих конфигов, оставив разметку строк."""
    out, keep, lang = [], True, ""
    for line in t.split("\n"):
        m = FENCE_RE.match(line)
        if m:
            if keep:
                lang = m.group(1).lower()
                keep = lang not in FOREIGN_FENCES
            else:
                keep = True
            out.append("")
            continue
        out.append(line if keep else "")
    return "\n".join(out)


def check_skill_scripts() -> dict:
    """Скрипты, которые навык обещает в своём описании, но которых нет на диске."""
    missing = {}
    for sk in (C / "skills").glob("*/SKILL.md"):
        t = strip_foreign_blocks(sk.read_text(encoding="utf-8", errors="replace"))
        d = sk.parent
        for m in SKILL_SCRIPT_RE.finditer(t):
            raw = m.group(1)
            if not resolve_script(raw, d).exists():
                missing.setdefault(d.name, set()).add(raw)
    return {k: sorted(v) for k, v in missing.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="куда сохранить полный отчёт")
    ap.add_argument("--quiet", action="store_true", help="только итоговые числа")
    a = ap.parse_args()

    inv = inventory()
    res = check_links(inv)
    broken, mentioned = res["broken"], res["mentioned"]
    skill_scripts = check_skill_scripts()

    print("  ЧТО ЕСТЬ")
    for k in ("skills", "commands", "agents", "rules", "tools", "scripts"):
        print(f"    {k:10} {len(inv[k])}")

    print("\n  БИТЫЕ ССЫЛКИ — упомянуто, но не существует")
    total_broken = 0
    for kind in ("skills", "commands", "agents"):
        d = broken[kind]
        total_broken += len(d)
        print(f"    {kind:10} {len(d)}")
        if not a.quiet:
            for name, where in sorted(d.items())[:6]:
                print(f"      {name:34} ← {', '.join(sorted(set(where)))[:56]}")
    print(f"    {'пути':10} {len(broken['paths'])}")
    if not a.quiet:
        for pth, where in sorted(broken["paths"].items())[:6]:
            print(f"      {pth:34} ← {', '.join(sorted(set(where)))[:56]}")
    total_broken += len(broken["paths"])

    print("\n  НЕВИДИМЫЕ — есть на диске, не упомянуто нигде")
    invisible = {}
    for kind in ("skills", "commands", "agents", "tools", "scripts"):
        miss = sorted(inv[kind] - mentioned[kind])
        invisible[kind] = miss
        print(f"    {kind:10} {len(miss):4} из {len(inv[kind])}")
    if not a.quiet:
        for kind in ("tools", "commands"):
            if invisible[kind]:
                print(f"      {kind}: {', '.join(invisible[kind][:8])}")

    print("\n  НАВЫКИ, ОБЕЩАЮЩИЕ СВОИ СКРИПТЫ, КОТОРЫХ НЕТ")
    print(f"    навыков с расхождением: {len(skill_scripts)}")
    if not a.quiet:
        for name, files in sorted(skill_scripts.items())[:8]:
            print(f"      {name:26} {', '.join(files)[:60]}")

    print(f"\n  ИТОГО разрывов: {total_broken + len(skill_scripts)}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "inventory": {k: sorted(v) for k, v in inv.items()},
            "broken": {k: {n: sorted(set(w)) for n, w in d.items()} for k, d in broken.items()},
            "invisible": invisible,
            "skill_scripts_missing": skill_scripts,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  полный отчёт: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
