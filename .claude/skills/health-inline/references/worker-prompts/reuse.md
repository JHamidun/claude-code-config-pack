# Worker Prompts for Code Reuse Health Check

> Written 2026-07-18 by analogy with `bug.md` (the only worker-prompts file that
> existed before the health-inline merge) — closes the formerly broken link in
> reuse-health-inline. Workers verified to exist: `agents/health/workers/reuse-hunter.md`,
> `agents/health/workers/reuse-fixer.md`.
> NOTE: reuse mode has NO critical priority — scale is high → medium → low.

## Reuse Hunter - Detection

```
subagent_type: "reuse-hunter"
description: "Detect all code duplications"
prompt: |
  Execute comprehensive code duplication scan.

  ## Scan Categories
  1. **Duplicated TypeScript interfaces/types**
  2. **Duplicated Zod schemas**
  3. **Duplicated constants and configuration objects**
  4. **Copy-pasted utility functions**
  5. **Similar code patterns that should be abstracted**

  ## Output
  Generate `reuse-hunting-report.md` with structure:

  ```markdown
  # Reuse Hunting Report

  **Generated**: {timestamp}
  **Status**: {PASSED/FAILED}

  ## Summary
  - High: {count}
  - Medium: {count}
  - Low: {count}

  ## High Priority Duplications
  ### DUP-001: {title}
  - **Locations**: `path/a.ts:10`, `path/b.ts:42`
  - **Category**: Type/Schema/Constant/Utility/Pattern
  - **Description**: {what is duplicated}
  - **Canonical location**: {suggested Single Source of Truth, usually packages/shared-types/src/}

  ## Medium Priority Duplications
  [same format]

  ## Low Priority Duplications
  [same format]

  ## Validation Results
  - Type Check: {PASSED/FAILED}
  - Build: {PASSED/FAILED}
  ```

  Return summary: "Found X duplications (Y high, Z medium, W low)"
```

---

## Reuse Hunter - Verification

```
subagent_type: "reuse-hunter"
description: "Verification scan"
prompt: |
  Re-scan codebase after consolidation.

  ## Tasks
  1. Run full detection scan (same as initial)
  2. Compare with previous `reuse-hunting-report.md`
  3. Identify:
     - Duplications that were resolved
     - Duplications that remain
     - New duplications introduced by consolidation

  ## Output
  Overwrite `reuse-hunting-report.md` with new scan results.

  Return summary:
  - "Verification complete: X resolved, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Reuse Fixer - By Priority

```
subagent_type: "reuse-fixer"
description: "Consolidate {priority} duplications"
prompt: |
  Consolidate all {priority} priority duplications from reuse-hunting-report.md
  using the Single Source of Truth pattern.

  ## Protocol
  For EACH duplication:

  1. **Read** duplication details from report
  2. **Backup** every affected file before editing:
     ```bash
     cp {file} .tmp/current/backups/{sanitized-path}.backup
     ```
  3. **Determine canonical location** (usually shared-types or shared package)
  4. **Create/update canonical file** with the type/schema/constant
  5. **Replace duplicates** with imports/re-exports
     (`export * from '@package/shared-types/{module}'` — NEVER copy code between packages)
  6. **Log** change to `.tmp/current/changes/reuse-changes.json`:
     ```json
     {
       "files_modified": [{
         "path": "path/to/file.ts",
         "backup": ".tmp/current/backups/path-to-file.ts.backup",
         "dup_id": "DUP-001",
         "reason": "Consolidated into packages/shared-types/src/{module}"
       }]
     }
     ```
  7. **Validate** after each consolidation: `pnpm type-check`

  ## Output
  Update `reuse-consolidation-implemented.md`:

  ```markdown
  # Reuse Consolidation Report

  **Priority**: {priority}
  **Timestamp**: {timestamp}

  ## Consolidated
  - [x] DUP-001: {description} → Canonical: `shared-types/src/x.ts`, re-exported in 3 files
  - [x] DUP-002: {description} → Canonical: `shared-types/src/y.ts`

  ## Failed
  - [ ] DUP-003: {description} → Reason: {why failed}

  ## Summary
  - Consolidated: X/{total}
  - Failed: Y/{total}

  ## Rollback
  Changes log: `.tmp/current/changes/reuse-changes.json`
  ```

  Return: "Consolidated X/{total} {priority} duplications"
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

If validation fails after consolidation:

```bash
# Read changes log
cat .tmp/current/changes/reuse-changes.json

# For each modified file, restore from backup
cp .tmp/current/backups/{file}.backup {original-path}

# For each created canonical file, delete
rm {created-file-path}
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/reuse-changes.json
```
