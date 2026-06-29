# Code Health

> Bug/cleanup/deps/reuse/security health audits, security audit, threat hunting.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `bug-health-inline` | Inline orchestration workflow for automated bug detection and fixing. |
| `cleanup-health-inline` | Inline orchestration workflow for dead code detection and removal. |
| `defense-in-depth` | Use when invalid data causes failures deep in execution - validates at every layer data passes through to make bugs structurally impossible |
| `deps-health-inline` | Inline orchestration workflow for dependency audit and updates. |
| `reuse-health-inline` | Inline orchestration workflow for code duplication detection and consolidation. |
| `security-audit` | Security auditing - vulnerability scanning, code review, OWASP checks, penetration testing guidance |
| `security-health-inline` | Inline orchestration workflow for security vulnerability detection and remediation. |
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
- `/health-metrics`
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
