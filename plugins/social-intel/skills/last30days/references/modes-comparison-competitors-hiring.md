# COMPARISON, --competitors and --hiring-signals modes

Engine invocation and per-entity planning for comparison queries plus the two named modes.
**Read when the topic contains `vs`/`versus`, or when the user asked for a competitor sweep or hiring signals.** Skip on ordinary GENERAL/NEWS/RECOMMENDATIONS runs.

## Contents

- If QUERY_TYPE = COMPARISON
- Competitor mode (`--competitors`)
- Hiring Signals mode (`--hiring-signals`)

---

## If QUERY_TYPE = COMPARISON

When the user asks "X vs Y" (or "X vs Y vs Z"), the engine fans out N full `pipeline.run()` calls in parallel — one per entity — each with its own Step 0.55-grade targeting. This restored the old N-pass architecture (reverted the one-pass latency optimization that removed per-entity depth); parallel execution keeps wall clock ≈ a single pass.

**MANDATORY per-entity resolution.** For each entity, resolve the full Step 0.55 stack (X handle, subreddits, GitHub user/repos, news context). Then assemble a `--competitors-plan` JSON mapping each entity to its targeting, and invoke the engine ONCE with the vs-topic string.

**Output shape per run:**
- For `--emit=compact` / `--emit=md`, there is no separate merged Markdown raw file. The main topic saves to `{main-slug}-raw.md`; each peer saves to `{peer-slug}-raw.md`.
- For `--emit=html`, the main saved artifact is the merged comparison HTML at `{main-slug}-vs-{peer-slug}-raw-html[...].html`; each peer may also save its own per-entity HTML artifact.
- The engine logs every written file as `[last30days] Saved output to {path}` and, for comparison runs, follows with `[last30days] Comparison artifact set: main={path}; peers={path, ...}`. Treat that log line as authoritative instead of recomputing paths from slugs.
- Stdout shows a merged comparison with the `## Head-to-Head` scaffold + per-entity Resolved Entities block.

**Invocation:**
```bash
# SKILL_DIR = absolute path of the directory containing THIS SKILL.md you just Read.
# Substitute the actual path below — your harness told you where this file lives via
# the Read tool result. Examples:
#   Read ~/.claude/skills/last30days/SKILL.md      → SKILL_DIR=$HOME/.claude/skills/last30days
#   Read ~/.codex/skills/last30days/SKILL.md       → SKILL_DIR=$HOME/.codex/skills/last30days
#   Read ~/.claude/plugins/cache/last30days-skill/last30days/{version}/skills/last30days/SKILL.md
#     → SKILL_DIR=$HOME/.claude/plugins/cache/last30days-skill/last30days/{version}/skills/last30days
#   ({version} — фактический номер каталога в кеше; на этой машине plugin-кеша last30days
#    сейчас нет вовсе — рабочая копия одна: ~/.claude/skills/last30days)
# scripts/last30days.py is always a direct child of SKILL_DIR (every install layout
# packages SKILL.md and scripts/ as siblings).
SKILL_DIR="<absolute path of the directory containing the SKILL.md you Read>"

if [ ! -f "$SKILL_DIR/scripts/last30days.py" ]; then
  echo "ERROR: scripts/last30days.py not found under SKILL_DIR=$SKILL_DIR" >&2
  echo "Re-check the directory of the SKILL.md you Read and substitute it as SKILL_DIR above." >&2
  exit 1
fi

# Write the per-entity plan to a tmpfile and pass the path to the engine.
# The engine's parse_competitors_plan() reads file paths transparently. This
# avoids the inline-single-quoted-JSON apostrophe trap (resolved context
# strings like "people's choice" or "McDonald's" otherwise close the outer
# single-quote and break shell parsing before the engine is even invoked).
# Trailing XXXXXX (no .json suffix) so BSD/macOS mktemp works the same as
# GNU; BSD only substitutes X's at the end of the template.
COMPETITORS_PLAN_FILE=$(mktemp "${TMPDIR:-/tmp}/last30days-competitors.XXXXXX")
trap 'rm -f "$COMPETITORS_PLAN_FILE"' EXIT
# >| not >: mktemp already created the file, so a plain > is refused under
# `set -o noclobber` (leaving the plan empty -> deterministic fallback).
cat >| "$COMPETITORS_PLAN_FILE" <<'PLAN_EOF'
{
  "{TOPIC_B}": {"x_handle":"{TOPIC_B_HANDLE}","subreddits":["{TOPIC_B_SUB_1}","{TOPIC_B_SUB_2}"],"github_user":"{TOPIC_B_GH}","context":"{TOPIC_B_CONTEXT}"},
  "{TOPIC_C}": {"x_handle":"{TOPIC_C_HANDLE}","subreddits":["{TOPIC_C_SUB_1}"],"github_user":"{TOPIC_C_GH}","context":"{TOPIC_C_CONTEXT}"}
}
PLAN_EOF

"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" "{TOPIC_A} vs {TOPIC_B} vs {TOPIC_C}" \
  --emit=compact \
  --save-dir="${LAST30DAYS_MEMORY_DIR}" \
  --save-suffix=v3 \
  --x-handle={TOPIC_A_HANDLE} \
  --subreddits={TOPIC_A_SUBS} \
  --competitors-plan "$COMPETITORS_PLAN_FILE"
```

