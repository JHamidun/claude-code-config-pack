# 3D-воркспейс: сборка runtime и подключение

Шаблон папки, в которой Claude Code работает с 3D и CAD локально: **CadQuery** (параметрические
тела в миллиметрах, экспорт STEP/STL/SVG) и **Blender** (сцена, импорт сетки, рендер) — оба как
MCP-серверы по stdio. Платной CAD-лицензии, ключей и облака не нужно.

Серверы подключаются только в этой папке, а не глобально: их старт долгий, и таймаут старта MCP
поднимается только здесь. Проверено на Windows 11, Blender 5.2.1 LTS, CPython 3.12.11 (uv 0.9.13).
macOS и Linux описаны ниже, но не проверялись.

## Что в шаблоне

| Файл | Зачем |
| --- | --- |
| `.mcp.json` | два сервера: `blender` и `cadquery`; путь к Blender — `BLENDER_PATH` |
| `.claude/settings.json` | `MCP_TIMEOUT=300000` (5 мин на старт) + deny на 17 GUI-инструментов Blender |
| `.claude/settings.local.json` | `enabledMcpjsonServers` — оба сервера одобрены заранее (установщик пака его не раскладывает, см. раздел 3) |
| `CLAUDE.md` | правила папки: миллиметры, масштаб 0.001, папки заданий, только `*_for_cli` |
| `tools/accept_local3d.py` | приёмочный тест всей связки CadQuery → Blender |
| `setup/dependencies-only.lock.txt` | точные версии зависимостей без самих MCP-серверов |
| `setup/requirements.lock.txt` | полный снимок окружения, серверы — git-ссылками на те же коммиты |
| `setup/blender-windows-stdin.patch` | патч Blender MCP для Windows (см. ниже) |
| `examples/` | `mounting_plate.py` (код CadQuery) и результат: `.step`, `.stl`, `.svg`, `.blend`; `starter.blend` — стартовая сцена |

## 1. Что поставить заранее

- **Blender 5.2 LTS** — <https://www.blender.org/download/> . На Windows по умолчанию
  `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`.
- **uv** — <https://docs.astral.sh/uv/> (он же скачает Python 3.12, если его нет).
- **git**.

## 2. Исходники: апстрим на закреплённых коммитах

| Сервер | Репозиторий | Коммит | Пакет |
| --- | --- | --- | --- |
| Blender MCP (официальный, Blender Lab) | <https://projects.blender.org/lab/blender_mcp> | `ff54e4d8f6b09502f2f466189cca0e52b4a91643` | `blender-mcp` 1.0.2, подпапка `mcp/` |
| CadQuery MCP | <https://github.com/CadQuery/cadquery-contrib> | `06b5e50a87fcf6808859f33d84e224fce675f8d7` | `cadquery-mcp` 0.1.0, подпапка `mcp-server/`; CadQuery 2.8.0 |

Runtime живёт отдельно от шаблона: `~/.claude/tools/local-3d/` с подпапками `src/` (чекауты) и
`runtime/` (venv). Ниже `TPL` — папка этого шаблона; после установки пака это
`~/.claude/templates/3d-workspace`.

**Windows (PowerShell):**

```powershell
$L3D = "$env:USERPROFILE\.claude\tools\local-3d"
$TPL = "$env:USERPROFILE\.claude\templates\3d-workspace"
New-Item -ItemType Directory -Force "$L3D\src" | Out-Null

git clone https://projects.blender.org/lab/blender_mcp.git "$L3D\src\blender_mcp"
git -C "$L3D\src\blender_mcp" checkout ff54e4d8f6b09502f2f466189cca0e52b4a91643
git clone https://github.com/CadQuery/cadquery-contrib.git "$L3D\src\cadquery-contrib"
git -C "$L3D\src\cadquery-contrib" checkout 06b5e50a87fcf6808859f33d84e224fce675f8d7

# патч — ДО установки, чтобы в venv попала исправленная копия
git -C "$L3D\src\blender_mcp" apply --check "$TPL\setup\blender-windows-stdin.patch"
git -C "$L3D\src\blender_mcp" apply "$TPL\setup\blender-windows-stdin.patch"

uv venv --python 3.12 "$L3D\runtime"
uv pip install --python "$L3D\runtime\Scripts\python.exe" -r "$TPL\setup\dependencies-only.lock.txt"
uv pip install --python "$L3D\runtime\Scripts\python.exe" --no-deps "$L3D\src\blender_mcp\mcp" "$L3D\src\cadquery-contrib\mcp-server"

# патч действительно в установленной копии:
Select-String -Path "$L3D\runtime\Lib\site-packages\blmcp\tools_helpers\blender_cli.py" -Pattern "stdin=subprocess.DEVNULL"
```

**macOS / Linux (bash):**

