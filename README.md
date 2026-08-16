# Claude Code Configuration Pack

> Depersonalised Claude Code setup. Drop into `~/.claude/`, fill in API keys, run.

## Три способа установки

Один и тот же набор инструментов раздаётся тремя путями. Разница — в объёме и в том,
трогается ли твой `~/.claude`.

| Способ | Что получаешь | Когда выбирать |
|---|---|---|
| 1. Весь конфиг | плоский `~/.claude/`: скиллы, агенты, команды, правила, хуки, MCP | нужна вся рабочая среда целиком |
| 2. Маркетплейс | 33 плагина, ставишь любые по имени | свой `~/.claude` уже есть, файлы в него докладывать не хочется |
| 3. Один плагин | ровно один плагин, без остальных | нужен конкретный набор (например, video-media) и ничего больше |

### 1. Весь конфиг целиком

```powershell
git clone https://github.com/JHamidun/claude-code-config-pack.git
cd claude-code-config-pack
./install.ps1 -DryRun     # показать план, ничего не менять
./install.ps1
```

Если Windows отказывается запускать скрипт («running scripts is disabled»):
`powershell -ExecutionPolicy Bypass -File .\install.ps1`.

```bash
git clone https://github.com/JHamidun/claude-code-config-pack.git
cd claude-code-config-pack
chmod +x install.sh uninstall.sh
./install.sh --dry-run
./install.sh
```

