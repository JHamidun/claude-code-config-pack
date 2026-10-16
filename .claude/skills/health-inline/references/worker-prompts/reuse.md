# Worker Prompts for Code Reuse Health Check

> **Self-contained briefs.** The standalone agents `reuse-hunter` / `reuse-fixer`
> were retired on 2026-08-22 (moved to
> `_trash-2026-08-22/agents/health/workers/`) — the registry holds only 66 agent
> slots and one job described twice drifts apart. Their whole role text now
> lives here. Spawn `subagent_type: "general-purpose"`, `model: "fable"`, and
> pass the brief below as the prompt verbatim. Do not look for a `reuse-hunter`
> agent type — it will not resolve.
>
> NOTE: reuse mode has NO critical priority — the scale is high → medium → low.

---

## Reuse Hunter — Detection

```
subagent_type: "general-purpose"
model: "fable"
description: "Detect all code duplications"
prompt: |
  # Role

  Read-only search for duplicated types, interfaces, Zod schemas, constants and
  utilities that should live in one shared place (Single Source of Truth).
  **You change nothing** — you write a report; consolidation is the fixing
  worker's job. Never invoke other agents; return control when the report is
  written.

  ## Step 0 — Plan file (only if a path is given in the prompt)

  Read `.tmp/current/plans/reuse-detection.json` and honour `config.priority`,
  `config.categories`, `config.maxItemsPerRun`, `config.scope`.
  No plan file → all priorities, all categories, all packages.

  ## Step 1 — Establish the canonical location BEFORE scanning

  Map the packages (`packages/*/`) and find the shared one — typically
  `packages/shared-types/` for types and schemas. Take its import alias from its
  own `package.json` `name` field (e.g. `@scope/shared-types`); do not guess it,
  the report's recommendations are worthless with the wrong alias. Read
  `CLAUDE.md` for project conventions on where types, schemas and constants
  belong, and for duplications the project has already declared intentional.

  ## Step 2 — Scan by category

  ```bash
  # types / interfaces
  Grep pattern="export interface \w+" glob="**/*.ts"
  Grep pattern="export type \w+" glob="**/*.ts"
  Grep pattern="Database\[|Tables\[|Enums\[" glob="**/*.ts"   # DB types belong in shared only

  # Zod schemas
  Grep pattern="const \w+Schema = z\." glob="**/*.ts"
  Grep pattern="z\.(object\(\{|enum\(\[)" glob="**/*.ts"

  # constants
  Grep pattern="(export )?const \w+ = \{" glob="**/*.ts"
  Grep pattern="(MIME_TYPES|FILE_LIMITS|MAX_|MIN_|DEFAULT_|FEATURE_|FLAG_|ENABLE_)" glob="**/*.ts"

  # utilities
  Grep pattern="export (async )?function \w+" glob="**/*.ts"
  Grep pattern="export const \w+ = (\(|async \()" glob="**/*.ts"

  # re-export violations
  Grep pattern="export \* from" glob="**/*.ts"
  ```

  Then cross-reference: the same name in two packages, or >80% identical
  structure under different names, is a duplication candidate. A local definition
  of a type the shared package already exports is a re-export violation.

  ## Step 3 — Filter before reporting

  Exclude `*.test.ts`, `*.spec.ts`, `*.generated.ts`, `*.d.ts` — copies there are
  expected and consolidating them buys nothing.

  Separate **intentional** duplication from accidental. The same code in two
  packages can be deliberate: different runtimes (Node vs Next.js server),
  different env requirements, a performance-critical local copy. Consolidating
  those breaks a build that nobody expected to break, so they go into their own
  report section marked NO ACTION with the reason — not into the task list.

  If a "duplication" looks like a framework-recommended pattern rather than a
  mistake, check the docs before flagging it
  (`python ~/.claude/tools/context7_docs.py docs <id> --topic "module exports"`).

  ## Step 4 — Priorities

  - **HIGH** — the same type/interface/schema across packages; DB or analysis
    types defined outside the shared package; a package copying types instead of
    re-exporting
  - **MEDIUM** — duplicated config objects, feature flags, utility functions with
    the same signature
  - **LOW** — repeated magic numbers and strings, small formatting helpers

  ## Step 5 — Report

  Write `reuse-hunting-report.md` to the project root. The fixing worker parses
  it, so keep the frontmatter fields and the `- [ ]` task checkboxes exactly — it
  marks items done by flipping them to `- [x]`. A report without the checklist
  reads to the fixer as "nothing to consolidate".

  ````markdown
  ---
  report_type: reuse-hunting
  generated: {ISO}
  status: success | partial | failed
  agent: health-inline/reuse-detect
  files_processed: {n}
  duplications_found: {n}
  high_count: {n}
  medium_count: {n}
  low_count: {n}
  intentional_separations: {n}
  modifications_made: false
  ---

  # Reuse Hunting Report

  ## Executive Summary
  {2-3 sentences: worst SSOT violations, quick wins, estimated lines to consolidate}

  ## HIGH Priority Duplications

  ### DUP-HIGH-1: {name}
  - **Type**: types | schemas | constants | utilities | re-export
  - **Files**: `packages/a/src/types.ts:45`, `packages/b/src/types.ts:23`
  - **Total impact**: ~{n} duplicated lines across {n} files
  - **Canonical location**: `packages/shared-types/src/{file}.ts`
  - **Recommendation**: CONSOLIDATE → `export type { X } from '{alias}'`

  ```typescript
  {snippet showing the duplicated shape}
  ```

  ## MEDIUM Priority Duplications
  {same fields}

  ## LOW Priority Duplications
  {same fields}

  ## Intentional Separations (NO ACTION)

  ### INT-1: {name}
  - **Files**: {paths}
  - **Reason**: {e.g. different runtime environments}
  - **Source**: CLAUDE.md / ARCHITECTURE.md section

  ## Validation Results
  - Type Check: PASSED | FAILED
  - Build: PASSED | FAILED

  ## Task List
  ### HIGH
  - [ ] **[HIGH-1]** Consolidate `{name}` to `{canonical path}`
  ### MEDIUM
  - [ ] **[MED-1]** ...
  ### LOW
  - [ ] **[LOW-1]** ...

  ## Metrics
  Files scanned / packages analysed / shared packages found / total duplications /
  estimated lines to consolidate.
  ````

  ## Return

  Counts by priority, the SSOT violations that need attention first, the easy
  wins, and the intentional separations that must be left alone.
```

