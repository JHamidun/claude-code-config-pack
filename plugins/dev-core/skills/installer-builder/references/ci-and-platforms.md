# Packaging, CI & platform specifics

## Windows packaging (electron-builder)

Target **portable** (single self-extracting exe that runs the GUI directly — no "install the installer" step) with admin elevation:

```json
"win": {
  "target": [{ "target": "portable", "arch": ["x64"] }],
  "artifactName": "Setup-Windows.${ext}",
  "requestedExecutionLevel": "requireAdministrator"
},
"portable": { "requestExecutionLevel": "admin", "artifactName": "Setup-Windows.${ext}" }
```

Build: `npm run dist:win` (= `fetch:config && fetch:vendor && electron-builder --win`). Add a `dist:win:lite` without `fetch:vendor` for the online/hybrid variant.

`extraResources` bundles `scripts/`, the JSON configs, and `vendor/`. Per-platform vendor is achieved naturally: on Windows only `fetch-vendor.ps1` runs (Windows binaries); on the Mac runner only `fetch-vendor-mac.sh` runs (Mac binaries). Same `vendor → vendor` mapping works for both.

First build downloads electron + winCodeSign + nsis into the electron-builder cache (slow once). Recompressing a ~1.2GB vendor takes minutes per build.

## macOS build — without owning a Mac

A `.dmg` can be built **only on macOS** (needs `hdiutil`, Mac toolchain). Use a **GitHub Actions macOS runner**:

```yaml
# .github/workflows/build-mac.yml
on: { workflow_dispatch: {} }
jobs:
  build-mac:
    runs-on: macos-latest      # Apple Silicon (arm64) since 2024
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm install --no-audit --no-fund
      - run: npm run fetch:config
      - run: bash tools/fetch-vendor-mac.sh        # omit for hybrid (config-only) build
      - env: { CSC_IDENTITY_AUTO_DISCOVERY: 'false' }   # unsigned v1
        run: npx electron-builder --mac --arm64 --publish never
      - uses: actions/upload-artifact@v4
        with: { name: Setup-Mac, path: release/*.dmg, if-no-files-found: error }
```

Flow: push the installer repo to GitHub (private; gitignore the heavy/built files) → `gh workflow run build-mac.yml` → `gh run watch <id> --exit-status` → `gh run download <id> --name Setup-Mac`. ~3-10 min depending on vendor.

**Mac arch reality:** mac wheels + browser engines are arch-specific. Build **arm64-only** for full-offline (Apple Silicon, ~all Macs since 2020). Intel needs a separate x64 vendor+build (future). Hybrid (apps online via brew/dmg) sidesteps this and can be universal.

**Mac offline specifics:** Node/Python `.pkg` from python.org/nodejs.org are universal2 (install via `installer -pkg ... -target /`, admin via `osascript ... with administrator privileges`). Install the bundled Python ON the runner first, then `pip download` with THAT interpreter so wheels match. **Git** on Mac is awkward to bundle offline (dylib relocation) — leave it to Xcode CLT / system git (the one online exception). Cursor/editor extension via marketplace is also online unless you bundle the `.vsix`.

## Hybrid vs full-offline (the size question)

- Full-offline Windows ~800MB, Mac(arm64) ~900MB — bundles editor, runtimes, language wheels, browser engine (the dominant size), npm cache, config.
- Hybrid Mac ~100MB = Electron runtime (~88MB) + config (~16MB); apps download at install. If a user asks "why is it so small?", that's the answer: the ~700MB difference is exactly the bundled offline apps.

## Code signing (to remove warnings) — costs

| OS | Unsigned UX | To fix |
|----|-------------|--------|
| Windows | SmartScreen "unknown publisher" (both OV/EV now build reputation over time) | Azure Trusted Signing (~$10/mo, cloud HSM) |
| macOS | Gatekeeper "can't be opened / damaged" | Apple Developer ID ($99/yr) + `codesign` + `notarytool` + `stapler` |

v1 user workaround: Win "More info → Run anyway"; Mac right-click → Open (or `xattr -dr com.apple.quarantine /Applications/App.app`). Bake these into the download page so beginners don't get stuck.

## Clean-machine autotest

Ship `test/clean-machine-test.ps1` (and a `.sh`) that runs all component scripts headlessly then verifies outcomes (tool `--version`, config dir populated, deps importable) and prints PASS/FAIL + a log. Add a `-DryRun` switch (sets `HM_DRY_RUN=1`) for a safe first pass. This turns "you test it" into "run one file, send the log."
