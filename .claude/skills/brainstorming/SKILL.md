---
name: brainstorming
description: Use when starting new features, planning implementations, or exploring solutions - guides structured dialogue to transform rough ideas into validated designs with documentation
---

# Brainstorming Ideas Into Designs

## Overview

Transform rough concepts into fully-formed specifications through structured dialogue.

**Core principle:** Understand before building. One question at a time.

**Don't use during:** Clear "mechanical" processes where implementation is obvious.

## Core Workflow

### Phase 1: Discovery (Divergent)

Review existing project state, then incrementally clarify:

1. **Review context** - What exists? What's the goal?
2. **Ask one question per message** - Avoid overwhelming
3. **Prefer multiple choice** - Easier to answer
4. **Clarify purpose, constraints, success criteria**

```markdown
## Discovery Questions Template

1. What problem does this solve?
2. Who is the primary user?
3. What's the MVP scope?
4. What are the hard constraints?
5. How will we measure success?
```

### Phase 2: Design Presentation (Convergent)

Once concept understood, present design in sections:

1. **Architecture** (200-300 words)
2. **Components** (200-300 words)
3. **Data flow** (200-300 words)
4. **Error handling** (200-300 words)
5. **Testing approach** (200-300 words)

**Validate each section before proceeding.**

### Phase 3: Documentation & Next Steps

1. Save validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
2. Git commit the design
3. Optionally transition to implementation planning

## Key Principles

- **One question at a time** - Avoid overwhelming collaborators
- **YAGNI ruthlessly** - Eliminate unnecessary features
- **Incremental validation** - Section-by-section feedback
- **Explore alternatives** - Present 2-3 approaches with trade-offs

## Brainstorming Techniques

### SCAMPER Framework

| Letter | Question |
|--------|----------|
| **S**ubstitute | What can be replaced? |
| **C**ombine | What can be merged? |
| **A**dapt | What similar thing exists? |
| **M**odify | What can be changed/amplified? |
| **P**ut to other uses | Different context? |
| **E**liminate | What can be removed? |
| **R**everse | What if done opposite? |

### Six Thinking Hats

| Hat | Focus |
|-----|-------|
| White | Facts - What do we know? |
| Red | Emotions - What feels right? |
| Black | Caution - What could go wrong? |
| Yellow | Optimism - What's the upside? |
| Green | Creativity - What alternatives? |
| Blue | Process - What's next? |

### "How Might We" Questions

Transform problems into opportunities:

```markdown
❌ Problem: "Users don't complete onboarding"

✅ HMW Questions:
- How might we make onboarding feel like a game?
- How might we reduce onboarding to 30 seconds?
- How might we show immediate value before onboarding?
```

### Reverse Brainstorming

1. **Define:** "How can we improve retention?"
2. **Reverse:** "How can we LOSE all customers?"
3. **Generate:** Never respond, make it harder, raise prices randomly
4. **Flip:** Respond in 1 hour, simplify onboarding, transparent pricing

## Idea Prioritization

### Impact/Effort Matrix

```
        HIGH IMPACT
             │
    Quick    │    Big Bets
    Wins     │    (plan carefully)
   ──────────┼──────────────
    Fill-ins │    Time Sinks
   (if time) │    (avoid)
             │
        LOW IMPACT

    LOW EFFORT ──────── HIGH EFFORT
```

### RICE Score

```
Score = (Reach × Impact × Confidence) / Effort

Reach: Users affected per quarter
Impact: 0.25 (minimal) to 3 (massive)
Confidence: 0-100%
Effort: Person-months
```

## Idea Development Template

```markdown
# Idea: [Name]

## One-liner
[Describe in one sentence]

## Problem it solves
[What pain point?]

## Target user
[Who benefits?]

## Key features
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

## Trade-offs
| Approach | Pros | Cons |
|----------|------|------|
| Option A | ... | ... |
| Option B | ... | ... |

## Risks
- [Risk 1]
- [Risk 2]

## Next steps
1. [Validate assumption X]
2. [Prototype Y]
```

## Design Documentation Format

```markdown
# Design: [Feature Name]
Date: YYYY-MM-DD

## Context
[Why are we doing this?]

## Requirements
- [ ] Must have: ...
- [ ] Should have: ...
- [ ] Nice to have: ...

## Architecture
[High-level design]

## Components
[Key modules and responsibilities]

## Data Flow
[How data moves through system]

## Error Handling
[Failure modes and recovery]

## Testing Strategy
[How we verify correctness]

## Alternatives Considered
| Option | Trade-off |
|--------|-----------|
| ... | ... |

## Decision
[What we chose and why]
```

## Integration with Git Worktrees

After design is approved:
1. Use `using-git-worktrees` skill to create isolated workspace
2. Implement in worktree
3. Use `finishing-a-development-branch` for completion

## Session Facilitation

```markdown
## Brainstorm Session (60 min)

1. **Setup** (5 min) - State problem, review rules
2. **Warm-up** (5 min) - Quick creative exercise
3. **Ideation** (15 min) - Free generation, no discussion
4. **Sharing** (10 min) - Each shares top 3
5. **Building** (10 min) - Combine concepts
6. **Voting** (5 min) - Dot voting
7. **Action** (10 min) - Define next steps
```

## Tips

1. **Warm up** - начни с разминки
2. **Defer judgment** - критика потом
3. **Go for quantity** - количество важнее качества
4. **Build on ideas** - развивай чужие мысли
5. **Visual thinking** - рисуй, не только пиши
6. **Time-box** - ограничь время
7. **Document everything** - записывай ВСЁ