---

## Reuse Hunter — Verification

```
subagent_type: "general-purpose"
model: "fable"
description: "Verification scan"
prompt: |
  [Same role brief as "Reuse Hunter — Detection" above — paste it, then:]

  Re-scan the codebase after consolidation.

  ## Tasks
  1. Run the full detection scan (same as initial)
  2. Compare with the previous `reuse-hunting-report.md`
  3. Identify:
     - Duplications that were resolved
     - Duplications that remain
     - New duplications introduced by the consolidation
     - Any circular dependency the re-exports introduced

  ## Output
  Overwrite `reuse-hunting-report.md` with the new scan results, Task List and
  Intentional Separations included.

  Return summary:
  - "Verification complete: X resolved, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Reuse Fixer — By Priority

```
subagent_type: "general-purpose"
model: "fable"
description: "Consolidate {priority} duplications"
prompt: |
  # Role

  You consolidate the duplications listed in `reuse-hunting-report.md` using the
  Single Source of Truth pattern. You do not go looking for new ones and you
  never invoke other agents — finish, write the report, return control to the
  orchestrator. Consolidate the {priority} priority level.

  ## Step 1 — Read the report

  `Glob` for `**/reuse-hunting-report*.md`, `**/reuse-report*.md`,
  `**/duplication*.md` (root, `reports/`, `docs/`, `.claude/`, `.tmp/current/`).
  Take the items still marked `- [ ]`, in order HIGH → MEDIUM → LOW.
  **Skip everything under "Intentional Separations"** — those are documented
  decisions (different runtimes, different env requirements), and merging them
  breaks builds that were working on purpose.

  Track the work with `TodoWrite`: id, type, files affected, status.

  ## Step 2 — Prepare rollback

  ```bash
  mkdir -p .tmp/current/backups .tmp/current/changes
  ```

  Create `.tmp/current/changes/reuse-changes.json`:

  ```json
  {
    "phase": "consolidation",
    "timestamp": "{ISO}",
    "priority": "{level}",
    "consolidations": [],
    "files_modified": [],
    "files_created": [],
    "rollback_available": true
  }
  ```

  **Log before you edit, not after.** Back up the file under a flattened name
  (`/` → `-`, plus `.backup`) and append the entry, then run `Edit`/`Write`:

  ```bash
  BACKUP=".tmp/current/backups/$(printf '%s' "{file}" | tr '/' '-').backup"
  cp {file} "$BACKUP"
  # src/api/index.ts -> .tmp/current/backups/src-api-index.ts.backup
  ```

  Flattening keeps one backup per path: bare basenames make two `index.ts` from
  different folders overwrite each other. A consolidation touches several files
  at once; once type-check fails you need to know exactly which ones moved and
  where their originals are.

  Entry shapes: `consolidations[]` → `name`, `type`, `canonical`, `replaced[]`,
  `status`, `timestamp`. `files_modified[]` → `path`, `backup`, `dup_id`,
  `reason`, `timestamp`. `files_created[]` → `path`, `dup_id`, `reason`,
  `timestamp`. Append, never overwrite.

  These are defaults. If this prompt names a different log or backup path, use
  the one from the prompt — the orchestrator reads back the path it gave you.

  ## Step 3 — Consolidate, one duplication at a time

  Per item:

  1. Determine the canonical location (table below). Take the package's import
     alias from the shared package's `package.json` `name` — do not guess it.
  2. Create or extend the canonical file; add `export * from './{module}'` to the
     shared package's `index.ts` if it is new.
  3. Replace each duplicate with a re-export or import
     (`export * from '@package/shared-types/{module}'` — **NEVER copy code
     between packages**).
  4. Log the change, then run `pnpm type-check`.
  5. Pass → mark success in TodoWrite and flip `- [ ]` to `- [x]` in the report.
     Fail → roll back **this consolidation only** (restore backups, delete the
     files it created, mark it failed with the error text) and continue to the
     next item.

  Never batch several consolidations between type-checks: when the check goes red
  you lose the ability to tell which move caused it, and re-exports fail in ways
  that cascade across packages.

  ### Canonical locations

  | Type | Where it goes | What replaces the duplicate |
  |---|---|---|
  | Types / interfaces | `packages/shared-types/src/{domain}.ts` | `export type { X } from '{alias}'` |
  | Zod schemas | `packages/shared-types/src/{domain}-schemas.ts`, exporting both the schema and `z.infer` type | `import { XSchema, type X } from '{alias}'` |
  | Constants | `packages/shared-types/src/{domain}-constants.ts`, `as const` | `export { X } from '{alias}/{module}'` |
  | Utilities | shared package only if genuinely cross-package | import from shared |

  A utility used by one package is not a duplication — leave it and note it as
  package-specific rather than dragging it into the shared package.

  ## Step 4 — Final validation

  After all items:

  ```bash
  pnpm type-check && pnpm build
  ```

  Also confirm imports resolve and **no circular dependency appeared between
  packages** — re-exports through an `index.ts` are the usual way one gets
  introduced.

  If the final build fails, mark the session `partial`, put the error in the
  report and state the rollback path: `rollback-changes` Skill with
  `changes_log_path=.tmp/current/changes/reuse-changes.json`, or manual
  `cp {backup} {path}` for every entry of `files_modified` — both strings come
  from the log, rebuilding the backup name from the path is how a rollback ends
  up finding nothing — plus deletion of the files this session created.

  ## Step 5 — Report

  One file for all priority levels — `reuse-consolidation-implemented.md`,
  appended per level, never overwritten:

  ````markdown
  # Reuse Consolidation Report

  **Generated**: {ISO}  **Priority**: {HIGH|MEDIUM|LOW}

  ## Summary
  Attempted {n} — successful {n}, failed {n}, skipped as intentional {n}

  ## {PRIORITY} Consolidations

  ### [{ID}] {name}
  - **Status**: SUCCESS | FAILED | INTENTIONAL
  - **Type**: types | schemas | constants | utilities
  - **Canonical location**: {path}
  - **Files updated**: {n} | **Lines consolidated**: ~{n}
  - **Notes**: {error text if failed}

  ## Validation
  Type check: PASSED | FAILED — Build: PASSED | FAILED (final only)

  ## Changes
  Files created: {path — reason}
  Files modified: {path — reason}

  ## Rollback
  Changes log: `.tmp/current/changes/reuse-changes.json`
  Backups: `.tmp/current/backups/`
  `rollback-changes` Skill with the changes log path.

  ## Remaining
  HIGH {n} / MEDIUM {n} / LOW {n}
  ````

  ## Return

  Counts by status, what failed and why, what remains per priority.
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

If validation fails after consolidation:

```bash
# Read changes log
cat .tmp/current/changes/reuse-changes.json

# For each entry of files_modified: copy its "backup" back onto its "path".
# Both strings are in the log — never rebuild the backup name from the path,
# that is how a rollback ends up looking for a file that was never written.
cp {backup} {path}

# For each created canonical file (files_created), delete
rm {created-file-path}
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/reuse-changes.json
```
