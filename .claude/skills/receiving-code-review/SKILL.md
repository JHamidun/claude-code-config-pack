---
name: receiving-code-review
description: Use when receiving code review feedback - requires technical rigor and verification, not performative agreement or blind implementation
---

# Receiving Code Review

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

When receiving code review feedback:

1. **READ** - Complete feedback without reacting
2. **UNDERSTAND** - Restate requirement in own words (or ask)
3. **VERIFY** - Check against codebase reality
4. **EVALUATE** - Technically sound for THIS codebase?
5. **RESPOND** - Technical acknowledgment or reasoned pushback
6. **IMPLEMENT** - One item at a time, test each

## Forbidden Responses

**Never say:**
- "You're absolutely right!"
- "Great point!"
- "Of course, that makes sense!"

**Instead:**
- Restate technical requirement
- Ask clarifying questions
- Provide technical reasoning for pushback
- Proceed directly to action

## Handling Unclear Feedback

**IF any item is unclear:**
1. STOP - do not implement anything yet
2. ASK for clarification on unclear items

Items may be interdependent. Partial understanding leads to incorrect implementation.

## Source-Specific Handling

### From Your Human Partner

- Trusted - implement after understanding
- Still ask if scope unclear
- No performative agreement
- Skip to action or technical acknowledgment

### From External Reviewers

Before implementing, verify:
- Technical correctness
- Won't break functionality
- Understand reason for current implementation
- Test across platforms/versions
- Reviewer has complete context

**IF suggestion seems wrong:** Push back with technical reasoning.

## Implementation Order

1. Clarify anything unclear FIRST
2. Then implement:
   - Blocking issues
   - Simple fixes
   - Complex fixes
3. Test each fix individually
4. Verify no regressions

## When To Push Back

Push back when:
- Suggestions break functionality
- Reviewers lack context
- Feature is unused (YAGNI)
- Approach is technically incorrect
- Legacy reasons exist
- Architectural decisions conflict

## Acknowledging Correct Feedback

Use factual language:
- "Fixed. [Brief description]"
- "Good catch - [specific issue]. Fixed in [location]."

Avoid gratitude expressions.

## Correcting Your Pushback

When wrong about pushback:
- "You were right - I checked [X] and it does [Y]. Implementing now."

State correction factually without apologies or over-explanation.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness matters most |
| Partial implementation | Clarify all items first |

## The Bottom Line

External feedback = suggestions to evaluate, not orders to follow.

Verify. Question. Then implement.
