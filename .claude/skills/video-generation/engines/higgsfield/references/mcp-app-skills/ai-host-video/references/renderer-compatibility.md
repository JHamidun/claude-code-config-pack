# Native renderer contract

The current MCP develop base ships native Higgsedit 0.14.0. Inspect the actual
hosted `higgsedit --help`, installed `types/fable.d.ts` and doctor; updating repository
files does not prove an existing sandbox was rebuilt. Use `$video-editing` for project
and export APIs and `$motion-craft` for the chosen animation technique.

Build the authored edit with `higgsedit build edit.jsx`. Let that script only create
and compose the timeline; render separately with `higgsedit render . --out ...`.
This prevents an in-script render plus another CLI render from encoding twice.
No custom workflow command or environment guard is required.

The native 0.14 CLI supports draft/final quality and worker/concurrency limits.
Check installed help before adding optional flags; do not force the removed
`--engine` switch. A reasonable render worker cap is 3, lowered if resources require.
Use only one supported worker/concurrency control, and report actual defaults when
an option is unavailable. A claimed cheap draft must actually use supported draft
quality; inspect the full-quality result for encode detail.

Native frames, raw tracks, masks, token text and custom GLSL are supported by the
matching runtime. Do not carry forward the old blanket prohibition on shaders.
Unsupported individual effects must be detected from the installed API/build; browser
preview output does not establish native compatibility. No HTML animation or runtime
callbacks are part of this native composition contract.

Use `p.read()` / CLI read and inspect for evaluated geometry, and frame/sheet/render
for actual pixels. There is no `p.compose(..., {dryRun:...})` in the current public
Project/ComposeOptions contract. Successful geometry inspection is not visual QA.
For a tiny preflight project, use actual documented APIs, render native pixels and
probe the produced file. Missing required capabilities need resolution before a
paid full-episode run; do not install or upgrade the shared renderer from the skill.

For the final master, request `--quality final --depth 10` when the installed CLI
supports both. Check the actual output pixel format/bit depth and renderer diagnostics;
a fallback is disclosed, not called 10-bit. Use one worker flag or its concurrency
alias, never both. Host-cut and proof retain preview settings. A process timeout does
not establish exit: inspect the existing process/log before retrying. On a killed
FFmpeg process, inspect memory and orphaned render processes before one bounded retry.
