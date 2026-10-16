#!/usr/bin/env python3
"""Вес системного промпта: что грузится в КАЖДЫЙ запрос и сколько это стоит.

Смысл в том, чтобы диета конфига опиралась на замер, а не на ощущение. Пока
измеряешь глазами, режется то, что жалко, а не то, что дорого: описания навыков
поодиночке выглядят копеечными и в сумме дают больше, чем весь routing.

Замеряется ровно то, что уходит в модель на каждом запросе:

* `rules/*.md` и `CLAUDE.md` — авто-загрузка, целиком;
* `MEMORY.md` — с отсечкой по фактическому лимиту (хвост за 200 строк / 25 КБ
  отбрасывается молча, и платить за него не приходится, но и пользы нет);
* листинг навыков — ТОЛЬКО поле `description` каждого навыка, тело SKILL.md
  грузится лишь при вызове. Скрытые через `settings.json` → `skillOverrides`
  (`name-only`) считаются по имени;
* описания агентов и команд.

Токены — tiktoken (o200k_base) при наличии, иначе оценка по символам. Оценка
намеренно грубее в бóльшую сторону: заниженный замер успокаивает зря.

    python ~/.claude/skills/config-health/scripts/prompt_weight.py            # сводка + топ едоков
    python ~/.claude/skills/config-health/scripts/prompt_weight.py --top 40   # длиннее топ
    python ~/.claude/skills/config-health/scripts/prompt_weight.py --json     # для сравнения «до/после»
"""

from __future__ import annotations

# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866, и первый же
# не-ASCII символ (кириллица, ⚠️) валит процесс UnicodeEncodeError.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
import json
import os
import pathlib
import re
import sys

HOME = pathlib.Path(os.path.expanduser("~"))
CLAUDE = HOME / ".claude"


def _find_memory_dir() -> pathlib.Path:
    """Каталог авто-памяти: самый свежий ~/.claude/projects/*/memory, где есть MEMORY.md."""
    found = [p for p in (CLAUDE / "projects").glob("*/memory/MEMORY.md") if p.is_file()]
    if not found:
        return CLAUDE / "projects" / "-" / "memory"  # нет памяти: ниже будет «MEMORY.md не найден»
    return max(found, key=lambda p: p.stat().st_mtime).parent


MEMORY_DIR = _find_memory_dir()

MEMORY_LINE_LIMIT = 200
MEMORY_BYTE_LIMIT = 25 * 1024


