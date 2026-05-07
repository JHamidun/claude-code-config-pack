# Workflow: Coding Tasks

> Разработка, исправление багов, рефакторинг, review

## Keywords
`код`, `fix`, `implement`, `refactor`, `bug`, `feature`, `PR`, `review`, `code`

## Inputs
- **task**: описание задачи из Todoist
- **type**: bug_fix | feature | refactor | review | docs
- **codebase**: какой проект
- **priority**: P0 (critical) | P1 (high) | P2 (medium) | P3 (low)

## Steps

### 1. Understand the Task
```
Questions:
- What exactly needs to be done?
- Where in the codebase? (files, modules)
- What's the acceptance criteria?
- Are there tests?
- Who needs to review?
```

### 2. Context Gathering
```
Tool: Memory MCP + Codebase exploration
Get:
- Related past changes
- Architecture decisions
- Team conventions
- Similar implementations
```

### 3. Create Work Plan
```
Template:

## Task: [title]
Type: [bug_fix|feature|refactor]
Priority: [P0-P3]

### Understanding
- [What's broken / What's needed]
- [Root cause analysis if bug]

### Approach
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Files to Touch
- `path/to/file1.py`
- `path/to/file2.ts`

### Tests Needed
- [ ] Unit test for X
- [ ] Integration test for Y

### Risks
- [Risk 1]
- [Risk 2]
```

### 4. Execute by Type

#### Bug Fix
```
1. Reproduce the bug
2. Write failing test
3. Find root cause
4. Fix with minimal changes
5. Verify test passes
6. Check for regressions
7. Document fix
```

#### New Feature
```
1. Design approach
2. Create branch
3. Implement in small commits
4. Write tests (TDD preferred)
5. Manual testing
6. Documentation
7. PR creation
```

#### Refactor
```
1. Ensure tests exist (add if not)
2. Small, atomic changes
3. Run tests after each change
4. No functional changes
5. Document architectural decisions
```

#### Code Review
```
1. Understand context (PR description, linked issues)
2. Check for:
   - Logic correctness
   - Edge cases
   - Security issues
   - Performance
   - Code style
   - Test coverage
3. Leave constructive comments
4. Approve or request changes
```

### 5. Quality Assurance
```
Checklist:
- [ ] Tests pass
- [ ] Linter clean
- [ ] No console errors
- [ ] Edge cases handled
- [ ] Error handling proper
- [ ] Performance acceptable
- [ ] Security reviewed (if applicable)
```

### 6. PR & Commit
```
Commit format:
[type]: [short description]

[longer description if needed]

Types: feat, fix, refactor, docs, test, chore

Example:
fix: Resolve race condition in message queue

Added mutex lock to prevent concurrent access
to shared state. Fixes #123.
```

### 7. Track Completion
```
Tool: Todoist + Linear (if work task)
- Mark task done
- Link PR
- Update any dependent tasks
```

## Quality Checks
- [ ] Task понят полностью (не половина)
- [ ] Tests написаны/обновлены
- [ ] Code reviewed (self или peer)
- [ ] Linting passed
- [ ] Documentation updated
- [ ] No obvious regressions

## Completion Criteria
- Code merged или PR создан
- Tests passing
- Task marked done in Todoist
- Linear updated (if applicable)

## Time Estimate by Type
- **Small bug fix**: 15-30 minutes
- **Medium feature**: 1-3 hours
- **Large feature**: 4+ hours (break into subtasks)
- **Refactor**: varies
- **Code review**: 15-45 minutes

## Routing Rules

### When to use Linear (work tasks)
```
Keywords: sprint, jira, issue, work, client, production
→ Create Linear issue, link to Todoist
```

### When to stay in Todoist (personal)
```
Keywords: personal, side project, learning, experiment
→ Keep in Todoist only
```

## Claude Code Integration

### Quick Commands
```bash
# Review код
/kimi-review src/path/

# Исправить код
/kimi-fix src/path/file.py

# Analyze архитектуру
/kimi-reasoning "Architecture analysis of X"

# Generate tests
Task(subagent_type="qa-engineer", prompt="Write tests for X")
```

### Agent Selection
```
Simple fix → Direct edit (no agent)
Complex feature → general-purpose agent
Architecture → software-architect agent
Security concern → security-engineer agent
Performance → kimi-performance-optimizer agent
```

## Notes
- Always create branch for non-trivial changes
- Small commits > big commits
- Tests before fix (TDD) where practical
- Save learnings to Memory for future reference
- Track time spent for estimation improvement
