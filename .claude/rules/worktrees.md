# Git Worktrees Workflow

## What Are Worktrees?
Git worktrees let you have multiple working copies of the same repo, each on a different branch. Perfect for parallel development without stashing or switching branches.

## When to Use Worktrees
- Working on feature while hotfix is needed
- Running tests on one branch while coding on another
- Agent isolation: let subagent work in a worktree without affecting your current state
- Comparing implementations side-by-side

## Quick Commands

### Create a worktree
```bash
git worktree add ../my-feature feature/my-feature
# Creates ../my-feature/ on branch feature/my-feature
```

### List worktrees
```bash
git worktree list
```

### Remove a worktree
```bash
git worktree remove ../my-feature
```

### Clean up stale worktrees
```bash
git worktree prune
```

## Claude Code Integration

### Using /worktree command
```
/worktree create my-feature    # Create new worktree + branch
/worktree list                 # Show all worktrees
/worktree remove my-feature    # Clean up
/worktree cleanup              # Remove all stale worktrees
```

### Agent Isolation
Claude Code agents can run in isolated worktrees:
```
Agent(
  isolation="worktree",
  prompt="Implement feature X without affecting current branch"
)
```
- Agent gets its own copy of the repo
- Changes are on a separate branch
- If agent makes no changes, worktree is auto-cleaned
- If changes are made, you get the branch name to review/merge

## Best Practices
1. **Name worktrees meaningfully** — `fix/login-bug`, `feat/new-api`
2. **Clean up after merging** — `git worktree remove` after PR is merged
3. **Don't nest worktrees** — keep them as siblings, not inside each other
4. **Use for risky experiments** — easy to discard entire worktree
5. **Combine with agents** — let agents work in isolation, review their branch

## Gotchas
- Can't have two worktrees on the same branch
- `node_modules/` must be installed separately in each worktree
- `.env` files are NOT shared — copy manually if needed
- Worktrees share `.git` — commits are visible across all worktrees
