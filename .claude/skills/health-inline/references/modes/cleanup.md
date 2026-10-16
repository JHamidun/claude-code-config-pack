> Mode file of skill `health-inline` (merged 2026-07-18 from `skills/cleanup-health-inline`,
> original frontmatter: version 2.0.0). Body preserved verbatim; only the
> worker-prompts link path updated to the new references layout.

> **2026-08-22:** the ten standalone worker agents were retired into
> `_trash-2026-08-22/agents/health/workers/` — the agent registry holds only 66
> slots. Every worker is now spawned as `subagent_type: "general-purpose"`,
> `model: "fable"`, with the full role brief pasted from
> `references/worker-prompts/cleanup.md`. The short prompts below are the
> orchestration outline; the brief is what the worker actually needs.


# Cleanup Health Check (Inline Orchestration)

You ARE the orchestrator. Execute this workflow directly without spawning a separate orchestrator agent.

## Workflow Overview

```
Detection → Validate → Remove by Priority → Verify → Repeat if needed
```

**Max iterations**: 3
**Priorities**: critical → high → medium → low

---

## Phase 1: Pre-flight

1. **Setup directories**:
   ```bash
   mkdir -p .tmp/current/{plans,changes,backups}
   ```

2. **Validate environment**:
   - Check `package.json` exists
   - Check `type-check` and `build` scripts exist

3. **Initialize TodoWrite**:
   ```json
   [
     {"content": "Dead code detection", "status": "in_progress", "activeForm": "Detecting dead code"},
     {"content": "Remove critical dead code", "status": "pending", "activeForm": "Removing critical dead code"},
     {"content": "Remove high priority dead code", "status": "pending", "activeForm": "Removing high dead code"},
     {"content": "Remove medium priority dead code", "status": "pending", "activeForm": "Removing medium dead code"},
     {"content": "Remove low priority dead code", "status": "pending", "activeForm": "Removing low dead code"},
     {"content": "Verification scan", "status": "pending", "activeForm": "Verifying cleanup"}
   ]
   ```

---

## Phase 2: Detection

**Invoke the detection worker** via Task tool:

```
subagent_type: "general-purpose"   # brief: worker-prompts/cleanup.md § Dead Code Hunter — Detection
description: "Detect all dead code"
prompt: |
  Scan the entire codebase for dead code:
  - Unused imports and exports
  - Commented out code blocks
  - Unreachable code
  - Debug statements (console.log, debugger)
  - Unused variables and functions
  - Unused dependencies
  - Categorize by priority (critical/high/medium/low)

  Generate: dead-code-report.md

  Return summary with dead code counts per priority.
```

**After the detection worker returns**:
1. Read `dead-code-report.md`
2. Parse dead code counts by priority
3. If zero dead code → skip to Final Summary
4. Update TodoWrite: mark detection complete

---

## Phase 3: Baseline (non-blocking — NEVER exits)

Run inline validation to **record the starting state**, not to gate:

```bash
pnpm type-check
pnpm build
```

- Both pass → baseline = GREEN, proceed to removal
- Either fails → baseline = RED: record the exact error list, hand it to
  the removal worker as context, **proceed to removal anyway**

A red build is the usual reason this workflow was invoked, so exiting here would
mean exiting on exactly the input the workflow exists to repair. The gate that
can stop the run lives in Phase 4, after a removal, and compares against this
baseline.

---

## Phase 4: Removal Loop

**For each priority** (critical → high → medium → low):

1. **Check if dead code exists** for this priority
   - If zero → skip to next priority

2. **Update TodoWrite**: mark current priority in_progress

3. **Invoke the removal worker** via Task tool:
   ```
   subagent_type: "general-purpose"   # brief: worker-prompts/cleanup.md § Dead Code Remover — By Priority
   description: "Remove {priority} dead code"
   prompt: |
     Read dead-code-report.md and remove all {priority} priority dead code.

     For each item:
     1. Backup file before editing
     2. Remove dead code
     3. Log change to .tmp/current/changes/cleanup-changes.json

     Generate/update: dead-code-cleanup-summary.md

     Return: count of removed items, count of failed removals.
   ```

4. **Quality Gate** (inline, vs Phase 3 baseline) — this is the gate that can
   stop the run:
   ```bash
   pnpm type-check
   pnpm build
   ```

   - Any error NOT present in the baseline → the removals made things worse:
     report error, suggest rollback, exit
   - Same errors as baseline, or fewer → continue to the next priority
   - Green baseline stays strict: any failure at all is "worse than baseline"

5. **Update TodoWrite**: mark priority complete

6. **Repeat** for next priority

---

## Phase 5: Verification

After all priorities cleaned:

1. **Update TodoWrite**: mark verification in_progress

2. **Invoke the detection worker** (verification mode):
   ```
   subagent_type: "general-purpose"   # brief: worker-prompts/cleanup.md § Dead Code Hunter — Verification
   description: "Verification scan"
   prompt: |
     Re-scan codebase after cleanup.
     Compare with previous dead-code-report.md.

     Report:
     - Dead code removed (count)
     - Dead code remaining (count)
     - New dead code introduced (count)
   ```

3. **Decision**:
   - If dead_code_remaining == 0 → Final Summary
   - If iteration < 3 AND dead_code_remaining > 0 → Go to Phase 2
   - If iteration >= 3 → Final Summary with remaining items

---

## Phase 6: Final Summary

Generate summary for user:

```markdown
## Cleanup Health Check Complete

**Iterations**: {count}/3
**Status**: {SUCCESS/PARTIAL}

### Results
- Found: {total} dead code items
- Removed: {removed} ({percentage}%)
- Remaining: {remaining}

### By Priority
- Critical: {removed}/{total}
- High: {removed}/{total}
- Medium: {removed}/{total}
- Low: {removed}/{total}

### Validation
- Type Check: {status}
- Build: {status}

### Artifacts
- Detection: `dead-code-report.md`
- Cleanup: `dead-code-cleanup-summary.md`
```

---

## Error Handling

**If quality gate fails**:
```
Rollback available: .tmp/current/changes/cleanup-changes.json

To rollback:
1. Read changes log
2. Restore files from .tmp/current/backups/
3. Re-run workflow
```

**If worker fails**:
- Report error to user
- Suggest manual intervention
- Exit workflow

---

## Key Differences from Old Approach

| Old (Orchestrator Agent) | New (Inline Skill) |
|--------------------------|-------------------|
| 9+ orchestrator calls | 0 orchestrator calls |
| ~1400 lines (cmd + agent) | ~150 lines |
| Context reload each call | Single session context |
| Plan files for each phase | Direct execution |
| ~10,000+ tokens overhead | ~500 tokens |

---

## Worker Prompts

See `references/worker-prompts/cleanup.md` for detailed prompts.
