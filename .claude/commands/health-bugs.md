---
description: Bug detection and fixing workflow (inline orchestration)
---

# Bug Health Check

Execute the `health-inline` skill (mode: bug) for inline orchestration.

**You ARE the orchestrator.** Do not spawn a separate orchestrator agent.

## Quick Start

1. Read `.claude/skills/health-inline/SKILL.md` (mode table) + `.claude/skills/health-inline/references/modes/bug.md` (full workflow)
2. Follow the workflow phases directly
3. Use Task tool only for workers (bug-hunter, bug-fixer)
4. Run quality gates inline via Bash

## Workflow Summary

```
Pre-flight → Detect → [Fix by Priority] → Verify → Report
```

**Workers**: bug-hunter, bug-fixer
**Quality gates**: `pnpm type-check && pnpm build`
**Max iterations**: 3

---

Now read and execute the workflow: `.claude/skills/health-inline/references/modes/bug.md`
