> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Onboarding — First-Time Setup

> Pre-configured Claude Code environment: сотни skills, 75 agents, 156 commands, 33 plugins, MCP-серверы в `settings.json` + справочник `mcp.json`. Точные счётчики не вкапываем — они устаревают молча; актуальные: `python ~/.claude/scripts/config_health.py`.

---

## Prerequisites

- **Claude Code CLI** installed and on PATH (`npm install -g @anthropic-ai/claude-code`)
- **Claude Max subscription** (unlocks Opus 5, Sonnet 5, Haiku 4.5 — no rate limits)
- **Git** installed (for version control, PR workflows, commit hooks)
- **Node.js 18+** (required by CLI and some MCP servers)
- **Python 3.10+** (required by tools: tg_client, vector_memory, search_chats, etc.)

---

## Step 1: Credentials Setup

1. Copy the example file:
   ```bash
   cp ~/.claude/templates/.credentials.master.env.example ~/.claude/.credentials.master.env
   ```
2. **No API keys are required.** Claude Code runs entirely on your Claude subscription —
   text, code, reasoning, agents, skills all work with ZERO third-party keys. Leave the file as is.
3. OPTIONAL paid features — uncomment and add a key only if you want them:
   - `GOOGLE_API_KEY` — Google Gemini (image/video gen; free tier at aistudio.google.com)
   - `OPENAI_API_KEY` — GPT models, DALL-E
   - `ANTHROPIC_API_KEY` — only needed for standalone bots (Claude Code uses subscription auth)
   - `ELEVENLABS_API_KEY` — text-to-speech
   - `DEEPGRAM_API_KEY` — transcription
   - `DEEPL_API_KEY` — translation
   - `BRAVE_SEARCH_API_KEY` — web search MCP
   - `CRM_WEBHOOK_URL` — CRM integration
4. **Never commit this file to git.** It is already in `.gitignore`.

---

## Step 2: Verify Installation

```bash
claude --version          # Confirm CLI is installed
claude doctor             # Health check — reports missing deps, broken MCP servers
```

Внутри сессии: `/doctor` — здоровье, `/context` — что загружено, `/mcp` — живые MCP-серверы.

Expected: all rules from `~/.claude/rules/` auto-loaded; MCP `graph-memory`, `filesystem`, `playwright-live1` active.

---

## Step 3: Enable MCP Servers

Активно по умолчанию (см. `settings.json` → `mcpServers`): `graph-memory`,
`filesystem`, `playwright-live1`; рядом выключенные `runway`, `pageindex`, `miro`.

`~/.claude/mcp.json` — СПРАВОЧНИК из 17 готовых блоков (postgres, redis,
brave-search, n8n, puppeteer, playwright, affine, replicate, perplexity,
elevenlabs, figma-mcp и др.). Claude Code его НЕ читает.

To enable: скопируй блок из `mcp.json` в `settings.json` → `mcpServers`, убери
`"disabled": true`, подставь свои URL/токены и АБСОЛЮТНЫЙ путь вместо `${HOME}`.

Test by asking Claude to use a tool from that server (e.g., "search the web for X" after enabling brave-search).

---

## Step 4: Smoke Test

Run these to confirm everything works end-to-end:

1. **Commands**: type `/help` to see all available slash commands
2. **Basic task**: ask `create a hello world Python script` — tests file writing
3. **Skill**: try `/deep-research "Claude Code best practices"` — tests research pipeline
4. **Agent delegation**: ask `review this code` on any file — triggers `code-reviewer` agent
5. **Image generation** (OPTIONAL — only if you configured `GOOGLE_API_KEY`): ask `draw a sunset`
6. **Memory**: ask `/memory-stats` — confirms vector memory is operational

---

## Step 5: Key Concepts

| Concept | Where | What it is |
|---------|-------|------------|
| **Skills** | `~/.claude/skills/*/SKILL.md` | Prompt templates — enhance Claude's domain expertise |
| **Agents** | `~/.claude/agents/**` (75) | Specialized subagents (code-reviewer, bug-hunter, test-writer) — auto-delegated by complexity |
| **Commands** | `~/.claude/commands/**` (156) | Slash commands (`/deploy`, `/translate`, `/gmail`) — shortcuts for common workflows |
| **Rules** | `~/.claude/rules/` | Auto-loaded files — guidelines Claude follows every session |
| **Plugins** | `settings.json` → `enabledPlugins` (33) | Community extensions |
| **MCP Servers** | `settings.json` → `mcpServers` | Живые серверы; `mcp.json` — справочник блоков для копирования |

> Счётчики устаревают молча — сверяй `python ~/.claude/scripts/config_health.py`, а не цифры в документах.

**Routing**: `rules/routing.md` maps natural language triggers to the correct tool. Say "translate this" and it routes to DeepL. Say "deploy" and it routes to the deploy command.

**Delegation**: `rules/delegation.md` defines complexity levels. Single-file changes are handled directly. Multi-file features spawn subagents. Epics use orchestration.

---

## Step 6: Daily Workflow

1. **Start your day**: `/plan-my-day` (personal) or `/daily` (dev standup)
2. **Find the right tool**: check `rules/routing.md` or just describe what you need — routing is automatic
3. **Memory persists**: important decisions, bug fixes, and patterns are auto-saved to `~/.claude/projects/*/memory/`
4. **Search history**: `/search-chats query` to find anything from past sessions

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Model not found" | Check `rules/models.md` — use aliases: `opus`, `sonnet`, `haiku` |
| "API key not found" | Verify `~/.claude/.credentials.master.env` has the key, loaded via `os.getenv()` |
| "MCP server failed to start" | Check `mcp.json` — ensure env vars are set and `disabled` is `false` |
| Slow startup (>5s) | Disable unused MCP servers — each one adds cold-start latency |
| Hook errors / crashes | See `config/rules-ref/hooks.md` — активны только `guard.js` (PreToolUse) и `gsd-check-update.js` (SessionStart), см. settings.json → hooks |
| Context7 not resolving | Ensure `context7` plugin is enabled in `settings.json` |
| Telegram tools fail | Run `python ~/.claude/tools/tg_client.py` once to authenticate Telethon session |

---

## Further Reading

- `CLAUDE.md` — master navigation file (auto-loaded every session)
- `rules/routing.md` — full routing table (100+ task types)
- `rules/security.md` — credential handling rules
- `rules/quality-gates.md` — mandatory checks after code changes
- `config/` — server configs, API references, project registry
