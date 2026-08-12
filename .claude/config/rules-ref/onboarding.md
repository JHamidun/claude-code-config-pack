> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Onboarding — First-Time Setup

> Pre-configured Claude Code environment: 172 skills, 49 agents, 109 commands, 35 plugins (+3 disabled), 19 local MCP + 10 cloud MCP servers.

---

## Prerequisites

- **Claude Code CLI** installed and on PATH (`npm install -g @anthropic-ai/claude-code`)
- **Claude Max subscription** (unlocks Opus 4.6, Sonnet 4.5, Haiku 4.5 — no rate limits)
- **Git** installed (for version control, PR workflows, commit hooks)
- **Node.js 18+** (required by CLI and some MCP servers)
- **Python 3.10+** (required by tools: tg_client, vector_memory, search_chats, etc.)

---

## Step 1: Credentials Setup

1. Copy the example file:
   ```bash
   cp ~/.claude/.credentials.master.env.example ~/.claude/.credentials.master.env
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
claude /doctor            # Health check — reports missing deps, broken MCP servers
claude /status            # Shows loaded rules, active plugins, MCP servers
```

Expected: all rules from `~/.claude/rules/` auto-loaded, `filesystem` MCP server active.

---

## Step 3: Enable MCP Servers

Only `filesystem` and `chrome-devtools` are active by default (in `settings.json`).

Additional servers live in `mcp.json` — enable as needed:

| Server | When to enable |
|--------|---------------|
| `postgres` | Working with databases on your server |
| `redis` | Cache and pub/sub operations |
| `brave-search` | Web search during research tasks |
| `n8n` | Workflow automation |
| `puppeteer` | Browser screenshots and scraping |
| `affine` | AFFiNE workspace / knowledge base |
| `replicate` | Running 1000+ AI models |
| `microsoft-office` | Generating PPTX, XLSX, DOCX files |

To enable: set `"disabled": false` in `~/.claude/mcp.json` for the desired server.

Test by asking Claude to use a tool from that server (e.g., "search the web for X" after enabling brave-search).

---

## Step 4: Smoke Test

Run these to confirm everything works end-to-end:

1. **Commands**: type `/help` to see all 109 available slash commands
2. **Basic task**: ask `create a hello world Python script` — tests file writing
3. **Skill**: try `/deep-research "Claude Code best practices"` — tests research pipeline
4. **Agent delegation**: ask `review this code` on any file — triggers `code-reviewer` agent
5. **Image generation** (OPTIONAL — only if you configured `GOOGLE_API_KEY`): ask `draw a sunset`
6. **Memory**: ask `/memory-stats` — confirms vector memory is operational

---

## Step 5: Key Concepts

| Concept | Count | What it is |
|---------|-------|------------|
| **Skills** | 172 | Prompt templates in `~/.claude/skills/*/SKILL.md` — enhance Claude's domain expertise |
| **Agents** | 49 | Specialized subagents (code-reviewer, bug-hunter, test-writer) — auto-delegated by complexity |
| **Commands** | 109 | Slash commands (`/deploy`, `/translate`, `/gmail`) — shortcuts for common workflows |
| **Rules** | 23 | Auto-loaded files in `~/.claude/rules/` — guidelines Claude follows every session |
| **Plugins** | 35 | Community extensions (Figma, Slack, Linear, Telegram) — configured in `settings.json` |
| **MCP Servers** | 19+10 | 19 local (filesystem, postgres...) + 10 cloud (Airtable, Gmail, Canva...) |

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
| Hook errors / crashes | See `config/rules-ref/hooks.md` — only blocking hooks and beep are active by design |
| Context7 not resolving | Ensure `context7` plugin is enabled in `settings.json` |
| Telegram tools fail | Run `python ~/.claude/tools/tg_client.py` once to authenticate Telethon session |

---

## Further Reading

- `CLAUDE.md` — master navigation file (auto-loaded every session)
- `rules/routing.md` — full routing table (100+ task types)
- `rules/security.md` — credential handling rules
- `rules/quality-gates.md` — mandatory checks after code changes
- `config/` — server configs, API references, project registry
