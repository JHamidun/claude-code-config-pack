# NVIDIA SkillSpector runtime: one-time setup

The NVIDIA line of the audit is optional. Without it `audit_skill.py` still runs the
local `leak-scan` line and reports the NVIDIA line as
`{"status": "unavailable", "reason": "SkillSpector runtime not installed"}` with exit
code 2: an incomplete audit, never a clean one. Installing the runtime is a separate,
explicit decision of the user; an audit never installs, updates or repairs it.

SkillSpector is third-party code (https://github.com/NVIDIA/SkillSpector, Apache-2.0).
It runs only through `scripts/nvidia_static.py`, which blocks Python socket and DNS
calls, with `--no-llm` and a credential-stripped environment. The install below does
need the network once.

## Where it lives

| Setting | Value |
|---|---|
| venv directory | `$SKILLSPECTOR_HOME`, default `~/.claude/tools/skillspector` (with `CLAUDE_CONFIG_DIR` set: `<that dir>/tools/skillspector`) |
| interpreter the wrapper calls | `Scripts\python.exe` on Windows, `bin/python` elsewhere; `--nvidia-python <path>` overrides |
| Python | 3.12-3.14 (upstream `requires-python = ">=3.12,<3.15"` at the pinned commit); the recorded lock was built on 3.13 |
| pinned upstream | commit `d162d9b343e559be13df8ebba093df3bc9d58c90`, package 2.11.2 |
| exact dependency set | `references/runtime-lock.txt` (includes the pinned SkillSpector archive URL) |

A non-default `SKILLSPECTOR_HOME` must be visible to the process that runs the
wrapper, e.g. via the `env` block of `~/.claude/settings.json`:
`"env": { "SKILLSPECTOR_HOME": "/path/to/skillspector" }`.

## Install with uv (recommended)

uv fetches a matching Python if none is installed.

bash (Linux, macOS, Git Bash):

```bash
SS="${SKILLSPECTOR_HOME:-$HOME/.claude/tools/skillspector}"
uv venv --python 3.13 "$SS"
uv pip install --python "$SS/bin/python" -r ~/.claude/skills/skill-manager/references/runtime-lock.txt
```

On Git Bash for Windows the interpreter is `"$SS/Scripts/python.exe"`.

PowerShell:

```powershell
$SS = if ($env:SKILLSPECTOR_HOME) { $env:SKILLSPECTOR_HOME } else { "$env:USERPROFILE\.claude\tools\skillspector" }
uv venv --python 3.13 $SS
uv pip install --python "$SS\Scripts\python.exe" -r "$env:USERPROFILE\.claude\skills\skill-manager\references\runtime-lock.txt"
```

## Install with plain venv + pip

Needs a Python 3.12-3.14 already installed.

```bash
SS="${SKILLSPECTOR_HOME:-$HOME/.claude/tools/skillspector}"
python3.13 -m venv "$SS"
"$SS/bin/python" -m pip install -r ~/.claude/skills/skill-manager/references/runtime-lock.txt
```

```powershell
$SS = if ($env:SKILLSPECTOR_HOME) { $env:SKILLSPECTOR_HOME } else { "$env:USERPROFILE\.claude\tools\skillspector" }
py -3.13 -m venv $SS
& "$SS\Scripts\python.exe" -m pip install -r "$env:USERPROFILE\.claude\skills\skill-manager\references\runtime-lock.txt"
```

`runtime-lock.txt` records a working Windows / Python 3.13 install. If one of its
pinned wheels does not exist for your OS or Python, install only the pinned
SkillSpector revision and let the resolver pick the dependencies:

```bash
uv pip install --python "$SS/bin/python" "skillspector @ https://github.com/NVIDIA/SkillSpector/archive/d162d9b343e559be13df8ebba093df3bc9d58c90.zip"
```

Then record what you actually got (for example `uv pip freeze --python "$SS/bin/python" > "$SS/runtime-lock.local.txt"`)
so a later audit can be compared against a known state.

## Check the install

```bash
python -I -B ~/.claude/skills/skill-manager/scripts/audit_skill.py --help
```

The `--nvidia-python` default in the help text is the interpreter the wrapper will
call; it must exist. Then audit a tiny benign skill you created in a scratch folder
(reports outside `~/.claude/skills`): the printed summary should show
`"nvidia": "completed"` or `"incomplete"` with a reason, never `"unavailable"`.
The first run can take several minutes: importing `skillspector.cli` is slow.

## Updates and removal

Never update during an ordinary audit. To move to a newer upstream commit: review the
upstream diff, build a fresh venv at a new path, audit a few known-good and known-bad
fixtures with it, then point `SKILLSPECTOR_HOME` at it and record the new commit and
freeze. To remove the NVIDIA line, delete the venv directory; audits fall back to
`unavailable` for that line.
