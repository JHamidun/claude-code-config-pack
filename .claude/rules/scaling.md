# Scaling Patterns

> Extends `delegation.md` with decision trees, parallel patterns, and context management.

## Decision Tree: How Many Agents?

```
Task received
|
+-- Single file, <50 lines change?
|   +-- Level 0: Do it yourself (no agents)
|       Examples: typo fix, add import, rename variable, update config
|
+-- 2-5 files, single feature?
|   +-- Level 1: One specialized agent
|       Examples: add API endpoint, implement component, fix bug
|       Pattern: Agent(subagent_type="senior-developer", prompt="...")
|
+-- 5+ files, multiple concerns?
|   +-- Level 2: Orchestrator + workers
|       Examples: new feature with frontend+backend+tests
|       Pattern: orchestrator dispatches to frontend-dev, backend-dev, test-writer
|
+-- Project-wide, multi-system?
    +-- Level 3: Full workflow (plan -> agents -> QA)
        Examples: new microservice, major refactoring, security audit
        Pattern: Plan mode -> parallel agents -> code-reviewer -> qa-specialist
```

## Parallel Agent Patterns

### Pattern 1: Fan-out Research (2-3 agents)

When you need information from multiple parts of the codebase:

```
Agent 1 (Explore): "Find all API endpoints"
Agent 2 (Explore): "Find all database models"
Agent 3 (Explore): "Find all test patterns"
-> Synthesize results -> Plan implementation
```

Best for: onboarding to unfamiliar codebase, pre-implementation research.

### Pattern 2: Parallel Implementation (2-4 agents)

When changes are independent and do not touch the same files:

```
Agent 1 (frontend-dev): "Implement UI component"
Agent 2 (backend-dev): "Implement API endpoint"
Agent 3 (test-writer): "Write integration tests"
-> Review all changes -> Integrate
```

Best for: full-stack features, multi-module changes.

### Pattern 3: Pipeline (sequential agents)

When each step depends on the previous output:

```
Agent 1 (software-architect): "Design architecture"
-> Agent 2 (senior-developer): "Implement based on design"
-> Agent 3 (code-reviewer): "Review implementation"
-> Agent 4 (test-writer): "Write tests for reviewed code"
```

Best for: greenfield features, complex refactors requiring design-first.

### Pattern 4: Worktree Isolation

When you need to test changes without affecting current work:

```
Agent(isolation="worktree", prompt="Implement feature X")
-> Review changes in isolated branch
-> Merge or discard
```

Best for: experimental changes, risky refactors, parallel feature branches.

## Context Window Management at Scale

| Situation | Strategy |
|-----------|----------|
| Reading 10+ files | Use Explore agent (saves main context) |
| Multiple sequential tasks | /compact between tasks |
| Long-running session (>50 turns) | /clear and /session-restore |
| Parallel features | Git worktrees via /worktree |
| Large file analysis | Read with offset+limit, not full file |
| Repetitive operations | Write a script, run once |

## Model Selection for Subagents

| Task complexity | Model | Rationale |
|-----------------|-------|-----------|
| Simple edits, search | haiku | Fast, cheap, sufficient |
| Standard features, reviews | sonnet | Good balance of speed and quality |
| Architecture, complex bugs | opus | Maximum reasoning quality |

Default to **sonnet** for subagents. Escalate to opus only when the task
requires deep reasoning or cross-system analysis.

## When NOT to Scale

- Simple tasks do not need agents -- overhead exceeds benefit
- If you can do it in <5 tool calls, do it directly
- Do not parallelize dependent tasks -- sequential is safer
- Do not create agents just to delegate; create them to parallelize or specialize
- Single-concern bugs: fix directly, delegate only if root cause is unclear

## Cross-Worker Communication

### Scratchpad Directory
`~/.claude/scratchpad/` — shared directory for cross-agent durable knowledge.
Workers can read and write here without permission prompts. Use for:
- Research summaries that multiple workers need
- Shared specs and design docs
- Intermediate results between pipeline stages

Clean up after task completion.

## Anti-Patterns

| Anti-pattern | Why it fails | Fix |
|--------------|-------------|-----|
| Agent per file | Too much overhead, merge conflicts | One agent per concern |
| Opus for everything | Slow, expensive, often unnecessary | Use haiku/sonnet for simple tasks |
| No synthesis step | Parallel results never integrated | Always review + integrate after fan-out |
| Skipping Explore | Main context bloated with search | Delegate codebase exploration |
| Sequential when parallel is possible | Wastes time | Identify independent tasks, fan out |
| "Based on your findings" | Delegates understanding, not work | Synthesize findings, write specific spec |
| Lazy delegation prompts | Worker has no context | Include file paths, line numbers, what to change |

## Mandatory Delegations (reference from delegation.md)

| Task | Agent | Why |
|------|-------|-----|
| Code review | code-reviewer | Specialized checklist |
| Bug hunting | bug-hunter -> bug-fixer | Systematic debugging |
| Tests | test-writer | Mocking, coverage |
| Security | security-scanner | OWASP Top 10 |
| Codebase search | Explore agent | Saves main context |
| Performance | performance-optimizer | Core Web Vitals |
| Dead code | dead-code-hunter | Knip, accurate detection |

## Quick Reference

```
< 5 tool calls     -> do it yourself
5-15 tool calls    -> one agent (Level 1)
15+ tool calls     -> orchestrator (Level 2)
multi-system       -> full workflow (Level 3)
```
