---
name: subagent-driven-development
description: Use when executing implementation plans within a single session - dispatches fresh subagents for each task with code review checkpoints between them
---

# Subagent-Driven Development

## Overview

Execute plans by dispatching fresh subagents for each task with code review between tasks.

**Core principle:** Fresh subagent per task + review between tasks = high quality, fast iteration.

## When to Use

**Use when:**
- Staying in current session
- Tasks are mostly independent
- Want continuous progress with quality gates

**Don't use when:**
- Plan needs review first (use brainstorming)
- Tasks are tightly coupled
- Plan needs revision before execution

## The Process

### Step 1: Load Plan and Create Task List

```markdown
## Implementation Plan Loaded

Tasks:
1. [ ] Create user model
2. [ ] Add authentication endpoints
3. [ ] Implement session management
4. [ ] Add password reset flow

Starting with Task 1...
```

### Step 2: Dispatch Implementation Subagent

For each task, dispatch fresh subagent:

```markdown
## Task: Create user model

### Context
[Project context, existing patterns]

### Requirements
[Specific requirements from plan]

### Constraints
- Follow existing code style
- Add tests for all new code
- Don't modify unrelated files

### Deliverable
- Implementation complete
- All tests passing
- Summary of changes
```

### Step 3: Code Review After Each Task

After subagent completes:
1. Review changes
2. Run full test suite
3. Fix any issues found

### Step 4: Apply Feedback

If review finds issues:
- Dispatch fix subagent
- Or fix manually if simple

### Step 5: Mark Complete and Continue

```markdown
## Task 1 Complete ✓

Changes:
- Created `src/models/user.ts`
- Added tests in `tests/user.test.ts`
- Updated `src/index.ts` exports

Moving to Task 2...
```

### Step 6: Final Review

After all tasks:
- Run full test suite
- Review overall changes
- Check for systematic issues

### Step 7: Finish Development

Use `finishing-a-development-branch` skill.

## Critical Guidelines

**Never:**
- Skip code review between tasks
- Proceed with unfixed Critical issues
- Dispatch multiple implementation subagents in parallel

**If subagent fails:**
- Dispatch fix subagent with error context
- Don't manually intervene mid-task

## Required Skills

This skill depends on:
- `writing-plans` - Plan should exist first
- `requesting-code-review` - Review between tasks
- `finishing-a-development-branch` - After all tasks

## Task Dispatch Template

```markdown
## Implement: [Task Name]

### Goal
[What should be implemented]

### Files to Create/Modify
- [file1.ts]
- [file2.ts]

### Patterns to Follow
[Reference existing code patterns]

### Tests Required
- [Test case 1]
- [Test case 2]

### Done When
- [ ] Implementation complete
- [ ] Tests pass
- [ ] No linter errors
```
