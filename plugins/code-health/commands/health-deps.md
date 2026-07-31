---
description: Dependency audit and update workflow (inline orchestration)
---

# Dependency Health Check

Execute the `health-inline` skill (mode: deps) for inline orchestration.

**You ARE the orchestrator.** Do not spawn a separate orchestrator agent.

## Quick Start

1. Read `.claude/skills/health-inline/SKILL.md` (mode table) + `.claude/skills/health-inline/references/modes/deps.md` (full workflow)
2. Follow the workflow phases directly
3. Use Task tool only for workers (dependency-auditor, dependency-updater)
4. Run quality gates inline via Bash

## Workflow Summary

```
Pre-flight → Audit → [Update by Priority] → Verify → Report
```

**Workers**: dependency-auditor, dependency-updater
**Quality gates**: `pnpm type-check && pnpm build`
**Max iterations**: 3

---

Now read and execute the workflow: `.claude/skills/health-inline/references/modes/deps.md`