def _make_counter():
    """Возвращает (функция подсчёта, название способа)."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("o200k_base")
        return (lambda s: len(enc.encode(s, disallowed_special=()))), "tiktoken o200k"
    except Exception:
        # 3.1 символа на токен — эмпирика для смеси русского и латиницы в этом
        # конфиге; чистая латиница дала бы ~4, русский ~2.5.
        return (lambda s: int(len(s) / 3.1)), "оценка по символам (tiktoken нет)"


COUNT, METHOD = _make_counter()


def read(p: pathlib.Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def frontmatter_description(text: str) -> str:
    """description из YAML-шапки; поддерживает кавычки и многострочный скаляр."""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    head = text[3 : end if end > 0 else len(text)]
    m = re.search(r"^description:[ \t]*(.*)$", head, re.M)
    if not m:
        return ""
    val = m.group(1).strip()
    if val in (">", "|", ">-", "|-", ""):  # блочный скаляр — собрать отступ
        lines = []
        started = False
        for line in head[m.end() :].splitlines():
            if not started:
                if not line.strip():
                    continue
                started = True
            if line.strip() and not line.startswith((" ", "\t")):
                break
            lines.append(line.strip())
        return " ".join(lines).strip()
    return val.strip("\"'")


def author_hidden(text: str) -> bool:
    """`disable-model-invocation: true` в шапке = навыка в листинге НЕТ вовсе.

    Без этой проверки замер завышал: reference-пакеты с таким флагом считались
    как сотни токенов, которых в промпте нет.
    """
    return bool(re.search(r"^disable-model-invocation:\s*true", text[:2000], re.M))


def skill_overrides() -> dict:
    try:
        s = json.loads(read(CLAUDE / "settings.json"))
    except json.JSONDecodeError:
        return {}
    return s.get("skillOverrides", {}) or {}


def enabled_plugin_dirs():
    """[(имя, каталог)] для ВКЛЮЧЁННЫХ плагинов.

    Тела плагинов лежат в `plugins/cache/<маркетплейс>/<плагин>/<версия>/`;
    версий может быть несколько — берём последнюю по времени, ту же, что берёт
    сам CLI.
    """
    try:
        s = json.loads(read(CLAUDE / "settings.json"))
    except json.JSONDecodeError:
        return []
    out = []
    cache = CLAUDE / "plugins" / "cache"
    for key, on in (s.get("enabledPlugins") or {}).items():
        if not on or "@" not in key:
            continue
        name, mkt = key.split("@", 1)
        d = cache / mkt / name
        if not d.is_dir():
            continue
        vers = [v for v in d.iterdir() if v.is_dir()]
        if vers:
            out.append((name, max(vers, key=lambda p: p.stat().st_mtime)))
    return out


def memory_index_tokens() -> tuple[int, int, str]:
    """(оплачиваемые токены, отброшенные токены, пояснение)."""
    text = read(MEMORY_DIR / "MEMORY.md")
    if not text:
        return 0, 0, "MEMORY.md не найден"
    lines = text.splitlines(keepends=True)
    kept, size = [], 0
    for i, line in enumerate(lines):
        b = len(line.encode("utf-8"))
        if i >= MEMORY_LINE_LIMIT or size + b > MEMORY_BYTE_LIMIT:
            break
        kept.append(line)
        size += b
    dropped = "".join(lines[len(kept) :])
    note = (
        f"{len(lines)} строк / {len(text.encode('utf-8'))//1024} КБ"
        + (f" — ХВОСТ ОТБРОШЕН: {len(lines)-len(kept)} строк" if dropped else " — влезает целиком")
    )
    return COUNT("".join(kept)), COUNT(dropped), note


def collect() -> dict:
    parts: dict[str, int] = {}
    items: list[tuple[str, int, str]] = []  # (имя, токены, группа)

    # 1. Правила и CLAUDE.md — грузятся телом
    rules = 0
    for p in sorted((CLAUDE / "rules").glob("*.md")):
        t = COUNT(read(p))
        rules += t
        items.append((f"rules/{p.name}", t, "rules"))
    parts["rules/"] = rules

    for name, path in (("CLAUDE.md", HOME / "CLAUDE.md"), ("~/.claude/CLAUDE.md", CLAUDE / "CLAUDE.md")):
        if path.exists():
            t = COUNT(read(path))
            parts[name] = parts.get(name, 0) + t
            items.append((name, t, "claude.md"))

    # 2. Индекс памяти
    kept, dropped, note = memory_index_tokens()
    parts["MEMORY.md"] = kept
    items.append(("MEMORY.md (индекс)", kept, "memory"))

    # 3. Листинг навыков — только описания
    ov = skill_overrides()
    hidden = author_off = 0
    listing = 0
    for p in sorted((CLAUDE / "skills").glob("*/SKILL.md")):
        name = p.parent.name
        body = read(p)
        if author_hidden(body):
            author_off += 1
            continue
        mode = ov.get(name)
        if mode == "name-only":
            t = COUNT(name)
            hidden += 1
        elif mode in ("disabled", "off", False):
            continue
        else:
            t = COUNT(f"{name}: {frontmatter_description(body)}")
        listing += t
        items.append((f"skill:{name}", t, "skills"))
    parts["листинг навыков"] = listing

    # 3b. Навыки, команды и агенты ВКЛЮЧЁННЫХ плагинов — они в том же листинге
    # skillOverrides do NOT apply to plugin skills: the CLI returns "on" for source=plugin
    # before it reads them (binary 2.1.207/2.1.235/2.1.280, checked 23.09.2026), so a
    # plugin skill always costs its full description.
    plug, plugin_skills = 0, set()
    for name, path in enabled_plugin_dirs():
        for p in sorted(path.glob("skills/*/SKILL.md")):
            sk = p.parent.name
            plugin_skills.add(sk)
            t = COUNT(f"{sk}: {frontmatter_description(read(p))}")
            plug += t
            items.append((f"plugin:{name}/{sk}", t, "plugins"))
        for sub, glob in (("cmd", "commands/*.md"), ("agent", "agents/*.md")):
            for p in sorted(path.glob(glob)):
                t = COUNT(f"{p.stem}: {frontmatter_description(read(p))}")
                plug += t
                items.append((f"plugin:{name}/{sub}:{p.stem}", t, "plugins"))
    parts["плагины (навыки/команды/агенты)"] = plug

    # 4. Агенты и команды
    for group, glob in (("agents", "agents/*.md"), ("commands", "commands/*.md")):
        total = 0
        for p in sorted(CLAUDE.glob(glob)):
            t = COUNT(f"{p.stem}: {frontmatter_description(read(p))}")
            total += t
            items.append((f"{group[:-1]}:{p.stem}", t, group))
        parts[f"{group}/"] = total

    own_skills = {p.parent.name for p in (CLAUDE / "skills").glob("*/SKILL.md")}
    ghost = sorted(k for k in ov if k not in own_skills and k not in plugin_skills)
    plugin_ov = sorted(k for k in ov if k not in own_skills and k in plugin_skills)

    return {
        "ghost_overrides": ghost,
        "plugin_overrides": plugin_ov,
        "parts": parts,
        "items": items,
        "memory_note": note,
        "memory_dropped": dropped,
        "hidden_skills": hidden,
        "author_hidden": author_off,
        "method": METHOD,
        "total": sum(parts.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=20, help="сколько самых дорогих единиц показать")
    ap.add_argument("--json", action="store_true", help="машинный вывод для сравнения до/после")
    a = ap.parse_args()

    d = collect()
    if a.json:
        print(json.dumps({k: v for k, v in d.items() if k != "items"}, ensure_ascii=False, indent=2))
        return 0

    print(f"Способ подсчёта: {d['method']}\n")
    print("=== Что грузится в КАЖДЫЙ запрос ===")
    width = max(len(k) for k in d["parts"])
    for k, v in sorted(d["parts"].items(), key=lambda kv: -kv[1]):
        share = v / d["total"] * 100 if d["total"] else 0
        print(f"  {k:<{width}}  {v:>7,} ток  {share:5.1f}%".replace(",", " "))
    print(f"  {'ИТОГО':<{width}}  {d['total']:>7,} ток".replace(",", " "))

    print(f"\nMEMORY.md: {d['memory_note']}")
    if d["memory_dropped"]:
        print(f"  ⚠️  за лимитом молча теряется ~{d['memory_dropped']} ток указателей — "
              f"ужать: python ~/.claude/scripts/memory_fit.py")
    if d["hidden_skills"]:
        print(f"Скрыто через skillOverrides (name-only): {d['hidden_skills']} навыков — "
              f"их описания в промпт не идут, но вызвать их по-прежнему можно.")
    if d["author_hidden"]:
        print(f"Скрыто шапкой автора (disable-model-invocation): {d['author_hidden']} — "
              f"модель их НЕ видит и позвать НЕ может, только /имя.")
    if d["ghost_overrides"]:
        print(
            "  ⚠️  skillOverrides ссылается на несуществующие навыки — запись молча "
            "не делает ничего, а выглядит как сделанная экономия:\n     "
            + ", ".join(d["ghost_overrides"])
        )
    if d["plugin_overrides"]:
        print(
            "  ⚠️  skillOverrides на навыки ПЛАГИНОВ не действуют (CLI их не читает для "
            "source=plugin) — описания всё равно в промпте; рычаг один — выключить плагин:\n     "
            + ", ".join(d["plugin_overrides"])
        )

    print(f"\n=== Топ-{a.top} самых дорогих единиц ===")
    for name, tok, _ in sorted(d["items"], key=lambda x: -x[1])[: a.top]:
        print(f"  {tok:>6} ток  {name}")

    print(
        "\nЧто с этим делать:\n"
        "  • правило, нужное редко → config/rules-ref/, читать по требованию;\n"
        "  • навык из семейства, который зовут раз в квартал → skillOverrides: name-only,\n"
        "    но обязательно перенеси его сценарии на видимый вход (строка в роутинге),\n"
        "    иначе он перестанет находиться вовсе;\n"
        "  • плагин, которым не пользуешься → false в enabledPlugins: уносит разом\n"
        "    все свои навыки, команды, агентов и MCP.\n"
        "Сравнивать до/после: --json в файл и diff."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
