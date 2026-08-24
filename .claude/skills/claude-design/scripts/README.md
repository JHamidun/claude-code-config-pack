# claude-design-mcp

MCP server для claude.ai/design через Connect-RPC API (internal RPC service (do not name publicly)).

## Tools (13 total — 8 минимум + 5 helpers)

**Минимум 8 (Phase 1):**
- `claude_design_list_projects` — список проектов (org/user scope)
- `claude_design_create_project` — создать пустой
- `claude_design_get_project` — метаданные + декодированный data blob
- `claude_design_update_project_data` — записать project state обратно
- `claude_design_delete_project` — удалить
- `claude_design_download_zip` — REST `/v1/design/projects/<id>/download`
- `claude_design_get_handoff_token` — токен для Handoff to Claude Code
- `claude_design_chat` — **Phase 2** (нужен Connect streaming envelope)

**Бонус-helpers:**
- `claude_design_list_files` / `claude_design_get_file`
- `claude_design_remix_project` (= duplicate)
- `claude_design_get_preview_url` (sandbox subdomain + signed token)
- `claude_design_get_me`

## Установка cookies

В отличие от Perplexity, нужны 4-5 cookies. Httponly `sessionKey` и
visible `__ssid`/`lastActiveOrg`/`anthropic-device-id`.

### Способ 1 — Chrome DevTools

1. Открыть https://claude.ai/design
2. F12 → Application → Cookies → `https://claude.ai`
3. Скопировать значения:
   - `sessionKey`     ← httpOnly, главный
   - `__ssid`
   - `lastActiveOrg`  ← это твой org UUID
   - `anthropic-device-id`
4. В `~/.claude/.credentials.master.env`:
   ```bash
   CLAUDE_DESIGN_COOKIES='{"sessionKey":"...","__ssid":"...","lastActiveOrg":"...","anthropic-device-id":"..."}'
   CLAUDE_DESIGN_ORG_UUID='YOUR_ANTHROPIC_ORG_UUID'
   ```

### Способ 2 — через Playwright (автоматически)

```bash
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    ctx = b.new_context()
    page = ctx.new_page()
    page.goto('https://claude.ai/design')
    input('Log in then press Enter...')
    cookies = {c['name']: c['value'] for c in ctx.cookies('https://claude.ai')}
    import json; print(json.dumps(cookies))
"
```

Скопировать вывод в `CLAUDE_DESIGN_COOKIES`.

## mcp.json

```json
"claude-design": {
  "type": "stdio",
  "command": "python",
  "args": ["/home/ИМЯ/.claude/skills/claude-design/scripts/claude_design_mcp.py"],
  "env": {
    "CLAUDE_DESIGN_COOKIES": "${CLAUDE_DESIGN_COOKIES}",
    "CLAUDE_DESIGN_ORG_UUID": "${CLAUDE_DESIGN_ORG_UUID}"
  },
  "description": "Claude Design (claude.ai/design) — Connect-RPC client. Read/write projects, download ZIP, handoff."
}
```

Путь до скрипта — **абсолютный, целиком**: ни `~`, ни `${HOME}` в JSON никто не разворачивает,
а `HOME` на Windows обычно не заведён вовсе (там `USERPROFILE`). Неразвёрнутый путь даёт
`can't open file` в логе MCP, а в `/mcp` сервер выглядит просто отсутствующим.
Windows-форма: `C:/Users/ИМЯ/.claude/skills/claude-design/scripts/claude_design_mcp.py`.

## Smoke test

```bash
export CLAUDE_DESIGN_COOKIES='{...}'
export CLAUDE_DESIGN_ORG_UUID='YOUR_ANTHROPIC_ORG_UUID'
python -c "
from claude_design_client import get_me, list_projects
print(get_me())
print(f'Total projects: {len(list_projects())}')
"
```

## Известные ограничения

- **Chat пока не работает** (Phase 2) — нужен Connect streaming envelope decoder
- Cookies истекают раз в N дней — обновляй когда `failed_precondition`
- Examples gallery — lazy-loaded, ID не в bundle (можно отдельно через UI клики)
