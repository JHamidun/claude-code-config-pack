# Claude Code Configuration Pack

> Depersonalised Claude Code setup. Drop into `~/.claude/`, fill in API keys, run.

## Quick install

### Windows (PowerShell)

```powershell
# Optional: backup existing config
./install.ps1 -BackupExisting
```

### macOS / Linux (bash)

```bash
chmod +x install.sh
./install.sh --backup
```

The installer:
1. Copies `.claude/*` → `~/.claude/`
2. Copies `CLAUDE.md` → `~/CLAUDE.md`
3. Seeds `~/.claude/.credentials.master.env` from the template (only if not present)
4. Optionally installs Python deps (`pip install -r requirements.txt`)

After installation: launch Claude Code in any project. Plugins auto-download (~30-60s).

## What you must fill in

| File | What |
|------|------|
| `~/.claude/.credentials.master.env` | API keys for any service you use |
| `~/.claude/rules/user-profile.md` | Your name, email, hardware specs |
| `~/.claude/config/projects-registry.md` | Your project catalog |
| `~/.claude/config/server-primary.md` | Server IP / SSH config (optional) |
| `~/CLAUDE.md` | Domain, server IPs, quick links |

Everything else (rules, skills, plugins, agents, commands, hooks, MCP servers) works out of the box once the keys are set.

## Inventory

- 270+ skills (`~/.claude/skills/`)
- 50+ agents (`~/.claude/agents/`)
- 110+ slash commands (`~/.claude/commands/`)
- 23 auto-loaded rules (`~/.claude/rules/`)
- 35 plugins (3 disabled by default — see `settings.json`)
- 20+ MCP servers (most disabled by default — enable via `mcp.json` or `settings.json`)
- 5 GSD hooks (`~/.claude/hooks/`)
- 6 generic Python tools (`~/.claude/tools/`)

## Hardened defaults

- `defaultMode: default` — Claude asks before running new bash patterns
- `permissions.allow` — concrete patterns (no wildcard `Bash`)
- `cleanupPeriodDays: 90` — sessions auto-archive
- All MCP servers tied to personal credentials are `disabled: true`
- All MCP servers with hardcoded local paths rewritten to portable `npx -y`

## Requirements

- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Claude Max subscription (recommended)
- Node.js 18+
- Python 3.10+ (optional, for tools)
- Git

## Security

- `.credentials.master.env` is gitignored — single source of truth
- No plaintext keys in `mcp.json` (env vars only)
- `leak_scan.py` script bundled if you want to verify before forking

## License

MIT.
