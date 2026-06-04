---
name: finishing-a-development-branch
description: Use when completing development work - guides through verification, options presentation, and cleanup
---

# Finishing a Development Branch

## Overview

Complete development work through structured verification and options presentation.

**Core principle:** Always verify tests before offering options.

## The Four Steps

### Step 1: Verify Tests Pass

```bash
npm test  # or appropriate test command
```

**If tests fail:** Fix them first. Do not proceed with failing tests.

### Step 2: Determine Base Branch

```bash
git log --oneline -1 origin/main
# or
git log --oneline -1 origin/master
```

### Step 3: Present Exactly Four Options

```markdown
## Work Complete - Choose Next Step

All tests passing. Choose how to proceed:

1. **Merge locally** - Merge to [base branch], delete feature branch
2. **Push and create PR** - Push branch, open pull request
3. **Keep as-is** - Leave branch for later
4. **Discard** - Delete branch and all changes

Which option?
```

### Step 4: Execute Choice

#### Option 1: Merge Locally

```bash
git checkout main
git pull origin main
git merge feature-branch
npm test  # Verify post-merge
git branch -d feature-branch
```

#### Option 2: Push and Create PR

```bash
git push -u origin feature-branch

gh pr create --title "Feature: [description]" --body "$(cat <<'EOF'
## Summary
[Brief description of changes]

## Testing
- All tests passing
- [Additional testing notes]

## Changes
[List of key changes]
EOF
)"
```

#### Option 3: Keep As-Is

```
Understood. Branch preserved at current state.
Remember: Branch name is `feature-branch`
```

#### Option 4: Discard

**Requires confirmation:**
```
⚠️ This will permanently delete branch and all changes.
Type 'CONFIRM' to proceed:
```

Then:
```bash
git checkout main
git branch -D feature-branch
```

## Critical Rules

**Never:**
- Proceed with failing tests
- Merge without post-merge verification
- Discard without explicit confirmation

**Always:**
- Run tests before presenting options
- Show all four options
- Get explicit choice before executing

## Git Worktree Cleanup

If working in a git worktree:

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
- `executing-plans` - After all tasks complete
- `subagent-driven-development` - After implementation done
- Any development workflow reaching completion

**Pairs with:**
- `using-git-worktrees` - For worktree cleanup
