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

## Permission model — read this before installing

This config ships **`defaultMode: bypassPermissions`**. Claude runs commands without asking
you to confirm each one. That is deliberate: the config is built for uninterrupted autonomous
work, and confirming every step defeats it.

Protection does not disappear, it moves:

- **`hooks/bash-guard.js`** inspects every Bash and PowerShell call *before* it runs and exits
  with code 2 on 43 destructive patterns — `rm -rf` of roots, `DROP DATABASE/TABLE`, `mkfs`,
  `dd`, force-push to main, `docker rm -f`, `docker compose down -v`, `docker system prune`,
  `pm2 delete`, `systemctl stop`, `kubectl delete`. It also unwraps `ssh host "…"`,
  `bash -c "…"` and base64-encoded PowerShell, so hiding a command inside quotes does not help.
- **`hooks/security-guard.js`** does the same for Write/Edit.
- **`permissions.deny`** stays as the final backstop.

If you would rather be asked, set `permissions.defaultMode` to `"default"` in
`~/.claude/settings.json` and drop `skipDangerousModePermissionPrompt`. Nothing else depends
on the bypass mode.

## Other defaults

- `cleanupPeriodDays: 99999` — chat history is kept, not auto-deleted. Claude Code prunes
  sessions older than this many days; the 90-day default silently ate three-month-old
  work, which is exactly the history you want when you come back to an old project.
- All MCP servers tied to personal credentials are `disabled: true`
- All MCP servers with hardcoded local paths rewritten to portable `npx -y`
- Plugins that were declared but disabled are stripped, so nothing is resolved at startup for
  a marketplace you do not have

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