**Keep the heredoc marker quoted as `'PLAN_EOF'`.** Quoting suppresses shell interpolation so apostrophes, `$`, backticks, etc. pass through verbatim. If you ever switch to an unquoted `<<PLAN_EOF`, every variable reference and apostrophe inside the JSON becomes a parse hazard.

Topic A (the main topic, first in the vs-string) uses outer `--x-handle`, `--x-related`, `--subreddits`, `--github-user`, `--github-repo`, `--trustpilot-domain`, `--tiktok-*`, `--ig-creators` as usual. Topics B and C get their targeting from `--competitors-plan` entries (keyed by entity name, case-insensitive) — the engine does NOT read a main-topic entry out of the plan, so the main topic's Trustpilot domain must ride the outer flag.

**Step 0.55 for N entities.** The same pre-research protocol that applies to a single-entity topic applies to EACH entity in a vs-run. For N=3, that means 3 WebSearches for X handles, 3 for subreddits, 3 for GitHub, 3 for news context — or equivalent batched queries. A `## Resolved Entities` block with dashes for any entity means you skipped Step 0.55 for that one. Re-run with a corrected plan.

**Then do WebSearch supplements** for: `{TOPIC_A} vs {TOPIC_B} comparison {YEAR}` and `{TOPIC_A} vs {TOPIC_B} which is better` — these catch rivalry articles that per-entity passes might not surface.

**Use `RESOLVED_POSITIONING` per entity (Step 0.55 item 6) in two ways.** First, ground each entity's `What it is` cell in its CURRENT fetched pitch - describe the entity as it pitches itself today, never from memory. Second, if an entity's month of evidence directly bears on its pitch - SUPPORTS a specific claim, CUTS AGAINST one, or the conversation is squarely ABOUT the pitched ground - say so in ONE prose sentence inside that entity's section of the comparison synthesis (right after the Community Sentiment line - the template marks the slot), anchored to the real item with its engagement. When the pulse is orthogonal to the pitch (on-entity but about something the pitch doesn't speak to), say NOTHING about the pitch: omission is the correct output, and a manufactured connection is worse than silence. Match altitude: test SPECIFIC claims ("zero-config", "fastest", an uptime number) against specific threads; never grade a broad tagline ("financial infrastructure") against an individual thread - it is too broad to hit or miss. Keep claims windowed - "this month's conversation" - never trend verbs like "losing the narrative" that one 30-day window cannot support. If positioning was not actually fetched this run for an entity, skip both uses for that entity - never supply a pitch from memory.

**Skip the normal Step 1 below** - go directly to the comparison synthesis format (see "If QUERY_TYPE = COMPARISON" in the synthesis section).

**COMPARISON TABLE SCAFFOLD (engine-emitted, pass through verbatim):** For comparison topics, the engine's compact output includes a `## Head-to-Head` block with an empty markdown table (columns = entities, rows = axes like "What it is", "Philosophy", "Best for"). Your synthesis MUST include this block verbatim with filled cells, positioned between the narrative and the emoji-tree footer. Keep each cell to 5-15 words. Use ' - ' (hyphen with spaces) not em-dashes inside cells.

### Competitor mode (`--competitors`)

`--competitors` is a SKILL.md-level shortcut for vs-mode with auto-discovery. The engine flag itself just signals intent; YOU (the hosting reasoning model) do the discovery and Step 0.55 via your own WebSearch tool, then invoke the vs-topic path above.

