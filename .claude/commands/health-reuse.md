---
description: Code duplication detection and consolidation workflow (inline orchestration)
---

# Code Reuse Health Check

Execute the `health-inline` skill (mode: reuse) for inline orchestration.

**You ARE the orchestrator.** Do not spawn a separate orchestrator agent.

## Quick Start

1. Read `.claude/skills/health-inline/SKILL.md` (mode table) + `.claude/skills/health-inline/references/modes/reuse.md` (full workflow)
2. Follow the workflow phases directly
3. Use Task tool only for workers (reuse-hunter, reuse-fixer)
4. Run quality gates inline via Bash

## Workflow Summary

```
Pre-flight → Detect → [Consolidate by Priority] → Verify → Report
```

**Workers**: reuse-hunter, reuse-fixer
**Quality gates**: `pnpm type-check && pnpm build`
**Max iterations**: 3

---

Now read and execute the workflow: `.claude/skills/health-inline/references/modes/reuse.md`
