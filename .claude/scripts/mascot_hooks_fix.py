#!/usr/bin/env python3
"""Убрать зависшие хуки маскота из настроек Claude Code.

Маскот прописывает себе хуки на четырнадцать событий, чтобы реагировать на работу
Claude Code. Пока приложение запущено, это стоит доли миллисекунды. Но убирает оно
их только по команде из меню — при закрытии окна, снятии через диспетчер, падении
или перезагрузке хуки остаются в настройках навсегда.

Дальше каждый вызов любого инструмента идёт стучаться в порт, где никого нет.
Одна попытка — около двух секунд, а хуков четырнадцать. Работа становится втрое
медленнее разговора, и со стороны выглядит как «Claude Code тормозит».

Скрипт находит такие хуки по признаку «http на локальный адрес» и убирает их,
сохраняя рядом копию настроек. Живые хуки (запуск скриптов, звук, гарды) не трогает.

    python mascot_hooks_fix.py            # проверить и убрать
    python mascot_hooks_fix.py --check    # только показать, ничего не менять
    python mascot_hooks_fix.py --port 45700   # if you know the mascot's port
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import socket
import sys

SETTINGS = pathlib.Path.home() / ".claude" / "settings.json"
LOCAL = re.compile(r"https?://(?:127\.0\.0\.1|localhost|\[::1\]):(\d+)")


def alive(port: int) -> bool:
    s = socket.socket()
    s.settimeout(1.0)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def scan(data: dict, port: int | None) -> tuple[dict, list, set]:
    """Отделить хуки, стучащиеся в локальный порт, от всех остальных."""
    hooks = data.get("hooks") or {}
    removed, ports = [], set()
    kept_hooks: dict = {}

    for event, groups in hooks.items():
        new_groups = []
        for grp in groups or []:
            keep = []
            for hk in grp.get("hooks") or []:
                url = hk.get("url", "") if isinstance(hk, dict) else ""
                m = LOCAL.search(url) if url else None
                if m and (port is None or int(m.group(1)) == port):
                    ports.add(int(m.group(1)))
                    removed.append((event, url))
                    continue
                keep.append(hk)
            if keep:
                g = dict(grp)
                g["hooks"] = keep
                new_groups.append(g)
        if new_groups:
            kept_hooks[event] = new_groups

    out = dict(data)
    if kept_hooks:
        out["hooks"] = kept_hooks
    else:
        out.pop("hooks", None)
    return out, removed, ports


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="только показать")
    ap.add_argument("--port", type=int, help="убрать только этот порт")
    ap.add_argument("--settings", type=pathlib.Path, default=SETTINGS)
    a = ap.parse_args()

    if not a.settings.exists():
        raise SystemExit(f"нет файла настроек: {a.settings}")
    data = json.loads(a.settings.read_text(encoding="utf-8"))

    new, removed, ports = scan(data, a.port)
    if not removed:
        print("  зависших хуков нет — настройки чистые")
        return 0

    live = {p for p in ports if alive(p)}
    print(f"  хуков на локальный порт: {len(removed)}")
    for p in sorted(ports):
        state = "приложение ЗАПУЩЕНО" if p in live else "никого нет"
        print(f"    порт {p}: {state}")
    for ev, url in removed[:20]:
        print(f"    {ev}")

    if live:
        print("\n  часть портов живая — эти хуки работают, убирать их не надо.")
        print("  запусти с --port <мёртвый порт>, чтобы убрать только зависшие")
        return 1

    cost = len(removed) * 2.0
    print(f"\n  цена простоя: ~{cost:.0f} с на КАЖДЫЙ вызов инструмента")

    if a.check:
        print("  проверка без изменений — ничего не тронуто")
        return 0

    backup = a.settings.with_suffix(".json.bak-hooks")
    shutil.copy2(a.settings, backup)
    a.settings.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    left = sum(len(g.get("hooks") or []) for gs in (new.get("hooks") or {}).values()
               for g in gs)
    print(f"  убрано: {len(removed)}, осталось рабочих хуков: {left}")
    print(f"  копия настроек: {backup.name}")
    print("  вернуть хуки, когда маскот запущен: в трее → Install hooks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
