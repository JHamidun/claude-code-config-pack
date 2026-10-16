# Полный шаблон bug-hunting-report.md

> Вынесено из тела агента `health/workers/bug-hunter.md` 2026-08-20; сам агент
> сведён в этот навык 2026-08-22 (тело → `references/worker-prompts/bug.md`,
> файл → `_trash-2026-08-22/`). Читать на этапе генерации отчёта, если нужна
> точная структура секций. Поле `agent:` в шапке — свободная метка, воркер
> спавнится как `general-purpose`.

## Report Structure

Generate a comprehensive `bug-hunting-report.md` file with the following enhanced structure:

```markdown
---
report_type: bug-hunting
generated: 2025-10-18T14:30:00Z
version: 2025-10-18
status: success
agent: health-inline/bug-detect
duration: 3m 45s
files_processed: 147
issues_found: 23
critical_count: 3
high_count: 8
medium_count: 12
low_count: 0
modifications_made: false
changes_log: .bug-changes.json (if modifications_made: true)
---

# Bug Hunting Report

**Generated**: [Current Date]
**Project**: [Project Name]
**Files Analyzed**: [Count]
**Total Issues Found**: [Count]
**Status**: ✅/⚠️/❌ [Status]

---

## Executive Summary
[Brief overview of critical findings and recommended immediate actions]

### Key Metrics
- **Critical Issues**: [Count]
- **High Priority Issues**: [Count]
- **Medium Priority Issues**: [Count]
- **Low Priority Issues**: [Count]
- **Files Scanned**: [Count]
- **Modifications Made**: Yes/No
- **Changes Logged**: Yes/No (if modifications made)

### Highlights
- ✅ Scan completed successfully
- ❌ Critical issues requiring immediate attention
- ⚠️ Warnings or partial failures
- 📝 Modifications logged in .bug-changes.json (if applicable)

---

## Critical Issues (Priority 1) 🔴
*Immediate attention required - Security vulnerabilities, data loss risks, system crashes*

### Issue #1: [Issue Title]
- **File**: `path/to/file.ext:line`
- **Category**: Security/Crash/Data Loss
- **Description**: [Detailed description]
- **Impact**: [Potential impact if not fixed]
- **Fix**: [Specific fix recommendation]
```code
[Code snippet showing the issue]
```

## High Priority Issues (Priority 2) 🟠
*Should be fixed before deployment - Performance bottlenecks, memory leaks, breaking changes*

[Similar format as above]

## Medium Priority Issues (Priority 3) 🟡
*Should be scheduled for fixing - Type errors, missing error handling, deprecated APIs*

[Similar format as above]

## Low Priority Issues (Priority 4) 🟢
*Can be fixed during regular maintenance - Code style, documentation, minor optimizations*

[Similar format as above]

## Code Cleanup Required 🧹

### Debug Code to Remove
| File | Line | Type | Code Snippet |
|------|------|------|--------------|
| file1.js | 42 | console.log | `console.log('debug:', data)` |
| file2.ts | 156 | TODO comment | `// TODO: Fix this hack` |

### Dead Code to Remove
| File | Lines | Type | Description |
|------|-------|------|-----------|
| utils.js | 234-267 | Commented Code | Large commented function |
| helper.ts | 89 | Unreachable | Code after return statement |
| api.js | 15-17 | Unused Import | Unused lodash functions |

### Duplicate Code Blocks
| Files | Lines | Description | Refactor Suggestion |
|-------|-------|-------------|-------------------|
| file1.js, file2.js | 45-67, 123-145 | Identical validation logic | Extract to shared utility |

---

## Changes Made (If Applicable)

**Modifications**: [Yes/No]

[If Yes, include this section:]

### Files Modified: [Count]

| File | Backup Location | Reason | Timestamp |
|------|----------------|--------|-----------|
| src/api/db.ts | .rollback/src/api/db.ts.backup | Fixed memory leak | 2025-10-18T14:31:15Z |

### Files Created: [Count]

| File | Reason | Timestamp |
|------|--------|-----------|
| bug-hunting-report.md | Bug detection report | 2025-10-18T14:35:00Z |

### Changes Log

All modifications logged in: `.bug-changes.json`

**Rollback Available**: ✅ Yes

To rollback changes if needed:
```bash
# Use rollback-changes Skill
Use rollback-changes Skill with changes_log_path=.bug-changes.json

# Or manual rollback
cp .rollback/[file].backup [file]
```

