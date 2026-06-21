---
name: executing-plans
description: Use when partner provides a complete implementation plan to execute in controlled batches with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for architect review.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load and Review Plan

1. Read plan file
2. Review critically - identify any questions or concerns
3. If concerns: Raise them before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Batch

**Default: First 3 tasks**

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Report

When batch complete:
```markdown
## Batch 1 Complete

### Implemented
- [Task 1]: [brief description]
- [Task 2]: [brief description]
- [Task 3]: [brief description]

### Verification
```
[test output]
```

Ready for feedback.
```

### Step 4: Continue

Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Complete Development

After all tasks complete:
1. Announce: "Using finishing-a-development-branch skill"
2. Verify all tests pass
3. Present completion options
4. Execute chosen option

## When to Stop and Ask

**STOP executing immediately when:**
- Hit a blocker mid-batch
- Plan has critical gaps
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Batch Size Guidelines

| Situation | Batch Size |
|-----------|------------|
| Default | 3 tasks |
| Complex/risky changes | 1-2 tasks |
| Simple/mechanical changes | 5 tasks |
| Partner requests different | As requested |

## Remember

- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Between batches: just report and wait
- Stop when blocked, don't guess
