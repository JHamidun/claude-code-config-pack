# Toolset Catalog

> All available toolsets for Hermes and OpenClaw engines.
> Use this reference when configuring `platform_toolsets` (Hermes) or `toolsAllow` (OpenClaw cron).

---

## Hermes Toolsets

### Core Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `web` | `web_search`, `web_fetch` | Internet search and URL fetching. web_search uses Perplexity (requires PERPLEXITY_API_KEY). web_fetch retrieves page content as markdown. |
| `vision` | `analyze_image` | Analyze images sent by users. Works with photos, screenshots, documents. Model must support vision (most modern models do). |
| `memory` | `memory_search`, `memory_write` | Long-term memory via MEMORY.md. memory_search finds relevant past entries. memory_write saves new knowledge. 2200 char limit per entry. |
| `session_search` | `session_search` | Search across past conversation sessions. Finds relevant context from previous chats. Heavier than memory_search. |

### Media Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `image_gen` | `image_generate` | Generate images via configured provider (FAL, OpenAI, etc.). Requires `image_gen` config section. |
| `tts` | `text_to_speech` | Convert text to voice messages. Sent as Telegram voice notes. Requires DEEPGRAM_API_KEY or configured TTS provider. |

### File & System Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `file` | `read_file`, `write_file`, `list_files` | File operations within HERMES_HOME. Can read/write text files, list directories. |
| `terminal` | `bash_execute` | Execute shell commands inside the container. **DANGEROUS** for public bots. Allows arbitrary code execution. |
| `skills` | Skill activation | Enable custom skills defined in /opt/data/skills/. Skills are SKILL.md files with tool definitions. |

### Task Management Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `todo` | `todo_add`, `todo_list`, `todo_complete`, `todo_delete` | Simple task list management. Persisted in HERMES_HOME. |
| `kanban` | `kanban_create_board`, `kanban_add_card`, `kanban_move_card`, `kanban_list` | Kanban board for project management. Multiple boards supported. |
| `cronjob` | 7 cron actions | Create, list, enable, disable, delete, trigger, and describe scheduled jobs. Jobs run as agent turns at specified times. |

### Agent Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `delegation` | `delegate_task` | Spawn subagent to handle subtask. Subagent shares max_iterations budget (90 total). |

### Platform-Specific Tools

| Toolset | Tools Included | Description |
|---------|---------------|-------------|
| `hermes-telegram` | `sendPhoto`, `sendAudio`, `sendVideo`, `sendDocument`, `sendSticker`, `sendVoice`, `sendAnimation`, `sendLocation`, `sendContact`, `editMessage`, `deleteMessage`, `pinMessage`, `forwardMessage` | Full Telegram Bot API access. Enables sending media, editing messages, pinning, forwarding. Without this toolset, agent can only send text replies. |

---

## Hermes Safety Recommendations

### By Bot Type

| Bot Type | INCLUDE | REMOVE |
|----------|---------|--------|
| Personal assistant (trusted user) | ALL | (none) |
| Child-facing | web, vision, image_gen, tts, memory, skills | terminal, delegation, kanban, file |
| Client-facing (paid) | web, vision, image_gen, memory, skills, hermes-telegram | terminal, delegation, kanban |
| Public (open DM) | web, vision, memory | terminal, delegation, kanban, file, image_gen |
| Monitoring/alerts | web, memory, cronjob, hermes-telegram | terminal, delegation, kanban, file |
| Trading bot | web, memory, cronjob, hermes-telegram | terminal, delegation, kanban |
| Content creator | web, vision, image_gen, memory, file, skills, hermes-telegram | terminal, delegation |

### Risk Levels

| Toolset | Risk | Why |
|---------|------|-----|
| `terminal` | **HIGH** | Arbitrary code execution inside container |
| `delegation` | **MEDIUM** | Can spawn subagents that consume resources |
| `file` | **MEDIUM** | Can read/write any file in HERMES_HOME |
| `kanban` | **LOW** | State management, no external effects |
| `web` | **LOW** | Read-only internet access |
| `memory` | **LOW** | Internal state only |
| `vision` | **LOW** | Read-only image analysis |

---

## OpenClaw Tool Categories

### Built-in Tools

| Category | Tools | Notes |
|----------|-------|-------|
| Memory | `memory_search`, `memory_write` | Always available. Knowledge graph based. |
| Web | `web_fetch` | HTTP GET/POST for APIs and web pages |
| Browser | Playwright CDP actions | Requires `browser.enabled: true` in config. Full browser automation. |

### Bundled Skills (opt-in)

Available via `skills.allowBundled` in config:

| Skill | Tools Provided | Description |
|-------|---------------|-------------|
| `github` | GitHub API operations | Issues, PRs, repos, actions |
| `notion` | Notion API operations | Database queries, page creation, updates |
| `obsidian` | Obsidian vault operations | Read/write notes, search vault |

### Custom Skills

Place in `/home/node/.openclaw/skills/<skill-name>/SKILL.md`:

```
/home/node/.openclaw/skills/
  my-skill/
    SKILL.md          # Skill definition (required)
    scripts/          # Optional helper scripts
    references/       # Optional reference docs
```

### Extensions (Plugins)

TypeScript modules in `/home/node/.openclaw/extensions/`:

```json
{
  "plugins": {
    "entries": {
      "my-extension": {
        "enabled": true,
        "config": {}
      }
    }
  }
}
```

---

## OpenClaw Cron `toolsAllow`

Whitelist of tools available during cron job execution:

```json
"payload": {
  "kind": "agentTurn",
  "message": "Do the scheduled task",
  "toolsAllow": ["web_fetch", "memory_search", "memory_write"]
}
```

Common cron tool combinations:

| Cron Purpose | toolsAllow |
|-------------|------------|
| Web monitoring | `["web_fetch", "memory_search", "memory_write"]` |
| Daily summary | `["memory_search"]` |
| Data collection | `["web_fetch", "memory_write"]` |
| Report generation | `["web_fetch", "memory_search"]` |

---

## Toolset Configuration Examples

### Minimal (support bot)

```yaml
# Hermes
platform_toolsets:
  telegram:
    - web
    - memory
    - vision
```

### Standard (personal assistant)

```yaml
# Hermes
platform_toolsets:
  telegram:
    - web
    - vision
    - image_gen
    - tts
    - file
    - skills
    - todo
    - cronjob
    - memory
    - session_search
    - hermes-telegram
```

### Full (developer bot)

```yaml
# Hermes
platform_toolsets:
  telegram:
    - web
    - vision
    - image_gen
    - tts
    - file
    - skills
    - todo
    - cronjob
    - memory
    - session_search
    - terminal
    - delegation
    - kanban
    - hermes-telegram
```