---

## Validation Results

### Type Check

**Command**: `pnpm type-check`

**Status**: ✅ PASSED / ❌ FAILED

**Output**:
```
[Command output]
```

**Exit Code**: 0

### Build

**Command**: `pnpm build`

**Status**: ✅ PASSED / ❌ FAILED

**Output**:
```
[Build output]
```

**Exit Code**: 0

### Tests (Optional)

**Command**: `pnpm test`

**Status**: ✅ PASSED / ⚠️ PARTIAL / ❌ FAILED

**Output**:
```
[Test output]
```

**Exit Code**: 0

### Overall Status

**Validation**: ✅ PASSED / ⚠️ PARTIAL / ❌ FAILED

[Explanation if not fully passed]

[If validation failed and modifications were made:]
**Rollback Recommended**: ⚠️ Yes - See "Changes Made" section above

---

## Metrics Summary 📊
- **Security Vulnerabilities**: [Count]
- **Performance Issues**: [Count]
- **Type Errors**: [Count]
- **Dead Code Lines**: [Count]
- **Debug Statements**: [Count]
- **Code Coverage**: [Percentage if available]
- **Technical Debt Score**: [High/Medium/Low]

---

## Task List 📋

### Critical Tasks (Fix Immediately)
- [ ] **[CRITICAL-1]** Fix SQL injection vulnerability in `api/users.js:45`
- [ ] **[CRITICAL-2]** Remove hardcoded API key in `config.js:12`

### High Priority Tasks (Fix Before Deployment)
- [ ] **[HIGH-1]** Fix memory leak in `services/cache.js:234`
- [ ] **[HIGH-2]** Optimize O(n²) loop in `utils/search.js:89`

### Medium Priority Tasks (Schedule for Sprint)
- [ ] **[MEDIUM-1]** Add error handling for async operations in `api/`
- [ ] **[MEDIUM-2]** Replace deprecated APIs in `legacy/`

### Low Priority Tasks (Backlog)
- [ ] **[LOW-1]** Remove all console.log statements (23 occurrences)
- [ ] **[LOW-2]** Delete commented-out code blocks (156 lines total)

### Code Cleanup Tasks
- [ ] **[CLEANUP-1]** Remove all debug code (see Debug Code table)
- [ ] **[CLEANUP-2]** Delete unused imports across 12 files
- [ ] **[CLEANUP-3]** Refactor 5 duplicate code blocks

---

## Recommendations 🎯

1. **Immediate Actions**:
   - [Specific critical fixes needed]
   [If modifications failed validation:]
   - ⚠️ Rollback changes using `.bug-changes.json`
   - Review validation failures before retrying

2. **Short-term Improvements**:
   - [1-2 week timeframe recommendations]

3. **Long-term Refactoring**:
   - [Architecture improvements needed]

4. **Testing Gaps**:
   - [Areas lacking test coverage]

5. **Documentation Needs**:
   - [Critical missing documentation]

---

## Next Steps

### Immediate Actions (Required)

1. **Review Critical Issues** (Priority 1)
   - Start with highest impact bugs
   - Fix in order of severity

[If modifications were made and validation failed:]
2. **Rollback Failed Changes**
   ```bash
   Use rollback-changes Skill with changes_log_path=.bug-changes.json
   ```

3. **Re-run Validation**
   - After rollback or fixes
   - Verify all checks pass

### Recommended Actions (Optional)

- Schedule high-priority bugs for current sprint
- Create tickets for medium-priority bugs
- Plan code cleanup sprint

### Follow-Up

- Re-run bug scan after fixes
- Monitor for regression
- Update documentation

---

## File-by-File Summary

<details>
<summary>Click to expand detailed file analysis</summary>

### High-Risk Files
1. `path/to/file1.js` - 5 critical, 3 high priority issues
2. `path/to/file2.ts` - 2 critical, 7 medium priority issues

### Clean Files ✅
- Files with no issues found: [List or count]

</details>

---

## Artifacts

- Bug Report: `bug-hunting-report.md` (this file)
[If modifications were made:]
- Changes Log: `.bug-changes.json`
- Backups Directory: `.rollback/`

---

*Report generated by the health-inline bug-detection worker*
*Changes logging enabled - All modifications tracked for rollback*
```
