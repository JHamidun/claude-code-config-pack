# 3D-воркспейс: Blender + CadQuery через MCP

Здесь — и только здесь — подключены два локальных MCP (`.mcp.json`): `cadquery` (параметрический CAD)
и `blender` (Blender 5.2 LTS, проверено на 5.2.1, в фоновом режиме, инструменты `*_for_cli`). Глобально их нет: старт
Blender 40–100 с, CadQuery 60–175 с, поэтому таймаут старта MCP (300 с) поднят только в этой папке
(`.claude/settings.json`). Сборка runtime и подключение — `SETUP.md`.

- Каждое задание — своя папка `jobs/<ГГГГ-ММ-ДД>-<slug>/`; чужие модели не перезаписывать.
- CadQuery считает в **миллиметрах**; STL не хранит единицы — при импорте в Blender масштаб **0.001**.
  STEP — точная геометрия, STL — сетка, `.blend` — сцена. DWG/AutoCAD не обещаны, DXF не проверяли.
- Код для CadQuery: `import cadquery as cq` в начале, `show_object(result)` в конце. Инструменты:
  `inspect`, `render` (отдаёт SVG, не PNG), `get_parameters`, `export`.
- Blender: только `*_for_cli` (временный фоновый процесс + .blend-файл). 17 GUI-инструментов,
  которым нужен аддон с открытым окном, запрещены deny-правилами.
- Новую сцену начинать с копии `examples/starter.blend` в папку задания; сам стартер не перезаписывать.
- Оба сервера выполняют Python с правами пользователя — сторонние скрипты читать до запуска.
- Runtime и исходники: `~/.claude/tools/local-3d/` (`runtime/` и `src/`, собираются по `SETUP.md`);
  Windows-патч `stdin=DEVNULL` в `blmcp/tools_helpers/blender_cli.py` — `setup/blender-windows-stdin.patch`.
- Проверка связки целиком: `tools/accept_local3d.py` (команда запуска — в `SETUP.md`).
