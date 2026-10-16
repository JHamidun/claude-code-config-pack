---
name: sharing-skills
description: "Отправка своего навыка в upstream-репозиторий через PR: ветка, коммит, пуш. Триггеры: «поделись навыком», «контрибьютни skill»."
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
- Локальный клон upstream-репозитория (в `~/.claude` его нет — см. ниже)

> ⚠️ **`~/.claude` — локальный git без remote.** `git remote -v` там пустой, поэтому
> `git pull origin main` / `git push -u origin` оттуда не работают. Навык **копируется**
> из `~/.claude/skills/<name>/` в клон upstream-репо, и вся работа с ветками идёт там.
>
> ⚠️ **Навык — это папка, а не файл.** На диске `skills/<name>/SKILL.md` (+ `scripts/`,
> `references/`, `templates/`), а не `skills/<name>.md`.

## Sharing Workflow

### 1. Get the upstream clone and sync it

```bash
# один раз: форк + клон upstream-репозитория навыков
gh repo fork <owner>/<repo> --clone --remote
cd ~/src/<repo>          # клон, НЕ ~/.claude

git checkout main
git pull upstream main   # upstream добавлен gh repo fork --remote
```

### 2. Create Feature Branch

```bash
skill_name="your-skill-name"
git checkout -b "add-${skill_name}-skill"
```

### 3. Copy the Skill Folder In

```bash
# навык = папка с SKILL.md внутри
cp -r ~/.claude/skills/${skill_name} skills/${skill_name}

# перед копированием прогнать leak-scan: наружу не должно уехать личное
python ~/.claude/skills/leak-scan/scripts/leak_scan.py skills/${skill_name}
```

### 4. Commit Changes

```bash
git add "skills/${skill_name}"
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
# Sync your fork's main (в клоне upstream-репо, не в ~/.claude)
git checkout main
git pull upstream main
git push origin main

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
| PR merge conflicts | Rebase: `git fetch upstream && git rebase upstream/main` |
| "fatal: 'origin' does not appear to be a git repository" | Ты в `~/.claude` — у него нет remote; перейди в клон upstream-репо |
