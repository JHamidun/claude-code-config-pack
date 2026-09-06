#!/usr/bin/env python3
"""Ставит MCP-серверы пака в ~/.claude.json — единственный файл, откуда Claude Code их читает.

Зачем отдельный скрипт. Раньше серверы лежали в `.claude/settings.json`, установщик
копировал файл целиком, и всё выглядело настроенным. Но секция `mcpServers` в
settings.json движком **не читается вовсе** — молча, без ошибки и без строки в логе.
То есть серверы не поднимались ни у кого ни разу, а диагностика уходила в сторону:
человек видел их в своём конфиге и искал причину в сервере, а не в адресе файла.

Логика слияния выбрана так, чтобы обновление пака не могло затереть чужую работу:

    сервера нет у пользователя      -> добавляем
    есть, но его положил пак        -> обновляем (при --repair)
    есть, и он пользовательский     -> НЕ трогаем никогда

Различаются они по реестру `~/.claude/.ccpack-mcp.txt`: туда пишутся имена, которые
положил именно пак. Без реестра «обновить своё, не тронув чужое» неотличимы, и любая
из двух ошибок болезненна — либо пак не обновляется, либо стирает личную настройку.

    python mcp_install.py --dry-run     что изменится, ничего не трогая
    python mcp_install.py               добавить недостающие
    python mcp_install.py --repair      плюс обновить те, что клал пак
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import time

HOME = pathlib.Path.home()
TARGET = HOME / ".claude.json"                     # канон: только отсюда читаются mcpServers
TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "mcp-servers.json"
REGISTRY = HOME / ".claude" / ".ccpack-mcp.txt"    # что положил пак — чтобы не спутать с личным


def materialise(node, home_fwd: str):
    """${HOME} -> абсолютный путь. На Windows именно прямые слеши: обратные
    в JSON пришлось бы экранировать, и одна пропущенная пара молча ломает путь."""
    if isinstance(node, str):
        return node.replace("${HOME}", home_fwd)
    if isinstance(node, list):
        return [materialise(x, home_fwd) for x in node]
    if isinstance(node, dict):
        return {k: materialise(v, home_fwd) for k, v in node.items()}
    return node


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ОШИБКА: {path} — битый JSON ({e}). Ничего не меняю, почини файл.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="показать план, ничего не менять")
    ap.add_argument("--repair", action="store_true", help="обновить и те серверы, что клал пак")
    args = ap.parse_args()

    if not TEMPLATE.exists():
        sys.exit(f"ОШИБКА: не найден шаблон {TEMPLATE}")

    home_fwd = str(HOME).replace("\\", "/")
    template = load_json(TEMPLATE).get("mcpServers", {})
    if not template:
        sys.exit(f"ОШИБКА: в {TEMPLATE} нет секции mcpServers")

    target = load_json(TARGET)
    existing = target.get("mcpServers", {})
    ours = set()
    if REGISTRY.exists():
        ours = {l.strip() for l in REGISTRY.read_text(encoding="utf-8").splitlines() if l.strip()}

    to_add, to_update, skipped = [], [], []
    for name, cfg in template.items():
        if name not in existing:
            to_add.append(name)
        elif name in ours:
            if args.repair and existing[name] != materialise(cfg, home_fwd):
                to_update.append(name)
        else:
            skipped.append(name)

    print(f"файл назначения : {TARGET}")
    print(f"добавить        : {', '.join(to_add) if to_add else '—'}")
    print(f"обновить        : {', '.join(to_update) if to_update else '—'}"
          + ("" if args.repair else "   (нужен --repair)"))
    print(f"не трогаю (твои): {', '.join(skipped) if skipped else '—'}")

    if args.dry_run:
        print("\n[dry-run] ничего не записано")
        return
    if not to_add and not to_update:
        print("\nизменений нет")
        return

    if TARGET.exists():
        backup = TARGET.with_name(f".claude.json.bak-mcp-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(TARGET, backup)
        print(f"бэкап           : {backup.name}")

    servers = dict(existing)
    for name in to_add + to_update:
        servers[name] = materialise(template[name], home_fwd)
    target["mcpServers"] = servers
    TARGET.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")

    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text("\n".join(sorted(ours | set(to_add) | set(to_update))) + "\n",
                        encoding="utf-8")

    # Записали — значит обязаны убедиться, что файл читается. Битый ~/.claude.json
    # оставляет Claude Code вообще без MCP, и заметно это далеко не сразу.
    try:
        json.loads(TARGET.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ОШИБКА: после записи {TARGET} не читается ({e}) — верни из бэкапа!")

    print(f"\nготово: серверов в {TARGET.name} теперь {len(servers)}")
    print("проверить:  claude mcp list")


if __name__ == "__main__":
    main()
