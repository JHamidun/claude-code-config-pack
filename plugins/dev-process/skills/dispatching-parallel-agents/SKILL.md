---
name: dispatching-parallel-agents
description: Use when facing 3+ independent failures that can be investigated without shared state - dispatches multiple agents to investigate and fix independent problems concurrently
---

# Dispatching Parallel Agents

## Overview

When multiple unrelated failures exist across different test files or subsystems, sequential investigation wastes time.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would interfere with each other

## The Pattern

### Step 1: Identify Independent Domains

Group failures by what's broken:
- File A tests: abort logic
- File B tests: batch completion
- File C tests: race conditions

### Step 2: Create Focused Agent Tasks

Each agent receives:
- Specific scope
- Clear goal
- Constraints
- Expected output

```markdown
## Agent Task: Fix abort logic tests

### Scope
Only modify files in `src/abort/` and `tests/abort/`

### Goal
Make all tests in `tests/abort.test.ts` pass

### Constraints
- Don't modify other test files
- Don't change public API signatures

### Expected Output
- Summary of root cause
- List of files changed
- Verification that tests pass
```

### Step 3: Dispatch in Parallel

Use Task tool with multiple agents:

```
[Agent 1] → abort logic investigation
[Agent 2] → batch completion investigation
[Agent 3] → race condition investigation
```

### Step 4: Review and Integrate

1. Read summaries from each agent
2. Verify no conflicts in edited code
3. Run full test suite
4. Spot check for systematic errors

## Agent Prompt Template

```markdown
## Task: [Specific Problem]

### Context
[Brief description of the failure]

### Scope
- Files to investigate: [list]
- Files to modify: [list]

### Goal
[Clear success criteria]

### Constraints
- [What NOT to change]
- [Boundaries]

### Output Required
1. Root cause analysis
2. Changes made (with file paths)
3. Verification results
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Too broad scopes | Specific, focused scopes |
| Missing context | Include error messages, test names |
| No constraints | Clear boundaries on what to change |
| Vague outputs | Request detailed summaries |

## When NOT to Use

- **Related failures** - One fix might solve multiple problems
- **Need system context** - Must understand complete state
- **Exploratory debugging** - Unknown what's wrong
- **Shared state** - Agents would interfere

## Verification Process

After agents complete:
1. Review each summary for understanding
2. Check for conflicts in edited code
3. Run full test suite
4. Spot check for systematic errors

## Real Example

6 test failures across 3 files:
- `abort.test.ts`: 2 failures (abort timing)
- `batch.test.ts`: 3 failures (completion logic)
- `race.test.ts`: 1 failure (condition wait)

Dispatched 3 agents in parallel:
- Agent 1: Fixed abort timing (2 tests)
- Agent 2: Fixed completion logic (3 tests)
- Agent 3: Fixed race condition (1 test)

Result: All fixes independent, zero conflicts, 3 problems solved in time of 1.
