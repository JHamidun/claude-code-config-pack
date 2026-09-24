# Authorized installation and updates

1. Confirm an existing user request covers this exact skill/action. Search-only
   stops at results. If choice or permission is unresolved, ask before mutation.
2. Stage inert source at a recorded immutable revision in the session scratchpad.
   Follow audit.md, inspect full execution closure, and reject malicious/deceptive
   behavior. An incomplete static line remains incomplete even when manual review
   explains its limitations. Disclose material CAUTION risks; do not silently accept
   unresolved risk.
3. Install reviewed bytes to `~/.claude/skills/<name>` (or `$CLAUDE_CONFIG_DIR/skills/<name>`)
   by copying the reviewed folder without executing its contents, then compare hashes.
   `npx skills add` only with an explicit destination directory and a pinned revision,
   never with installer defaults. Plugins go through `/plugin` (marketplace + install)
   and stay disabled in `enabledPlugins` until the user enables them. Do not write
   into other agents' configuration or skill directories.
4. Existing target: preserve it unless replacement is authorized. Before an approved
   replacement, retain a verified backup outside active skill roots (for example
   `~/claude-backups/<task>-<date>/`). Check resolved paths and links before moving
   anything. Never overwrite unrelated user edits.
5. Validate and report:
   - `python ~/.claude/skills/skill-creator/scripts/quick_validate.py <dir>`
     (frontmatter and structure)
   - `python ~/.claude/scripts/config_health.py --quick` (declared vs existing
     scripts, stale references)
   - `python ~/.claude/scripts/config_links.py` (broken skill/command/agent links,
     dead paths)
   - the description stays one line, carries its triggers and a `НЕ:` routing note
     like the other skills of this pack
   Compare reviewed/installed hashes and report exact name/location. A routing line
   goes into `config/routing-ext.md` (cold map); add one to `rules/routing.md` only
   when the description cannot cover it. The skill appears from the next session.

No bulk update-all, target lifecycle hooks, implicit runtime/account setup, or
hidden MCP connections. Running target code remains a separate authorization.
For updates, review the new revision/diff; previous approval is not transferable.
