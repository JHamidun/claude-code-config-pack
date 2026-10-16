---
name: health-inline
description: "Чинит codebase health инлайн: /health bugs|cleanup|deps|reuse|security — детекция→фикс→верификация. Только pnpm+TypeScript-репо. НЕ одна красная сборка→build-fix."
version: 2.1.0
---

# Health Checks (Inline Orchestration) — 5 modes

You ARE the orchestrator. Execute the workflow directly without spawning a
separate orchestrator agent. Pick the mode, open its full workflow in
`references/modes/<mode>.md`, use worker prompts from
`references/worker-prompts/<mode>.md`.

## Mode table

| Mode | Command | Detect brief | Fix brief | Priorities | Report | Changes log | Fixes artifact |
|---|---|---|---|---|---|---|---|
| bug | /health bugs | Bug Hunter | Bug Fixer | critical → high → medium → low | bug-hunting-report.md | bug-changes.json | bug-fixes-implemented.md |
| cleanup | /health cleanup | Dead Code Hunter | Dead Code Remover | critical → high → medium → low | dead-code-report.md | cleanup-changes.json | dead-code-cleanup-summary.md |
| deps | /health deps | Dependency Auditor | Dependency Updater | critical → high → medium → low | dependency-scan-report.md | deps-changes.json | dependency-updates-implemented.md |
| reuse | /health reuse | Reuse Hunter | Reuse Fixer | high → medium → low (no critical) | reuse-hunting-report.md | reuse-changes.json | reuse-consolidation-implemented.md |
| security | /health security | Security Scanner | Vulnerability Fixer | critical → high → medium → low | security-scan-report.md | security-changes.json | security-fixes-implemented.md |

## Workers: no dedicated agent types (changed 2026-08-22)

The ten standalone worker agents (`bug-hunter`, `bug-fixer`, …) were retired into
`_trash-2026-08-22/agents/health/workers/`: the agent registry holds only 66
slots, and the same job described both here and in an agent file drifts apart —
the two copies have to be edited in lockstep, and a rollback already broke
because they were not.

Every worker is now spawned as **`subagent_type: "general-purpose"`,
`model: "fable"`**, with the full role brief pasted from
`references/worker-prompts/<mode>.md`. The brief names in the table above are
section headings inside that file, not agent types — `subagent_type:
"bug-hunter"` will fail with `Agent type not found`. The mode files carry a short
orchestration prompt; the brief is what the worker actually needs, so paste it.

## Shared workflow skeleton (identical in every mode)

```
Detection → Baseline → Fix/Remove/Update/Consolidate by Priority → Gate vs baseline → Verify → Repeat if needed
```

**The quality gate runs AFTER a fix, never before it.** A red `type-check`/`build`
is the usual reason this skill is invoked, so a gate placed in front of the fixing
loop exits on exactly the input it exists to repair — and in `security` mode an
unrelated broken build would block patching a live vulnerability. The pre-fix run
is therefore a *baseline record*, not a gate: it can never end the workflow.

**Max iterations**: 3

1. **Phase 1 — Pre-flight**: `mkdir -p .tmp/current/{plans,changes,backups}`;
   validate environment (`package.json`, `type-check` + `build` scripts exist);
   initialize TodoWrite with one item per priority + detection + verification.
2. **Phase 2 — Detection**: invoke the mode's detect worker via Task tool
   (prompt in the mode file); read the report, parse counts by priority;
   zero findings → skip to Final Summary.
3. **Phase 3 — Baseline (non-blocking, never exits)**: run `pnpm type-check` and
   `pnpm build` inline and RECORD the outcome as the baseline — green, or the set
   of pre-existing errors. Red baseline → note it, hand the error list to the fix
   worker as context, continue to Phase 4. Never report-and-exit here.
4. **Phase 4 — Fixing Loop**: for each priority — invoke the mode's fix worker
   via Task tool (backup each file, log to the mode's changes json, produce the
   fixes artifact), then the inline quality gate `pnpm type-check && pnpm build`
   **compared against the baseline**: any error absent from the baseline → report,
   suggest rollback, exit; same-or-fewer errors → next priority. Green is not
   required to proceed when the baseline was already red — the gate proves the
   fixes did not make things worse, and Phase 5 reports what is still broken.
5. **Phase 5 — Verification**: re-invoke the detect worker in verification mode,
   compare with the previous report. remaining == 0 → Final Summary;
   iteration < 3 and remaining > 0 → back to Phase 2; iteration >= 3 → Final
   Summary with remaining items.
6. **Phase 6 — Final Summary**: iterations {count}/3, status SUCCESS/PARTIAL,
   found/fixed/remaining totals, per-priority breakdown, validation as
   `baseline → final` for both type-check and build, artifacts list (exact
   templates — in the mode files).

**Error handling** (all modes): quality gate fails → rollback available from the
mode's changes log + `.tmp/current/backups/` (or `rollback-changes` skill);
worker fails → report error, suggest manual intervention, exit workflow.

## Per-mode deltas (details in references/modes/<mode>.md)

- **bug** — scan: type-check/build, security vulns, dead code, debug statements.
- **cleanup** — scan: unused imports/exports, commented blocks, unreachable
  code, debug statements, unused variables/functions/dependencies; Knip.
- **deps** — extra pre-flight: lockfile must exist (pnpm-lock.yaml,
  package-lock.json, yarn.lock); updater works ONE dependency at a time with
  validate-after-each and per-dependency rollback; rollback additionally
  restores package.json + lockfile and runs `pnpm install`.
- **reuse** — priorities high/medium/low only (no critical); extra section
  «Duplication Categories» + Single Source of Truth pattern (canonical
  `packages/shared-types/src/`, re-export `export * from
  '@package/shared-types/{module}'`, NEVER copy code between packages).
- **security** — scan: SQLi, XSS, auth/authz, RLS policy violations, hardcoded
  secrets, insecure dependencies.

## Why inline (vs old orchestrator agent)

| Old (Orchestrator Agent) | New (Inline Skill) |
|--------------------------|-------------------|
| 9+ orchestrator calls | 0 orchestrator calls |
| ~1400 lines (cmd + agent) | ~150 lines |
| Context reload each call | Single session context |
| Plan files for each phase | Direct execution |
| ~10,000+ tokens overhead | ~500 tokens |

## References

- `references/modes/{bug,cleanup,deps,reuse,security}.md` — full original
  workflows, verbatim (formerly the 5 standalone skills).
- `references/worker-prompts/{bug,cleanup,deps,reuse,security}.md` — **the full
  role briefs**: detection, verification and fix worker, each self-contained
  (rewritten 2026-08-22, absorbing the bodies of the ten retired agents).
- `references/bug-report-template.md` — section-by-section template of
  `bug-hunting-report.md` (раньше лежал в agents/references под именем bug-hunter-report-template.md — файла больше нет).
