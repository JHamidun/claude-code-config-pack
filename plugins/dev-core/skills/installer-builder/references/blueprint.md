# Blueprint — Electron installer architecture

Ниже — структура и переиспользуемые куски кода целиком: отдельного репозитория-образца пак не несёт, собирай по этому файлу.

## File layout

```
installer/
├── package.json            # electron + electron-builder; build config (win portable, mac dmg)
├── config.json             # repo URLs, server endpoints, links (bot/video), finish flags
├── components.json         # checkbox items + dependency graph (groups -> components)
├── packs.json              # human-readable bundles that FILTER sub-items (e.g. skill packs)
├── src/
│   ├── main.js             # main process: read JSON, run scripts via IPC, stream logs, shell open
│   ├── preload.js          # contextBridge: bootstrap/runComponent/onLog/open*/launchEditor/quit
│   └── renderer/           # index.html + styles.css + app.js (checkbox UI, deps, progress, finish)
├── scripts/windows/*.ps1   # one idempotent, offline-first script per component
├── scripts/macos/*.sh      # same, bash
├── tools/fetch-vendor.ps1  # build-time: download Windows vendor (offline)
├── tools/fetch-vendor-mac.sh # build-time on mac runner: download Mac vendor
├── tools/fetch-config.js   # build-time: clone config repo into vendor/config-pack
├── vendor/                 # (gitignored) bundled apps/wheels/browsers/config — produced at build
├── .github/workflows/build-mac.yml
└── .gitignore + .gitattributes
```

## Component & pack model

`components.json`: groups → components with `{id, name, desc, default, requires:[ids], needsAdmin, sizeHint}`. Dependency resolution (topological install order, enable-with-deps, disable-dependents) lives in a UMD module `src/renderer/deps.js` so it's shared with tests.

`packs.json`: `{core:[...], packs:[{id,emoji,name,desc,skills:[...]}]}`. Packs are ADDITIVE on top of a base — they don't replace the config. The config component always installs the base (rules, agents, commands, etc. + core items); packs just choose which optional sub-items (skills) stay. Default packs ON = full out-of-the-box, user trims.

**Pruning logic (the key insight):** install everything, then remove only sub-items that belong to SOME pack but whose pack wasn't selected. Items in `core` or in no pack are never pruned. The renderer passes two env vars to the config script: `HM_KEEP_SKILLS` (core ∪ selected packs) and `HM_ALL_PACK_SKILLS` (union of all packs). Script removes dir D iff `D ∈ ALL_PACK ∧ D ∉ KEEP`.

## Offline-first install-script pattern (every component)

```powershell
# 1. detect (respect dry-run: don't early-exit so the install branch is testable)
$DRY = [bool]$env:HM_DRY_RUN
if (Get-Command git -EA SilentlyContinue) { Write-Host "уже есть"; if (-not $DRY){exit 0} }
# 2. offline-first: bundled -> winget -> direct download
$local = if ($env:HM_VENDOR){ Join-Path $env:HM_VENDOR 'apps\git-setup.exe' } else {''}
if ($local -and (Test-Path $local)) { $action='offline' }
elseif (Get-Command winget -EA SilentlyContinue) { $action='winget' }
else { $action='download' }
# 3. mutating action guarded by dry-run
if ($DRY) { Write-Host "  [dry-run] WOULD: $local /VERYSILENT ..."; exit 0 }
# ... run the chosen install ...
# 4. honest final verify
Update-Path
if (Get-Command git -EA SilentlyContinue){ Write-Host "OK"; exit 0 } else { exit 1 }
```

`main.js` injects `HM_VENDOR` (= `resources/vendor`) and `HM_BUNDLED_CONFIG` (= `resources/vendor/config-pack`) into every child script's env, plus the renderer's per-run env (`HM_KEEP_SKILLS`, invite codes, etc.).

## Config component (don't reinvent)

If the config is a GitHub repo with its own `install.ps1/.sh`: the config script prefers the **bundled** copy (`$HM_BUNDLED_CONFIG/install.ps1`, offline) else `git clone` (online), runs it, then applies pack pruning, then verifies `~/.claude` exists. Wrap the nested installer in `try/catch` (it may have its own `Stop`).

## main.js essentials

- `resourceRoot()` = `app.isPackaged ? process.resourcesPath : projectRoot`.
- IPC: `bootstrap` (returns platform/homedir/config/components/packs), `run-component` (spawn `powershell.exe -File` / `bash`, stream stdout+stderr to renderer), `open-external`/`open-path`/`launch-cursor` (via `shell` + `spawn`), `quit`.
- Stream logs line-by-line to the renderer; resolve `{id, ok: code===0, code}`.

## Finish screen ("What's next")

Both stakeholders wanted this. On finish render: 3-step mini-instruction + buttons (Open editor, Open keys file `shell.openPath`, Return-to-bot `shell.openExternal` from `config.links.bot`, Video link from `config.links.video` — hidden if empty) + a checkbox "open editor on Done" (default from `config.finish.autoOpenCursorDefault`) + **"Retry failed"** button that re-runs only the failed component ids (the client's "auto-debug" request). Wire buttons with `addEventListener` after `innerHTML` (CSP `script-src 'self'` blocks inline `onclick`).

## Verification ladder (no clean machine available)

1. Syntax: PowerShell `[Parser]::ParseFile` (AST) for `.ps1`; `bash -n` for `.sh`; `node --check` for JS; JSON parse.
2. `HM_DRY_RUN=1` run of every script → confirms offline branch + exact command, mutates nothing.
3. Config E2E into a sandbox `$HOME` (set `$env:USERPROFILE` to a temp dir) → real clone+deploy+prune, verify file counts, real machine untouched.
4. Offline pip dry-run in a fresh venv (see gotchas #9).
5. Boot smoke: launch Electron 8s, grep stderr for renderer errors (clear `ELECTRON_RUN_AS_NODE` first).
6. The only true proof: a real clean machine (or the GitHub Actions runner). Expect to fix silent-install flags there — iterate from the user's log, like any real build.
