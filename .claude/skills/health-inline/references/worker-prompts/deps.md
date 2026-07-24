# Worker Prompts for Dependency Health Check

> Written 2026-07-18 by analogy with `bug.md` (the only worker-prompts file that
> existed before the health-inline merge) — closes the formerly broken link in
> deps-health-inline. Workers verified to exist: `agents/health/workers/dependency-auditor.md`,
> `agents/health/workers/dependency-updater.md`.

## Dependency Auditor - Detection

```
subagent_type: "dependency-auditor"
description: "Audit all dependencies"
prompt: |
  Execute comprehensive dependency audit.

  ## Audit Categories
  1. **Security vulnerabilities**: `npm audit` / `pnpm audit`
  2. **Outdated packages**: major/minor/patch
  3. **Unused dependencies**: via Knip
  4. **Deprecated packages**
  5. **License compliance issues**

  ## Output
  Generate `dependency-scan-report.md` with structure:

  ```markdown
  # Dependency Scan Report

  **Generated**: {timestamp}
  **Status**: {PASSED/FAILED}

  ## Summary
  - Critical: {count}
  - High: {count}
  - Medium: {count}
  - Low: {count}

  ## Critical Issues
  ### DEP-001: {package}@{version}
  - **Category**: Vulnerability/Outdated/Unused/Deprecated/License
  - **Advisory**: {CVE/GHSA id if applicable}
  - **Description**: {description}
  - **Fix**: {target version or removal}

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

  Return summary: "Found X dependency issues (Y critical, Z high, ...)"
```

---

## Dependency Auditor - Verification

```
subagent_type: "dependency-auditor"
description: "Verification audit"
prompt: |
  Re-audit dependencies after updates.

  ## Tasks
  1. Run full audit (same as initial)
  2. Compare with previous `dependency-scan-report.md`
  3. Identify:
     - Issues that were fixed
     - Issues that remain
     - New issues introduced by updates

  ## Output
  Overwrite `dependency-scan-report.md` with new audit results.

  Return summary:
  - "Verification complete: X fixed, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Dependency Updater - By Priority

```
subagent_type: "dependency-updater"
description: "Update {priority} dependencies"
prompt: |
  Fix all {priority} priority issues from dependency-scan-report.md.

  ## Protocol — ONE dependency at a time
  For EACH issue:

  1. **Read** issue details from report
  2. **Backup** package.json AND the lockfile before the update:
     ```bash
     cp package.json .tmp/current/backups/package.json.backup
     cp pnpm-lock.yaml .tmp/current/backups/pnpm-lock.yaml.backup
     ```
  3. **Update** the single dependency (install exact target version)
  4. **Validate** immediately: `pnpm type-check && pnpm build`
     - If FAIL → rollback this dependency (restore backups, `pnpm install`), mark as failed, continue with next
  5. **Log** change to `.tmp/current/changes/deps-changes.json`:
     ```json
     {
       "files_modified": [{
         "path": "package.json",
         "backup": ".tmp/current/backups/package.json.backup",
         "issue_id": "DEP-001",
         "reason": "{package} {from} -> {to}"
       }]
     }
     ```

  ## Output
  Update `dependency-updates-implemented.md`:

  ```markdown
  # Dependency Updates Report

  **Priority**: {priority}
  **Timestamp**: {timestamp}

  ## Updated
  - [x] DEP-001: {package} {from} → {to}
  - [x] DEP-002: {package} removed (unused)

  ## Failed
  - [ ] DEP-003: {package} → Reason: {build/type-check failure, breaking change}

  ## Summary
  - Updated: X/{total}
  - Failed: Y/{total}

  ## Rollback
  Changes log: `.tmp/current/changes/deps-changes.json`
  ```

  Return: "Updated X/{total} {priority} dependencies"
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

If validation fails after updates:

```bash
# Read changes log
cat .tmp/current/changes/deps-changes.json

# Restore package.json and lockfile from backups
cp .tmp/current/backups/package.json.backup package.json
cp .tmp/current/backups/pnpm-lock.yaml.backup pnpm-lock.yaml

# Reinstall to match restored lockfile
pnpm install
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/deps-changes.json
```
