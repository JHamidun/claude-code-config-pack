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

## Blocking Hooks

Какие гарды реально стоят — смотри `~/.claude/settings.json` → `hooks.PreToolUse` (и код в `~/.claude/hooks/`); в сессии — `/doctor`. Не пересказывай их по памяти: устаревший список уже приводил к «найденной» несуществующей дыре. Принципы и стоимость хуков → `config/rules-ref/hooks.md`.

## Permission Boundaries

- Security agents (security-engineer, security-scanner) have READ-ONLY tools
- Актуальный режим и списки — `settings.json` → `permissions` (defaultMode, allow/deny/ask) и `/context`
- MCP servers should use least-privilege API tokens
- Scope OAuth grants to minimum required permissions
- Revoke unused MCP server tokens promptly

---

> **Справочник (по требованию):** Audit Logging · Data Protection · Supply Chain Security · Network Security · Incident Response · Commercial Distribution Checklist — вынесены в `config/rules-ref/security-hardening-ref.md`. Читать при audit/compliance, pre-distribution, incident response.
