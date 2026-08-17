#!/usr/bin/env python3
"""Починить конфигурацию Claude Code, установленную старым установщиком курса.

Две беды, обе выглядят одинаково — «Claude Code постоянно переспрашивает и тормозит»,
но причины разные и лечатся по-отдельности.

ПЕРВАЯ: режим. Установщик курса до августа прописывал режим, в котором Claude Code
спрашивает разрешение почти на каждое действие. Свежая версия ставит режим без
вопросов, но у тех, кто установил раньше, остался старый.

ВТОРАЯ: осиротевшие записи маскота. Приложение-маскот прописывает себе 14 записей
в настройки, чтобы получать уведомления о работе. Убирает оно их только через своё
меню — если окно просто закрыли, сняли процесс или перезагрузили машину, записи
остаются. Дальше каждое действие Claude Code ждёт ответа от выключенного маскота
по две секунды. Четырнадцать записей — почти полминуты ожидания на каждый шаг.

Скрипт чинит обе, сохраняя копию настроек рядом. Ничего не удаляет сверх этого:
разрешения, запреты и рабочие записи остаются как были.

    python fix_student_config.py            # посмотреть и починить
    python fix_student_config.py --check    # только посмотреть
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
LOCAL_URL = re.compile(r"https?://(?:127\.0\.0\.1|localhost|\[::1\]):(\d+)")
FREE_MODE = "bypassPermissions"


def port_alive(port: int) -> bool:
    s = socket.socket()
    s.settimeout(1.0)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def fix_mode(data: dict) -> list[str]:
    """Режим без постоянных вопросов + не переспрашивать подтверждение этого режима."""
    notes = []
    perm = data.setdefault("permissions", {})
    was = perm.get("defaultMode") or data.get("defaultMode")
    if was != FREE_MODE:
        perm["defaultMode"] = FREE_MODE
        notes.append(f"режим: {was or 'не задан'} → {FREE_MODE}")
    # Без этого при каждом запуске показывается подтверждение выбранного режима.
    if data.get("skipDangerousModePermissionPrompt") is not True:
        data["skipDangerousModePermissionPrompt"] = True
        notes.append("подтверждение режима при запуске: больше не показывается")
    # Ключ верхнего уровня остался от старых версий и спорит с permissions.defaultMode.
    if "defaultMode" in data:
        data.pop("defaultMode")
        notes.append("убран устаревший ключ режима верхнего уровня")
    return notes


def fix_hooks(data: dict) -> tuple[list[str], list[int]]:
    """Убрать записи, ведущие на локальный порт, где никто не отвечает."""
    hooks = data.get("hooks") or {}
    notes, dead_ports, kept = [], [], {}

    for event, groups in hooks.items():
        new_groups = []
        for grp in groups or []:
            keep = []
            for hk in grp.get("hooks") or []:
                url = hk.get("url", "") if isinstance(hk, dict) else ""
                m = LOCAL_URL.search(url) if url else None
                if m:
                    port = int(m.group(1))
                    if port_alive(port):
                        keep.append(hk)          # приложение работает — не трогаем
                        continue
                    dead_ports.append(port)
                    continue
                keep.append(hk)
            if keep:
                g = dict(grp)
                g["hooks"] = keep
                new_groups.append(g)
        if new_groups:
            kept[event] = new_groups

    removed = sum(len(g.get("hooks") or []) for gs in hooks.values() for g in gs or []) \
        - sum(len(g.get("hooks") or []) for gs in kept.values() for g in gs or [])
    if removed:
        data["hooks"] = kept if kept else None
        if data.get("hooks") is None:
            data.pop("hooks", None)
        notes.append(f"убрано записей на выключённое приложение: {removed} "
                     f"(экономия ~{removed * 2} с на каждом действии)")
    return notes, dead_ports


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="только посмотреть")
    ap.add_argument("--settings", type=pathlib.Path, default=SETTINGS)
    a = ap.parse_args()

    if not a.settings.exists():
        print(f"  файла настроек нет: {a.settings}")
        print("  значит Claude Code ещё не настраивался — чинить нечего")
        return 0

    try:
        data = json.loads(a.settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  настройки испорчены и не читаются: {e}")
        print("  почини файл вручную или удали его — Claude Code создаст заново")
        return 1

    before = json.dumps(data, sort_keys=True)
    notes = fix_mode(data)
    hook_notes, dead = fix_hooks(data)
    notes += hook_notes

    if json.dumps(data, sort_keys=True) == before:
        print("  всё уже в порядке, чинить нечего")
        return 0

    print("  что будет исправлено:")
    for n in notes:
        print(f"    · {n}")
    if dead:
        print(f"    (порты без ответа: {', '.join(str(p) for p in sorted(set(dead)))})")

    if a.check:
        print("\n  это была проверка — файл не изменён")
        print("  чтобы починить, запусти ту же команду без --check")
        return 0

    backup = a.settings.with_suffix(".json.bak-fix")
    shutil.copy2(a.settings, backup)
    a.settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(f"\n  готово. Копия прежних настроек: {backup.name}")
    print("  перезапусти Claude Code, чтобы изменения вступили в силу")
    return 0


if __name__ == "__main__":
    sys.exit(main())
