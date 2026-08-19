---
name: sharing-skills
description: "Contribute your skill upstream via pull request: branch, commit, push. Triggers: «share the skill», «contribute skill»."
---

# Sharing Skills

## Overview

Contribute skills from your local branch back to upstream repositories.

**Workflow:** Branch → Edit/Create skill → Commit → Push → PR

## When to Share

**Share when:**
- Skill applies broadly (not project-specific)
- Pattern/technique others would benefit from
- Well-tested and documented
- Follows writing-skills guidelines

**Keep personal when:**
- Project-specific or organization-specific
- Experimental or unstable
- Contains sensitive information
- Too narrow/niche for general use

## Prerequisites

- `gh` CLI installed and authenticated
- Skill has been tested

## Sharing Workflow

### 1. Ensure You're on Main and Synced

```bash
cd ~/.claude/skills/
git checkout main
git pull origin main
```

### 2. Create Feature Branch

```bash
skill_name="your-skill-name"
git checkout -b "add-${skill_name}-skill"
```

### 3. Create or Edit Skill

```bash
# Create skill file
# skills/your-skill-name.md
```

### 4. Commit Changes

```bash
git add skills/your-skill-name.md
git commit -m "Add ${skill_name} skill

Brief description of what this skill does and why it's useful.

Tested with: [describe testing approach]"
```

### 5. Push to Your Fork

```bash
git push -u origin "add-${skill_name}-skill"
```

### 6. Create Pull Request

```bash
gh pr create \
  --title "Add ${skill_name} skill" \
  --body "$(cat <<'EOF'
## Summary
Brief description of the skill and what problem it solves.

## Testing
Describe how you tested this skill.

## Context
Any additional context about why this skill is needed.
EOF
)"
```

## After PR is Merged

```bash
# Sync your local main
git checkout main
git pull origin main

# Delete feature branch
git branch -d "add-${skill_name}-skill"
git push origin --delete "add-${skill_name}-skill"
```

## Multi-Skill Contributions

**Do NOT batch multiple skills in one PR.**

Each skill should:
- Have its own feature branch
- Have its own PR
- Be independently reviewable

**Why?** Individual skills can be reviewed, iterated, and merged independently.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "gh: command not found" | Install GitHub CLI: https://cli.github.com/ |
| "Permission denied" | Check SSH keys: `gh auth status` |
| "Skill already exists" | Consider different name or coordinate |
| PR merge conflicts | Rebase: `git fetch origin && git rebase origin/main` |
