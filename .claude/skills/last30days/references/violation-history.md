# LAW violation history (full catalog)

Extended incident narratives behind the OUTPUT CONTRACT LAWs. The LAWs in SKILL.md carry the
rule + short reason; this file preserves the full observed-failure record for maintenance and
future debugging of the contract itself. Not needed at run time.

## v3.0.6 public 0/8 regression (2026-04-18)

On 8 consecutive public invocations, Opus 4.7 treated `/last30days` as a generic research
keyword and improvised. Every run violated LAW 2 (invented titles like "The headline",
"Kanye West: the last 30 days"), LAW 4 (section headers like "Why he is everywhere this
month", "1. gstack dominates", "The 'Homecoming' peak"), or both. One run (Matt Van Horn)
skipped Step 0.5 / 0.55 entirely and ran the engine bare with zero resolution flags. Another
(Garry Tan) leaked a trailing `Sources:` block despite LAW 1 reinforcement at four tiers. Two
runs (Peter Steinberger, Kanye vs Kim) landed on a stale `~/.your-gateway-project/skills/last30days/`
engine copy via a self-written path-discovery loop. The 10/10 beta validation from the same
day had the same model and similar content; the delta was the three structural anchors
(badge, SKILL_DIR substitution, the no-improvisation preface).

## LAW 1 — trailing Sources block

- Peter Steinberger run 1 (2026-04-18): 9-item Sources list.
- Peter Steinberger run 2, post plan 008 (2026-04-18): 7-item Sources list. Model's
  self-debug named the WebSearch tool's verbatim reminder ("CRITICAL REQUIREMENT: ... you
  MUST include a 'Sources:' section ...") as the cause. Three tiers of reinforcement were not
  enough; the post-synthesis self-check became the fourth tier.

## LAW 2 / formatting authority — memory-vs-skill conflict

Peter Steinberger disaster #2 (2026-04-18): model resolved a conflict between a personal
"no bold" memory rule and the skill template as "memory wins" and stripped all bold, producing
narrative-with-section-headers instead of the canonical bold-lead-in paragraphs. Correct
resolution: skill template wins inside skill output.

## LAW 4 — section headers

Peter Steinberger disaster #2 (2026-04-18): emitted `Headline`, `What he is actually saying`,
`Cross-source corroboration`, `Where evidence is thin`, `Bottom line` on a GENERAL query.

## LAW 6 — raw evidence dump

Hermes Agent Use Cases (2026-04-19): two consecutive runs returned the raw
`## Ranked Evidence Clusters` block verbatim as user output, with 8 cluster entries carrying
`(score N, M items, sources: ...)` tuples and `- Uncertainty: single-source` lines. Root
cause: prior boundary text said "Pass through the lines ABOVE this boundary verbatim," which
the model scoped broadly to include the scratchpad. A third run on the same topic produced
the correct `What I learned:` prose synthesis.

## LAW 7 — missing --plan

Hermes Agent Use Cases Run 1 (2026-04-19): model called the engine bare. The engine's stderr
warning ("No --plan and no LLM provider configured. Using deterministic fallback...") was
misread as a capability constraint ("I don't have a key") instead of a skipped planning step.
The misread came from the word "provider". Run 2 with `--plan` produced clean results.

## LAW 8 — citation rendering

2026-04-20 inline-links saga: the citation rule lived at line ~1224, below the chunked-read
window; four consecutive runs (Matt Van Horn, Peter Steinberger, Best Headphones, OpenClaw vs
Hermes) never read it. Hoisting it into the guaranteed-loaded band fixed that. 2026-06-25
split: a Codex run then obeyed the rule and inline-linked every citation, but Codex prints
URLs inline, so the output rendered as URL soup — hence the two-regime rule keyed on
`CLAUDECODE`.

## LAW 9 — missed community voice

2026-06-17: five consecutive runs (Kanye, Steinberger, Kevin Rose, Lan Xuezhao,
Matt-vs-Trevin) shipped news-shaped reports that missed every funny comment, fabricated one
citation URL, and leaked tooling meta-commentary — the comment-weaving rule lived below the
chunked-read window and `## Best Takes` was often empty. Fix: engine always surfaces
`## Top Community Comments`, and the rule was hoisted into the LAWs.

## Step 0.45 — keyword trap

"Birthday gift for 42 year old man" (2026-04-18): engine ran on the literal phrase and
returned 5 minutes of r/todayilearned / r/japannews / r/LivestreamFail noise — no human posts
"I bought a 42 year old man a gift" on Reddit, and "42" collides with jersey numbers.

## Step 0.55 — category peers

`GPT Image 2` (2026-04-22): model resolved only OpenAI-brand subs
(`r/OpenAI, r/ChatGPT, r/singularity, r/ChatGPTpromptengineering`) and missed
`r/StableDiffusion, r/midjourney, r/dalle2, r/aiArt` where prompting techniques actually
live. User had to manually prompt "check image generation reddits too".

## Step 0.75 — disambiguation

2026-06-17: bare "Kevin Rose" subqueries returned 55 items with ~0 about the Digg founder
(collides with Kevin Warsh / Leon Rose / Kevin Hart) until every subquery was anchored to
"Digg founder". Same class: "lan xuezhao" (Lanzhou food, cdrama edits), "trevin chow"
(Trevin Wax / Trevin Brown), "tella" (soccer player).

## First-run setup skip

Fredy Montero run (2026-06-22): model read "proceed to Step 0.5" in the branching rule and
bypassed the setup wizard. Result: no browser cookie extraction, no yt-dlp, no Digg CLI,
WebSearch-only synthesis with no X/YouTube/TikTok data. Fix: the FIRST-RUN GATE bash check.

## Stale marketplace clone

Three 2026-04-22 test runs (Linear, Coinbase) loaded SKILL.md from
`~/.claude/plugins/marketplaces/last30days-skill/` (a git clone auto-restored to origin/main
on session start, which can lag the versioned cache), ran `--help` from the same stale path,
did not see the `--competitors` flag that existed in the cache, and fell back to a manual
comparison plan. 2 of 3 windows never invoked the feature they were asked to test.
