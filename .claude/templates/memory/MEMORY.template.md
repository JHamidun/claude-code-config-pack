# Memory — Index

> This is the **master index** of long-term memory. Keep it under ~200 lines / ~25 KB.
> One line per fact or topic. Details live in **topic-files** in this same folder; link to them, don't inline them.
> Location: `~/.claude/projects/<project>/memory/MEMORY.md` (index) + `*.md` topic-files beside it.
> 🗂️ Notes marked `_` (e.g. `_ORPHANS_INDEX.md`, `_archive-*.md`) are service files — the graph ignores them as nodes.

## RULES — ALWAYS APPLY

> Durable behavioral rules and hard-won conventions. Load these first every session.
> Format: one-line takeaway + `[link](topic-file.md)`. Prefix ⭐ for the most load-bearing.

- [Prefer the project's existing helper over a new dependency for one-off needs](patterns.md) ⭐
- [Run `type-check` + production `build` after any non-trivial edit — build is stricter than tsc](quality-gates.md) ⭐
- [After a bug fix, record the root cause immediately, not at session end](debugging.md)

## ACTIVE OPS — LATEST

> Rolling log of current work: status, blockers, next step. Newest on top.
> When an entry goes stale, move it to an `_archive-*.md` topic-file and drop the line here.

- YYYY-MM-DD: [Short headline of what changed / what's blocked / what's next](active-ops.md) ⭐
- YYYY-MM-DD: [Second most recent operational note — one line, link for detail](active-ops.md)

## TOOLS & SKILLS

> Non-obvious behavior of tools, libraries, CLIs, and internal scripts. Save from success too.

- [Tool X flag `--foo` silently does Y — pass `--bar` instead](tools.md)
- [Library Z needs config `{...}` before it works in this stack](tools.md)

## REFERENCE PLAYBOOKS / GOTCHAS

> Reusable step-by-step recipes and traps discovered the hard way.

- [Deploy playbook for service A — exact command order + the one gotcha](deploy-config.md) ⭐
- [Data-migration recipe: dump → transform → verify → cut over](playbooks.md)

## PROJECTS

> One line per project pointing at its own topic-file (architecture, decisions, status).

- Project Alpha: [stack, key decisions, current status](project-alpha.md)
- Project Beta: [what it is, where it lives, open questions](project-beta.md)

---

### How to read this index

- Every line is a **pointer**, not the content. If a line needs more than a sentence, it belongs in a topic-file.
- `[[wikilinks]]` inside topic-files are what the memory graph traverses (`memory_graph.py`). Link related notes to each other so nothing becomes an orphan.
- Keep dates **absolute** (`YYYY-MM-DD`), never "yesterday" / "last week" — relative dates rot.
- Don't duplicate: before adding a topic-file, check whether an existing one already covers it.