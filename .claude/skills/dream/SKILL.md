---
name: dream
description: Memory consolidation — reflective pass over memory files. Use when memory is cluttered, stale, or after many sessions without cleanup.
triggers:
  - "dream"
  - "консолидируй память"
  - "почисти память"
  - "memory consolidation"
---

# Dream: Memory Consolidation

You are performing a dream — a reflective pass over your memory files. Synthesize what you've learned recently into durable, well-organized memories so that future sessions can orient quickly.

Memory directory: `~/.claude/projects/C--Users-youruser/memory/`

## Phase 1 — Orient

- `ls` the memory directory to see what already exists
- Read `MEMORY.md` to understand the current index
- Skim existing topic files so you improve them rather than creating duplicates

## Phase 2 — Gather Recent Signal

Look for new information worth persisting. Sources in priority order:

1. **Existing memories that drifted** — facts that contradict something you see in the codebase now
2. **Stale entries** — memories about projects/tools that no longer exist or changed
3. **Oversized entries** — MEMORY.md lines over ~150 chars that carry content belonging in topic files

Don't exhaustively read everything. Look only for things you already suspect matter.

## Phase 3 — Consolidate

For each thing worth updating:
- Merge new signal into existing topic files rather than creating near-duplicates
- Convert relative dates ("yesterday", "last week") to absolute dates
- Delete contradicted facts — if current state disproves an old memory, fix it at the source
- Update frontmatter (name, description, type) to match current content

## Phase 4 — Prune and Index

Update `MEMORY.md` so it stays under 200 lines AND under ~25KB:
- Remove pointers to stale, wrong, or superseded memories
- Demote verbose entries: if an index line is over ~200 chars, shorten it, move detail to topic file
- Add pointers to newly important memories
- Resolve contradictions — if two files disagree, fix the wrong one
- Group related entries together (by topic, not chronologically)

## Output

Return a brief summary of what you consolidated, updated, or pruned.
If nothing changed (memories are already tight), say so.