Кладёт файлы поверх твоего `~/.claude` (по умолчанию — только недостающие, существующее
не трогается), перед этим снимает резервную копию, в конце доводит рантайм (браузер
Playwright, маркетплейсы, node_modules). Всё разложенное записывается в манифест, поэтому
`./uninstall.sh` / `.\uninstall.ps1` убирает ровно то, что положил установщик. Детали и
гарантии — раздел [Install](#install) ниже.

**Когда выбирать:** ставишь конфиг как рабочую среду — правила, роутинг, память, хуки,
интеграции. Плагины из каталога поверх не нужны: те же скиллы уже лежат в `~/.claude/skills/`.

### 2. Маркетплейс: все 33 плагина

В Claude Code:

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install video-media@hamidun
/plugin install design-system@hamidun
```

Из терминала то же самое: `claude plugin marketplace add …` / `claude plugin install …`.
Список плагинов — `/plugin` или каталог в `.claude-plugin/marketplace.json`.

**Когда выбирать:** у тебя уже настроенный `~/.claude`, и мержить в него чужие файлы не
хочется. Плагины живут в собственном кэше, включаются по одному, обновляются
`/plugin update`, удаляются `/plugin uninstall` — твой конфиг не затрагивается.

### 3. Один плагин отдельно

Через отдельный репозиторий — выкачивается только этот плагин:

```text
/plugin marketplace add JHamidun/claude-plugin-video-media
/plugin install video-media@hamidun-video-media
```

Через git-subdir из монорепо — Claude Code делает sparse clone одного подкаталога, не
выкачивая остальной репозиторий. В нашем каталоге есть рабочий образец такой записи
(`video-media-subdir`); для собственного `marketplace.json` она выглядит так:

```json
{
  "name": "video-media",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/JHamidun/claude-code-config-pack.git",
    "path": "plugins/video-media"
  }
}
```

**Когда выбирать:** нужен один набор инструментов, остальные 32 плагина не интересуют.
Отдельный репозиторий — самый короткий путь для человека. git-subdir — для того, кто ведёт
собственный `marketplace.json` и хочет тянуть плагин прямо из монорепо, пиня версию через
`ref`/`sha`. Если каталог монорепо у тебя уже добавлен — ставь просто
`video-media@hamidun`, git-subdir тут ничего не ускорит.

---

## Install

If you already use Claude Code, read this section before running anything. The installer is
built around one rule: **it never moves or deletes your `~/.claude`.**

### Windows (PowerShell)

```powershell
./install.ps1 -DryRun     # see exactly what would happen, change nothing
./install.ps1             # install
```

### macOS / Linux (bash)

```bash
chmod +x install.sh uninstall.sh
./install.sh --dry-run    # see exactly what would happen, change nothing
./install.sh              # install
```

### What the installer actually does

1. **Backs up `~/.claude` first**, before touching anything — a *copy* to
   `~/.claude.backup.<timestamp>`, not a move. On by default; the 3 most recent copies are kept
   and older ones removed. Your API keys and Telegram session are deliberately **excluded** from
   the copy (they would otherwise be duplicated in cleartext across three backups; the originals
   stay untouched in `~/.claude`). If some file is locked (Cursor/Claude running), you get a
   warning, not a failure — the original was never moved, so nothing is at risk.
2. **Merges the pack on top of your existing tree.** Default mode adds **only files you don't
   have**. Anything already present is left exactly as it is, whatever version it is.
3. **Never writes through a symlink or junction — at any depth.** Before copying anything, the
   installer walks the whole `~/.claude` tree (without ever following a link) and collects every
   symlink, junction and directory reparse point in it: `skills/`, `agents/health/`,
   `config/rules-ref/hooks.md`, a single `settings.json` — wherever it sits. A destination is
   then skipped when **the file itself or any directory along its path** is a link, so nothing is
   written into the external target. Every skipped link is printed, not hidden. If that scan
   cannot be completed (an unreadable directory, for instance), the installer stops and changes
   nothing rather than guessing.
   The flip side worth knowing: the backup copies links *as links*, so it does not contain the
   contents of external targets. This pre-write check is therefore the only protection there is,
   which is exactly why a failed scan aborts the install.
   The scan runs **twice**: once at the start (so `--dry-run` can report it) and again immediately
   before the first write. The backup copy in between takes seconds — long enough for a link to
   appear and be missed by a single early scan. Links that show up in that gap are reported and
   excluded. What remains uncovered is a link created *during* the copy itself; closing that too
   would mean giving up `rsync`/`robocopy` (and with it long-path support on Windows) for a
   per-file loop that still has a microsecond-wide window of its own.
4. **Never overwrites a file in place when it has a second name (a hard link).** A hard link is a
   second name for the *same* file, not a copy: nothing marks it as a link, and the scan above
   cannot see it — both names are equal. A plain in-place overwrite would therefore change your
   file wherever its other name lives (`~/work/config.json`), silently, with nothing to restore
   from: the backup holds `~/.claude`, not the outside name. So an already existing destination is
   written the safe way — into a temporary file next to it, then renamed over it. A rename swaps
   the *directory entry*, so the old file lives on under its other name with its old content.
   Content, permissions and modification time come out exactly as a direct copy would leave them,
   and repeated runs stay idempotent. A file whose content and timestamp already match is left
   alone, link intact (`robocopy` and `rsync` skip it; only the plain-`cp` fallback used when
   `rsync` is absent rewrites everything). The run reports only links it actually split, and
   `--dry-run --repair` / `-DryRun -Repair` warns about the candidates beforehand.
5. **Creates `~/CLAUDE.md` only if you don't have one.** An existing one is never overwritten,
   not even with `--repair`.
6. **Seeds `~/.claude/.credentials.master.env` from the template only if it does not exist.**
7. Records everything it placed in `~/.claude/.ccpack-manifest.txt` (that is what makes a clean
   uninstall possible).
8. Optionally installs Python deps — skip with `--skip-deps` / `-SkipDeps`.

After installation: launch Claude Code in any project. Plugins auto-download (~30-60s).

### Never overwritten — in any mode, including `--repair`

| Path | Why |
|------|-----|
| `.credentials.master.env`, `.credentials.json` | all your API keys, Claude Code OAuth |
| `settings.local.json` | your local settings (`settings.json` is ours and does get updated) |
| `MEMORY.md`, `memory/` | your auto-memory |
| `projects/` | session history — the least recoverable thing you own |
| `todos/`, `shell-snapshots/` | session runtime |
| `chats.db*` | chat database (incl. `-wal`/`-shm`/`-journal`) |
| `tg_session.session*` | Telegram client authorization |
| `~/CLAUDE.md` | your personal instructions |
| `rules/user-profile.md` | your profile — name, email, phone. The pack ships a blank template and asks you to fill it in, so it is placed only when missing and never overwritten afterwards |

### `--repair` / `-Repair`

Overwrites **our** base files with fresh copies — use it when the config got mangled and you
want the pack's version back. The table above still applies. But note: if you edited a file
whose name matches a pack file (say `skills/<name>/SKILL.md`), `--repair` replaces it with ours.
Your version is in the backup taken moments earlier. If you want to keep your edits, install
without `--repair`.

### Flags

| Flag (bash / PowerShell) | Effect |
|------|-----|
| `--dry-run` / `-DryRun` | print the plan, change nothing |
| `--repair` / `-Repair` | refresh our base files (see above) |
| `--skip-deps` / `-SkipDeps` | don't install Python dependencies |
| `--no-backup` / `-NoBackup` | skip the backup copy (not recommended) |

## Uninstall / rollback

```bash
./uninstall.sh --dry-run     # list what would be removed
./uninstall.sh
```

```powershell
./uninstall.ps1 -DryRun
./uninstall.ps1
```

It removes a file only if **all** of these hold:

1. the file is listed in `~/.claude/.ccpack-manifest.txt` — i.e. the installer actually created
   it. A file that already existed under a name the pack also uses is *not* ours and is never
   listed, so it is never removed;
2. it lives inside `~/.claude` (or it is the `~/CLAUDE.md` we created);
3. neither the file **nor any directory above it** is a symlink/junction. If you moved, say,
   `~/.claude/skills` into your own repo and linked it back, nothing under that link is deleted —
   and the uninstaller names every link it skipped for that reason;
4. its size and timestamp still match what was recorded at install time — **if you edited it, it
   stays**, and the uninstaller says so.

Directories that become empty are removed with `rmdir` only (a non-empty directory is never
touched, and a directory reached through a link at any level is not touched either). A handful of directories the pack ships *empty* stay behind — the manifest tracks
files, so nothing proves those directories are ours, and guessing could delete a folder you
created. `.credentials.master.env` is deliberately left in place — it may hold your keys.
Backups under `~/.claude.backup.*` are never deleted by the uninstaller.

**No manifest, no deletion.** If the manifest is missing or unreadable, the uninstaller removes
nothing at all and tells you why — it cannot tell pack files from yours, and guessing is not an
option.

### Full rollback

The backup copy is a plain directory. To go back to your pre-install state, run the uninstaller
and then copy back from `~/.claude.backup.<timestamp>` (remember it intentionally contains no
keys and no Telegram session — those were never touched in the original).

## Free by default — no third-party API key required

**You need nothing but your Claude subscription.** Text, code, reasoning, agents, skills,
commands and memory all run on Claude Code itself. `.credentials.master.env` ships with
every key commented out, and that is the supported state — leave it alone and the pack works.

A handful of features call outside services (image/video generation, TTS, transcription,
cross-model second opinions). Those are **optional**. Without a key they announce themselves
as unavailable in one line and offer a path without them. Nothing in this pack will ever ask
you to enable billing or buy an API plan.

> Keeping it that way is enforced, not remembered: `python guard_free_by_default.py --check`
> fails the build if the no-key policy erodes. See *Keeping the free-by-default promise* below.

## What you must fill in

| File | What |
|------|------|
| `~/.claude/.credentials.master.env` | Nothing by default. Optional paid features only — uncomment a key if you want that feature |
| `~/.claude/rules/user-profile.md` | Your name, email, hardware specs |
| `~/.claude/config/projects-registry.md` | Your project catalog |
| `~/.claude/config/server-primary.md` | Server IP / SSH config (optional) |
| `~/CLAUDE.md` | Domain, server IPs, quick links |

Everything else (rules, skills, plugins, agents, commands, hooks, MCP servers) works out of the
box with no keys at all — **provided the installer finished its last step**.

Copying files is not the whole install. Three things live in machine state, not in files, and
the installer sets them up by running `~/.claude/scripts/setup_runtime.py` at the end:

- the **Playwright browser binary** — `pip` installs the Python package, not the browser;
  42 skills depend on it (cards, PNG/PDF/PPTX export, decks, screenshot tests);
- **plugin marketplaces** — 33 plugins are declared, but a fresh machine does not know where
  to fetch them from (`claude plugin list` comes back empty);
- **`node_modules`** for the `dev-browser` skill.

If any of it did not land, nothing is broken — run it again at any time:

```bash
python ~/.claude/scripts/setup_runtime.py --check   # what is missing
python ~/.claude/scripts/setup_runtime.py           # fix it (idempotent)
```

## Inventory

- 270+ skills (`~/.claude/skills/`)
- 50+ agents (`~/.claude/agents/`)
- 110+ slash commands (`~/.claude/commands/`)
- 23 auto-loaded rules (`~/.claude/rules/`)
- 33 plugins (3 disabled by default — see `settings.json`)
- 21 MCP servers, **2 enabled by default**: `filesystem` and `playwright-live1`.
  The other 19 are `disabled: true` on purpose — some need your own keys and accounts, some
  point at infrastructure only the author has, and `playwright-live2..10` are parallel browser
  profiles that each add ~7 s to session startup.
  Enable one by editing `mcpServers` in `~/.claude/settings.json` (that is the file Claude Code
  actually reads). `~/.claude/mcp.json` is a **reference sheet of ready-made blocks**, not live
  config — copy a block from there into `settings.json`; the file explains this at its top.
- 5 GSD hooks (`~/.claude/hooks/`)
- 6 generic Python tools (`~/.claude/tools/`)

## Permission model — read this before installing

This config ships **`defaultMode: bypassPermissions`**. Claude runs commands without asking
you to confirm each one. That is deliberate: the config is built for uninterrupted autonomous
work, and confirming every step defeats it.

Protection does not disappear, it moves:

- **`hooks/bash-guard.js`** inspects every Bash and PowerShell call *before* it runs and exits
  with code 2 on 43 destructive patterns — `rm -rf` of roots, `DROP DATABASE/TABLE`, `mkfs`,
  `dd`, force-push to main, `docker rm -f`, `docker compose down -v`, `docker system prune`,
  `pm2 delete`, `systemctl stop`, `kubectl delete`. It also unwraps `ssh host "…"`,
  `bash -c "…"` and base64-encoded PowerShell, so hiding a command inside quotes does not help.
- **`hooks/security-guard.js`** does the same for Write/Edit.
- **`permissions.deny`** stays as the final backstop.

If you would rather be asked, set `permissions.defaultMode` to `"default"` in
`~/.claude/settings.json` and drop `skipDangerousModePermissionPrompt`. Nothing else depends
on the bypass mode.

## Other defaults

- `cleanupPeriodDays: 90` — sessions auto-archive
- All MCP servers tied to personal credentials are `disabled: true`
- All MCP servers with hardcoded local paths rewritten to portable `npx -y`
- Plugins that were declared but disabled are stripped, so nothing is resolved at startup for
  a marketplace you do not have

## Requirements

- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Claude Max subscription (recommended)
- Node.js 18+
- Python 3.10+ (optional, for tools)
- Git

## Security

- `.credentials.master.env` is gitignored — single source of truth
- No plaintext keys in `mcp.json` (env vars only)
- `leak_scan.py` script bundled if you want to verify before forking

## Keeping the free-by-default promise (maintainers)

`.claude/` in this repo is re-synced wholesale from a live personal config. A sync overwrites
whole files, so any policy sentence living *inside* a synced file dies with the next sync.
That is not hypothetical — the no-key policy was added on 2026-07-21 and was gone by 2026-07-31:

| Commit | Date | Files carrying the `NO-KEY GUARD` |
|--------|------|-----------------------------------|
| `46036a6` | 2026-07-21 | 16 (added) |
| `3ad0da6` | 2026-07-24 | 10 (first sync ate 6) |
| `3a337b6` | 2026-07-31 | 0 (second sync ate the rest) |
| `01dd6cb` | 2026-08-03 | 0 (shipped to `main`) |

So the policy text is **owned by `guard_free_by_default.py`**, not by the files it lives in.
The correct order after any re-sync is:

```bash
#  1. sync .claude/ from wherever you sync it
python guard_free_by_default.py --dry-run   # 2. see what the sync ate
python guard_free_by_default.py --apply     # 3. put it back (idempotent)
python _build_plugins.py                    # 4. propagate .claude/ -> plugins/
python guard_free_by_default.py --check     # 5. must exit 0
```

Three independent tripwires, so forgetting step 3 cannot ship:

1. **local, per commit** — `git config core.hooksPath .githooks` enables a `pre-commit` hook
   that refuses the commit while the guard is eroded;
2. **manual** — `_check.py` runs the guard first, before anything else it checks;
3. **remote** — `.github/workflows/free-by-default.yml` fails the push/PR on `main`.

What is checked:

- the `NO-KEY GUARD` block in 16 agent/skill files — 8 sources under `.claude/`
  plus their 8 `plugins/` mirrors;
- the policy paragraphs in `CLAUDE.md`, `.claude/config/models.md`,
  `.claude/rules/dont-do.md`, `.claude/config/rules-ref/onboarding.md`;
- the installers' closing lines (`install.sh`, `install.ps1`) — they are the first thing a
  new user reads, and "впиши свои ключи" there undoes every sentence above it;
- that no secret-ish variable ships uncommented in `.credentials.template.env`
  (auto-repaired; a pasted real value is dropped, not preserved as a comment).

Why the template must stay commented: `OPENAI_API_KEY=your_openai_api_key` is a *non-empty*
string, so every `if not os.getenv(...)` guard in the pack reads it as configured, sends the
placeholder upstream, and the user gets a bare `401` instead of "this feature needs a key".

> `guard_free_by_default.py` is deliberately **not** named `_guard.py` — `.gitignore` excludes
> `_*.py`, so an underscore name would never reach the repo and CI would fail on a missing file.

## License

MIT.
