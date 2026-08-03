---
name: dream
description: "Memory consolidation — рефлексивный проход по памяти + Second Brain sleeptime. Несёт полный регламент v2 из rules/auto-learning.md: frontmatter v2, rethink/supersede (bi-temporal), decay −0.02/нед, prune pending>30д, promote project→global, TOP-INSTINCTS."
triggers:
  - "dream"
  - "консолидируй память"
  - "почисти память"
  - "memory consolidation"
  - "brain dream"
  - "sleeptime"
  - "frontmatter v2"
  - "top-instincts"
---

# Dream: Memory Consolidation + Second Brain Sleeptime

You are performing a dream — a reflective pass over your memory files AND the Second Brain database. Synthesize what you've learned recently into durable, well-organized memories so that future sessions can orient quickly.

Memory directory: `~/.claude/projects/C--Users-youruser/memory/`
Second Brain DB: `ваше локальное хранилище памяти`

**Full v2 regulation** (frontmatter schema, supersede protocol, decay/prune/promote formulas, TOP-INSTINCTS block format): `references/memory-v2.md`. Read it before Phases 2–5.

**Related pattern (reference only, not installed):** `references/pi-llm-wiki-layered-pattern.md` — 4-layer wiki architecture (immutable source packets / editable pages / auto metadata / config) mapped against our own bi-temporal system; flags one low-cost addition worth considering (append-only `events.jsonl` audit log for dream's own actions).

## Ground Rules (apply to every phase)

- **Anti-churn:** if a file needs no change — do NOT touch it. No cosmetic edits, no timestamp refresh, no bulk frontmatter migration. Needless diffs break prompt-cache. "Memory already tight" is a valid outcome.
- **Bi-temporal immutability:** contradicted facts are never deleted or rewritten. New note with `supersedes:`, old note gets `status: superseded` / `superseded_by:` / `invalid_at:`. Only the index (`MEMORY.md`) swaps pointers freely.
- **Budgets:** `MEMORY.md` ≤200 lines and ≤~25KB; index lines ≤~200 chars.
- **Authority criterion (consolidation):** знание = «проверенное» только если (1) проверено реальным прогоном, (2) названа неработающая альтернатива, (3) описана конкретная решаемая проблема; иначе — `status: pending`, не канон.
- **On demand only:** dream runs when asked ("dream", "консолидируй память") or voluntarily once every few sessions. Not a cron, not a hook. Every phase is idempotent — a re-run is always safe.

---

## Phase 0 — Brain Stats (Before)

Capture brain state BEFORE consolidation so we can report the delta.

1. Call `brain_stats` MCP tool (server: `second-brain`)
2. Note: total memories, contacts, chunks pending embed, active commitments, awaiting items
3. Save these numbers for the "before/after" report in Phase 7

---

## Phase 1 — Orient

- `ls` the memory directory to see what already exists
- Read `MEMORY.md` to understand the current index
- Skim existing topic files so you improve them rather than creating duplicates

## Phase 2 — Rethink (Gather Signal + Detect Drift)

Look for new information worth persisting and old information that drifted. Sources in priority order:

1. **Drifted memories** — notes that contradict what the codebase / configs / reality show now
2. **Contradictions between notes** — two files that disagree with each other
3. **Stale entries** — memories about projects/tools that no longer exist or changed
4. **Oversized entries** — MEMORY.md lines over ~150 chars that carry content belonging in topic files

Don't exhaustively read everything. Look only for things you already suspect matter.

For every conflict found — mark it for the supersede protocol in Phase 3. Do NOT resolve conflicts by deleting or rewriting the older note.

## Phase 2b — Transcript pass (по запросу / когда заметки отстали)

Фазы 1-2 смотрят только на то, что УЖЕ записано. Отдельный слой сырья — транскрипты прошлых сессий: там лежат уроки, которые в заметки не попали вовсе. Запускай этот проход, когда dream вызван с фокусом («dream по проекту X», «что я вынес за неделю») или когда сессий прошло много, а новых заметок почти нет.

- **Фокус — параметр прохода.** Тот же корпус под разным фокусом раскладывается по-разному; это ожидаемо. Фиксируй формулировку фокуса в отчёте, иначе потом не понять, почему память организована именно так. Без фокуса — обычный полный проход по Фазам 1-2.
- **Не грузить транскрипты целиком.** Работай точечно: `search_chats.py search "<тема>" --days N` → `timeline <id>` → `get <id,id>` только по отобранным якорям. Тот же принцип, что и с любыми большими данными: сузить, потом читать.
- **Извлекать только durable:** root cause + фикс, решения владельца («выбрал X потому что Y»), неочевидное поведение инструментов/библиотек, рабочие конфиги, сработавшие неочевидные подходы. Ход задачи, промежуточные попытки и одноразовые детали — не память.
- **Извлечённое из транскрипта не канон по умолчанию:** пока не выполнен authority criterion (см. Ground Rules) — `status: pending`. Ссылку на сессию-источник клади в `evidence`.
- Дальше извлечённое идёт обычным путём: Фаза 3 (merge/supersede), Фаза 4 (decay/prune/promote).

**Кандидатный слой для крупной реорганизации.** Если проход переписывает не пару файлов, а перекладывает структуру памяти — пиши сначала в `_candidate/`, сравни с живыми файлами, и только после просмотра принимай (принятое переносится, отклонённый кандидат удаляется целиком). Для точечных правок это лишняя церемония — там действует anti-churn.

## Phase 3 — Consolidate (with supersede protocol)

For each thing worth updating:

- Merge new signal into existing topic files rather than creating near-duplicates
- Convert relative dates ("yesterday", "last week") to absolute dates
- **Contradicted facts → supersede, don't delete:** create a new note (`id`, `valid_at`, `supersedes: [old-id]`); in the old note set only `status: superseded`, `superseded_by:`, `invalid_at:` — body stays intact. Trivial typos/paths may be fixed in place without ceremony.
- **Frontmatter v2 upgrade on touch:** any note you are editing anyway gets upgraded to the v2 schema (`id`, `type`, `status`, `trigger`, `action`, `confidence`, `evidence`, `valid_at`/`invalid_at`, `last_confirmed`, `discovery_tokens` — see `references/memory-v2.md` §1). Never migrate untouched notes in bulk.
- **Confirmations:** when a session proved a note right — append a dated line to `evidence`, set `last_confirmed`, optionally +0.05 confidence (cap 0.98)

## Phase 4 — Decay, Prune, Promote

Apply the lifecycle math from `references/memory-v2.md` §3–5:

- **Decay:** `effective_confidence = confidence − 0.02 × weeks_since(last_confirmed || valid_at)`, floor 0.05. Compute in-flight; persist into a file only if you're writing it anyway or the value crosses an action threshold (anti-churn).
- **Prune:** `status: pending` + older than 30 days + effective confidence < 0.3 → move file to `_archive/`, drop its index line. Never prune superseded notes (they are history) or live references.
- **Promote:** a `project` note confirmed in ≥3 distinct sessions AND genuinely cross-project → copy to global memory dir as `user`/`feedback`, index it globally, mark the project copy `status: promoted`.

## Phase 5 — TOP-INSTINCTS + Index

**Rebuild TOP-INSTINCTS** (no hook — dream itself does this every pass):

1. Collect `type: feedback`, `status: active` notes; rank by effective (decayed) confidence, tie-break by newer `last_confirmed`; take top K=7 (5–10 ok)
2. Rewrite ONLY the block between `<!-- TOP-INSTINCTS:BEGIN -->` and `<!-- TOP-INSTINCTS:END -->` markers in `MEMORY.md` (insert the marked block after the intro if missing). Line format: `` N. `conf` trigger → action — [id](file.md) ``. Exact format and idempotency rules: `references/memory-v2.md` §6
3. Anti-churn: if the rendered list is unchanged except the date stamp — don't write

**Then update the rest of `MEMORY.md`** so it stays under 200 lines AND ~25KB:

- Swap index pointers from superseded notes to their successors; remove pointers to archived notes
- Demote verbose entries: if an index line is over ~200 chars, shorten it, move detail to topic file
- Add pointers to newly important memories
- Group related entries together (by topic, not chronologically)
- The hand-curated `RULES — ALWAYS APPLY` section stays hand-curated — TOP-INSTINCTS complements it, doesn't replace it

**Rebuild memory graph** (Layer 1 — after note/link/supersede changes settle): `python ~/.claude/scripts/memory_graph.py build`, then `dangling` + `orphans` — dangling `[[links]]` (target has no note) and high-degree orphans are hygiene signals: create the missing note, fix a name mismatch, or link the orphan. The graph (`~/.claude/memory-graph/graph.db`) powers recall routing «что связано с / хронология / что заместило».

---

## Phase 6 — Second Brain Sleeptime

After file-based consolidation, run the Second Brain sleeptime pipeline.

### Run sleeptime via CLI:

```bash
python ${HOME}/.brain/brain_sleeptime.py run
```

This executes the full consolidation pipeline:
1. **SHMR pass** — Self-Harmonizing Memory Review: clusters similar memories by cosine similarity, keeps best version, dampens duplicates
2. **Forgetting pass** — Weibull decay on low-importance, unused memories
3. **Contradiction scan** — checks recent 7-day memories for contradictions
4. **Pheromone decay** — decays entity importance scores in the knowledge graph
5. **Contact decay** — recalculates relationship_strength for all contacts
6. **Stats snapshot** — logs final state to action_log

### Then generate insights:

```bash
python ${HOME}/.brain/brain_sleeptime.py insights
```

This produces data-driven insights: hot entities, frequent memories, contact patterns,
memory growth. (No vector database here on purpose: local embeddings need a decent GPU,
and this pack must work on any laptop. The graph gives you связи without one.)

### If CLI fails (e.g. missing deps), explain:

> Second Brain sleeptime can be run manually:
> ```
> cd ${HOME}/.brain
> python brain_sleeptime.py run
> python brain_sleeptime.py insights
> ```

---

## Phase 7 — Brain Stats (After) + Report

1. Call `brain_stats` MCP tool again to capture post-consolidation state
2. Compare before/after numbers
3. Report the combined results in this format:

### Dream Report

**File Memory (Phases 1-5):**
- Фокус прохода (если задавался) + сколько сессий-транскриптов просмотрено в Фазе 2b и сколько уроков из них извлечено (или «transcript pass не запускался»)
- Files updated / created / superseded / archived / promoted
- TOP-INSTINCTS: rebuilt or unchanged (list the K entries if rebuilt)
- MEMORY.md line count and size

**Second Brain Sleeptime (Phase 6):**
- SHMR: N clusters found, N memories harmonized/dampened
- Forgetting: N memories archived/dampened by Weibull decay
- Contradictions: N found among recent memories (list top 3 if any)
- Pheromone decay: N entities decayed
- Contact decay: N contacts recalculated
- Insights generated: (list each insight)

**Brain Stats Delta:**
| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Memories | X | Y | +/-Z |
| Contacts | X | Y | +/-Z |
| Chunks pending | X | Y | +/-Z |
| Commitments | X | Y | +/-Z |
| Awaiting | X | Y | +/-Z |

---

## Output

Return the full Dream Report above.
If file memories were already tight, say so — that is a valid outcome (anti-churn).
If brain sleeptime had errors in any step, report which steps succeeded and which failed.
