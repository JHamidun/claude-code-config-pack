---
name: figma-api
description: "Figma REST API по своему токену: браузинг команды и проектов, чтение файлов и текста, экспорт фреймов в PNG, комментарии, Variables. Триггеры: «что в фигме», «скриншот фрейма», «вытащи текст из макета». НЕ генерация кода из дизайна → плагин figma."
---

# Figma API Skill

> Direct Figma REST API access for reading, browsing, and modifying designs.

## Что тебе понадобится

**`FIGMA_ACCESS_TOKEN` — свой личный токен.** Бесплатного аккаунта Figma достаточно:
токен даётся на любом тарифе, отдельной оплаты за REST API нет.

1. <https://www.figma.com/settings> → **Personal access tokens** → *Generate new token*
2. Скоупы: для чтения хватит `file_content:read` + `file_comments:read`;
   для комментариев и Variables добавь `file_comments:write`, `file_variables:write`.
3. Положи в переменные окружения или в свой `~/.claude/.credentials.master.env`
   (образец — `~/.claude/templates/.credentials.master.env.example`):

```
FIGMA_ACCESS_TOKEN=figd_твой_токен
FIGMA_TEAM_ID=1234567890123456789
```

`FIGMA_TEAM_ID` нужен только команде `projects` (число из URL твоей команды —
см. раздел «Свои ID: где взять» ниже). Не задан — команда честно скажет об этом,
остальные работают и без него.

Токен даёт доступ ко ВСЕМ твоим файлам Figma — в репозиторий и в чужие руки не попадает.

## When to Use

- "зайди в фигму", "что в фигме", "покажи файлы фигмы"
- "прочитай дизайн", "какие страницы", "листы в фигме"
- "скопируй блок", "измени текст в фигме"
- "экспортируй из фигмы", "скриншот фрейма"
- Any Figma file/project/team browsing

## Important

The **Figma plugin** (`figma@claude-plugins-official`) provides ONLY development skills:
- `figma:implement-design` — translate Figma to code
- `figma:code-connect-components` — connect components
- `figma:create-design-system-rules` — generate design rules

For **reading/browsing/modifying** Figma files, use **direct API calls** via Python.

## Authentication

```python
import os

TOKEN = os.getenv("FIGMA_ACCESS_TOKEN")
if not TOKEN:
    raise SystemExit(
        "FIGMA_ACCESS_TOKEN не задан. Возьми токен на "
        "https://www.figma.com/settings -> Personal access tokens"
    )
# 403 Token expired -> перевыпусти там же. Токены Figma не вечные.
```

Готовый CLI без написания кода — `~/.claude/tools/figma_api.py`
(`me`, `projects`, `files`, `pages`, `tree`, `text`, `export`, `parse-url`).
Он читает тот же `FIGMA_ACCESS_TOKEN` из окружения.

## Свои ID: где взять

Скилл ничего не знает о твоём аккаунте — всё берётся за один вызов и из URL браузера.

| Что | Откуда |
|---|---|
| **User ID**, имя аккаунта | `GET /me` — первый же вызов, проверка что токен живой |
| **Team ID** | открой команду в Figma: `figma.com/files/team/<TEAM_ID>/...` — число в URL |
| **Project ID** | `GET /teams/{team_id}/projects` (рецепт «List all team projects» ниже) |
| **File key** | из URL файла: `figma.com/design/<FILE_KEY>/Name?node-id=534-901` |
| **Node ID** | из того же URL, `node-id=534-901`; в API он пишется `534:901` |

```bash
python ~/.claude/tools/figma_api.py me         # проверить токен
python ~/.claude/tools/figma_api.py projects   # список проектов команды
```

## API Endpoints Reference

Base URL: `https://api.figma.com/v1/`

### Read Operations

| Endpoint | Description |
|----------|-------------|
| `GET /me` | Current user info |
| `GET /teams/{team_id}/projects` | List team projects |
| `GET /projects/{project_id}/files` | List files in project |
| `GET /files/{file_key}?depth=N` | Get file structure (depth 1 = pages only) |
| `GET /files/{file_key}/nodes?ids=X&depth=N` | Get specific nodes with children |
| `GET /images/{file_key}?ids=X&format=png` | Export nodes as images |
| `GET /files/{file_key}/comments` | Get file comments |
| `GET /files/{file_key}/versions` | Get file version history |
| `GET /files/{file_key}/components` | Get published components |
| `GET /files/{file_key}/styles` | Get published styles |

### Write Operations (Figma REST API)

| Endpoint | Description |
|----------|-------------|
| `POST /files/{file_key}/comments` | Add comment |
| `DELETE /files/{file_key}/comments/{comment_id}` | Delete comment |

### Write Operations (Figma Plugin API — NOT REST)

Figma REST API is **read-heavy**. To modify designs (add/copy/edit nodes), you need:
1. **Figma Plugin API** (runs inside Figma desktop/browser)
2. **Figma Variables REST API** (for variables/tokens only)

For text modifications: export → modify externally → re-import, or use Figma Plugin.

## URL Parsing

