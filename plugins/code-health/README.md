# Code Health

> Bug/cleanup/deps/reuse/security health audits, security audit, threat hunting, finding and vetting third-party skills before install.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `config-health` | Здоровье конфига Claude Code: битые ссылки, вес промпта, лимит памяти, живость MCP. |
| `health-inline` | Чинит codebase health инлайн: /health bugs\|cleanup\|deps\|reuse\|security — детекция→фикс→верификация. |
| `leak-scan` | PII/деанон перед публикацией (leak_scan.py) + prompt-injection в чужом скилле (skill_injection_scan.py). |
| `osint-recon` | Разведка инфраструктуры домена/IP CLI osint_client.py: DNS, whois, субдомены, порты/CVE, санкции. |
| `privacy-filter` | Локальный PII-фильтр (OpenAI opf, on-device): обезличить текст перед облачным LLM, обратимая редакция. |
| `security-audit` | Security-аудит: секреты в коде, pip/npm audit, OWASP Top 10. |
| `skill-audit` | Заглушка: проверка чужого скилла/плагина до установки переехала в skill-manager, режим «Аудит». |
| `skill-manager` | Навыки и плагины: найти, подобрать, проверить. |
| `threat-hunting` | Threat hunting: правила Sigma, detection engineering. |

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