**The four-step protocol:**
1. **Discover peers** via WebSearch: `"{topic} competitors"` / `"{topic} alternatives"`. Pick N=2 by default (match the flag's default), N=argument value if the user passed `--competitors=N`.
2. **Run Step 0.55 for the main topic AND each peer** — same protocol you use for a single-entity topic, just N times. X handle, subreddits, GitHub, news context, per entity.
3. **Build the vs-topic string**: `"{main} vs {peer1} vs {peer2}"`.
4. **Invoke the engine** with the vs-topic, `--competitors-plan` JSON covering both peers (and the main topic if you want to override the outer flags), and the outer `--x-handle`/`--subreddits`/`--github-*` for the main topic.

**Flag surface (engine):**
- `--competitors` (bare) - signals the hosting model to discover 2 peers (3-way total).
- `--competitors=N` - N peers (1..6; out-of-range clamps with stderr warning).
- `--competitors-list="A,B,C"` - minimum escape hatch; names only, no per-entity targeting. Peer sub-runs fall back to planner defaults (visibly thinner data).
- `--competitors-plan '{entity: {x_handle, subreddits, github_user, github_repos, trustpilot_domain, context}}'` - full per-entity targeting; implies vs-mode; preferred.
- `--polymarket-keywords "kw1,kw2"` - disambiguate Polymarket for ambiguous single-token topics ("Warriors" → `nba,gsw,golden-state`).
- `--hiring-signals` - deep-dive into public jobs/careers evidence for company focus signals. Use signal language only: leaning into, investing in, increasing focus, priority shift. Do NOT claim exact roadmap predictions from job postings.

**Why --competitors-plan over --competitors-list:** without per-entity handles/subs, peer sub-runs run with deterministic single-word planner queries and produce visibly thinner evidence than the main topic. The Resolved Entities block in stdout makes the gap visible — dashes for a peer = you skipped its Step 0.55.

**Engine-internal auto-resolve (headless fallback):** if the engine detects BRAVE_API_KEY / EXA_API_KEY / SERPER_API_KEY / PARALLEL_API_KEY / PERPLEXITY_API_KEY / OPENROUTER_API_KEY, it runs its own per-entity `resolve.auto_resolve()` before each sub-run. The hosting-model path does NOT need those keys — you are the WebSearch. The engine's auto-resolve is the cron/CI fallback for when no reasoning model is driving.

**Output:** for Markdown/compact runs, one `{slug}-raw.md` per entity in `--save-dir` plus the merged comparison on stdout. For HTML runs, the main saved artifact is merged comparison HTML and peer artifacts remain per-entity. Always use the `[last30days] Comparison artifact set: main=...; peers=...` log line as the source of truth. Synthesis contract identical to the vs-mode protocol above.

### Hiring Signals mode (`--hiring-signals`)

Use `--hiring-signals` when the user asks what a company's jobs page, careers page, LinkedIn jobs, or competitor hiring suggests about strategic focus. This is strongest for early-stage startups and weaker for large companies, where many unrelated roles are hiring noise.

**Hit the company's OWN job board - that is the entire point.** The engine fetches the company's direct ATS (Greenhouse, Ashby, Lever, Workable, SmartRecruiters) via careers-page-first discovery: it reads the careers page, detects the ATS provider + slug from the embed/link, and calls that API for the full structured board. Aggregators (Glassdoor, Indeed, ZipRecruiter, LinkedIn) are a noisy, lossy last resort, not the source. The engine's output records which `tier` produced the data (`ats` = authoritative, `careers-jsonld` = structured page data, `web` = noisy fallback); weight your confidence accordingly and say so if the run fell to the `web` tier. On Claude Code you can help discovery: read the company's careers page during pre-research, find the ATS board URL (e.g. `jobs.ashbyhq.com/{slug}`), and the engine will resolve the rest.

**Weight by novelty and departure-from-baseline, not raw role count.** A single strategic role can outweigh a department's worth of headcount. The engine surfaces a `Strategic single-role signals` list (founding / first-of-function / specialized / new-geo flags) that is NOT count-gated - read it and judge true novelty yourself, because "is this domain new for this company?" needs world knowledge a keyword map cannot encode. Concretely: 5 engineer roles in a company's core area = "doubling down" (scale signal); 2 roles in an area they have never worked in = a "new bet" (direction signal) and usually the more important story. A `Founding {Role}, {New Capability}` posting (e.g. "Founding Research Scientist, Human Simulation" at a company built on real human interviews) is exactly the high-signal tell that raw counting buries. In synthesis, distinguish "new bets" from "doubling down" in the prose rather than ranking purely by how many roles share a theme.

**Output title for a scoped `--hiring-signals` report.** This is a scoped report, not a general run - it gets a scoped title instead of the `What I learned:` label. Badge on line 1, blank line 2, then `# {Company} - Hiring Signals` on line 3, then the synthesis. Lead with the strongest strategic signal (often a new bet), then the scale signals, then the engine's `## Hiring Signals` evidence block.

**`--hiring-signals` is jobs-scoped - do not build a multi-source plan for it.** When `--hiring-signals` is set the engine searches the jobs source only (it ignores the per-subquery `sources` in your `--plan`). So for a pure hiring-signals run, skip the Step 0.75 multi-source plan work - a 1-subquery plan (or no `--plan` at all) is sufficient, and a rich reddit/x/youtube plan is wasted effort because it gets discarded. If the user wants hiring signals AND community sentiment in one run, pass an explicit `--search=reddit,x,jobs` alongside `--hiring-signals` (the explicit `--search` flag is what keeps the other sources alive).

The output must distinguish evidence from interpretation. Good: "3 current roles mention SSO, SOC 2, and procurement workflows, which signals increased enterprise-readiness focus." Bad: "They will ship enterprise SSO next quarter." In standard `/last30days Company` runs, include Hiring Signals only when the engine surfaces a strong signal; otherwise omit the topic entirely.

---

