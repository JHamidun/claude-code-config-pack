---
name: installer-builder
description: "One-click installers (Windows .exe + macOS .dmg) on Electron: выбор компонентов, fully-offline bundling, GitHub Actions macOS build (без Mac). Triggers: «сделай инсталлятор», «установщик в один клик», «офлайн-инсталлятор», «exe + dmg», «вшить ПО в один установщик», «накатить софт на чистую машину», «offline installer», «electron installer». NOT: npm packages, MSI-only (WiX), App Store."
metadata:
  version: 1.0.0
  updated: 2026-06-23
  reference-implementation: ${WORKSPACE}/yourname-installer
---

# Installer Builder

Build a beginner-proof, one-click installer that drops a fully-configured stack onto a clean machine: an Electron GUI with checkbox component selection that silently installs third-party apps (editors, runtimes, CLIs, VPN), deploys a config from GitHub, and installs language deps. Supports **full offline** (everything bundled) or **online bootstrapper** (downloads at install).

A complete, working reference implementation lives at `${WORKSPACE}/yourname-installer` — read its files for exact, current code. This skill is the map + the non-obvious lessons.

## Read first

**`references/gotchas.md` — read it before writing any code.** Every entry cost hours on a real build. Most are silent-until-clean-machine failures (BOM, PowerShell stderr, Store-python stub, Cursor `-Wait`, GitHub 100MB). Skipping it guarantees re-discovering them.

- `references/blueprint.md` — architecture, file layout, the component/pack model, offline-vendor design, the offline-first install-script pattern, IPC, dry-run, next-step screen.
- `references/ci-and-platforms.md` — Windows portable+admin packaging, the GitHub Actions macOS `.dmg` build (build a Mac version without owning a Mac), code signing reality.

## Core architecture (decide up front)

1. **One product → two platform builds.** No single binary runs on Win+Mac. Ship `Setup-Windows.exe` and `Setup-Mac.dmg` from one Electron codebase. A download page detects OS.
2. **Don't install "the installer".** Use a **portable** Windows exe (runs the GUI directly, no install-then-launch) with admin elevation; macOS ships a `.dmg`.
3. **Offline vs online — pick per project:**
   - **Full offline**: a build-time `fetch-vendor` script downloads every installer/wheel/browser into `vendor/`; electron-builder bundles it; install scripts install from `vendor/` (no internet). ~800MB-1.2GB. Versions freeze at build → rebuild to refresh.
   - **Online bootstrapper**: small (~70MB), downloads components at install via winget/brew/direct. Always latest, needs internet.
   - **Hybrid**: bundle the cheap/yours-anyway parts (your config), download heavy apps online.
4. **Config-driven**: `components.json` (checkbox items + dependency graph), `packs.json` (human-readable bundles that filter which sub-items install), `config.json` (URLs, endpoints, flags). Editing JSON + rebuild = patch.

## Workflow

1. **Scope** — list components (apps, runtimes, CLIs, the config, language deps, VPN) and decide offline level. Confirm with the user: offline level, code-signing budget, any server endpoints, the config repo URL.
2. **Scaffold** the Electron app (main process runs platform scripts via IPC and streams output; preload exposes a safe bridge; renderer = checkbox UI + log + finish screen). See `blueprint.md`.
3. **Write per-component install scripts** — `scripts/windows/*.ps1` + `scripts/macos/*.sh`, one per component, **idempotent + offline-first** (`if bundled → install local; elif winget/brew → ; else download`). Follow the script rules in `gotchas.md` exactly.
4. **Build-time vendor fetch** (if offline) — `tools/fetch-vendor.ps1` (Win) / `fetch-vendor-mac.sh` (Mac runner): download apps, language wheels (pin to the bundled runtime version), browser engines, npm cache.
5. **Package** — `electron-builder --win` (portable, requestExecutionLevel admin) and `--mac` (dmg). See `ci-and-platforms.md`.
6. **Verify** — there is no clean machine here. Use: AST/`bash -n` syntax checks, a `HM_DRY_RUN` flag that prints "WOULD install X" without mutating, a config-deploy E2E into a sandbox `$HOME`, an offline `pip --dry-run` in a fresh venv, and a boot smoke. Then a real clean-machine run (or GitHub Actions) is the only true proof.
7. **Polish** — a "What's next" finish screen (open editor button + auto-open checkbox, open-keys-file, return-to-bot link, video link, **retry-failed**), all driven by `config.json`.

## Hard rules (from real failures — do not skip)

- **Windows `.ps1` with non-ASCII MUST be UTF-8 with BOM**, else `powershell.exe` mis-reads it and the script won't parse. Re-apply BOM after every edit.
- **Install scripts: `$ErrorActionPreference='Continue'`, not `Stop`** — native tools (npm/pip/python) write notices to stderr; under `Stop` that becomes a fatal `NativeCommandError`. Use explicit `exit 0/1` + final verification for honest status.
- **Never `git add`/commit the built `.exe`/`.dmg`** — GitHub rejects files >100MB. Gitignore `*.exe *.dmg release/ release-mac/ vendor/ node_modules/`.
- **`.gitattributes`: `*.sh text eol=lf`** (CRLF breaks the shebang on Mac).
- A `.dmg` can be built **only on macOS** → use the GitHub Actions mac runner (`ci-and-platforms.md`).

After creating or changing the skill, register it (routing.md row + CLAUDE.md count). The reference project is the source of truth for code — prefer reading/adapting it over writing from scratch.
