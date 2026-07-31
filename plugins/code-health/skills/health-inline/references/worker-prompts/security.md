# Worker Prompts for Security Health Check

> Written 2026-07-18 by analogy with `bug.md` (the only worker-prompts file that
> existed before the health-inline merge) — closes the formerly broken link in
> security-health-inline. Workers verified to exist: `agents/health/workers/security-scanner.md`,
> `agents/health/workers/vulnerability-fixer.md`.

## Security Scanner - Detection

```
subagent_type: "security-scanner"
description: "Detect all vulnerabilities"
prompt: |
  Execute comprehensive security vulnerability scan.

  ## Scan Categories
  1. **SQL injection**
  2. **XSS vulnerabilities**
  3. **Authentication/authorization issues**
  4. **RLS policy violations**
  5. **Hardcoded secrets** (keys, tokens, passwords)
  6. **Insecure dependencies** (`pnpm audit`)

  ## Output
  Generate `security-scan-report.md` with structure:

  ```markdown
  # Security Scan Report

  **Generated**: {timestamp}
  **Status**: {PASSED/FAILED}

  ## Summary
  - Critical: {count}
  - High: {count}
  - Medium: {count}
  - Low: {count}

  ## Critical Vulnerabilities
  ### SEC-001: {title}
  - **File**: `path/to/file.ts:123`
  - **Category**: SQLi/XSS/Auth/RLS/Secret/Dependency
  - **Description**: {description + attack scenario}
  - **Fix**: {suggestion}

  ## High Priority Vulnerabilities
  [same format]

  ## Medium Priority Vulnerabilities
  [same format]

  ## Low Priority Vulnerabilities
  [same format]

  ## Validation Results
  - Type Check: {PASSED/FAILED}
  - Build: {PASSED/FAILED}
  ```

  Return summary: "Found X vulnerabilities (Y critical, Z high, ...)"
```

---

## Security Scanner - Verification

```
subagent_type: "security-scanner"
description: "Verification scan"
prompt: |
  Re-scan codebase after security fixes.

  ## Tasks
  1. Run full detection scan (same as initial)
  2. Compare with previous `security-scan-report.md`
  3. Identify:
     - Vulnerabilities that were fixed
     - Vulnerabilities that remain
     - New vulnerabilities introduced by fixes

  ## Output
  Overwrite `security-scan-report.md` with new scan results.

  Return summary:
  - "Verification complete: X fixed, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Vulnerability Fixer - By Priority

```
subagent_type: "vulnerability-fixer"
description: "Fix {priority} vulnerabilities"
prompt: |
  Fix all {priority} priority vulnerabilities from security-scan-report.md.

  ## Protocol
  For EACH vulnerability:

  1. **Read** vulnerability details from report
  2. **Backup** file before editing:
     ```bash
     cp {file} .tmp/current/backups/{sanitized-path}.backup
     ```
  3. **Log** change to `.tmp/current/changes/security-changes.json`:
     ```json
     {
       "files_modified": [{
         "path": "path/to/file.ts",
         "backup": ".tmp/current/backups/path-to-file.ts.backup",
         "vuln_id": "SEC-001",
         "reason": "Fix description"
       }]
     }
     ```
  4. **Fix** the vulnerability using Edit tool
     (fix the root cause — parameterized queries, output encoding, authz checks,
     move secrets to env; do not mask symptoms)
  5. **Validate** after each fix: `pnpm type-check`

  ## Output
  Update `security-fixes-implemented.md`:

  ```markdown
  # Security Fixes Report

  **Priority**: {priority}
  **Timestamp**: {timestamp}

  ## Fixed
  - [x] SEC-001: {description} → Fixed in `file.ts:123`
  - [x] SEC-002: {description} → Fixed in `other.ts:45`

  ## Failed
  - [ ] SEC-003: {description} → Reason: {why failed}

  ## Summary
  - Fixed: X/{total}
  - Failed: Y/{total}

  ## Rollback
  Changes log: `.tmp/current/changes/security-changes.json`
  ```

  Return: "Fixed X/{total} {priority} vulnerabilities"
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

If validation fails after fixes:

```bash
# Read changes log
cat .tmp/current/changes/security-changes.json

# For each modified file, restore from backup
cp .tmp/current/backups/{file}.backup {original-path}

# For each created file, delete
rm {created-file-path}
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/security-changes.json
```
