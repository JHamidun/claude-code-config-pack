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

ПРО ВЕРСИЮ БИБЛИОТЕКИ. Первая редакция была написана на низкоуровневом API
(`mcp.server.Server` + декораторы `@app.list_tools()`), который живёт в mcp 1.x.
В mcp 2.0 — а именно это колесо едет в пакете офлайн — декораторов у Server больше
нет, и сервер падал на импорте, не отдав ни одного инструмента. Причём проверка вида
«импорты прошли» этого НЕ ловит: имена на месте, атрибутов нет. Поэтому здесь взят
API, одинаковый в обеих версиях: `add_tool(fn, name=…, description=…)` и
`run(transport="stdio")`. Различается только путь импорта класса.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

try:                                            # mcp 2.x
    from mcp.server import MCPServer as _ServerClass
except ImportError:                             # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _ServerClass

ENGINE = Path.home() / ".claude" / "scripts" / "memory_graph.py"
TIMEOUT_SEC = 120


def engine_missing() -> str | None:
    """Сообщение, если запускать нечего. Пустой граф — это НЕ ошибка, а вот
    отсутствие движка означает неполную установку, и молчать об этом нельзя."""
    if not ENGINE.exists():
        return (f"Движок графа не найден: {ENGINE}\n"
                f"Похоже, конфиг разложен не полностью — переустанови его целиком.")
    if not shutil.which(sys.executable or "python"):
        return "Не нашёл интерпретатор Python для запуска движка графа."
    return None


def run_engine(*argv: str) -> str:
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


def _number(value: str, what: str) -> str | None:
    """Позиционное число для движка. Отсекаем здесь, а не там: движок на int('abc')
    упал бы трейсбеком, а клиенту нужен ответ, который можно прочитать."""
    v = (value or "").strip()
    if not v:
        return None
    if not v.isdigit():
        raise ValueError(f"{what} должно быть целым числом, получено: {value!r}")
    return v


# --- команды движка ---------------------------------------------------------
# По одной функции на команду: описание инструмента и схема аргументов строятся
# из подписи и docstring, поэтому расхождение «инструмент есть, а команды нет»
# становится невозможным — обе стороны берутся из одного места.

def graph_build() -> str:
    """Пересобрать граф из заметок памяти. Безопасно повторять."""
    return run_engine("build")


def graph_stats() -> str:
    """Сколько узлов, рёбер, типов и битых ссылок."""
    return run_engine("stats")


def graph_neighbors(name: str, depth: str = "") -> str:
    """Соседи узла. depth — глубина обхода (число), по умолчанию 1."""
    d = _number(depth, "depth")
    return run_engine("neighbors", name, *( [d] if d else [] ))


def graph_path(from_node: str, to_node: str) -> str:
    """Кратчайший путь между двумя узлами."""
    return run_engine("path", from_node, to_node)


def graph_timeline(name: str) -> str:
    """Цепочка «что считали верным и когда» для узла."""
    return run_engine("timeline", name)


def graph_hubs(top: str = "") -> str:
    """Самые связанные узлы. top — сколько показать (число)."""
    t = _number(top, "top")
    return run_engine("hubs", *( [t] if t else [] ))


def graph_orphans() -> str:
    """Узлы без единой связи."""
    return run_engine("orphans")


def graph_search(query: str) -> str:
    """Узлы, в имени или заголовке которых есть подстрока."""
    return run_engine("search", query)


def graph_cases(query: str) -> str:
    """Кейсы (прошлые сессии) по проекту или подстроке названия."""
    text = run_engine("cases", query)
    # «-- 0 кейсов» на чистой машине — штатная ситуация: кейсбук это отдельный слой
    # поверх заметок, и на свежей установке его нет. Голая цифра выглядит как
    # поломка, поэтому поясняем словами.
    if text.strip() == "-- 0 кейсов":
        text += ("\nКейсбук не собран или по запросу ничего не нашлось. "
                 "Граф заметок работает и без него — это не ошибка.")
    return text


def graph_dangling() -> str:
    """Ссылки на заметки, которых ещё нет — кандидаты дописать."""
    return run_engine("dangling")


def graph_gaps() -> str:
    """Разрывы: одинокие узлы, битые ссылки, залежавшиеся хабы."""
    return run_engine("gaps")


TOOLS = (graph_build, graph_stats, graph_neighbors, graph_path, graph_timeline,
         graph_hubs, graph_orphans, graph_search, graph_cases, graph_dangling,
         graph_gaps)

app = _ServerClass("graph-memory")
for _fn in TOOLS:
    app.add_tool(_fn, name=_fn.__name__, description=(_fn.__doc__ or "").strip())


if __name__ == "__main__":
    app.run(transport="stdio")
