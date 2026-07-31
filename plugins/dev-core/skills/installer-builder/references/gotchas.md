# Installer gotchas (each cost real hours)

Most are **silent until a clean machine** — they pass syntax checks and even run fine on the dev box (where tools are already installed), then break for the end user. Treat as hard rules.

## PowerShell / Windows scripts

### 1. `.ps1` with Cyrillic/non-ASCII MUST be UTF-8 **with BOM**
- **Symptom:** `powershell.exe -File script.ps1` → `The string is missing the terminator` / `MissingEndCurlyBrace` / garbled mojibake. Passes `[Parser]::ParseFile` though.
- **Cause:** Windows PowerShell 5.1 (which Electron's `spawn('powershell.exe')` uses) reads a no-BOM file as cp1251, mangling UTF-8 Cyrillic and breaking string quotes.
- **Fix:** Save every `.ps1` as UTF-8 **with BOM**. After ANY edit (the Edit tool strips BOM), re-apply:
  ```powershell
  $f='ABS\PATH\x.ps1'; $t=[IO.File]::ReadAllText($f,[Text.Encoding]::UTF8)
  [IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $true))
  ```
- **Note:** `[IO.File]::ReadAllText/WriteAllText` resolve RELATIVE paths against the process dir (`C:\Users\<you>`), NOT PowerShell's `cd`. Use absolute paths or `$_.FullName`.
- JSON and `.sh` must stay **without** BOM (Node/bash break on BOM).

### 2. `$ErrorActionPreference='Stop'` + native stderr = fatal
- **Symptom:** Step dies at a `& npm/pip/python ...` line with `NativeCommandError`, even though the command "worked".
- **Cause:** Native tools print notices to stderr; under `Stop`, PowerShell turns that into a terminating error.
- **Fix:** Install scripts use `$ErrorActionPreference='Continue'`. Get honest red/green from explicit `if ($LASTEXITCODE -ne 0){exit 1}` + a final verification (`Get-Command x` / `Test-Path`).

### 3. The Windows Store python stub
- **Symptom:** On a clean Win11, python step dies in version-detection before installing the bundled Python.
- **Cause:** `Get-Command python` returns `...\WindowsApps\python.exe` (App Execution Alias) which prints "Python was not found…" to stderr.
- **Fix:** In `Get-Py`, skip paths matching `WindowsApps`, validate output `-match 'Python \d'`, and fall back to known install paths (`%LOCALAPPDATA%\Programs\Python\PythonXYZ\python.exe`).

### 4. `"$var: text"` ParserError
- **Symptom:** `Variable reference is not valid. ':' was not followed by…`
- **Cause:** `:` after a variable name is a scope/drive qualifier.
- **Fix:** `"${var}: text"`.

### 5. PATH not refreshed across steps
- **Cause:** Each component runs as its own `powershell.exe` with the env snapshot from when Electron started; a tool installed by a prior step isn't on PATH.
- **Fix:** Every script starts with `Update-Path` reading Machine+User PATH from the registry. For just-installed tools also probe known install dirs (don't trust PATH).

## Silent-install / app specifics

### 6. Cursor installer auto-launches → `-Wait` hangs forever
- **Symptom:** Install "freezes" after Cursor; only un-freezes when the user closes the Cursor window.
- **Cause:** Cursor's `/S` installer launches Cursor; `Start-Process -Wait` waits on the whole tree.
- **Fix:** Start WITHOUT `-Wait`; poll for `Cursor.exe` to appear (up to ~180s); then `Get-Process Cursor | Stop-Process -Force` (kills the auto-launched app — also fixes the next bug).

### 7. Editor extension install fails
- **Symptom:** `cursor --install-extension X` → `aborted`; the `code` path reports `VS Code 1.67.1 incompatible`.
- **Causes:** (a) Cursor was running (kill it first — see #6). (b) `Get-Command code` resolves to Cursor's bundled `code` shim (old engine), not real VS Code.
- **Fix:** Kill the editor before installing; use ONLY the real VS Code path (`%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd`); verify via `--list-extensions` (exit code lies); honest message if it fails (the CLI still works without the extension).

### 8. Dead vendor download URLs
- `downloader.cursor.sh` is dead. Use `https://www.cursor.com/api/download?platform=win32-x64-user&releaseTrack=stable` (or `darwin-arm64`/`darwin-x64`) → JSON `.downloadUrl`. May 308-redirect → try www + apex, `-MaximumRedirection 10`.
- Silent flags that worked: Git `/VERYSILENT /NORESTART /SP- /SUPPRESSMSGBOXES`; Node MSI `msiexec /i x.msi /qn /norestart`; Cursor/NSIS `/S`; Python `/quiet InstallAllUsers=0 PrependPath=1 Include_test=0`. **Flag acceptance is only truly proven on a clean machine.**

## Offline language deps (Python)

### 9. Cross-platform `pip download` → ResolutionImpossible
- **Symptom:** `pip download -r req --only-binary=:all: --platform win_amd64 --python-version 3.12` errors, downloads almost nothing.
- **Fix:** Bundle a Python matching the BUILD machine's version, then plain `pip download -r req -d wheels` (no cross flags). Wheels then match the bundled runtime. Verify in a **fresh venv**: `python -m pip install --no-index --find-links wheels -r req --dry-run` → must exit 0 and list "Would install …" for all packages. On macOS use `--break-system-packages`; bundle Python via python.org `.pkg`, run pip with that exact interpreter so wheels match.
- The config's tools call bare `python`, so install with `pip install --user` (not a venv) so plain `python` sees them. Playwright browsers: bundle the browsers dir and copy to the default cache (`%LOCALAPPDATA%\ms-playwright` / `~/Library/Caches/ms-playwright`).

## electron-builder / packaging

### 10. `app-builder.exe CANNOT_EXECUTE` / `remove d3dcompiler_47.dll: Access denied`
- **Cause:** `release\win-unpacked` locked by a still-running Electron (from a smoke test) OR two builds writing `release\` at once (7za collision).
- **Fix:** Before building: kill `electron|YourName|app-builder|7za`, `Remove-Item -Recurse -Force release\win-unpacked`, and run only ONE build at a time.

### 11. `ELECTRON_RUN_AS_NODE` breaks smoke tests
- **Symptom:** Launching Electron for a smoke test → `Cannot read properties of undefined (reading 'whenReady')`.
- **Cause:** The host (VS Code / Claude Code) sets `ELECTRON_RUN_AS_NODE=1`, so Electron runs as plain Node.
- **Fix:** `Remove-Item Env:\ELECTRON_RUN_AS_NODE` before launching. The shipped exe is unaffected.

## Git / GitHub

### 12. Push rejected — file >100MB
- **Symptom:** `pre-receive hook declined` after `git add -A`.
- **Cause:** A built `.exe`/`.dmg` (or downloaded artifact) got staged; GitHub hard-limit is 100MB.
- **Fix:** Gitignore `*.exe *.dmg release/ release-mac/ vendor/ node_modules/`. If already committed: `git reset --soft HEAD~1; git rm -r --cached <artifact>; git add -A; commit`.

### 13. `.sh` checked out with CRLF on Mac
- **Fix:** `.gitattributes` → `*.sh text eol=lf` (and `*.ps1 text eol=crlf`). CRLF breaks `#!/usr/bin/env bash`.

## Distribution / trust (set expectations)

### 14. macOS says the unsigned app is **"damaged"** — it is NOT corrupt (verified live 2026-06)

- **Symptom:** User downloads the dmg in a browser, dmg mounts fine, but launching the app → «Приложение повреждено, и его не удается открыть. Переместите в Корзину». Looks exactly like a broken file; hashes match perfectly.
- **Cause:** Gatekeeper. Modern macOS (Sequoia/Tahoe) shows the *damaged* wording for **quarantined + unsigned/un-notarized** apps. The old right-click → Open bypass NO LONGER WORKS for these. The dialog even shows "Chrome загрузил этот файл…" — that's the quarantine metadata.
- **Fix (3 layers):**
  1. **Always ad-hoc sign** via an `afterPack` hook (`codesign --force --deep --sign - "<App>.app"` + `codesign --verify`). `CSC_IDENTITY_AUTO_DISCOVERY=false` alone leaves the bundle with NO signature at all, and a fully unsigned **arm64** binary is killed by the kernel even after dequarantine. Hook: `build.afterPack: "tools/mac-adhoc-sign.js"`, guard `context.electronPlatformName === 'darwin'`.
  2. **Ship a README inside the dmg** (`build.dmg.contents` entry `{type:"file", path:"assets/mac/ПРОЧТИ….txt"}` — override includes app + /Applications link too) telling the user: drag to Applications, then in Terminal `xattr -cr "/Applications/<App>.app"`, then open. `.txt` opens fine from a quarantined dmg.
  3. Put the same 2-step instruction wherever the download link is given (bot/landing).
- **Real fix (no dialog at all):** Apple Developer ID + `notarytool` + staple ($99/yr). Windows side: SmartScreen "More info → Run anyway" still works as before; Azure Trusted Signing (~$10/mo) for reputation.

## Test-harness traps (when verifying on the dev box)

- `Select-Object -First N` piped from a running `powershell -File ...` **kills the process** after N lines → the script never finishes. Capture full output when testing scripts.
- The dev box already has the tools → detection branches skip the install path. Add `HM_DRY_RUN` that (a) does NOT early-exit on "already installed" and (b) replaces the real action with `Write-Host "[dry-run] WOULD: <cmd>"` — this lets the offline-install branch be exercised on a dirty machine without mutating it.
