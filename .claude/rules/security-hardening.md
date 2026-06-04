# Security Hardening (Commercial Deployment)

> Extends `security.md` (API keys, image format). This file covers sandbox, audit, and commercial deployment security.

## Credential Management

- ALL keys in `~/.claude/.credentials.master.env` (single source of truth)
- MCP servers reference via `${VAR_NAME}` in mcp.json — NEVER plaintext
- `.credentials.master.env` is listed in `.gitignore` (already included by default)
- Rotation schedule: API keys quarterly, OAuth tokens auto-refresh
- Never commit `.env` files, `credentials.json`, or service account keys
- Use `os.getenv()` exclusively — no fallback defaults for secrets

## Sandbox Configuration

- Shell commands run in user's shell — no isolation by default
- For untrusted code: use Docker containers with `--read-only` and `--no-new-privileges`
- For CI/CD: use ephemeral environments, destroy after pipeline completes
- PreToolUse hooks can BLOCK dangerous commands (configured in settings.json)
- Never run `eval()` or `exec()` on LLM-generated strings without validation

## Current Blocking Hooks

| Pattern | What It Blocks |
|---------|---------------|
| `Bash(rm -rf)` | Recursive deletion |
| `Bash(DROP DATABASE)` | Database destruction |
| `Bash(DROP TABLE)` | Table destruction |

Add new hooks in `~/.claude/settings.json` under `hooks.PreToolUse` as needed.

## Audit Logging

- Claude Code logs all tool calls to session files
- Session files: `~/.claude/projects/<project>/`
- Archive old sessions: `/search-chats archive`
- For compliance: export sessions with `/export`
- Retain session logs for minimum 90 days in regulated environments
- Monitor for anomalous patterns: bulk file reads, credential access, mass deletions

## Permission Boundaries

- Security agents (security-engineer, security-scanner) have READ-ONLY tools
- Write operations require explicit user approval (first time per session)
- MCP servers should use least-privilege API tokens
- Scope OAuth grants to minimum required permissions
- Revoke unused MCP server tokens promptly

## Data Protection

1. **PII handling:** Never store PII in CLAUDE.md or rules/ files
2. **User profile:** `rules/user-profile.md` exists for personal use — must NOT ship in commercial product
3. **Memory files:** May contain sensitive project data — exclude from distribution
4. **Chat history:** Contains full conversation — encrypt at rest
5. **LLM outputs:** Validate before writing to DB, sending via email, or using as query params
6. **File uploads:** Scan for malware, enforce size limits, restrict allowed MIME types

## Supply Chain Security

- Plugin sources: verify publisher and repository before installing
- MCP servers: audit npm packages, prefer official packages with active maintenance
- Custom scripts: code review before first execution
- Dependencies: run `npm audit` and `pip audit` periodically
- Pin dependency versions in production — no `latest` or `*` ranges
- Review lockfiles (`package-lock.json`, `poetry.lock`) for unexpected changes

## Network Security

- AI Gateway: bind to localhost only (127.0.0.1), no external exposure without auth
- MCP SSE endpoints: require JWT tokens (e.g., n8n webhooks)
- SSH to servers: key-based auth only, disable password authentication
- External APIs: all credentials through env vars, never hardcoded
- TLS everywhere: no HTTP endpoints in production
- Rate-limit outbound API calls to prevent cost runaway

## Incident Response

- If a credential is leaked: rotate immediately, audit usage logs, notify affected services
- If a session file is compromised: revoke any tokens referenced in the session
- If an MCP server is compromised: disconnect, audit, redeploy from clean source
- Maintain a contact list for each third-party API provider's security team

## Commercial Distribution Checklist

Before distributing this configuration to customers or open-sourcing:

- [ ] Remove `.credentials.master.env` (include `.credentials.example.env` template)
- [ ] Remove `rules/user-profile.md` (personal data)
- [ ] Remove `memory/` files (project-specific knowledge)
- [ ] Audit `mcp.json` for hardcoded credentials or internal URLs
- [ ] Review `skills/` for proprietary business logic
- [ ] Strip personal Telegram, email, phone, national ID from all configs
- [ ] Replace project-specific agents with generic versions
- [ ] Remove session history and chat archives
- [ ] Run a secrets scan on the entire distribution directory
- [ ] Test clean install on a fresh machine with no prior state
- [ ] Document all required environment variables in a setup guide
- [ ] Verify no internal server IPs or hostnames remain in configs