```bash
L3D=~/.claude/tools/local-3d
TPL=~/.claude/templates/3d-workspace
mkdir -p "$L3D/src"

git clone https://projects.blender.org/lab/blender_mcp.git "$L3D/src/blender_mcp"
git -C "$L3D/src/blender_mcp" checkout ff54e4d8f6b09502f2f466189cca0e52b4a91643
git clone https://github.com/CadQuery/cadquery-contrib.git "$L3D/src/cadquery-contrib"
git -C "$L3D/src/cadquery-contrib" checkout 06b5e50a87fcf6808859f33d84e224fce675f8d7
git -C "$L3D/src/blender_mcp" apply "$TPL/setup/blender-windows-stdin.patch"   # безвреден и здесь

uv venv --python 3.12 "$L3D/runtime"
grep -v '^pywin32' "$TPL/setup/dependencies-only.lock.txt" > "$L3D/deps.txt"   # pywin32 — только Windows
uv pip install --python "$L3D/runtime/bin/python" -r "$L3D/deps.txt"
uv pip install --python "$L3D/runtime/bin/python" --no-deps "$L3D/src/blender_mcp/mcp" "$L3D/src/cadquery-contrib/mcp-server"
grep -n "stdin=subprocess.DEVNULL" "$L3D"/runtime/lib/python3.12/site-packages/blmcp/tools_helpers/blender_cli.py
```

Готовые серверы: `runtime/Scripts/blender-mcp.exe` и `runtime/Scripts/cadquery-mcp.exe` на Windows,
`runtime/bin/blender-mcp` и `runtime/bin/cadquery-mcp` на macOS/Linux.

### Про Windows-патч

Апстримный запуск Blender (`run_blender_cli` в `mcp/blmcp/tools_helpers/blender_cli.py`) на Windows
зависал, но только при вызове через MCP (по всей видимости, дочерний Blender наследовал stdin
сервера, по которому идёт сам протокол). Патч добавляет одну строку — `stdin=subprocess.DEVNULL`
в `subprocess.run(...)`.
После него весь цикл «создать → импортировать → сохранить → отрендерить» прошёл. Пересобираешь
runtime — накладывай патч заново.

Если ставил серверы не из чекаутов, а по `setup/requirements.lock.txt` (там они git-ссылками без
патча), наложи его прямо на установленную копию, из папки `~/.claude/tools/local-3d`:

```bash
git apply -p2 --directory=runtime/Lib/site-packages "$TPL/setup/blender-windows-stdin.patch"                  # Windows
git apply -p2 --directory=runtime/lib/python3.12/site-packages "$TPL/setup/blender-windows-stdin.patch"       # macOS/Linux
```

## 3. Папка для работы

Скопируй шаблон в любую рабочую папку и запускай Claude Code из неё:

```powershell
Copy-Item -Recurse "$env:USERPROFILE\.claude\templates\3d-workspace" "$env:USERPROFILE\3d"
```

```bash
cp -r ~/.claude/templates/3d-workspace ~/3d
```

Дальше две правки в `.mcp.json`:

1. **`BLENDER_PATH`** — путь к твоему `blender.exe`/`blender`. В шаблоне стоит путь установки
   Blender 5.2 на Windows по умолчанию. Если ключ убрать, сервер ищет `blender` в `PATH`.
2. **Только macOS/Linux** — команды серверов. В шаблоне Windows-вариант через `${USERPROFILE}`
   (Claude Code подставляет переменные окружения в `command`, `args` и `env`). Для macOS/Linux:

