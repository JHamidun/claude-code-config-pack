# Pi-LLM-Wiki 4-Layer Pattern (zosmaai/pi-llm-wiki, 202★)

> Distilled from github.com/zosmaai/pi-llm-wiki (2026-07-20). NOT installed — a
> **structural pattern** compared against our own bi-temporal memory system
> (`references/memory-v2.md`) to see what, if anything, is worth borrowing.

## The 4-layer model

pi-llm-wiki is a self-maintaining, Obsidian-compatible wiki extension for AI coding
tools. It separates knowledge into four strictly-typed layers instead of one flat pile
of markdown notes:

| Layer | Location | What lives there | Mutability |
|---|---|---|---|
| **1. Source packets** | `.llm-wiki/raw/sources/SRC-*/` | `manifest.json` (title/URL/format/timestamp) + `original/` (artifact as-is) + `extracted.md` (normalized text) + `attachments/` | **Immutable** — never edited after capture |
| **2. Knowledge pages** | `.llm-wiki/wiki/` | Concepts, entities, syntheses, analyses — collaboratively edited by model + human | Editable |
| **3. Auto-generated metadata** | `.llm-wiki/meta/` | `registry.json` (search index), `backlinks.json`, `index.md`/`log.md` (generated views), `events.jsonl` (append-only activity log) | Auto-rebuilt on every page edit, never hand-edited |
| **4. Config** | vault root | `config.json`, templates, schema docs | Rarely touched |

**Two-tier vault storage** — personal (`~/.llm-wiki/`, always active, zero setup,
knowledge follows the user across all projects) vs project (`.project/.llm-wiki/`,
explicit opt-in). `resolveVaultRoot()` walks: cwd → upward search for `.llm-wiki/` →
fallback to `~/.llm-wiki/`. Search tools query both and merge results with vault labels.

**Guardrails:** the extension blocks direct edits to `raw/` and `meta/` — only `wiki/`
pages are hand/model-editable. Editing a page triggers an automatic rebuild of
registry + backlinks, so the index can never silently drift from the content.
Citations use **stable source-page IDs** (`[[sources/SRC-YYYY-MM-DD-NNN]]`) rather than
titles, so provenance survives renames. `wiki_lint` is a deterministic health check —
orphans, broken links, duplicate aliases, coverage gaps.

## Mapping onto our own memory system

Our memory (`~/.claude/rules/auto-learning.md` + `~/.claude/skills/dream/`) already
implements a comparable separation, arrived at independently and via a different axis
(bi-temporal truth tracking, not source/synthesis separation):

| pi-llm-wiki concept | Our equivalent | Gap / difference |
|---|---|---|
| Layer 1 — immutable source packets | `chats.db` (FTS5 session archive) + `~/.claude/projects/*/archive/` raw transcripts | **We don't wrap raw captures in a manifest+extracted.md packet with a stable SRC-id.** Our raw layer is a searchable DB, not addressable per-artifact files a memory note can cite by ID. |
| Layer 2 — editable knowledge pages | Topic `.md` files in `memory/`, frontmatter v2 (`memory-v2.md` §1) | Ours carries MORE state per note (`confidence`, `evidence[]`, `valid_at`/`invalid_at`, `supersedes`) — richer than pi-llm-wiki's plain pages. Their citation-by-ID discipline (stable SRC-id survives retitling) is something our `evidence:` list does loosely (dated strings, not stable object IDs) — could tighten. |
| Layer 3 — auto metadata (registry/backlinks/events) | `memory_graph.py` (`~/.claude/memory-graph/graph.db`) — notes+[[links]]+supersedes graph, `dangling`/`orphans` health checks | Close parallel: `memory_graph.py dangling`/`orphans` ≈ `wiki_lint`. **We don't have an append-only `events.jsonl`** — dream's own actions (what got superseded/pruned/promoted, when) live only in git-less file diffs, not a durable event log a future dream pass could query ("show me every prune in the last month"). |
| Layer 4 — config | `rules/auto-learning.md` + `memory-v2.md` regulation itself | Direct match, no gap. |
| Two-tier vault (personal/project) | Global memory dir vs `~/.claude/projects/<project>/memory/` | Direct match already — same personal-follows-everywhere + project-opt-in split, just not named "vault". |

## What's worth taking, what isn't

**Worth considering (low-cost, additive):**
- **Append-only `events.jsonl` for dream itself.** Right now a dream pass's actions
  (supersede X→Y, prune Z, promote W) are only visible as file diffs/git history if
  tracked. A one-line-per-action JSONL log (`memory-graph/events.jsonl`:
  `{ts, action, note_id, detail}`) would let a future dream Phase 2 answer "what changed
  since last dream" without diffing the whole directory — cheap to add, doesn't touch
  the note format, doesn't violate anti-churn (it's an append, not an edit).
- **Stable citation IDs for raw sources**, if/when we start letting memory notes cite
  specific chat sessions by ID rather than paraphrasing — `chats.db` already has session
  ids, so the "SRC-id survives retitling" discipline is nearly free (cite `session_id`,
  not the chat title).

**Not worth taking (already superseded by our own design):**
- Their Layer 2 page model is *simpler* than our frontmatter v2 — we already have
  confidence/decay/bi-temporal supersede, which is strictly more expressive than
  "editable page." Adopting their page format would be a downgrade.
- A literal `.llm-wiki/` directory structure / Obsidian plugin install is not warranted
  — our memory already has an Obsidian vault (`~/Obsidian/Knowledge-Base/`, separate
  concern from `~/.claude/projects/*/memory/`) and adding a second wiki mechanism would
  fragment lookup instead of consolidating it.

## Verdict — pattern noted, not installed

No new tool, no new directory convention adopted wholesale. The one idea flagged for a
future low-effort addition is the **append-only events log** for dream's own audit
trail — everything else in the 4-layer model is already covered, and in most axes
(confidence/decay/supersede) our system is more capable than pi-llm-wiki's.
