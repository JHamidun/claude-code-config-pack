# Permission Modes & Security Boundaries

## Permission Modes

Claude Code has permission modes that control what actions require user approval.

### Default Mode (recommended for most users)
- **Read files:** Allowed automatically
- **Write/Edit files:** Allowed automatically
- **Run shell commands:** Requires approval (first time per command pattern)
- **MCP tools:** Requires approval per server

### Allowlisted Commands

Add patterns to settings.json `permissions.allow` to auto-approve:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(pnpm *)",
      "Bash(git *)",
      "Bash(python *)",
      "Bash(ssh your-server *)",
      "Bash(docker *)"
    ]
  }
}
```

## File Access Boundaries

- Claude Code can read/write any file the user has access to
- Sensitive files to NEVER commit: `.credentials.master.env`, `.env`, `*.pem`, `*.key`
- Gitignore patterns protect against accidental commits

## MCP Server Trust Levels

| Level | Servers | Policy |
|-------|---------|--------|
| Trusted | filesystem, context7, github | Auto-approve |
| Standard | postgres, redis, brave-search | Approve per session |
| Cautious | n8n, apify, puppeteer | Approve each call |

## Sandbox Configuration

- Shell commands run in user's shell environment
- No network sandbox by default
- Docker containers provide isolation for untrusted code
- SSH commands to servers are NOT sandboxed -- be careful

## Security Best Practices

1. Keep `.credentials.master.env` out of git (in .gitignore)
2. Use env var references in mcp.json (`${VAR_NAME}`), never plaintext
3. Review shell commands before approving new patterns
4. Audit MCP server permissions periodically
5. Use read-only tools for security agents (no Write/Edit)
6. Never allowlist destructive patterns like `Bash(rm *)` or `Bash(* --force)`
7. Prefer scoped permissions over blanket `Bash(*)` wildcards
