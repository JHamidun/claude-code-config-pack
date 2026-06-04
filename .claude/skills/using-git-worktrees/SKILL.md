---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

### 1. Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

If found: Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

If preference specified: Use it without asking.

### 3. Ask User

If no directory exists and no CLAUDE.md preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories

**MUST verify .gitignore before creating worktree:**

```bash
grep -q "^\.worktrees/$" .gitignore || grep -q "^worktrees/$" .gitignore
```

**If NOT in .gitignore:**
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

```bash
# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Verify Clean Baseline

```bash
npm test  # or appropriate test command
```

**If tests fail:** Report failures, ask whether to proceed or investigate.
**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify .gitignore) |
| `worktrees/` exists | Use it (verify .gitignore) |
| Neither exists | Check CLAUDE.md → Ask user |
| Not in .gitignore | Add it immediately + commit |
| Tests fail during baseline | Report failures + ask |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip .gitignore verification | Always check before creating |
| Assume directory location | Follow priority order |
| Proceed with failing tests | Report failures, get permission |
| Hardcode setup commands | Auto-detect from project files |

## Cleanup

After work is complete, use `finishing-a-development-branch` skill which handles:
- Merge or PR creation
- Worktree removal
- Branch cleanup

## Manual Cleanup

```bash
# Return to main worktree
cd /path/to/main/repo

# Remove worktree
git worktree remove /path/to/worktree

# Clean up branch if merged
git branch -d feature-branch
```

## Integration

**Called by:**
- `brainstorming` - When design approved and implementation follows
- Any skill needing isolated workspace

**Pairs with:**
- `finishing-a-development-branch` - Cleanup after work complete
