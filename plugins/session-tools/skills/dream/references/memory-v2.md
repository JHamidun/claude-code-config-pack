# Memory v2 Regulation — Frontmatter Schema + Dream v2 Process

> Canonical reference for the v2 memory regulation referenced from `~/.claude/rules/auto-learning.md`
> («Полный регламент frontmatter v2 + dream v2 — в skill `dream`»).
> Loaded on demand — it does not sit in the system prompt, so it can afford to be detailed.

Memory directory (global): `~/.claude/projects/C--Users-youruser/memory/`
Project memories: `~/.claude/projects/<project>/memory/`
Archive for pruned notes: `<memory dir>/_archive/`

---

## 1. Frontmatter v2 — schema for memory notes

Every memory note is a Markdown file with YAML frontmatter. v2 fields:

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `id` | slug | yes | Stable identifier = filename without `.md`. Never changes, never reused. |
| `type` | enum | yes | `user` (facts about YourFirstName), `feedback` (behavioral rule / instinct), `project` (project-scoped knowledge), `reference` (lookup data: contacts, configs, playbooks). |
| `status` | enum | yes | `active` \| `pending` (unconfirmed, single observation) \| `superseded` \| `archived` \| `promoted` (moved to global). |
| `trigger` | string | yes | WHEN the note is relevant — the recall cue. Written as a situation, not a keyword ("user asks for a КП for Company", "deploying to your-server"). |
| `action` | string | feedback only | WHAT to do when the trigger fires. Imperative, concrete. This is what makes a note an *instinct*. |
| `confidence` | 0..1 | yes | Belief that the note is still true/useful. New signal-based notes start at 0.7–0.8; explicit user decisions at 0.9–0.95. |
| `evidence` | list | yes | Dated confirmations: sessions, commits, quotes, file paths. Each new confirmation appends here (this is what "confirmed" means). |
| `valid_at` | date | yes | When the fact BECAME true (bi-temporal start). Absolute date, never "last week". |
| `invalid_at` | date/null | yes | When the fact STOPPED being true. `null` while current. Set on supersede — never delete the note. |
| `last_confirmed` | date | no | Last time evidence was added / the rule demonstrably worked. Decay counts from here (fallback: `valid_at`). |
| `supersedes` | list of ids | no | Older notes this one replaces. |
| `superseded_by` | id/null | no | Newer note that replaced this one. Set together with `invalid_at` + `status: superseded`. |
| `discovery_tokens` | list | yes | Search aliases: RU/EN synonyms, tool names, slang — everything a future search might use. |

### Filled example

```yaml
---
id: feedback-kp-use-deck-factory
type: feedback
status: active
trigger: "user asks for a КП / commercial proposal for a client"
action: "Собирать из шаблона и донор-дека, а не вёрсткой с нуля. Правка жаргона: топы→руководители."
confidence: 0.95
evidence:
  - "2026-07-16: ad-hoc HTML КП rejected by YourFirstName, redone via deck-factory"
  - "2026-07-17: deck-factory КП accepted without edits"
valid_at: 2026-07-16
last_confirmed: 2026-07-17
invalid_at: null
supersedes: []
superseded_by: null
discovery_tokens: [кп, коммерческое предложение, deck-factory, company, презентация клиенту, commercial proposal]
---
```

Body below the frontmatter = free-form details, code samples, gotchas.

### Migration rule (anti-churn compatible)

Do NOT sweep the memory dir converting old notes to v2 in bulk — that is pure churn.
Upgrade a note's frontmatter to v2 **only when dream touches it anyway** (rethink, supersede, evidence append). Untouched legacy notes stay as they are.

---

## 2. Bi-temporal immutability — the supersede protocol

Facts are never deleted or rewritten into their opposite. "What we believed and when" is data.

When a note contradicts current reality:

1. Create a NEW note with a new `id`, the corrected content, `valid_at: <today or when it actually changed>`, and `supersedes: [<old-id>]`.
2. In the OLD note change ONLY: `status: superseded`, `superseded_by: <new-id>`, `invalid_at: <date>`. Body stays intact.
3. In `MEMORY.md` the index line points to the NEW note (the index is navigation, not history — replacing pointers there is fine).
4. Superseded notes are never pruned to archive — they ARE the history and remain reachable via `supersedes` links.

Exception — trivial corrections (typo, broken path, formatting): fix in place, no supersede ceremony. Supersede is for *meaning* changes.

---

## 3. Decay — confidence erosion

Unconfirmed knowledge softly loses confidence:

```
effective_confidence = stored_confidence − 0.02 × full_weeks_since(last_confirmed or valid_at)
floor: 0.05
```

