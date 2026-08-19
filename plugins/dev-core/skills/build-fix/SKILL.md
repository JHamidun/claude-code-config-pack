---
name: build-fix
description: "Fix failing builds and type errors with minimal safe changes until green. Triggers: «fix build», «build broken», «type errors»."
origin: ECC
---

# Build and Fix

Incrementally fix build and type errors with minimal, safe changes.

## Step 1: Detect Build System

Identify the project's build tool and run the build:

| Indicator | Build Command |
|-----------|---------------|
| `package.json` with `build` script | `npm run build` or `pnpm build` |
| `tsconfig.json` (TypeScript only) | `npx tsc --noEmit` |
| `Cargo.toml` | `cargo build 2>&1` |
| `pom.xml` | `mvn compile` |
| `build.gradle` | `./gradlew compileJava` |
| `go.mod` | `go build ./...` |
| `pyproject.toml` | `python -m compileall -q .` or `mypy .` |

## Step 2: Parse and Group Errors

1. Run the build command and capture stderr
2. Group errors by file path
3. Sort by dependency order (fix imports/types before logic errors)
4. Count total errors for progress tracking

## Step 3: Fix Loop (One Error at a Time)

For each error:

1. **Read the file** — Use Read tool to see error context (10 lines around the error)
2. **Diagnose** — Identify root cause (missing import, wrong type, syntax error)
3. **Fix minimally** — Use Edit tool for the smallest change that resolves the error
4. **Re-run build** — Verify the error is gone and no new errors introduced
5. **Move to next** — Continue with remaining errors

## Step 4: Guardrails

Stop and ask the user if:
- A fix introduces **more errors than it resolves**
- The **same error persists after 3 attempts** (likely a deeper issue)
- The fix requires **architectural changes** (not just a build fix)
- Build errors stem from **missing dependencies** (need `npm install`, `cargo add`, etc.)

## Step 4b: Rollback Anchor (capture BEFORE the first edit)

A build-fix run touches many files quickly. Capture a return point before the first Edit — not after the third failed attempt:

- [ ] `git status --short` — is the tree already dirty? Someone else's uncommitted work will get mixed into yours
- [ ] Dirty tree → `git stash push -u -m "pre-build-fix"` or commit a WIP snapshot. Clean tree → record `git rev-parse --short HEAD`
- [ ] Not a git repo → copy the files you are about to touch: `cp <file> <file>.bak-build-fix`
- [ ] State the revert trigger up front: "if total error count grows, or the same error survives 3 attempts, revert to the anchor and report"

Revert path: `git checkout -- <specific files>` or `git stash pop`. Never `git checkout -- .` — it discards every uncommitted change in the tree, including work unrelated to this build (the bash-guard blocks that form for exactly this reason).

## Step 5: Summary

Show results:
- Errors fixed (with file paths)
- Errors remaining (if any)
- New errors introduced (should be zero)
- Suggested next steps for unresolved issues

## Recovery Strategies

| Situation | Action |
|-----------|--------|
| Missing module/import | Check if package is installed; suggest install command |
| Type mismatch | Read both type definitions; fix the narrower type |
| Circular dependency | Identify cycle with import graph; suggest extraction |
| Version conflict | Check `package.json` / `Cargo.toml` for version constraints |
| Build tool misconfiguration | Read config file; compare with working defaults |

Fix one error at a time for safety. Prefer minimal diffs over refactoring.
