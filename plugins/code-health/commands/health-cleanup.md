---
description: Dead code detection and cleanup workflow (inline orchestration)
---

# Cleanup Health Check

Execute the `health-inline` skill (mode: cleanup) for inline orchestration.

**You ARE the orchestrator.** Do not spawn a separate orchestrator agent.

## Quick Start

1. Read `.claude/skills/health-inline/SKILL.md` (mode table) + `.claude/skills/health-inline/references/modes/cleanup.md` (full workflow)
2. Follow the workflow phases directly
3. Use Task tool only for workers (dead-code-hunter, dead-code-remover)
4. Run quality gates inline via Bash

## Workflow Summary

```
Pre-flight → Detect → [Remove by Priority] → Verify → Report
```

**Workers**: dead-code-hunter, dead-code-remover
**Quality gates**: `pnpm type-check && pnpm build`
**Max iterations**: 3

---

Now read and execute the workflow: `.claude/skills/health-inline/references/modes/cleanup.md`