- **Effective** confidence is what dream uses for ranking (TOP-INSTINCTS) and prune decisions. Compute it in-flight.
- **Persist** the decayed value into the file only when the note is being written anyway, or when decay crosses an action threshold (falls out of TOP-K, becomes prunable). Never rewrite files solely to bump a number — that violates anti-churn.
- Adding evidence resets the clock: append to `evidence`, set `last_confirmed`, optionally raise `confidence` (max +0.05 per confirmation, cap 0.98).

---

## 4. Prune — archive, don't destroy

A note is prunable when ALL hold:

- `status: pending` (never confirmed beyond the original observation), AND
- older than **30 days** (by `valid_at`), AND
- `effective_confidence < 0.3`.

Action: move the file to `<memory dir>/_archive/`, remove its line from `MEMORY.md`. Archived ≠ deleted — it can be resurrected with fresh evidence.

Never prune: `superseded` notes (history), `reference` notes still pointing at live systems, anything listed under RULES / TOP-INSTINCTS.

---

## 5. Promote — project → global

A `project`-scoped note earns global status when:

- confirmed in **≥3 distinct sessions/contexts** (count dated `evidence` entries), AND
- the rule is genuinely cross-project (would apply in a different repo).

Action: copy the note into the global memory dir (`~/.claude/projects/C--Users-youruser/memory/`), retype as `user`/`feedback`, add an index line in global `MEMORY.md`. In the project copy set `status: promoted` + a `promoted_to:` pointer (or leave it if the project index still needs it locally).

---

## 6. TOP-INSTINCTS — the auto-rebuilt block in MEMORY.md

Dream rebuilds this block on every pass. No hook, no cron — dream itself does it.

**Eligibility:** `type: feedback` (behavioral rules with an `action`), `status: active`.
**Ranking:** effective (decayed) confidence, descending; tie-break by newer `last_confirmed`. Decay already encodes recency, so this = confidence × recency.
**K:** 7 by default (5–10 acceptable if quality warrants).

**Format** — the block lives between HTML-comment markers so a rebuild never touches the rest of MEMORY.md:

```markdown
<!-- TOP-INSTINCTS:BEGIN — auto-rebuilt by dream, do not hand-edit -->
## TOP-INSTINCTS (K=7 · rebuilt 2026-07-18)
1. `0.95` КП клиенту → только шаблон плюс донор-дек, не вёрстка с нуля — пример записи о предпочтении
2. `0.93` Всё публичное/внешнее → leak-scan ДО заливки — [feedback_depersonalize_before_upload](feedback_depersonalize_before_upload.md)
3. `0.91` UI-мокапы → HTML-мок + chrome-devtools скрин, не image-генерация — [ui-mockups-via-devtools](ui-mockups-via-devtools.md)
...
<!-- TOP-INSTINCTS:END -->
```

Line format: `N. \`conf\` trigger → action (compressed to one line) — [id](file.md)`.

**Rebuild algorithm (idempotent):**

1. Collect eligible notes, compute effective confidence, sort, take top K.
2. Render the block.
3. If markers exist in `MEMORY.md` — replace everything between `BEGIN` and `END` (inclusive of the heading, exclusive of the markers). If absent — insert the whole marked block right after the top intro of `MEMORY.md`, before the first content section.
4. **Anti-churn check:** if the freshly rendered list is identical to the current one except the `rebuilt <date>` stamp — do not write at all. The date stamp alone is not a reason to dirty the file.

Relation to the hand-curated `RULES — ALWAYS APPLY` section: that section stays human/context-curated; TOP-INSTINCTS is the machine-ranked complement. If an instinct already sits in RULES, it may still appear in TOP-INSTINCTS — ranking is the point — but don't duplicate its long description, just the one-liner + link.

---

## 7. Anti-churn — the meta-rule

If a dream pass finds nothing to change in a file — **do not touch the file**. No cosmetic reformatting, no frontmatter beautification, no re-sorting, no timestamp refresh. Every needless diff invalidates prompt-cache and pollutes history. "Already tight" is a valid and reportable dream outcome.

---

## 8. Budgets

- `MEMORY.md`: **≤200 lines AND ≤~25KB**. On overflow: compress index lines (one line + link), push detail into topic files, archive stale pointers.
- Index line: ≤~200 chars. Longer → shorten, move substance to the topic file.
- Topic files: no hard limit, but one topic = one file; near-duplicates get merged (via supersede if meanings conflict, plain merge if they don't).

---

## 9. Invocation

Dream runs **on demand** — user says "dream" / "консолидируй память" / "почисти память" — or voluntarily once every few sessions when memory feels cluttered. It is not a cron job, not a hook, not a background process. One full pass follows the phases in `SKILL.md`; every step is idempotent, so an interrupted dream can simply be re-run.
