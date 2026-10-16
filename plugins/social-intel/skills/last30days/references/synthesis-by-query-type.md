# Synthesis branches: RECOMMENDATIONS and COMPARISON

The two query-type-specific synthesis templates: signal-weighted picks for RECOMMENDATIONS, the full section scaffold for COMPARISON.
**Read after you have classified QUERY_TYPE and it is RECOMMENDATIONS or COMPARISON.** GENERAL / NEWS / PROMPTING runs use the `What I learned:` shape described in the OUTPUT CONTRACT and need nothing from this file.

## Contents

- If QUERY_TYPE = RECOMMENDATIONS — Signal-weighted picks, not mention counts
- If QUERY_TYPE = COMPARISON
- Quick Verdict
- {Entity 1}
- {Entity 2}
- {Entity 3}
- Head-to-Head
- The Bottom Line
- The emerging stack

---

### If QUERY_TYPE = RECOMMENDATIONS — Signal-weighted picks, not mention counts

**The failure mode for RECOMMENDATIONS queries is "counting when you should have judged."** Mention count rewards whatever is already popular, which is rarely what is actually recommended. Rank by signal quality instead.

**Signal weights (highest to lowest):**
1. **Practitioner testimony** (weight 5) - first-person "I use X and here's why" with specific reasoning, version numbers, or workflow details
2. **Expert defection / authority move** (weight 4) - a domain insider publicly switching, endorsing, or picking (e.g., Flask creator switching from Python to Go)
3. **Measurable claim** (weight 4) - specific number, benchmark, production adoption proof (e.g., "43.7% latency win", "LinkedIn and Uber running it in prod")
4. **Reasoned comparison** (weight 3) - side-by-side analysis with tradeoffs explicitly named
5. **Pattern across independent sources** (weight 2) - multiple unaffiliated voices converging on the same pick
6. **Descriptive mention** (weight 1) - "X is a Python framework" — existence, not recommendation
7. **Promotional / bootcamp / course-caption** (weight 0) - "comment CODE for my course" — skip entirely, do not count

**Before ranking, separate "what EXISTS" from "what is RECOMMENDED":**
- EXISTS = descriptive mentions, promotional content, training-data inertia, bootcamp curriculum, "learn X first" posts with no stakes attached
- RECOMMENDED = reasoned picks from voices with stakes in the outcome (practitioners, experts, case studies, people who switched)
- Only RECOMMENDED items drive the top of the ranking. Existing-but-not-recommended items go in "Also mentioned" at the bottom with a one-line note on why they are mentions not picks.

**Lead with the 30-day DELTA, not the status-quo baseline.** What is the interesting movement? Who is switching? What is the contrarian signal? A status-quo leader with no movement is a footer item, not the headline. "Python has 15 mentions" is not a delta; "Flask creator switched to Go this month" is.

**Output shape:**

```
🏆 Top recommendations (ranked by signal quality, not mention count):

**[Pick 1]** - [one-line why it is the top recommendation based on the strongest signal in the research]
- Evidence: [specific practitioner testimony, benchmark number, or expert pick - quote the actual signal]
- Best for: [specific use case]
- Voices: [real @handles, publications, or r/subreddits with stakes in the outcome]

**[Pick 2]** - [same shape]

**[Pick 3]** - [same shape]

Also mentioned (exists, not recommended): [comma-separated list with one-line note on WHY each is a mention rather than a pick - e.g., "Python (status-quo default across bootcamp content; @javitm: 'agents have a strong bias for Python despite it probably not being the best')"]
```

