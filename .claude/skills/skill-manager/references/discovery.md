# Discovery across the common base

Start with task/domain/platform and any explicit author constraint. Inspect local
capability inventory and focused router/catalog first; do not preload every skill.
Search public catalogs only with public task keywords, never private source/secrets.

## Local inventory first (Claude Code)

A skill missing from one source is not missing: check all of them before saying
"there is no such skill".

1. The skill listing already in the prompt (descriptions carry the triggers).
2. `~/.claude/rules/routing.md`: hot routing table, loaded every session.
3. `~/.claude/config/routing-ext.md`: cold full trigger map; Read on demand.
4. A Python walk of `~/.claude/skills/*/SKILL.md` (and `~/.claude/agents/**`,
   `~/.claude/commands/`). Prefer the walk to Grep/ripgrep here: if `~/.claude` is a
   git repository with a restrictive `.gitignore`, ripgrep silently skips the ignored
   files and returns a fraction of the matches without any warning.
5. Plugins: `~/.claude/plugins/installed_plugins.json` (installed),
   `enabledPlugins` in `~/.claude/settings.json` (enabled; installed is not enabled),
   and `~/.claude/plugins/marketplaces/*/.claude-plugin/marketplace.json` (available
   from added marketplaces, e.g. `claude-plugins-official`, which also lists
   `mattpocock-skills`).

With `CLAUDE_CONFIG_DIR` set, read the same paths under that directory.

## Public catalogs

- skills.sh: browse https://skills.sh or use domain-restricted web search, then open
  the original repository's SKILL.md. An already approved Skills CLI can use
  `npx skills find <query>`; prefer native web/MCP rather than bootstrapping an
  unreviewed CLI merely to search. `skills add` is not a search operation.
- SkillsMP (optional MCP server, not configured by this pack): if the user wants it,
  it is added once with
  `claude mcp add --transport http --scope user skillsmp https://skillsmp.com/mcp`
  and appears from the next session. Adding it is the user's decision, not a side
  effect of a search. When present, load its tools with ToolSearch
  (`mcp__skillsmp__*`, e.g. search_skills/get_skill/list_categories) and use their
  actual schemas. If the tools are not loaded in this session, say so and use
  https://skillsmp.com plus the original source as fallback. Do not silently
  reconfigure MCP or claim an unperformed search succeeded.
- Original repositories: verify revision, SKILL.md, license, scripts, permissions
  and dependencies. Deduplicate marketplace hits by owner/repository/skill path.
- Matt Pocock: https://github.com/mattpocock/skills. His upstream ask-matt routes
  only that collection; our routing.md explicitly generalizes it. Verify actual
  source rather than trusting the upstream router's summaries or install status.

Use specific terms and synonyms. Reputation, stars and installs are discovery
signals, not safety proof; cite counts/freshness only when checked now. Do not impose
an arbitrary popularity cutoff or silently replace an author's requested skill.

Return exact name/author/source, purpose and fit, permissions/dependencies, installed
status (installed / installed but disabled plugin / available in a marketplace /
external only) and audit status. Unreviewed candidates are not safe by default.
State which catalogs were searched. If no match is found, limit that statement to
searched sources; offer native capabilities or skill creation (`skill-creator`)
without starting an install.
