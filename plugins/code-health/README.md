# Code Health

> Bug/cleanup/deps/reuse/security health audits, security audit, threat hunting.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `health-inline` | Inline codebase-health orchestration in five modes — bugs, cleanup, dependencies, reuse, security — detect, fix, verify. |
| `leak-scan` | Сканер безопасности в две стороны. |
| `osint-recon` | Open-source recon on infrastructure and counterparties — IP/ASN, DNS, RDAP whois, BGP, subdomains, exposed ports, CVEs. |
| `privacy-filter` | Local on-device PII detection and redaction (OpenAI `opf` model): de-identify text BEFORE sending to any cloud LLM (152-ФЗ/GDPR), strip PII from… |
| `security-audit` | Security auditing - vulnerability scanning, code review, OWASP checks, penetration testing guidance |
| `threat-hunting` | Threat hunting with Sigma rules, detection engineering, security analysis |

### Agents

- `bug-fixer`
- `bug-hunter`
- `dead-code-hunter`
- `dead-code-remover`
- `dependency-auditor`
- `dependency-updater`
- `reuse-fixer`
- `reuse-hunter`
- `security-scanner`
- `vulnerability-fixer`
- `pentest-engineer`
- `security-engineer`

### Commands

- `/health-bugs`
- `/health-cleanup`
- `/health-deps`
- `/health-reuse`
- `/health-security`
- `/security-scan`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install code-health@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`dev-core` · `dev-process` · `browser-testing` · `gsd`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
