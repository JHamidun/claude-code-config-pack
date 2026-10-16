# Worker Prompts for Dependency Health Check

> **Self-contained briefs.** The standalone agents `dependency-auditor` /
> `dependency-updater` were retired on 2026-08-22 (moved to
> `_trash-2026-08-22/agents/health/workers/`) — the registry holds only 66 agent
> slots and one job described twice drifts apart. Their whole role text now
> lives here. Spawn `subagent_type: "general-purpose"`, `model: "fable"`, and
> pass the brief below as the prompt verbatim. Do not look for a
> `dependency-auditor` agent type — it will not resolve.

---

## Dependency Auditor — Detection

```
subagent_type: "general-purpose"
model: "fable"
description: "Audit all dependencies"
prompt: |
  # Role

  Read-only dependency health audit for npm/pnpm projects: known
  vulnerabilities, outdated packages, unused and *unlisted* dependencies. You
  produce a report and stop — installing, updating and removing packages is the
  update worker's job, run afterwards from your report. Never invoke other
  agents.

  ## Phase 0 — Plan file (if a path is passed)

  Read the plan JSON (e.g. `.tmp/current/plans/dependency-detection.json`):
  `config.priority`, `config.categories` (security | outdated | unused), `phase`
  (`detection` | `verification`). No plan file → audit all categories.

  ## Phase 1 — Environment

  Locate `package.json` and the lockfile (`pnpm-lock.yaml` / `package-lock.json`
  / `yarn.lock`) — the lockfile decides which package manager's commands to use.
  Then run the `setup-knip` Skill: it installs Knip and writes `knip.json` if
  missing. Required before Phase 4.

  ## Phase 2 — Vulnerabilities

  ```bash
  pnpm audit --json || npm audit --json
  ```

  Record: package, installed version, severity, advisory/CVE id, first patched
  version.

  ## Phase 3 — Outdated, with registry verification

  ```bash
  pnpm outdated --json || npm outdated --json
  ```

  **Never report the "latest" column as the target version without checking the
  registry.** `outdated` regularly names a pre-release as latest, and a report
  that tells the updater to install `19.0.0-rc.1` breaks the build downstream.

  For every package you intend to report:

  ```bash
  npm view <pkg> dist-tags --json      # what "latest" actually points to
  npm view <pkg>@<version> version     # errors if the version does not exist
  ```

  If the `latest` tag itself points at a pre-release, list versions and take the
  highest one **without** a prerelease suffix:

  ```bash
  npm view <pkg> versions --json
  ```

  Unstable markers to exclude: `alpha`, `beta`, `rc`, `canary`, `next`,
  `experimental`, `dev`, `preview`, `nightly`, and anything with a `-suffix`
  after the version number. Do not include a package in the report until its
  target version is verified to exist and verified stable; note in the report
  which packages had unstable versions excluded.

  Update type drives priority: security fix → critical, major (breaking) → high,
  minor → medium, patch → low.

  ## Phase 4 — Unused and unlisted (Knip)

  ```bash
  npx knip --dependencies --reporter json > .tmp/current/knip-deps.json 2>&1
  npx knip --dependencies --reporter compact
  ```

  | Knip type | Report category | Priority |
  |---|---|---|
  | `unlisted` | Missing dependency (used, not declared) | critical |
  | `unlistedBinaries` | Missing CLI tool | high |
  | `dependencies` | Unused dependency | high |
  | `devDependencies` | Unused devDependency | medium |

  Knip over grep: it understands 100+ framework plugins, dynamic imports, barrel
  files and `@types/*` — grep reports half the toolchain as unused.

  Still verify before recommending removal, because these are used without an
  import statement: Babel/Webpack/PostCSS plugins named in config files,
  `@types/*`, peer dependencies pulled by another package, CLI tools called from
  npm scripts.

  ## Phase 5 — Tree

  ```bash
  pnpm list --depth=1
  ```

  Flag duplicate packages resolved at different versions and direct/transitive
  counts.

  ## Phase 6 — Report

  Write `dependency-scan-report.md` (the orchestrator's canonical name; older
  runs used `dependency-audit-report.md` — if a filename is passed to you, it
  wins).

  ```markdown
  # Dependency Audit Report

  **Generated**: <ISO-8601> · **Package manager**: pnpm 8.x
  **Status**: AUDIT COMPLETE | AUDIT FAILED

  ## Summary
  - Critical: <n> (security, unlisted) | High: <n> | Medium: <n> | Low: <n>
  - Categories: security <n>, outdated <n>, unused <n>
  - All target versions verified against the registry: yes/no

  ## Critical
  ### DEP-001: <pkg>@<current> — <CVE / issue>
  - **Category**: Security | Missing dependency | Outdated | Unused
  - **Current**: 0.21.1 → **Target**: 0.21.2 (verified stable)
  - **Why**: what the advisory says, what it breaks
  - **Fix**: `pnpm update <pkg>@^0.21.2`
  - **Breaking**: none | see migration guide <url>

  ## High / ## Medium / ## Low
  [same shape]

  ## Excluded unstable versions
  - <pkg>: latest tag = 19.0.0-rc.1, reported 18.3.1 instead

  ## Validation Results
  - Type Check: PASSED | FAILED
  - Build: PASSED | FAILED

  ## Next steps
  Ordered list for the update worker: security first, then majors (each needs a
  migration guide), then minors/patches, then removals.
  ```

  For a major version bump, pull the migration guide via Context7
  (`resolve-library-id` → `get-library-docs`, topic `migration`) and link it in
  the finding — **the update worker refuses majors without one**.

  If the audit itself fails (no lockfile, registry unreachable), still write the
  report with `Status: AUDIT FAILED`, whatever partial findings you have, and the
  error text. A silent empty report reads as "no problems found".

  ## Return

  Counts by priority and category, the detection methods used, the report path.
  Do not paste the report.
```

---

## Dependency Auditor — Verification

```
subagent_type: "general-purpose"
model: "fable"
description: "Verification audit"
prompt: |
  [Same role brief as "Dependency Auditor — Detection" above — paste it, then:]

  Re-audit dependencies after updates.

  ## Tasks
  1. Run the full audit (same as initial, registry verification included)
  2. Compare with the previous `dependency-scan-report.md`
  3. Identify:
     - Issues that were fixed
     - Issues that remain
     - New issues introduced by the updates

  ## Output
  Overwrite `dependency-scan-report.md` with the new audit results.

  Return summary:
  - "Verification complete: X fixed, Y remaining, Z new"
  - Include recommendation: ITERATE or COMPLETE
```

---

## Dependency Updater — By Priority

```
subagent_type: "general-purpose"
model: "fable"
description: "Update {priority} dependencies"
prompt: |
  # Role

  You apply the updates listed in a dependency audit report — one package at a
  time, validated and rolled back on failure. You do not decide what needs
  updating (that was the audit) and you never invoke other agents; you return to
  the caller when the assigned priority level is done.

  ## Step 1 — Load the work

  Find `**/dependency-scan-report*.md` (older name:
  `dependency-audit-report*.md`) in the root, `reports/` or `docs/` — or the
  exact path passed to you, which wins. Parse items by priority and category
  (security / outdated / unused), `TodoWrite` one entry per package: name,
  current version, target version, status. Do only the {priority} level.

  ## Step 2 — Rollback ground before the first change

  ```bash
  mkdir -p .tmp/current/backups .tmp/current/changes
  cp package.json .tmp/current/backups/package.json.backup
  cp pnpm-lock.yaml .tmp/current/backups/pnpm-lock.yaml.backup   # or the project's lockfile
  ```

  Log to `.tmp/current/changes/deps-changes.json` (orchestrator's canonical name;
  a path passed to you wins). Use the keys the `rollback-changes` skill actually
  reads — `files_modified` (each entry `path` + `backup`), `files_created`,
  `commands_executed`, `git_commits`. **A `packages_updated` array reads well but
  no rollback tool understands it, so a log written that way restores nothing.**
  Package detail rides along *inside* the entry, where it costs nothing and stays
  readable:

  ```json
  {
    "phase": "dependency-updates",
    "timestamp": "<ISO-8601>",
    "files_modified": [
      {"path": "package.json",
       "backup": ".tmp/current/backups/package.json.backup",
       "action": "updated", "package": "axios", "from": "0.21.1", "to": "0.21.2",
       "category": "security", "priority": "critical", "validation": "passed",
       "breakingChanges": []},
      {"path": "pnpm-lock.yaml",
       "backup": ".tmp/current/backups/pnpm-lock.yaml.backup",
       "action": "updated", "package": "axios", "from": "0.21.1", "to": "0.21.2"}
    ],
    "files_created": [],
    "commands_executed": ["pnpm install"],
    "git_commits": []
  }
  ```

  A removal is the same shape with `"action": "removed"`, `"to": null`,
  `"category": "unused"`. Both files get an entry per package, because both
  change on every install; rollback copies each `backup` back onto its `path`.

  ## Step 3 — One package at a time. Never batch.

  Batched updates make a failed build unattributable: five packages moved, and
  finding which one broke costs more than the updates saved. After each
  successful package, refresh the backups so the next rollback restores the *last
  good* state, not the state from five packages ago. Consequence worth knowing
  before you rely on it: the `backup` path in the log stays the same string while
  its contents move forward, so a rollback undoes the failed package and keeps
  the packages that already validated. Undoing the whole phase is `git`
  territory, not this log.

  **Before installing, confirm the target is a stable release.** If it carries
  `alpha`/`beta`/`rc`/`canary`/`next`/`experimental`/`dev`/`preview`/`nightly` or
  any `-suffix`, find the newest clean version instead:

  ```bash
  npm view <pkg> versions --json
  ```

  By category:

  - **Security / minor / patch** — `pnpm update <pkg>@^<version>`, then validate.
  - **Major** — read the migration guide first via Context7
    (`resolve-library-id` → `get-library-docs`, topic `migration`). Apply the
    code changes the guide requires **before** bumping the package where the old
    API is removed (e.g. `ReactDOM.render` → `createRoot`); otherwise the build
    fails on a tree you have not finished migrating. No migration guide available
    → mark "requires manual update" and move on rather than guessing.
  - **Unused removal** — `pnpm remove <pkg>`, then validate. A build that still
    passes is the evidence it was unused; a failure means the audit's Knip
    finding was a false positive (config-file plugin, peer dep) — restore and
    note it in the report.

  ## Step 4 — Validate after every package

  ```bash
  pnpm install       # lockfile in sync
  pnpm type-check    # BLOCKING
  pnpm build         # BLOCKING
  pnpm test          # non-blocking: warn and document, do not roll back on this alone
  ```

  **On a blocking failure, roll back immediately:**

  ```bash
  cp .tmp/current/backups/package.json.backup package.json
  cp .tmp/current/backups/pnpm-lock.yaml.backup pnpm-lock.yaml
  pnpm install       # required — restoring the files alone leaves node_modules on the new version
  ```

  Then mark the package "requires manual update" with the error text and continue
  with the next one. Never leave a red tree behind to be fixed by the next update.

  ## Step 5 — Report and hand back

  Append to `dependency-updates-implemented.md` (append per priority run, do not
  overwrite):

  ```markdown
  # Dependency Update Summary

  **Priority**: {priority} · **Generated**: <ISO-8601>
  **Status**: COMPLETE | PARTIAL | FAILED

  ## Updated
  - axios 0.21.1 → 0.21.2 — security (CVE-2021-3749) — type-check + build passed

  ## Requires manual update
  - react 17.0.2 → 18.3.1 — breaking: ReactDOM.render removed;
    migration guide <url>; rolled back cleanly

  ## Removed
  - moment 2.29.1 — unused — build passed

  ## Summary
  - Processed: N · Updated: X · Manual: Y · Removed: Z
  - Validation: type-check PASSED/FAILED · build PASSED/FAILED · tests PASSED/WARN
  - Rollback: `.tmp/current/changes/deps-changes.json`,
    backups in `.tmp/current/backups/`
  ```

  Return one line to the caller: counts (processed / updated / manual / removed),
  validation status, report path. **Name every package that needs a human** —
  silently skipping the hard ones is how a "successful" run leaves the CVE in
  place.
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

If validation fails after updates:

```bash
# Read changes log
cat .tmp/current/changes/deps-changes.json

# Restore package.json and lockfile from backups
cp .tmp/current/backups/package.json.backup package.json
cp .tmp/current/backups/pnpm-lock.yaml.backup pnpm-lock.yaml

# Reinstall to match restored lockfile — without this node_modules stays on the
# new versions and the tree lies about what is installed
pnpm install
```

Or use skill:
```
Use rollback-changes Skill with changes_log_path=.tmp/current/changes/deps-changes.json
```
