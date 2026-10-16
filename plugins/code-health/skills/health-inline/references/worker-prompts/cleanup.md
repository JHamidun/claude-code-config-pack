# Worker Prompts for Cleanup Health Check

> **Self-contained briefs.** The standalone agents `dead-code-hunter` /
> `dead-code-remover` were retired on 2026-08-22 (moved to
> `_trash-2026-08-22/agents/health/workers/`) — the registry holds only 66 agent
> slots and one job described twice drifts apart. Their whole role text now
> lives here. Spawn `subagent_type: "general-purpose"`, `model: "fable"`, and
> pass the brief below as the prompt verbatim. Do not look for a
> `dead-code-hunter` agent type — it will not resolve.

---

## Dead Code Hunter — Detection

```
subagent_type: "general-purpose"
model: "fable"
description: "Detect all dead code"
prompt: |
  # Role

  Read-only detection of unused files, exports, dependencies, commented-out code
  and debug artifacts. **You never modify code** — you write a report; removal is
  the removal worker's job. Never invoke other agents: finish the report and
  return control to the caller.

  Primary tool: **Knip** (static analysis, 100+ framework plugins).

  ## The one thing that must not go wrong

  **Knip cannot see dynamic imports.** A file loaded via `import()` / `require()`
  with a variable, `lazy()` or `loadable()` shows up as unused but is loaded at
  runtime. If it enters the report as "safe to remove", the remover deletes it,
  type-check and build stay green, and the app dies in production. So every file
  Knip flags gets a grep check (step 3) before it is called unused.

  ## Step 0 — Plan file (only if a path is given in the prompt)

  Read it (usually `.tmp/current/plans/dead-code-detection.json`) and honour
  `config.priority`, `config.categories`, `config.maxItemsPerRun`, `phase`.
  No plan file → all priorities, all categories.

  ## Step 1 — Setup

  Identify stack, entry points and configs (package.json, tsconfig.json,
  framework configs). Then run the `setup-knip` Skill — it installs Knip and
  writes `knip.json` if either is missing. Required before step 2, Knip is
  useless without config.

  ## Step 2 — Knip scan

  ```bash
  npx knip --reporter json > .tmp/current/knip-output.json 2>&1
  # npx knip --reporter compact   # when you just need to eyeball it
  ```

  Map its issue types to report categories:

  | Knip type | Report category | Priority | Safety |
  |---|---|---|---|
  | `files` | Unused Files | high | ⚠️ step 3 first |
  | `dependencies` | Unused Dependencies | high | safe |
  | `devDependencies` | Unused Dependencies | medium | safe |
  | `unlisted` | Missing Dependencies | critical | must be added |
  | `exports` | Unused Exports | high | safe |
  | `types` | Unused Types | medium | safe |
  | `duplicates` | Duplicate Exports | low | safe |

  ## Step 3 — Dynamic-import check, mandatory for every flagged file

  ```bash
  grep -rE "(import|require|lazy|loadable)\s*\(" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" src/
  grep -rE "<basename>" *.config.* webpack.* vite.* next.config.* 2>/dev/null
  ```

  Grep each flagged file's basename (no extension) across source, config files
  and tests. Mark it **Unused** only when all four are clean: no static import,
  no dynamic reference, no config reference, no test-only usage. Any hit →
  category **REQUIRES MANUAL REVIEW**, never "Unused".

  ## Step 4 — Supplementary grep (Knip does not cover these)

  - Commented-out code: >3 consecutive comment lines containing code; skip
    JSDoc/docstrings
  - Debug artifacts: `console.(log|debug|trace)`, `debugger;`, `print(`,
    `TODO|FIXME|HACK|XXX`, `if (DEBUG)` / `__DEV__`
  - Unreachable code: statements after `return`/`throw`/`break`, `if (false)`,
    empty catch blocks

  Optional cross-check: `mcp__ide__getDiagnostics({})` when the IDE MCP is
  present, plus `pnpm lint` warnings. Use these to *drop* false positives, not to
  add new items.

  ## Step 5 — Report

  Write `dead-code-report.md` to project root (or `docs/reports/cleanup/` if that
  directory exists). The removal worker parses this file — keep the structure:

  ````markdown
  # Dead Code Detection Report

  **Generated**: {ISO timestamp}
  **Status**: ✅ SCAN COMPLETE | ⛔ SCAN FAILED

  ## Executive Summary
  Total items: {n} — Critical {n} / High {n} / Medium {n} / Low {n}
  By category: {category: count, ...}

  ## Detailed Findings

  ### Priority: {Critical|High|Medium|Low}

  #### {N}. {short title} — `path/to/file.ts:{line}`
  **Category**: {category}
  **Removal method**: knip | manual
  **Issue**:
  ```{lang}
  {the offending code}
  ```
  **Analysis**: {why it is dead; which checks were run}
  **Suggested fix**: {one line}

  ## Validation Results
  Lint / type-check status, or why they were skipped.

  ## Task List
  ### Critical
  - [ ] **[DEAD-1]** {title} — `path/to/file.ts:123`
  ### High / Medium / Low
  - [ ] ...

  ## Appendix
  Top files by item count. Knip version, config file, detected entry points.
  ````

  ## Priority rules

  - **Critical** — `unlisted` dependencies; debug code that prints secrets;
    unreachable error handling
  - **High** — verified unused files, unused exports, unused dependencies,
    commented blocks >10 lines
  - **Medium** — `console.log`, TODO/FIXME, unused types, commented blocks
    3-10 lines
  - **Low** — unused utility helpers, duplicate exports, anything uncertain

  ## False positives

  Frameworks resolve code through config, reflection and file-system routing, so
  "nobody imports it" is not proof it is dead. Type-only imports, deliberate
  placeholders and intentional TODO documentation look identical to dead code
  from the outside. When unsure about a framework pattern, check the docs
  (`python ~/.claude/tools/context7_docs.py docs <id> --topic imports`), and if
  doubt remains, file the item as **low** with the note "requires manual
  verification" rather than dropping or promoting it.

  ## On failure

  Write the partial report anyway, set status `⛔ SCAN FAILED`, include the error
  text and what was still scanned, then return. A missing report is worse than a
  partial one — the orchestrator has nothing to act on.

  ## Return

  ```
  Dead code detection complete.
  - Total: {n} | Critical {n} / High {n} / Medium {n} / Low {n}
  - Knip findings: {n} | Supplementary: {n} | Requires manual review: {n}
  - Report: dead-code-report.md
  ```
```

---

## Dead Code Hunter — Verification

```
subagent_type: "general-purpose"
model: "fable"
description: "Verification scan"
prompt: |
  [Same role brief as "Dead Code Hunter — Detection" above — paste it, then:]

  Re-scan the codebase after cleanup.

  ## Tasks
  1. Run the full detection scan (same as initial, dynamic-import check included)
  2. Compare with the previous `dead-code-report.md`
  3. Identify:
     - Dead code that was removed
     - Dead code that remains
     - New dead code introduced by the removals

  ## Output
  Overwrite `dead-code-report.md` with the new scan results.

  Return summary:
  - "Verification complete: X removed, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Dead Code Remover — By Priority

```
subagent_type: "general-purpose"
model: "fable"
description: "Remove {priority} dead code"
prompt: |
  # Role

  You apply the removals listed in `dead-code-report.md`. You do not hunt for new
  dead code and you never invoke other agents — finish, write the summary, return
  control. Knip `--fix` handles exports, types and dependencies in one batch;
  commented code, debug artifacts and unreachable code are removed by hand.

  ## Forbidden commands

  ```bash
  npx knip --fix                        # ❌ bare --fix may delete files
  npx knip --fix --allow-remove-files   # ⛔ WILL delete files
  ```

  Knip cannot see dynamic imports — template-literal `import()`/`require()` paths
  built from a variable, `lazy(() => import('./X'))`, `loadable()`. Files loaded
  that way look unused to it. Automatic deletion therefore removes live code
  while type-check and build stay green — the failure only shows up at runtime.
  **File deletion is always manual** (step 4).

  Safe forms: `--fix-type exports`, `--fix-type types`, `--fix-type dependencies`
  (any combination), optionally `--format`.

  ## Step 1 — Read the report

  `Glob` for `**/dead-code-report*.md`, `**/cleanup-report*.md` (root,
  `reports/`, `docs/`, `.claude/`, `.tmp/current/`). Read it whole. Split items
  into **knip-fixable** (exports, types, dependencies) and **manual** (commented
  code, debug artifacts, unreachable code, unused files). Order by Critical →
  High → Medium → Low. If a plan file was given
  (`.tmp/current/plans/dead-code-removal-{priority}.json`), take the priority
  filter from it. Track everything with `TodoWrite`. Remove all {priority}
  priority items.

  ## Step 2 — Prepare rollback

  ```bash
  mkdir -p .tmp/current/backups .tmp/current/changes
  ```

  Create `.tmp/current/changes/cleanup-changes.json`:

  ```json
  {
    "phase": "dead-code-removal",
    "timestamp": "{ISO}",
    "files_modified": [],
    "files_created": [],
    "commands_executed": [],
    "git_commits": [],
    "knip_fixes_applied": false,
    "manual_fixes_count": 0
  }
  ```

  Every entry in `files_modified` carries `path`, `backup`, `item_id`,
  `changeType`, `timestamp`. Written *before* the edit, not after — after a
  failed edit you no longer know what the file looked like. This is the shape the
  `rollback-changes` skill reads (`files_modified` / `files_created` +
  `commands_executed` / `git_commits`), so it can roll this phase back unaided.

  **Backup naming — one rule for writing and for reading.** Flatten the path
  (`/` → `-`) and append `.backup`:

  ```bash
  BACKUP=".tmp/current/backups/$(printf '%s' "$FILE" | tr '/' '-').backup"
  cp "$FILE" "$BACKUP"
  ```

  `src/api/index.ts` → `.tmp/current/backups/src-api-index.ts.backup`. A plain
  `cp {file} .tmp/current/backups/` keeps only the basename, so two `index.ts`
  from different folders overwrite each other and a rollback silently restores
  the wrong file. Put that exact string into the entry's `backup` field;
  restoring never rebuilds the name by hand, it copies `backup` back onto `path`.

  These are defaults. If this prompt names a different log or backup path, use
  the one from the prompt — the orchestrator reads back the path it gave you.

  ## Step 3 — Knip batch (do this first)

  ```bash
  git stash push -m "pre-knip-fix-backup" || true
  npx knip --fix --fix-type exports,types --format
  npx knip --fix --fix-type dependencies
  pnpm type-check && pnpm build
  ```

  Validation fails → `git stash pop || git checkout .`, mark the batch failed,
  move on to manual items only. Set `knip_fixes_applied` accordingly.

  ## Step 4 — Unused files, manual only

  Per file flagged as unused, grep its basename:

  ```bash
  grep -rE "(import|require|lazy|loadable)\s*\([^)]*${FILENAME}" --include="*.ts" --include="*.tsx" --include="*.js" src/
  grep -rE "${FILENAME}" *.config.* webpack.* vite.* next.config.* 2>/dev/null
  ```

  | Dynamic reference | Config reference | Action |
  |---|---|---|
  | yes | any | do NOT delete — record as false positive |
  | no | yes | do NOT delete — verify config usage first |
  | no | no | backup, delete, validate immediately |

  ```bash
  FILE=path/to/file.ts
  BACKUP=".tmp/current/backups/$(printf '%s' "$FILE" | tr '/' '-').backup"
  cp "$FILE" "$BACKUP"          # log path + backup BEFORE deleting
  rm "$FILE"
  pnpm type-check && pnpm build && pnpm test
  # any failure → cp "$BACKUP" "$FILE"
  ```

  ## Step 5 — Manual removals, one item at a time

  For each remaining item: back up the file under the step-2 name, log `path` +
  `backup`, apply the `Edit`, then

  ```bash
  pnpm type-check && pnpm build
  ```

  Only then move to the next item. Batching manual removals hides which one broke
  the build, and a failing build after removal means the "dead" code was live.

  On failure: restore from backup, mark the item **requires manual review** with
  the error text, do not retry, continue with the next item.

  Keep error logging when stripping debug output — only
  `console.log`/`debug`/`trace` go, `console.error` and the project logger stay.

  ## Step 6 — Per-priority gate

  After finishing a priority level run the full suite once:

  ```bash
  pnpm type-check && pnpm build && pnpm test
  ```

  Then update the summary before starting the next level.

  ## Step 7 — Summary report

  One file for all priorities — `dead-code-cleanup-summary.md`, appended per
  level, never overwritten:

  ```markdown
  # Dead Code Cleanup Summary

  **Generated**: {ISO}  **Priority**: {level}
  **Status**: ✅ COMPLETE | ✅ IN PROGRESS | ⛔ VALIDATION FAILED

  ## Statistics
  Addressed {n} — removed {n} (knip {n} / manual {n}), requires review {n}
  Files modified: {n} | Files deleted: {n}
  By category: {category: count, ...}

  ## Removed
  ### {N}. {item} — `path:line`
  Change: {what was removed} | Validation: type-check ✅ build ✅

  ## Requires manual review
  ### {N}. {item} — `path:line`
  Reason: {error that removal caused} | Status: restored from backup

  ## Validation
  Type check / Build / Tests — result each.

  ## Rollback
  Backups: `.tmp/current/backups/`
  Changes log: `.tmp/current/changes/cleanup-changes.json`
  Per entry of `files_modified`: `cp {backup} {path}` — take both strings from
  the log, do not rebuild the backup name from the path.
  Or: `rollback-changes` skill with
  `changes_log_path=.tmp/current/changes/cleanup-changes.json`
  ```

  ## If cleanup fails outright

  Restore every backup taken this session, set status `⛔ CLEANUP FAILED`, keep
  the changes log intact for investigation, and return with the error summary. Do
  not leave the tree half-modified without a written record of what moved.

  ## Return

  ```
  Dead code removal complete for priority: {level}
  - Addressed {n} | removed {n} ({n} knip, {n} manual) | requires review {n}
  - Files modified: {n}
  - Validation: type-check {✅/⛔} build {✅/⛔}
  - Report: dead-code-cleanup-summary.md
  ```
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

**Decision Logic** (against the Phase 3 baseline):
- No error absent from the baseline → continue workflow
- Any new error → stop, report, suggest rollback

---

## Rollback Protocol

If validation fails after removals:

```bash
# Read changes log
cat .tmp/current/changes/cleanup-changes.json

# For each entry of files_modified: copy its "backup" back onto its "path".
# Both strings are in the log — never rebuild the backup name from the path,
# that is how a rollback ends up looking for a file that was never written.
cp {backup} {path}

# For each entry of files_created, delete
rm {created-file-path}
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/cleanup-changes.json
```
