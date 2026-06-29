---
name: verification-before-completion
description: Use before claiming any work is complete - requires fresh verification evidence before any status claim
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

## Gate Function

Before ANY status claim:

1. Identify what command proves the claim
2. Execute the full command fresh and completely
3. Read full output, check exit code, count failures
4. Verify output confirms the claim
5. If no: state actual status with evidence
6. Only then make the claim

## Common Claims and Required Verification

| Claim | Required Evidence |
|-------|-------------------|
| "Tests pass" | Test command output: 0 failures |
| "Linter clean" | Linter output: 0 errors |
| "Build succeeds" | Build command: exit 0 |
| "Bug fixed" | Test original symptom passes |
| "Regression test works" | Red-green cycle verified |
| "Agent completed" | VCS diff showing changes |
| "Requirements met" | Line-by-line checklist |

## Red Flags

**Never use:**
- "should"
- "probably"
- "seems to"
- "I think"
- "likely"

**Never:**
- Express satisfaction before verification
- Commit without verification
- Trust agent reports alone
- Rely on partial verification

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the test |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | Every time matters |
| "It's a small change" | Small changes break things |
| "I already tested similar" | This specific case needs verification |
| "Time pressure" | Wrong faster isn't faster |
| "The logic is sound" | Sound logic with wrong output = bug |
| "It worked before" | Works now? Prove it |

## Verification Patterns

### Tests

```bash
# ❌ WRONG: "Tests should pass"
# ✅ RIGHT: Run and show output

npm test
# Output: 47 passing, 0 failing
# "All 47 tests pass."
```

### Regression Tests

```bash
# ❌ WRONG: "Added regression test"
# ✅ RIGHT: Show red-green cycle

# 1. Test fails without fix
npm test -- --grep "handles null user"
# FAIL: expected 'error' but got undefined

# 2. Add fix
# 3. Test passes with fix
npm test -- --grep "handles null user"
# PASS
```

### Requirements

```markdown
# ❌ WRONG: "Requirements met"
# ✅ RIGHT: Line-by-line verification

Requirements:
- [x] User can login (tested: login_test.py:15 passes)
- [x] Session persists (tested: session_test.py:42 passes)
- [ ] Password reset (NOT IMPLEMENTED)

"2 of 3 requirements verified. Password reset still needed."
```

## When To Apply

**ALWAYS before:**
- Any success claim
- Any satisfaction expression
- Any positive statement about work state
- Commits
- PR creation
- Task completion marking

## The Bottom Line

**Say only what you can prove right now.**

Not what should be true. Not what was true. What IS true, with evidence.
