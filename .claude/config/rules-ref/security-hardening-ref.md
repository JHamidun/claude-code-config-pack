# Security Hardening — Reference (occasional use)

> Вынесено из `rules/security-hardening.md` (ядро остаётся auto-load: Credential Management, Sandbox Configuration, Current Blocking Hooks, Permission Boundaries). Читать по требованию — audit/compliance, pre-distribution, incident response.

## Audit Logging

- Claude Code logs all tool calls to session files
- Session files: `~/.claude/projects/<project>/`
- Archive old sessions: `/search-chats archive`
- For compliance: export sessions with `/export`
- Retain session logs for minimum 90 days in regulated environments
- Monitor for anomalous patterns: bulk file reads, credential access, mass deletions

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
- [ ] **MUST-STRIP secret-bearing config files** (these carry live secrets/deanon fingerprints — NEVER distribute): `config/projects-registry.md`, `config/telegram.md`, `config/server-*.md`, `config/email.md`, `config/databases.md`, `config/cloudflare.md`, `config/aws.md`, and any `*.bak*` / `*.bak-pwrotate*`. Secrets in these were moved to `.credentials.master.env` (2026-07-17) and replaced with `<see ENV_VAR>` refs, but the files still hold operational PII (accounts, IPs, project names).
- [ ] Run `python skills/leak-scan/scripts/leak_scan.py ~/.claude/config` — must report 0 credential hits before any push.
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