```python
import re

def parse_figma_url(url):
    """Extract file_key, node_id, team_id from Figma URL."""
    # File: figma.com/design/FILE_KEY/Name?node-id=X-Y
    file_match = re.search(r'figma\.com/(?:design|file)/([a-zA-Z0-9]+)', url)
    node_match = re.search(r'node-id=([0-9]+-[0-9]+)', url)
    team_match = re.search(r'team/([0-9]+)', url)

    return {
        'file_key': file_match.group(1) if file_match else None,
        'node_id': node_match.group(1) if node_match else None,
        'team_id': team_match.group(1) if team_match else None,
    }

# Examples:
# figma.com/design/AbCdEf123456/Name?node-id=534-901 → file_key=AbCdEf123456, node_id=534-901
# figma.com/files/team/1234567890123456789/recents  → team_id=1234567890123456789
```

## Python Helper Pattern

```python
import urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')  # CRITICAL on Windows!

def figma_get(path, token):
    """GET request to Figma API."""
    req = urllib.request.Request(f'https://api.figma.com/v1/{path}')
    req.add_header('X-Figma-Token', token)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode('utf-8'))

# IMPORTANT: Always use `python -X utf8` on Windows to avoid encoding issues
```

## Common Recipes

### List all team projects
```python
projects = figma_get(f'teams/{TEAM_ID}/projects', TOKEN)
for p in projects['projects']:
    print(f"{p['name']} (id: {p['id']})")
```

### List files in a project
```python
files = figma_get(f'projects/{PROJECT_ID}/files', TOKEN)
for f in files['files']:
    print(f"{f['name']} (key: {f['key']}, modified: {f['last_modified'][:10]})")
```

### Get file pages (листы)
```python
data = figma_get(f'files/{FILE_KEY}?depth=1', TOKEN)
for page in data['document']['children']:
    print(f"{page['name']} (id: {page['id']})")
```

### Read all text from a page
```python
data = figma_get(f'files/{FILE_KEY}/nodes?ids={NODE_ID}&depth=10', TOKEN)

def extract_text(node, indent=0):
    if node.get('characters'):
        print(f"{'  '*indent}{node['name']}: {node['characters'][:100]}")
    for child in node.get('children', []):
        extract_text(child, indent+1)

node = data['nodes'][NODE_ID.replace('-', ':')]['document']
extract_text(node)
```

### Export frame as PNG
```python
data = figma_get(f'images/{FILE_KEY}?ids={NODE_ID}&format=png&scale=2', TOKEN)
image_url = data['images'][NODE_ID.replace('-', ':')]
# Download image_url with urllib
```

### Print full node tree
```python
def print_tree(node, indent=0):
    t = node.get('type', '')
    name = node.get('name', '')
    chars = node.get('characters', '')
    prefix = '  ' * indent
    if chars:
        display = chars[:120].replace('\n', ' | ')
        print(f'{prefix}{t}: "{name}" => "{display}"')
    else:
        print(f'{prefix}{t}: "{name}"')
    for c in node.get('children', []):
        print_tree(c, indent + 1)
```

## Свой справочник проектов и файлов

Поиска по файлам в API нет (см. Limitations), поэтому ходовые ID удобно один раз
выписать себе — иначе каждый запуск начинается с двух лишних вызовов.

Сделай себе табличку и держи её **вне пака** (`~/.claude/figma-ids.md`), чтобы она
не уехала вместе с конфигом, если ты им с кем-то поделишься:

```markdown
| Project | ID         |
|---------|------------|
| <твой>  | 2405…      |

| File    | Key        | Что это |
|---------|------------|---------|
| <твой>  | AbCdEf…    | брендбук |
```

Заполняется выводом `python ~/.claude/tools/figma_api.py projects`.

## Windows Gotchas

1. **Always** use `python -X utf8` flag for Russian text
2. **Always** add `sys.stdout.reconfigure(encoding='utf-8')` at script start
3. `chcp 65001` does NOT work in bash shell — use Python flag instead
4. Node IDs use `:` in API but `-` in URLs (e.g., `534:901` vs `534-901`)
5. `depth=1` returns only direct children (pages), `depth=10` for full tree
6. `?depth=0` in `/files/` returns no children at all — just metadata

## References (merged skills, 2026-07-18)

- `references/figma-import/SKILL.md` — ex-скилл **figma-import**: Figma-файл как референс (структура фреймов, цвета, типографика, PNG-превью, tokens.css); скрипт `references/figma-import/templates/figma-pull.mjs`; расширенная legacy-версия (styles→CSS токены-трансформ, components, антипаттерны) — `references/figma-import/references/legacy-figma-import.md`. Читай когда дали ссылку на Figma и надо «сделать как тут» / взять токены.
- `references/figma-write-back/SKILL.md` — ex-скилл **figma-write-back**: постинг комментариев в Figma (comment.mjs), обновление Variables из HTML (update-vars.mjs), pre-push hook, workflow «HTML как source-of-truth», этика и антипаттерны. Читай когда надо держать дизайнера в курсе правок HTML.

## Limitations

- **No `/me/files` endpoint** — must go through teams → projects → files
- **No file search** — browse by team/project only
- **REST API is read-mostly** — can't create/move/copy nodes
- **Token expires** — при 403 перевыпусти токен: <https://www.figma.com/settings> → Personal access tokens → Generate new token, и обнови `FIGMA_ACCESS_TOKEN` в окружении
- **Rate limits** — respect 429 responses, add delays for batch operations
