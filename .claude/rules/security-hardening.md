# Security Hardening (коммерческая поставка)

> Дельта к `security.md` (ключи, границы доверия входящих данных) и
> `permissions.md` (изоляция, MCP, что не разрешать). Дублировать их здесь
> нельзя: одно и то же правило в двух файлах расходится молча, и потом
> непонятно, какая версия действует. Здесь — только то, чего там нет.

## Ключи: сверх того, что уже сказано в `security.md`

- MCP-серверы ссылаются на ключ через `${ИМЯ}` в `mcp.json` — **никогда**
  открытым текстом. ⚠️ Подстановка берёт значение из **окружения процесса**, а
  `.credentials.master.env` движок не читает: незаведённая переменная даёт
  пустую строку и «Authorization header is badly formatted» вместо явной ошибки.
- Ротация: API-ключи раз в квартал, OAuth-токены обновляются сами.
- Не коммитить: `.env`, `credentials.json`, ключи сервис-аккаунтов.
- `os.getenv()` без запасного значения по умолчанию. Дефолт у секрета означает,
  что код молча поедет не на том ключе.

## Блокирующие хуки

Какие гарды реально стоят — только `~/.claude/settings.json` → `hooks.PreToolUse`
(и код в `~/.claude/hooks/`); в сессии — `/doctor`. **Не пересказывай их по
памяти:** устаревший список уже приводил к «найденной» несуществующей дыре.
Принципы и стоимость хуков — `config/rules-ref/hooks.md`.

## Permission Boundaries

- Security agents never patch the code they audit: no `Edit`, ever.
  - `security-engineer` — `Read, Glob, Grep`, report goes back in the reply, no file.
  - `pentest-engineer` — has `Bash`, and active recon is allowed **only after the
    authorization gate in the agent passes**: target named by the owner, no state
    change, responsible disclosure.
  - `health/workers/security-scanner` — `Write` **only** on its own
    `security-scan-report.md`. Its partner `vulnerability-fixer` picks that file up
    from disk, not from the scanner's reply text, so a blanket `Write` ban breaks
    the pair silently: scan runs, no file, fixer finds nothing to fix, no error.
  - Fixes are the fixer's job (`vulnerability-fixer` or `senior-developer`), never
    the scanner's.
- Актуальный режим и списки — `settings.json` → `permissions` (defaultMode, allow/deny/ask) и `/context`
- MCP servers should use least-privilege API tokens
- Scope OAuth grants to minimum required permissions
- Revoke unused MCP server tokens promptly

---

> **Справочник (по требованию → `config/rules-ref/security-hardening-ref.md`):**
> Audit Logging · Data Protection · Supply Chain Security · Network Security ·
> Incident Response · Commercial Distribution Checklist. Читать при
> аудите/комплаенсе, перед раздачей наружу и при разборе инцидента.