**Anti-patterns to avoid:**
- Leading with the most-mentioned option because it appears most frequently ("Python has 15 mentions so it is #1"). That is counting, not judging.
- Treating every mention equally. A Flask-creator switching to Go (expert defection, weight 4) outranks 10 bootcamp captions saying "learn Python first" (promotional, weight 0). The bootcamp captions do not belong in the ranking at all.
- Collapsing "best for what?" into one leaderboard. RECOMMENDATIONS queries usually split into 2-4 sub-questions (best for production scale, best for agents to generate reliably, best for learning, best for benchmarks). Separate them if the research supports it.
- Ignoring anti-signal quotes. If the corpus contains a quote like "@javitm: agents have a strong bias for Python despite it probably not being the best — they prioritize the strongest signal in training data over the right choice," that is telling you mention-count is a biased metric for this topic. Read it; surface it; do not ignore it.
- Stress-test your top pick before emitting. Ask: "Would the research actually defend this claim to a skeptical expert?" If the answer is no, re-rank.

**Named failure mode (2026-04-18):** On `best programming language for AI agents`, Opus 4.7 led with `🏆 Most mentioned: Python (15+x mentions)` and put Go at #3 with 7x mentions. Model self-debug: "I counted when I should have judged. @javitm's quote should have changed the ranking because it called Python mentions a bias signal, not evidence of fit. I read that quote and then ranked by mention count anyway. The Flask-creator switching to Go was the real headline; I buried it." Do not repeat this failure.

**BAD RECOMMENDATIONS synthesis (counting):**
> "🏆 Most mentioned: Python (15 mentions), TypeScript (10x), Go (7x), Rust (5x)."

**GOOD RECOMMENDATIONS synthesis (judging):**
> "🏆 Top recommendations (ranked by signal quality, not mention count):
>
> **Go** - Flask creator Miguel Grinberg publicly switched this month for a specific technical reason
> - Evidence: @miguelgrinberg blog post "Why I am moving Python projects to Go for AI agents" — cites reliability and concurrency model; 1.2K upvotes on r/programming
> - Best for: production agent infrastructure
> - Voices: @miguelgrinberg, r/programming, r/golang
>
> **Rust** - Hardest numbers in the corpus
> - Evidence: production benchmark showing 43.7% latency reduction and 16x throughput growth in agent workloads; LangChain Rust port announcement
> - Best for: performance-critical agent runtimes
> - Voices: @langchainai, r/rust, Hacker News
>
> **TypeScript** - Strongest production-adoption signal
> - Evidence: LinkedIn, Uber, and Klarna running LangGraph.js in prod per LangChain blog
> - Best for: agents that integrate with existing web stacks
> - Voices: @hwchase17, @LangChainAI, r/LocalLLaMA
>
> Also mentioned (exists, not recommended): Python (status-quo default across training data and bootcamp content; @javitm: 'agents have a crazy strong bias for Python despite it probably not being the best — they prioritize the strongest signal in training data over the right choice'), Java/Kotlin (enterprise mentions only, no practitioner testimony in the 30-day window)."

Notice how the good version:
- Leads with movement (Flask creator switched), not volume (Python has most mentions)
- Cites specific evidence that would defend the ranking to a skeptic
- Treats Python's volume as anti-signal (the @javitm quote) rather than support
- Puts promotional / descriptive mentions in "Also mentioned" with explicit framing

### If QUERY_TYPE = COMPARISON

**Comparison queries have their OWN synthesis template. Do NOT use the general-query `What I learned:` + bold-lead-in + `KEY PATTERNS:` structure for comparisons.** The comparison template below is the canonical shape proven by the April 9 launch-video exemplar. Follow it section-for-section.

Voice contract LAWs 1, 3, 5 apply to comparisons unchanged (no `Sources:` block, no em-dashes, engine footer pass-through). LAWs 2 and 4 have comparison-specific exceptions (see the LAW block: the comparison title and the five section headers below are REQUIRED, not violations).

**Required comparison structure (match the April 9 exemplar):**