```json
{
  "mcpServers": {
    "blender": {
      "type": "stdio",
      "command": "${HOME}/.claude/tools/local-3d/runtime/bin/blender-mcp",
      "args": [],
      "env": { "BLENDER_PATH": "/Applications/Blender.app/Contents/MacOS/Blender" }
    },
    "cadquery": {
      "type": "stdio",
      "command": "${HOME}/.claude/tools/local-3d/runtime/bin/cadquery-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

(на Linux `BLENDER_PATH` обычно `/usr/bin/blender` или путь к распакованному архиву).

**Одобрение серверов.** Серверы из `.mcp.json` проекта Claude Code запускает только после
одобрения. `.claude/settings.local.json` в шаблоне одобряет оба (`enabledMcpjsonServers`). Но
установщик пака (`install.sh` / `install.ps1`) файлы с именем `settings.local.json` не копирует
нигде — чтобы не затереть твои, — поэтому в `~/.claude/templates/3d-workspace` его не будет.
Возьми его из клона пака (`.claude/templates/3d-workspace/.claude/settings.local.json`) или создай
в рабочей папке сам:

```powershell
Set-Content -Encoding ascii "$env:USERPROFILE\3d\.claude\settings.local.json" '{ "enabledMcpjsonServers": ["blender", "cadquery"] }'
```

```bash
printf '%s\n' '{ "enabledMcpjsonServers": ["blender", "cadquery"] }' > ~/3d/.claude/settings.local.json
```

Без этого файла ничего не ломается: Claude спросит про оба сервера при первом запуске в папке.
Состояние видно в `/mcp` или через `claude mcp list`, если запустить его из этой папки.

**Время старта (замер на Windows 11):** Blender 40–100 с, CadQuery 60–175 с. Стандартного
таймаута на такое не хватает, поэтому в `.claude/settings.json` стоит `MCP_TIMEOUT=300000`.
Если в первые минуты `/mcp` показывает, что сервер ещё подключается, он просто не успел стартовать.

## 4. Как этим пользоваться

- **CadQuery** — инструменты `inspect`, `render`, `get_parameters`, `export`. Код начинается с
  `import cadquery as cq` и заканчивается `show_object(result)`. Проверены STEP, STL и SVG;
  апстрим заявляет ещё DXF, AMF, 3MF, VRML, BREP. `render` возвращает **SVG**
  (`image/svg+xml`), а не PNG.
- **Blender** — только инструменты `*_for_cli`, например `execute_blender_code_for_cli`: они
  открывают сохранённый `.blend` во временном фоновом Blender. Аддон, окно Blender, сетевой порт
  и постоянный процесс не нужны. Новую сцену начинай с копии `examples/starter.blend`.
- **Единицы.** CadQuery считает в миллиметрах, STL единиц не хранит — при импорте в Blender
  ставь масштаб 0.001 (метры).
- **Чего здесь нет:** это не AutoCAD/nanoCAD, нативного DWG нет. STEP — точные тела, STL — сетка,
  SVG — превью, `.blend` — сцена.

### Почему запрещены 17 инструментов Blender

Этим инструментам нужен аддон Blender MCP в запущенном Blender с открытым окном (скриншоты окна,
переходы по вкладкам, сводки по открытому файлу, рендер вьюпорта, выполнение кода в живом
Blender). В этой схеме нет ни окна, ни аддона, и работать они не могут. Их блокируют deny-правила в
`.claude/settings.json`:

`execute_blender_code`, `get_blendfile_summary_datablocks`, `get_blendfile_summary_missing_files`,
`get_blendfile_summary_of_linked_libraries`, `get_blendfile_summary_path_info`,
`get_blendfile_summary_usage_guess`, `get_object_detail_summary`, `get_objects_summary`,
`get_screenshot_of_area_as_image`, `get_screenshot_of_window_as_image`,
`get_screenshot_of_window_as_json`, `jump_to_tab_by_name`, `jump_to_tab_by_space_type`,
`jump_to_view3d_object_by_name`, `jump_to_view3d_object_data_by_name`,
`render_thumbnail_to_path`, `render_viewport_to_path` (все с префиксом `mcp__blender__`).

### Безопасность

Оба сервера работают локально по stdio, ключи им не передаются. venv изолирует зависимости, но не
права: `execute_blender_code_for_cli` и код CadQuery выполняют Python с правами твоего пользователя.
Чужие `.blend`, STEP и скрипты считай недоверенными: сначала читай, потом запускай. Результаты
складывай в папку задания, чужие модели без спроса не перезаписывай.

## 5. Проверка: приёмочный тест

`tools/accept_local3d.py` поднимает оба сервера так же, как Claude Code, и проверяет цепочку:
CadQuery `inspect` (пластина 80 × 50 × 6 мм, одно тело) → экспорт STEP/STL/SVG → `render` (SVG) →
Blender импортирует STL с масштабом 0.001, сохраняет `.blend` и рендерит PNG (Cycles) → размеры
тела 0.08 × 0.05 × 0.006 м. Пишет только в пустую папку `--out` и кладёт туда
`acceptance-report.json` с временем старта и sha256 каждого файла.

Запускать интерпретатором runtime (в нём есть клиент `mcp`). Прогон идёт несколько минут:

```powershell
& "$env:USERPROFILE\.claude\tools\local-3d\runtime\Scripts\python.exe" -B tools\accept_local3d.py `
  --out "$env:TEMP\3d-acceptance-1" `
  --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

```bash
~/.claude/tools/local-3d/runtime/bin/python -B tools/accept_local3d.py --out /tmp/3d-acceptance-1 --blender "$(command -v blender)"
```

Пути можно задать и переменными: `LOCAL3D_RUNTIME` (по умолчанию `~/.claude/tools/local-3d/runtime`),
`BLENDER_PATH`, `LOCAL3D_STARTER` (по умолчанию `examples/starter.blend`). Все флаги — `--help`.
Успех выглядит так: `"status": "PASS"`, `"cad_render_mime": "image/svg+xml"`,
`"dimensions_m": [0.08, 0.05, 0.006]` (порядок может отличаться).

Тесты самого CadQuery MCP (при установке автора: 27 passed, одно предупреждение апстрима):

```bash
~/.claude/tools/local-3d/runtime/bin/python -m pytest ~/.claude/tools/local-3d/src/cadquery-contrib/mcp-server/test_cadquery_mcp_server.py -q
```

(на Windows — `runtime\Scripts\python.exe`).
