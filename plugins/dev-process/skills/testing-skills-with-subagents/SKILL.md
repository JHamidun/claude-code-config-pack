---
name: testing-skills-with-subagents
description: Use when creating or editing skills - applies RED-GREEN-REFACTOR cycle to process documentation by running baseline without skill, writing to address failures, iterating to close loopholes
---

# Testing Skills With Subagents

## Overview

Apply TDD principles to skill documentation through pressure testing with subagents.

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill prevents the right failures.

## When to Use

Use for skills that:
- Enforce discipline with compliance costs
- Have behaviors agents might rationalize away
- Need to resist pressure scenarios

Skip for:
- Reference materials
- Skills without violation incentives

## The TDD Cycle for Skills

### RED Phase: Observe Failures

1. Run scenarios WITHOUT the skill
2. Observe actual agent failures
3. Capture exact rationalizations verbatim

```markdown
## Baseline Test (No Skill)

Prompt: "Implement this feature quickly"

Agent response:
"I'll just write the code first and add tests later
since the feature is straightforward..."

Failure captured: Skipped TDD, rationalized with "straightforward"
```

### GREEN Phase: Write Minimal Skill

1. Write skill addressing ONLY documented failures
2. Verify agents comply when skill is present

```markdown
## Skill Addition

Added to skill:
"Never skip test-first. 'Straightforward' is a rationalization."

Test result: Agent now writes test first ✓
```

### REFACTOR Phase: Close Loopholes

1. Identify new rationalizations discovered during testing
2. Add explicit counters for each loophole

```markdown
## New Rationalization Discovered

Agent said: "I'll write the test first, but I already
know the implementation, so I'll just verify it works..."

Added to skill:
"Writing code before test, even 'in your head', violates TDD.
Delete mental implementation. Start fresh from test."
```

## Pressure Scenario Design

Effective tests combine multiple pressures:

| Pressure Type | Example |
|---------------|---------|
| Time | "This is urgent" |
| Sunk cost | "Already spent 2 hours" |
| Authority | "Manager says skip tests" |
| Economic | "Save time/money" |
| Exhaustion | "Just this once" |
| Social | "Everyone does it" |
| Pragmatism | "Be practical" |

## Documentation Requirements

Each rationalization discovered requires:
1. Explicit negation in rules
2. Entry in rationalization table
3. Red flag designation
4. Description update noting violation symptoms

## Success Indicators

Bulletproof skills demonstrate:
- Correct choices under maximum pressure
- Citation of skill sections as justification
- Acknowledged temptation followed by compliance
- Meta-testing confirms clarity

## Common Mistakes

| Mistake | Impact |
|---------|--------|
| Skip RED phase | Don't know what skill prevents |
| Weak single-pressure scenarios | Miss multi-pressure failures |
| Capture failures vaguely | Can't write precise counters |
| Vague fixes | Agents find loopholes |
| Stop after first iteration | Miss evolved rationalizations |

## Testing Template

```markdown
## Skill Test: [Skill Name]

### Baseline (No Skill)
Prompt: [Pressure scenario]
Result: [Agent's actual response]
Failure: [Specific violation]

### With Skill
Prompt: [Same scenario]
Result: [Agent's response]
Success: [How skill prevented violation]

### Loophole Found
Prompt: [Evolved scenario]
New rationalization: [What agent said]
Fix needed: [What to add to skill]
```
