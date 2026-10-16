---
name: rollback-changes
description: "Откат упавшей фазы воркфлоу по changes-log: файлы из бэкапа, revert коммитов, чистка артефактов. Триггеры: «откати фазу», «верни как было». НЕ копия файла→version-snapshots."
allowed-tools: Bash, Read, Write
---

# Rollback Changes

Rollback failed workflow phases by reading changes log and reversing tracked modifications.

## When to Use

- Workflow phase fails and needs state restoration
- Error recovery in worker agents
- Quality gate failures requiring revert

## Boundary with `version-snapshots`: check what is on disk first

"Roll it back" / "put it back the way it was" fits this skill and `version-snapshots`
equally well, so the phrasing decides nothing. What decides is which artifact exists:

- `.bug-changes.json` (or another `.{domain}-changes.json`) plus `.rollback/` backups →
  this skill;
- a `.snapshots/` directory holding timestamped copies of one file → `version-snapshots`,
  where rollback is a single `cp` over the original;
- neither → nothing to reverse here; fall back to `git`.

The deeper difference is who wrote the safety net and what it holds. A snapshot is taken
**deliberately and in advance**, before editing one artifact, and stores that file's whole
state. A changes log is written **by a worker as the phase runs**; it stores no project
state at all — only the list of what the phase did, plus the inverse action for each entry.
So a snapshot restores a file to the exact look you saw, while this skill restores the
project to "the phase never ran" — including deleting files the phase created and
reverting its commits. Those are different outcomes; picking the wrong one loses work.

## Input

```json
{
  "changes_log_path": ".bug-changes.json",
  "phase": "bug-fixing",
  "confirmation_required": true
}
```

## Changes Log Format

```json
{
  "phase": "bug-fixing",
  "timestamp": "2025-10-18T14:30:00Z",
  "files_modified": [{"path": "src/app.ts", "backup": ".rollback/src-app.ts.backup"}],
  "files_created": ["src/new-file.ts"],
  "commands_executed": ["pnpm install", "pnpm build"],
  "git_commits": ["abc123"],
  "artifacts": [".bug-fixing-plan.json"]
}
```

## Process

### 1. Read & Parse Changes Log
Use Read tool to load JSON. Validate required fields: phase, timestamp, files_modified, files_created, commands_executed, git_commits.

### 2. Request Confirmation (if required)
Show summary of changes to revert. If user declines, return dry run result.

### 3. Restore Modified Files
```bash
cp "{backup}" "{path}"  # For each {path, backup} in files_modified
```

### 4. Delete Created Files
```bash
rm -f "{file}"  # For each file in files_created
```

### 5. Revert Commands
- `pnpm install` → re-run to restore lockfile
- `git add *` → `git restore --staged .`
- `pnpm build` → `rm -rf dist/`
- Other → log warning (cannot auto-revert)

### 6. Revert Git Commits
```bash
git revert --no-edit {sha}  # In reverse order
```

### 7. Cleanup Artifacts
Remove plan files and temporary artifacts.

## Output

```json
{
  "success": true,
  "phase": "bug-fixing",
  "actions_taken": ["Restored src/app.ts", "Deleted src/new-file.ts", "Reverted abc123"],
  "files_restored": 1,
  "files_deleted": 1,
  "git_commits_reverted": 1,
  "errors": [],
  "warnings": ["Backup not found: .rollback/file.backup (skipped)"]
}
```

## Error Handling

- **Missing log**: Return error "Changes log not found"
- **Invalid JSON**: Return parsing error
- **Backup not found**: Log warning, continue (partial rollback OK)
- **Git conflicts**: Log error with manual instructions, continue

## Safety Features

- Confirmation by default before any changes
- Partial rollback acceptable (documented in warnings)
- Never delete without verifying backup exists
- All actions logged for audit trail

## Worker Integration

Workers should track changes during operations:
1. Create `.{domain}-changes.json` before modifications
2. Create backups in `.rollback/` for modified files
3. Log all file creates, commands, and commits
4. On failure: invoke rollback-changes with confirmation_required=false
