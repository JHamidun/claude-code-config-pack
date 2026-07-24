# Worker Prompts for Cleanup Health Check

> Written 2026-07-18 by analogy with `bug.md` (the only worker-prompts file that
> existed before the health-inline merge) — closes the formerly broken link in
> cleanup-health-inline. Workers verified to exist: `agents/health/workers/dead-code-hunter.md`,
> `agents/health/workers/dead-code-remover.md`.

## Dead Code Hunter - Detection

```
subagent_type: "dead-code-hunter"
description: "Detect all dead code"
prompt: |
  Execute comprehensive dead code detection scan.

  ## Scan Categories
  1. **Unused imports and exports** (use Knip where available)
  2. **Commented out code blocks**
  3. **Unreachable code**
  4. **Debug statements**: console.log, debugger
  5. **Unused variables and functions**
  6. **Unused dependencies**

  ## Output
  Generate `dead-code-report.md` with structure:

  ```markdown
  # Dead Code Report

  **Generated**: {timestamp}
  **Status**: {PASSED/FAILED}

  ## Summary
  - Critical: {count}
  - High: {count}
  - Medium: {count}
  - Low: {count}

  ## Critical Issues
  ### DEAD-001: {title}
  - **File**: `path/to/file.ts:123`
  - **Category**: Unused Export/Commented Block/Unreachable/Debug/Unused Dependency
  - **Description**: {description}
  - **Removal**: {what exactly to delete}

  ## High Priority Issues
  [same format]

  ## Medium Priority Issues
  [same format]

  ## Low Priority Issues
  [same format]

  ## Validation Results
  - Type Check: {PASSED/FAILED}
  - Build: {PASSED/FAILED}
  ```

  Return summary: "Found X dead code items (Y critical, Z high, ...)"
```

---

## Dead Code Hunter - Verification

```
subagent_type: "dead-code-hunter"
description: "Verification scan"
prompt: |
  Re-scan codebase after cleanup.

  ## Tasks
  1. Run full detection scan (same as initial)
  2. Compare with previous `dead-code-report.md`
  3. Identify:
     - Dead code that was removed
     - Dead code that remains
     - New dead code introduced by removals

  ## Output
  Overwrite `dead-code-report.md` with new scan results.

  Return summary:
  - "Verification complete: X removed, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Dead Code Remover - By Priority

```
subagent_type: "dead-code-remover"
description: "Remove {priority} dead code"
prompt: |
  Remove all {priority} priority dead code from dead-code-report.md.
  Prefer Knip --fix for automated cleanup where applicable.

  ## Protocol
  For EACH item:

  1. **Read** item details from report
  2. **Backup** file before editing:
     ```bash
     cp {file} .tmp/current/backups/{sanitized-path}.backup
     ```
  3. **Log** change to `.tmp/current/changes/cleanup-changes.json`:
     ```json
     {
       "files_modified": [{
         "path": "path/to/file.ts",
         "backup": ".tmp/current/backups/path-to-file.ts.backup",
         "item_id": "DEAD-001",
         "reason": "Removal description"
       }]
     }
     ```
  4. **Remove** the dead code using Edit tool (or Knip --fix)
  5. **Validate** after each removal: `pnpm type-check`

  ## Output
  Update `dead-code-cleanup-summary.md`:

  ```markdown
  # Dead Code Cleanup Report

  **Priority**: {priority}
  **Timestamp**: {timestamp}

  ## Removed
  - [x] DEAD-001: {description} → Removed from `file.ts:123`
  - [x] DEAD-002: {description} → Removed from `other.ts:45`

  ## Failed
  - [ ] DEAD-003: {description} → Reason: {why failed}

  ## Summary
  - Removed: X/{total}
  - Failed: Y/{total}

  ## Rollback
  Changes log: `.tmp/current/changes/cleanup-changes.json`
  ```

  Return: "Removed X/{total} {priority} dead code items"
```

---

## Inline Quality Gate

Execute directly (no Task tool):

```bash
# Type check
pnpm type-check
# Exit code 0 = PASS, non-zero = FAIL

# Build
pnpm build
# Exit code 0 = PASS, non-zero = FAIL
```

**Decision Logic**:
- Both PASS → continue workflow
- Any FAIL → stop, report error, suggest rollback

---

## Rollback Protocol

If validation fails after removals:

```bash
# Read changes log
cat .tmp/current/changes/cleanup-changes.json

# For each modified file, restore from backup
cp .tmp/current/backups/{file}.backup {original-path}

# For each created file, delete
rm {created-file-path}
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/cleanup-changes.json
```
