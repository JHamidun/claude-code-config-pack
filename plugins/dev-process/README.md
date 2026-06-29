# Dev Process

> TDD, systematic debugging, planning, code review, worktrees, parallel agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `brainstorming` | Use when starting new features, planning implementations, or exploring solutions - guides structured dialogue to transform rough ideas into validated… |
| `code-reviewer` | Comprehensive code review skill for TypeScript, JavaScript, Python, Swift, Kotlin, Go. |
| `condition-based-waiting` | Use when tests have race conditions, timing dependencies, or inconsistent pass/fail behavior - replaces arbitrary timeouts with condition polling to… |
| `dispatching-parallel-agents` | Use when facing 3+ independent failures that can be investigated without shared state - dispatches multiple agents to investigate and fix independent… |
| `executing-plans` | Use when partner provides a complete implementation plan to execute in controlled batches with review checkpoints |
| `finishing-a-development-branch` | Use when completing development work - guides through verification, options presentation, and cleanup |
| `parse-git-status` | Parse git status output into structured data showing staged, modified, and untracked files. |
| `receiving-code-review` | Use when receiving code review feedback - requires technical rigor and verification, not performative agreement or blind implementation |
| `requesting-code-review` | Use when completing tasks, implementing major features, or before merging to verify work meets requirements |
| `rollback-changes` | Automatically rollback changes from failed workflow phases using changes log files. |
| `root-cause-tracing` | Use when errors occur deep in execution - systematically trace bugs backward through call stack, adding instrumentation when needed, to identify… |
| `run-quality-gate` | Execute quality gate validation with configurable blocking behavior. |
| `scaling-stage` | Letterbox wrapper for fixed-size content (video, posters, fixed mockups) — a deck-stage for non-slides. |
| `subagent-driven-development` | Use when executing implementation plans within a single session - dispatches fresh subagents for each task with code review checkpoints between them |
| `systematic-debugging` | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes |
| `test-driven-development` | Use when implementing any feature or bugfix - write the test first, watch it fail, write minimal code to pass; ensures tests actually verify behavior… |
| `testing-anti-patterns` | Use when writing or changing tests - prevents testing mock behavior, production pollution with test-only methods, and mocking without understanding… |
| `testing-skills-with-subagents` | Use when creating or editing skills - applies RED-GREEN-REFACTOR cycle to process documentation by running baseline without skill, writing to address… |
| `using-git-worktrees` | Use when starting feature work that needs isolation from current workspace - creates isolated git worktrees with smart directory selection and safety… |
| `validate-plan-file` | Validate that orchestrator plan files conform to expected JSON schema. |
| `verification-before-completion` | Use before claiming any work is complete - requires fresh verification evidence before any status claim |
| `writing-plans` | Use when creating implementation plans for features - breaks down work into bite-sized TDD tasks with exact file paths, code examples, and… |

### Agents

- `code-reviewer`

### Commands

- `/analyze`
- `/bug-triage`
- `/changelog`
- `/code-review`
- `/parallel-dev`
- `/push`
- `/review`
- `/worktree`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install dev-process@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Credits

Several process skills (brainstorming, systematic-debugging, test-driven-development, writing/executing-plans, root-cause-tracing, verification-before-completion, using-git-worktrees, dispatching-parallel-agents, subagent-driven-development, requesting/receiving-code-review) are adapted from **Superpowers** by Jesse Vincent / Prime Radiant — https://github.com/obra/superpowers.

## Related plugins

`dev-core` · `code-health` · `browser-testing` · `gsd`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
