---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

## Overview

Request structured code review at key development milestones.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

### Step 1: Get Git SHAs

```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

### Step 2: Dispatch Code Reviewer

Use Task tool with focused prompt:

```markdown
## Code Review Request

### What was implemented
[Description of changes]

### Requirements/Plan
[What it should do]

### Commits to review
Base: {BASE_SHA}
Head: {HEAD_SHA}

### Focus areas
- [Specific concerns]
- [Areas of uncertainty]
```

### Step 3: Act on Feedback

| Priority | Action |
|----------|--------|
| Critical | Fix immediately |
| Important | Fix before proceeding |
| Minor | Note for later |
| Disagree | Push back with reasoning |

## Review Request Template

```markdown
## Code Review: [Feature Name]

### Summary
[1-2 sentences describing what changed]

### Changes
- [File 1]: [What changed]
- [File 2]: [What changed]

### Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [ ] Manual testing needed for [X]

### Concerns
- [Any areas of uncertainty]

### Context
[Any background needed to review]
```

## Integration with Workflows

| Workflow | Review Cadence |
|----------|---------------|
| Subagent-driven | After each task |
| Plan execution | After batches of 3 tasks |
| Ad-hoc development | Before merge |

## Red Flags

**Never:**
- Skip review for "simple" changes
- Ignore Critical issues
- Proceed with unfixed Important issues
- Dismiss valid technical feedback

**If disagreeing:** Provide technical reasoning and supporting evidence.
