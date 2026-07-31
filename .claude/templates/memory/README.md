# Memory System — README

A lightweight, file-based long-term memory for the assistant. It survives across
sessions, is fully offline, is version-controllable (plain Markdown + SQLite),
and is queryable as a graph. This README explains how the pieces fit together.
The public pack ships **only the skeleton** — the owner's private notes are not
included. Populate it as you work.

---

## 1. Layout

```
~/.claude/projects/<project>/memory/
├── MEMORY.md            # the index — one line per fact, links to topic-files
├── <topic>.md           # topic-files: detailed notes (debugging.md, patterns.md, …)
├── _archive-*.md        # service files (ignored as graph nodes; prefix "_")
└── _ORPHANS_INDEX.md    # optional list of notes not yet linked into the graph
```

- **`MEMORY.md`** — the master index. Keep it under **~200 lines / ~25 KB**.
  It contains only *pointers*: a one-line takeaway plus a link to the topic-file
  that holds the detail. Start from the template `MEMORY.md` in this pack.
- **Topic-files** — the actual knowledge, grouped by theme (e.g. `debugging.md`,
  `patterns.md`, `deploy-config.md`, `project-alpha.md`). Structured notes with
  code examples. One theme per file; don't inline detail into the index.

**Golden rule:** the index links *down* to topic-files; topic-files link *sideways*
to each other with `[[wikilinks]]`. That sideways linking is what makes the graph
useful (below).

---

## 2. Topic-file frontmatter

Every topic-file may start with a YAML frontmatter block. The graph reader
(`memory_graph.py`) parses these fields:

```markdown
---
name: deploy-config-service-a          # canonical node id (defaults to filename if omitted)
description: One-sentence summary shown as the node title in the graph
type: reference                         # user | feedback | project | reference | memory
status: active                          # active | superseded
---

# Deploy config for Service A

Body of the note. Cross-link related notes so nothing is orphaned:
see [[quality-gates]] and [[project-alpha]].
```

Field meanings:

| Field | Purpose |
|-------|---------|
| `name` | Canonical node id. If absent, the filename (without `.md`) is used. `[[links]]` resolve by **either** filename-slug **or** `name`. |
| `description` | Human-readable title for the node in graph output. Falls back to the first `# H1` if omitted. |
| `type` | Classifies the node. Convention: `user` (identity/prefs), `feedback` (corrections to obey), `project` (project state), `reference` (playbooks/facts), `memory` (default catch-all). |
| `status` | `active` by default. Set to `superseded` when a newer note replaces this one (see immutability below). |

---

## 3. What to save — and when

Save immediately (don't wait for session end) whenever a **signal** appears:

- A bug's **root cause** and its fix.
- A new **pattern / convention / architectural decision**.
- A working **command or config** (docker, deploy, CI/CD) — including ones that *succeeded* and were non-obvious. Recording only failures makes you over-cautious.
- A **user decision** ("chose X because Y").
- **Non-obvious behavior** of a tool or library.

Capture the signal **plus 2–3 turns of surrounding context** — don't try to
"remember everything" retroactively at the end.

This mirrors `rules/auto-learning.md`, which is the always-loaded rule that tells
the assistant to maintain this folder every session. This README is the mechanics;
`auto-learning.md` is the standing instruction.

---

## 4. Applying memory (discipline)

- Apply what you know **invisibly**, as your own experience — not as a quoted
  fact. Don't say "according to memory" / "as I recall" / "MEMORY.md says".
  Only cite the source if explicitly asked where something came from.
- Sensitive topics (family, finances, health, conflicts) are **not** raised first
  from memory — wait until the user brings them up.
- Memory must not turn the assistant into a yes-man: prior feedback notes do not
  override giving honest, direct feedback now.

---

## 5. Immutability (bi-temporal) — close facts, don't delete them

When a new note contradicts an old one, **do not rewrite or delete the old note.**

1. Create the **new** note with `supersedes: [[old-note-id]]` in its frontmatter.
2. Mark the **old** note `status: superseded` (optionally add `superseded_by:` / `invalid_at:`).

The history of "what we believed was true, and when" is itself data. The graph's
`timeline` command walks these `supersedes` chains.

**Anti-churn:** if a consolidation pass finds nothing to change, **don't touch the
file** — a no-op diff only breaks prompt caching.

---

## 6. Dream consolidation (periodic)

Every few sessions, run a reflective pass ("dream") over the whole memory folder:

1. **Orient** — list the memory dir, read `MEMORY.md`, skim the topic-files.
2. **Gather** — find new info: drifted memories, notes that now contradict the code.
3. **Consolidate** — update/create files, convert relative dates to absolute,
   resolve contradictions via the immutability rule (don't delete — supersede).
4. **Prune** — keep `MEMORY.md` under ~200 lines / ~25 KB; drop stale index lines
   (move their detail into an `_archive-*.md` topic-file first).

---

## 7. Querying the graph — `scripts/memory_graph.py`

`memory_graph.py` turns the Markdown notes into a queryable knowledge graph and
stores it in a local SQLite DB at `~/.claude/memory-graph/graph.db` (offline,
durable, part of memory). It builds nodes from notes and edges from
`[[wikilinks]]` (`rel=link`) and `supersedes` frontmatter (`rel=supersedes`).

**Build / rebuild the graph** (run after adding or heavily editing notes, and as
part of a dream pass):

```bash
python ~/.claude/scripts/memory_graph.py build
```

**Everyday queries:**

```bash
# Overview: node/edge counts, types, orphans, dangling links
python ~/.claude/scripts/memory_graph.py stats

# Notes matching a substring (name or title)
python ~/.claude/scripts/memory_graph.py search deploy

# Direct neighbors of a node (optional depth, default 1)
python ~/.claude/scripts/memory_graph.py neighbors deploy-config-service-a 2

# Shortest path between two nodes (BFS)
python ~/.claude/scripts/memory_graph.py path project-alpha quality-gates

# supersedes chain: what a note replaced and what replaced it
python ~/.claude/scripts/memory_graph.py timeline old-decision-note

# Most-connected nodes (hubs), optional N
python ~/.claude/scripts/memory_graph.py hubs 15
```

**Maintenance / gap-finding** (useful during a dream pass):

```bash
# Notes with no edges — candidates to cross-link
python ~/.claude/scripts/memory_graph.py orphans

# [[links]] pointing at notes that don't exist yet — candidates to create
python ~/.claude/scripts/memory_graph.py dangling

# Combined gap analysis: orphans + dangling + stale hubs + unmarked-superseded
python ~/.claude/scripts/memory_graph.py gaps        # optional [stale_days], default 45
```

Notes on behavior:
- Nodes are indexed by `name` (frontmatter) but `[[links]]` may reference the
  filename slug — the builder resolves both.
- `MEMORY.md` and any `_`-prefixed files are **not** turned into nodes.
- The DB is rebuilt from scratch on every `build`; it is a derived artifact, so
  the Markdown notes remain the single source of truth.

---

## 8. Relationship to `rules/auto-learning.md`

| Concern | Where |
|---------|-------|
| *When* to save, *what* to save, apply-invisibly discipline | `rules/auto-learning.md` (auto-loaded every session) |
| *How* the files, frontmatter, and graph work | this README |
| The queryable index of everything saved | `MEMORY.md` + topic-files |
| Graph queries over the notes | `scripts/memory_graph.py` |

`auto-learning.md` is the standing policy; this folder is where that policy writes
its output. Keep the two in sync: if you change the folder conventions here, reflect
them in the rule, and vice-versa.