```
🌐 last30days v{VERSION} · synced {YYYY-MM-DD}

# {TOPIC_A} vs {TOPIC_B} [vs {TOPIC_C}]: What the Community Says (/Last30Days)

## Quick Verdict

[One paragraph. Frame the thesis (are these competitors or layers of a stack? who's dominant? who's challenging?). Include scale stats for each entity inline (GitHub stars, user counts, whatever metric is comparable). End with one quotable community framing — a tweet, a Reddit quote, a YouTube clip — that captures how the community sees the relationship.]

## {Entity 1}

**Community Sentiment:** [Positive / Mixed / Negative / Enthusiastic / Security-concerned / etc.] ({N}+ mentions across {source list})

[Optional pitch-vs-pulse sentence - ONLY if `RESOLVED_POSITIONING` was captured for this entity AND the month's evidence directly supports a specific claim, cuts against one, or is squarely about the pitched ground: one windowed prose sentence anchored to a real item with engagement. Otherwise omit entirely - silence, not a placeholder.]

**Strengths (what people love)**
- [Specific strength with `per <source>` attribution]
- [Specific strength with `per <source>` attribution]
- [Specific strength with `per <source>` attribution]

**Weaknesses (common complaints)**
- [Specific complaint with `per <source>` attribution]
- [Specific complaint with `per <source>` attribution]

## {Entity 2}

[Same structure: Community Sentiment, Strengths bullets, Weaknesses bullets]

## {Entity 3}

[Same structure]

## Head-to-Head

| Dimension | {Entity 1} | {Entity 2} | {Entity 3} |
|---|---|---|---|
| What it is | ... | ... | ... |
| GitHub stars | ... | ... | ... |
| Philosophy | ... | ... | ... |
| Skills | ... | ... | ... |
| Memory | ... | ... | ... |
| Models | ... | ... | ... |
| Security | ... | ... | ... |
| Best for | ... | ... | ... |
| Install | ... | ... | ... |

(Engine emits this scaffold; fill the cells with 5-15 words each. If an axis does not apply to the topic class, write "N/A" or a topic-appropriate substitute rather than inventing data. Ground the `What it is` row in `RESOLVED_POSITIONING` when captured - each entity described as it pitches itself today, fetched this run, never from memory.)

## The Bottom Line

**Choose {Entity 1} if** [specific use case, comfort profile, tradeoff]. [One supporting sentence with attribution.]

**Choose {Entity 2} if** [specific use case, comfort profile, tradeoff]. [One supporting sentence with attribution.]

**Choose {Entity 3} if** [specific use case, comfort profile, tradeoff]. [One supporting sentence with attribution.]

## The emerging stack

[One paragraph. Name the combination pattern the community is converging on. Cite specific sources (`per @handle`, `per r/sub`, `per {channel} on YouTube`). This is the synthesis moment of the piece. If the data does not support an emerging-stack observation, write "No emerging stack pattern has crystallized in the research window yet" rather than fabricating one.]

---
✅ All agents reported back!
├─ 🟠 Reddit: ...
├─ 🔵 X: ...
(engine footer passed through verbatim, LAW 5)
└─ 📎 Raw results saved to ...

I've compared {TOPIC_A} vs {TOPIC_B} [vs ...] using the latest community data. Some things you could ask:
- [follow-up referencing comparison specifics, e.g. "Deep dive into {Entity} alone with /last30days {Entity}"]
- [follow-up referencing a specific claim from the Strengths/Weaknesses block]
- [follow-up on a specific dimension from the Head-to-Head table]
- [follow-up on the emerging-stack combination pattern]
```

**Do NOT:**
- Use `What I learned:` prose label (that is general-query voice)
- Use bold-lead-in paragraphs with ` - ` separators for the body (that is general-query voice)
- Use a `KEY PATTERNS from the research:` numbered list (replaced by per-entity Strengths/Weaknesses bullets and the emerging-stack paragraph)
- Fabricate a `## Notable Stats` block (the engine footer IS the stats block, LAW 5)
- Produce section headers outside the six listed above (`## Quick Verdict`, `## {Entity}` per entity, `## Head-to-Head`, `## The Bottom Line`, `## The emerging stack` are the only allowed `##` headers per LAW 4 comparison exception)

**Reference exemplar:** `$LAST30DAYS_MEMORY_DIR/your-gateway-project-vs-hermes-vs-paperclip-LAUNCH-VIDEO-april9-exemplar.md` preserves the April 9 canonical output with full structural analysis. Match this shape section-for-section.

