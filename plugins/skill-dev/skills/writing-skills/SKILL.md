---
name: writing-skills
description: Use when creating new skills - applies TDD principles to process documentation to ensure skills prevent actual agent failures
---

# Writing Skills

## Overview

Create skills that effectively guide agent behavior under pressure.

**Core principle:** No skill without a failing test first.

## Skill Types

| Type | Purpose | Testing Approach |
|------|---------|------------------|
| Technique | Enforce discipline (TDD, debugging) | Pressure scenarios |
| Pattern | Guide decisions (architecture) | Decision scenarios |
| Reference | Provide information (API docs) | Accuracy checks |

## SKILL.md Structure

```yaml
---
name: skill-name
description: Use when [trigger] - [what it does]
---

# Skill Name

## Overview
[1-2 sentences explaining the skill]

## When to Use
[Triggers for when this skill applies]

## Core Content
[The actual guidance]

## Common Mistakes
[What to avoid]

## Red Flags
[Signs of violation]
```

## Description Format

The description field is critical for discoverability:

```yaml
# ✅ GOOD: Trigger + action
description: Use when fixing bugs - traces errors backward through call stack to find root cause

# ❌ BAD: Just describes
description: A skill for debugging code
```

Include:
- Trigger ("Use when...")
- What the skill does
- Key differentiator

## TDD for Skills

### RED Phase

1. Design pressure scenario
2. Run agent WITHOUT skill
3. Observe failure
4. Capture exact rationalization

```markdown
## Baseline Test

Prompt: "Fix this bug quickly, we're in a hurry"

Agent response (no skill):
"I'll just fix the symptom since we're pressed for time..."

Failure: Fixed symptom, not root cause
Rationalization: "pressed for time"
```

### GREEN Phase

1. Write minimal skill addressing failure
2. Run agent WITH skill
3. Verify correct behavior

```markdown
## With Skill

Added rule: "Never fix symptoms. Always trace to root cause,
even under time pressure."

Agent response (with skill):
"Even though we're in a hurry, I need to trace this to the
root cause. Fixing symptoms will cost more time later..."

Success: Traced to root cause
```

### REFACTOR Phase

1. Identify new rationalizations
2. Add explicit counters
3. Test again

## Rationalization Tables

Include tables of common excuses and counters:

```markdown
| Rationalization | Counter |
|-----------------|---------|
| "Time pressure" | Time pressure makes root cause MORE important |
| "It's simple" | Simple bugs have complex causes |
| "Just this once" | Every exception becomes precedent |
```

## Red Flags Section

List behaviors indicating skill violation:

```markdown
## Red Flags

- Fixing code without reproducing the bug first
- Skipping stack trace analysis
- Multiple "quick fixes" in succession
- "Let me just try..."
```

## Checklists

For skills with multiple steps, include checklists:

```markdown
## Debugging Checklist

- [ ] Reproduced the bug
- [ ] Read full error message
- [ ] Traced call stack
- [ ] Identified root cause
- [ ] Wrote failing test
- [ ] Fixed root cause
- [ ] Verified fix
```

## Deployment

1. Test skill with `testing-skills-with-subagents`
2. Place in `~/.claude/skills/`
3. Verify skill appears in available skills

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Vague guidance | Agents interpret loosely | Be extremely specific |
| No red flags | Can't detect violations | List violation symptoms |
| Missing rationalizations | Agents find loopholes | Test under pressure |
| Abstract examples | Hard to apply | Use concrete code/scenarios |
| No checklist | Steps get skipped | Add verification checklist |

## Skill Quality Checklist

Before deploying:

- [ ] Description has trigger + action
- [ ] Tested with pressure scenarios
- [ ] All discovered rationalizations countered
- [ ] Red flags section exists
- [ ] Examples are concrete, not abstract
- [ ] Checklist included (if multi-step)
