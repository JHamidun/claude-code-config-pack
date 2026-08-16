#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Граф памяти как MCP-сервер — поверх ~/.claude/scripts/memory_graph.py.

ЗАЧЕМ ЭТОТ ФАЙЛ. В конфиге была запись MCP «graph-memory», которая указывала на
graph-memory/mcp_server.py — сервер к FalkorDB, оставшийся от прежней схемы. В пакете
его нет и быть не может, поэтому у всех, кто ставил конфиг, эта запись молча не
поднималась: инструмент «есть» в настройках, а инструментов от него ноль.

При этом сам движок графа в пакете ЕСТЬ — scripts/memory_graph.py, локальный SQLite,
без внешних служб. Не хватало только обёртки, которая отдаёт его команды в Claude Code
как инструменты. Она перед вами.

ЧТО ВАЖНО ПРО ДАННЫЕ. Здесь нет ничьей памяти и никаких ключей. Граф строится из
заметок ТОГО, КТО ЗАПУСТИЛ, — ~/.claude/projects/<проект>/memory/*.md, — а база
создаётся пустой при первом `build` в ~/.claude/memory-graph/graph.db. На чистой
машине сервер честно ответит «заметок пока нет», и это правильный ответ, а не ошибка.

Движок вызывается отдельным процессом намеренно: он самодостаточен и уже покрыт
своими проверками, а импорт его как модуля потянул бы за собой глобальное состояние
и превратил бы одну поломку в две.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

ENGINE = Path.home() / ".claude" / "scripts" / "memory_graph.py"
TIMEOUT_SEC = 120

# Команда -> (описание, обязательные аргументы). Ровно то, что умеет движок: список
# держим здесь, чтобы расхождение «инструмент есть, команды нет» было видно сразу.
COMMANDS = {
    "build":     ("Пересобрать граф из заметок памяти (безопасно повторять).", []),
    "stats":     ("Сколько узлов, рёбер, типов и битых ссылок.", []),
    "neighbors": ("Соседи узла. Второй аргумент — глубина, по умолчанию 1.", ["name"]),
    "path":      ("Кратчайший путь между двумя узлами.", ["from", "to"]),
    "timeline":  ("Цепочка «что считали верным и когда» для узла.", ["name"]),
    "hubs":      ("Самые связанные узлы. Аргумент — сколько показать.", []),
    "orphans":   ("Узлы без единой связи.", []),
    "search":    ("Узлы, в имени или заголовке которых есть подстрока.", ["query"]),
    "cases":     ("Кейсы (прошлые сессии) по проекту или подстроке названия. Берутся из "
                  "кейсбука — опционального слоя поверх заметок; на свежей установке его "
                  "нет, и «0 кейсов» — нормальный ответ, а не поломка.", ["query"]),
    "dangling":  ("Ссылки на заметки, которых ещё нет — кандидаты дописать.", []),
    "gaps":      ("Разрывы: одинокие узлы, битые ссылки, залежавшиеся хабы.", []),
}


def engine_missing() -> str | None:
    """Сообщение, если запускать нечего. Пустой граф — это НЕ ошибка, а вот
    отсутствие движка означает неполную установку, и молчать об этом нельзя."""
    if not ENGINE.exists():
        return (f"Движок графа не найден: {ENGINE}\n"
                f"Похоже, конфиг разложен не полностью — переустанови его целиком.")
    if not shutil.which(sys.executable or "python"):
        return "Не нашёл интерпретатор Python для запуска движка графа."
    return None


def run_engine(argv: list[str]) -> str:
    problem = engine_missing()
    if problem:
        return problem
    try:
        p = subprocess.run(
            [sys.executable, str(ENGINE), *argv],
            capture_output=True, text=True, timeout=TIMEOUT_SEC,
            encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return f"Движок графа не ответил за {TIMEOUT_SEC} с — команда прервана."
    except Exception as e:  # noqa: BLE001
        return f"Не удалось запустить движок графа: {type(e).__name__}: {e}"

    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if p.returncode != 0:
        # Код возврата важнее пустого stdout: без него «ошибка» выглядела бы как
        # «просто ничего не нашлось».
        return f"Движок вернул код {p.returncode}.\n{err or out or '(без вывода)'}"
    if not out:
        return "Пусто. Если граф ещё не собирали — выполни build."
    return out


app = Server("graph-memory")


@app.list_tools()
async def list_tools() -> list[Tool]:
    tools = []
    for name, (desc, required) in COMMANDS.items():
        props = {}
        for arg in required:
            props[arg] = {"type": "string", "description": f"Аргумент «{arg}»"}
        if name in ("neighbors", "hubs"):
            props["limit"] = {"type": "string",
                              "description": "Число: для neighbors — глубина обхода, для hubs — размер топа"}
        tools.append(Tool(
            name=f"graph_{name}",
            description=desc,
            inputSchema={"type": "object", "properties": props, "required": required},
        ))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    cmd = name[len("graph_"):] if name.startswith("graph_") else name
    if cmd not in COMMANDS:
        return [TextContent(type="text", text=f"Неизвестная команда: {cmd}")]

    _, required = COMMANDS[cmd]
    argv = [cmd]
    for arg in required:
        val = (arguments or {}).get(arg)
        if not val:
            return [TextContent(type="text", text=f"Не хватает аргумента «{arg}» для {cmd}.")]
        argv.append(str(val))
    # limit — это ПОЗИЦИОННЫЙ аргумент движка, и есть он не у всех команд: neighbors
    # читает его как глубину, hubs — как размер топа. Остальным лишний позиционный
    # аргумент ломает вызов (например, search принимает ровно один — был бы TypeError
    # с трейсбеком вместо результата), поэтому для них limit не пробрасываем вовсе.
    if cmd in ("neighbors", "hubs"):
        limit = str((arguments or {}).get("limit") or "").strip()
        if limit:
            if not limit.isdigit():
                # Отсекаем здесь, а не в движке: движок на int('abc') упал бы
                # трейсбеком, а клиенту нужен ответ, который можно прочитать.
                return [TextContent(type="text",
                                    text=f"limit должен быть целым числом, получено: {limit!r}")]
            argv.append(limit)

    text = run_engine(argv)
    # «-- 0 кейсов» на чистой машине — штатная ситуация (кейсбука может не быть),
    # но голая цифра выглядит как поломка. Поясняем словами, чтобы не пугать.
    if cmd == "cases" and text == "-- 0 кейсов":
        text += ("\nКейсбук не собран или по запросу ничего не нашлось. "
                 "Граф заметок работает и без него — это не ошибка.")
    return [TextContent(type="text", text=text)]


async def main() -> None:
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
