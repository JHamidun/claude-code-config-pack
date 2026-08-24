# Scaling Patterns

> Extends `delegation.md` with decision trees, parallel patterns, and context management.

## Decision Tree: How Many Agents?

Level 0-3 decision tree (single file vs orchestrator vs full workflow) → `rules/delegation.md`.

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
| Long-running session (>50 turns) | /clear, предварительно сохранив learnings в память (rules/auto-learning.md) |
| Parallel features | Git worktrees via /worktree |
| Large file analysis | Read with offset+limit, not full file |
| Repetitive operations | Write a script, run once |

## Model Selection for Subagents

**Канон: движок ВСЕХ text-воркеров = Fable 5** (`model: "fable"`), ≤5 одновременно (комфорт 3-4).

| Роль | Модель | Когда |
|------|--------|-------|
| Text-воркер (default) | fable | ВСЕГДА — любой субагент, который читает/пишет код или текст |
| Массовые простые прогоны | haiku | ТОЛЬКО 10+ параллельных тривиальных задач (классификация, поиск) |
| Оркестратор / подхват | opus | Основная сессия; подхват после лимита Fable (resume + смена model) |

Сложность задачи регулируй **глубиной промпта и контекстом** (opus-level / standard / light — это уровни промпта), а НЕ сменой движка. Decision tree уровней → `rules/model-selection.md`.

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

### Incremental Output (mandatory for long workers)

Субагент отдаёт результат ПО ХОДУ работы, а не одним куском в конце: append в файл/отчёт
после каждой завершённой единицы (файл, глава, кластер правок), Edit'ы применяются сразу.
Финальный ответ агента = краткое summary, а не сам результат. Причина: сессия обрывается
по лимиту/крэшу, и всё, что не на диске, теряется (прецедент: 345K токенов разведки).
В промпт долгого воркера и в COMMON каждой Workflow-волны вставлять блок CRASH-SAFE PROTOCOL
**дословно** из `${HOME}/.claude/workflows/CRASH-SAFE-PROTOCOL.md` (~200 токенов на агента).

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
