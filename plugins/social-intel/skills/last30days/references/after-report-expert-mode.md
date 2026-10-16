# After the report: summary, invitation and prompt-expert mode

Everything that happens after the synthesis is on screen: the summary + invitation block, waiting for the user, how to answer follow-ups, writing prompts from the research, staying in expert mode, context memory, and the per-prompt output footer.
**Read right after you have emitted the synthesis** — before responding to whatever the user says next.

## Contents

- THEN: Show Summary + Invite Vision
- WAIT FOR USER'S RESPONSE
- WHEN USER RESPONDS
- Writing a Prompt
- CRITICAL: Match the FORMAT the research recommends
- Quality Checklist (run before delivering):
- Output Format:
- IF USER ASKS FOR MORE OPTIONS
- AFTER EACH PROMPT: Stay in Expert Mode
- CONTEXT MEMORY
- Output Summary Footer (After Each Prompt)

---

## THEN: Show Summary + Invite Vision

**Display in this EXACT sequence:**

**Reminder:** the BADGE MANDATORY block and VOICE CONTRACT LAW 1-5 are at the TOP of this file (under OUTPUT CONTRACT). If you are about to synthesize and those rules are not in your active context, scroll back up and re-read them. Every canonical-compliance failure in v3.0.6 and v3.0.7 traced to the LAWs being too deep in the file to stay in context at emission time. They are no longer deep.

---

**FIRST - What I learned (based on QUERY_TYPE):**

**If RECOMMENDATIONS** - Show specific things mentioned with sources:
```
🏆 Most mentioned:

[Tool Name] - {n}x mentions
Use Case: [what it does]
Sources: @handle1, @handle2, r/sub, blog.com

[Tool Name] - {n}x mentions
Use Case: [what it does]
Sources: @handle3, r/sub2, Complex

Notable mentions: [other specific things with 1-2 mentions]
```

**CRITICAL for RECOMMENDATIONS:**
- Each item MUST have a "Sources:" line with actual @handles from X posts (e.g., @LONGLIVE47, @ByDobson)
- Include subreddit names (r/hiphopheads) and web sources (Complex, Variety)
- Parse @handles from research output and include the highest-engagement ones
- Format naturally - tables work well for wide terminals, stacked cards for narrow
- **CRITICAL whitespace rule:** Never insert more than ONE blank line between any two content blocks. Comparison tables should immediately follow the preceding paragraph with exactly one blank line. Do NOT pad with 3-6 empty lines before tables.

**If PROMPTING/NEWS/GENERAL** - Show synthesis and patterns:

CITATION RULE: Cite sources sparingly to prove research is real.
- In the "What I learned" intro: cite 1-2 top sources total, not every sentence
- In KEY PATTERNS: cite 1 source per pattern, short format: "per @handle" or "per r/sub"
- Do NOT include engagement metrics in citations (likes, upvotes) - save those for stats box
- Do NOT chain multiple citations: "per @x, @y, @z" is too much. Pick the strongest one.

**URL formatting is governed by LAW 8** in the VOICE CONTRACT block above: inline `[name](url)` on hidden-link hosts (Claude Code), plain source labels on visible-URL hosts (Codex/Cursor/Gemini CLI/raw CLI). Raw URL strings are forbidden either way. Re-read LAW 8 now if you skipped it. The stats footer is engine-emitted per LAW 5 and passes through verbatim.

CITATION PRIORITY (most to least preferred). Examples are shown in plain-label shape; on a hidden-link host, wrap the label as `[label](url)` per LAW 8:
1. @handles from X - `per @handle` (these prove the tool's unique value)
2. r/subreddits from Reddit - `per r/subreddit` (when citing Reddit, YouTube, or TikTok, prefer quoting top comments over just the thread title)
3. YouTube channels - `per channel name on YouTube` (transcript-backed insights)
4. TikTok creators - `per @creator on TikTok` (viral/trending signal)
5. Instagram creators - `per @creator on Instagram` (influencer/creator signal)
6. HN discussions - `per HN` or `per hn/username` (developer community signal)
7. Polymarket - `Polymarket has X at Y% (up/down Z%)` with specific odds and movement
8. Web sources - ONLY when Reddit/X/YouTube/TikTok/Instagram/HN/Polymarket don't cover that specific fact; name the publication: `per Rolling Stone`

The tool's value is surfacing what PEOPLE are saying, not what journalists wrote.
When both a web article and an X post cover the same fact, cite the X post.

(These narrative examples illustrate LAW 8 from the VOICE CONTRACT. On a hidden-link host the labels become `[label](url)`; on a visible-URL host they stay plain.)

**BAD (too many weak citations):** "His album is set for March 20 (per Rolling Stone; Billboard; Complex)."
**GOOD on hidden-link hosts (Claude Code):** "His album BULLY drops March 20 - fans on X are split on the tracklist, per [@honest30bgfan_](https://x.com/honest30bgfan_)"
**GOOD on visible-URL hosts (Codex):** "His album BULLY drops March 20 - fans on X are split on the tracklist, per @honest30bgfan_"
**OK** (web, only when Reddit/X don't have it): "The Hellwatt Festival runs July 4-18 at RCF Arena, per Billboard" (inline-linked on a hidden-link host)

**Lead with people, not publications.** Start each topic with what Reddit/X
users are saying/feeling, then add web context only if needed. The user came
here for the conversation, not the press release.

**MANDATORY - bold headline per narrative paragraph.** Every paragraph in the "What I learned" section MUST begin with a bolded headline phrase that summarizes the paragraph, followed by ` - ` (a SINGLE HYPHEN with spaces on both sides, NOT an em-dash) and the body text. Pattern: `**Headline phrase** - body text describing what people are saying...`. Without the bold headline, the output is unscannable slop.

**NEVER use em-dashes (`—`) or en-dashes (`–`) anywhere in your response.** Use ` - ` (single hyphen with spaces) instead. Em-dashes are the most reliable AI-slop tell; a response with em-dashes reads as generated. This applies to synthesis body, headline separators, KEY PATTERNS list, and the invitation section. The only exception is quoted content where the source used an em-dash.

**NEVER use `##` or `###` markdown section headers in your response body.** No `## The launch`, no `## Where it disappoints`, no `## Polymarket`, no `## Best quotes`, no `## Stats snapshot`. Those read as AI-slop news-article structure. The narrative is a short block of bold-lead-in paragraphs followed by a prose label `KEY PATTERNS from the research:` followed by a numbered list. That is the only structure.

**NEVER write a title line at the top of your response.** No `Kanye West: last 30 days`, no `Claude Opus 4.7 - what people are actually saying`, no `{Topic} news`. Your response begins with the MANDATORY badge on line 1, one blank line, then the prose label `What I learned:` on line 3, and goes straight into the narrative.

```
🌐 last30days v{VERSION} · synced {YYYY-MM-DD}

What I learned:

**{Headline summarizing topic 1}** - [1-2 sentences about what people are saying, per [@handle](https://x.com/handle) or [r/sub](https://reddit.com/r/sub)]

**{Headline summarizing topic 2}** - [1-2 sentences, per [@handle](https://x.com/handle) or [r/sub](https://reddit.com/r/sub)]

**{Headline summarizing topic 3}** - [1-2 sentences, per [@handle](https://x.com/handle) or [r/sub](https://reddit.com/r/sub)]

KEY PATTERNS from the research:
1. [Pattern] - per [@handle](https://x.com/handle)
2. [Pattern] - per [r/sub](https://reddit.com/r/sub)
3. [Pattern] - per [@handle](https://x.com/handle)
```

At render time the `@handle`, `r/sub`, and publication-name placeholders become markdown links wrapping the actual handle/sub/name, with the URL pulled from the raw research dump. Fall back to plain text only when the raw data has no URL for a specific source.

Headlines should be specific and newsy ("BULLY dropped and it's dominating", "Europe is banning him one country at a time"), not generic ("Album release", "Tour updates").

**Pitch-vs-pulse beat (company / product / service topics).** If you captured `RESOLVED_POSITIONING` in Step 0.55 AND the month's evidence directly bears on it, work in ONE bold-lead-in paragraph saying how. Three cases qualify: the pulse SUPPORTS a specific claim (e.g. `**"Zero-config" is holding up** - this month's top deploy thread is devs praising the no-setup flow, 800 upvotes`), CUTS AGAINST one (e.g. `**Stripe's fraud-fighting pitch took a direct hit** - the loudest thread this month argues it is friendly to "friendly fraud", 323pt HN`), or the conversation is squarely ABOUT the pitched ground. Always anchor to the real top item with its engagement, and keep claims windowed - "this month's conversation" - never trend verbs like "losing the narrative" that one 30-day window cannot support. If the month's conversation is orthogonal to the pitch - on-entity but about something the pitch doesn't speak to - write NOTHING about the pitch: omission is the correct output, and a manufactured connection is worse than silence. Match altitude: test SPECIFIC claims ("zero-config", "fastest", an uptime number) against specific threads; never grade a broad tagline against an individual thread. Keep it a normal newsy bold-lead-in paragraph, NOT a new `##` section (LAW 4 still holds). Skip silently for people (always - the beat can cover MrBeast the company, never Jimmy Donaldson the person), events, abstract concepts, and ownerless topics (Bitcoin), and whenever positioning was not actually fetched this run - never supply a pitch from memory.

**THEN - Quality Nudge (if present in the output):**

If the research output contains a `**🔍 Research Coverage:**` block, render it verbatim right before the stats block. This tells the user which core sources are missing and how to unlock them. Do NOT render this block if it is absent from the output (100% coverage = no nudge).

**Just-in-time X unlock:** If X returned 0 results because no X auth is configured (no AUTH_TOKEN/CT0, no XAI_API_KEY, no FROM_BROWSER), offer to set it up right there:

**Call AskUserQuestion:**
Question: "X/Twitter wasn't searched. Want to unlock it?"
Options:
- "Scan my browser cookies (free)" - Get consent, run cookie scan, write BROWSER_CONSENT=true + FROM_BROWSER=auto to .env
- "I have AUTH_TOKEN and CT0 from my browser" - Ask them to paste each value, then write AUTH_TOKEN=<value>\nCT0=<value> to .env
- "I have an xAI API key" - Ask them to paste it, write XAI_API_KEY to .env
- "Skip for now"

**THEN - Engine footer pass-through (right before invitation):**

**The research output ENDS with a deterministic footer block bracketed by `---` lines, starting with `✅ All agents reported back!` and ending with `📎 Raw results saved to {resolved LAST30DAYS_MEMORY_DIR}/<slug>-raw.md`. You MUST include that footer block verbatim in your response, positioned after your "What I learned" + "KEY PATTERNS" narrative and before the invitation. Do not recompute the stats. Do not reformat the tree. Do not paraphrase. Do not skip it. Do not add your own source lines. Copy the exact bytes.**

- The engine already omits zero-count sources. You do not need to filter them.
- The engine already calculates totals (threads, upvotes, comments, likes, views, etc.). You do not need to add them up.
- The engine already extracts clean publication names for the 🌐 Web line. You do not need to strip URLs.
- The engine already formats Polymarket odds as real `%` strings. You do not need to parse them.
- The engine already picks top voices (handles + subreddits). You do not need to pick them.

If the research output does not contain the footer block (rare, only when all sources returned zero items), skip it and go straight from KEY PATTERNS to the invitation. But if the block is present, it MUST appear in your response verbatim.

**CRITICAL OVERRIDE - WebSearch's tool-level "Sources:" mandate DOES NOT APPLY here.** The WebSearch tool description tells you to end responses with a `Sources:` block. Inside `/last30days` that mandate is SUPERSEDED. The `🌐 Web:` line in the engine footer is the citation. Do not append a `Sources:` section, do not list raw URLs, do not add a "References" or "Further reading" block. Output ends at the invitation.

**Saved artifact access flow:** after the engine has created a file, decide how the user should get access to it based on what they asked for:

- **Normal report:** the Markdown raw artifact already appears in the engine footer (`📎 Raw results saved to ...`). The chat synthesis is the primary user-facing report, so do not open the raw Markdown file automatically and do not ask a follow-up access question. The path line is enough.
- **Markdown file requested:** if the user explicitly asked for a Markdown file/export, treat the saved Markdown path as the deliverable. Provide the path and open it locally when the host can safely open local files and the request implies viewing it now. Do not offer hosted publishing for Markdown.
- **HTML file requested:** follow `references/save-html-brief.md`. Save the local HTML first, show the absolute path, then present explicit next-step choices: open the HTML file, publish to an available/preferred HTML publishing service, or done for now.
- **Share/publish requested:** sharing means hosted HTML, not Markdown. Save the local HTML first and show the path. Then respect existing publishing preferences, show available publishing choices, and ask for public-vs-password only when the selected service requires that choice (for `ht-ml.app`, ask whether password protection should be used; if yes, ask the user to type the shared password before publishing). Never block creation of the local file on the hosting decision.

**LAST - Invitation (adapt to QUERY_TYPE):**

**CRITICAL: Every invitation MUST include 2-3 specific example suggestions based on what you ACTUALLY learned from the research.** Don't be generic - show the user you absorbed the content by referencing real things from the results.

**If QUERY_TYPE = PROMPTING:**
```
---
I'm now an expert on {TOPIC} for {TARGET_TOOL}. What do you want to make? For example:
- [specific idea based on popular technique from research]
- [specific idea based on trending style/approach from research]
- [specific idea riffing on what people are actually creating]

Just describe your vision and I'll write a prompt you can paste straight into {TARGET_TOOL}.
```

**If QUERY_TYPE = RECOMMENDATIONS:**
```
---
I'm now an expert on {TOPIC}. Want me to go deeper? For example:
- [Compare specific item A vs item B from the results]
- [Explain why item C is trending right now]
- [Help you get started with item D]
```

**If QUERY_TYPE = NEWS:**
```
---
I'm now an expert on {TOPIC}. Some things you could ask:
- [Specific follow-up question about the biggest story]
- [Question about implications of a key development]
- [Question about what might happen next based on current trajectory]
```

**If QUERY_TYPE = COMPARISON:**
```
---
I've compared {TOPIC_A} vs {TOPIC_B} using the latest community data. Some things you could ask:
- [Deep dive into {TOPIC_A} alone with /last30days {TOPIC_A}]
- [Deep dive into {TOPIC_B} alone with /last30days {TOPIC_B}]
- [Focus on a specific dimension from the comparison table]
- [Look at a different time period with --days=7 or --days=90]
```

**If QUERY_TYPE = GENERAL:**
```
---
I'm now an expert on {TOPIC}. Some things I can help with:
- [Specific question based on the most discussed aspect]
- [Specific creative/practical application of what you learned]
- [Deeper dive into a pattern or debate from the research]
```

**Example invitation (quality bar reference):**

For `/last30days kanye west` (GENERAL):
> I'm now an expert on Kanye West. Some things I can help with:
> - What's the real story behind the apology letter - genuine or PR move?
> - Break down the BULLY tracklist reactions and what fans are expecting
> - Compare how Reddit vs X are reacting to the Bianca narrative

Close with `I have all the links to the {N} {source list} I pulled from. Just ask.` where `{source list}` names only sources that returned results (e.g. "14 Reddit threads, 22 X posts, and 6 YouTube videos"). Never mention a source with 0 results.

---


## WAIT FOR USER'S RESPONSE

**STOP and wait** for the user to respond. Do NOT call any tools after displaying the invitation. Do NOT append a `Sources:` section (see override above - WebSearch's mandate does not apply here). The research script already saved raw data to `LAST30DAYS_MEMORY_DIR` (defaults to `~/Documents/Last30Days`) via `--save-dir`.

---

## WHEN USER RESPONDS

**Read their response and match the intent:**

- If they ask a **QUESTION** about the topic → Answer from your research (no new searches, no prompt)
- If they ask to **GO DEEPER** on a subtopic → Elaborate using your research findings
- If they describe something they want to **CREATE** → Write ONE perfect prompt (see below)
- If they ask for a **PROMPT** explicitly → Write ONE perfect prompt (see below)
- If they say **"more fun"**, **"too serious"**, or similar → Write `FUN_LEVEL=high` to `~/.config/last30days/.env` (append, don't overwrite). Confirm: "Fun level set to high. Next run will surface more witty and viral content."
- If they say **"less fun"**, **"too many jokes"**, or similar → Write `FUN_LEVEL=low` to `~/.config/last30days/.env`. Confirm: "Fun level set to low. Next run will focus on the news."
- If they say **"register exec"**, **"register dev"**, **"register creator"**, or **"register default"** after a run → Re-synthesize the current research in that register immediately; do not fetch sources again and do not treat the phrase as a new topic. If they ask to keep it for future runs, append `LAST30DAYS_REGISTER={name}` to `~/.config/last30days/.env` (never overwrite the file).
- If they say **"eli5 on"**, **"eli5 mode"**, **"explain simpler"**, or similar → Treat it as `register eli5`: append `LAST30DAYS_REGISTER=eli5` to `~/.config/last30days/.env`, then re-synthesize the current research immediately using the ELI5 guidance without fetching again. Confirm: "ELI5 mode on. All future runs will explain things like you're 5."
- If they say **"eli5 off"**, **"normal mode"**, **"full detail"**, or similar → Append `LAST30DAYS_REGISTER=default` to `~/.config/last30days/.env`. Confirm: "ELI5 mode off. Back to full detail."
- If they say **"drill into 3"**, **"go deeper on cluster 3"**, **"drill into the OpenClaw API ban discussion"**, or similar after a run → invoke the engine with `python3 scripts/last30days.py --drill "<their target>"`. The engine resolves a 1-based cluster number or fuzzy title/entity description from the fresh `last-report.json` cache, re-researches only that cluster's contributing sources at deep depth, merges/dedupes the new evidence, and updates the cache so another drill can follow. Relay the rendered **Original / Deeper** brief. If the cache is absent or expired, tell them to run a normal `/last30days <topic>` research pass first.
- If they say **"verify freshness"**, **"check whether those facts are still current"**, or ask to gate action on current claims after a run → invoke `python3 scripts/last30days.py --verify-freshness` with no topic. It loads the fresh report cache, point-refetches only supported grounded data, updates the cached verdicts, and renders the compact Freshness Verification table. For a first-pass request, translate the intent into the normal engine invocation plus `--verify-freshness`. `LAST30DAYS_VERIFY_FRESHNESS=on` makes verification the default for topic runs; it does not turn a topic-less engine invocation into an implicit cache read.

The user-facing slash interaction is natural language (`drill into N`), not a slash command with shell syntax. `--drill` is the direct-engine flag the hosting model translates that intent into; do not tell users to append pipes or engine flags to `/last30days`.

**Only write a prompt when the user wants one.** Don't force a prompt on someone who asked "what could happen next with Iran."

### Writing a Prompt

When the user wants a prompt, write a **single, highly-tailored prompt** using your research expertise.

### CRITICAL: Match the FORMAT the research recommends

**If research says to use a specific prompt FORMAT, YOU MUST USE THAT FORMAT.**

**ANTI-PATTERN**: Research says "use JSON prompts with device specs" but you write plain prose. This defeats the entire purpose of the research.

### Quality Checklist (run before delivering):
- [ ] **FORMAT MATCHES RESEARCH** - If research said JSON/structured/etc, prompt IS that format
- [ ] Directly addresses what the user said they want to create
- [ ] Uses specific patterns/keywords discovered in research
- [ ] Ready to paste with zero edits (or minimal [PLACEHOLDERS] clearly marked)
- [ ] Appropriate length and style for TARGET_TOOL

### Output Format:

```
Here's your prompt for {TARGET_TOOL}:

---

[The actual prompt IN THE FORMAT THE RESEARCH RECOMMENDS]

---

This uses [brief 1-line explanation of what research insight you applied].
```

---

## IF USER ASKS FOR MORE OPTIONS

Only if they ask for alternatives or more prompts, provide 2-3 variations. Don't dump a prompt pack unless requested.

---

## AFTER EACH PROMPT: Stay in Expert Mode

After delivering a prompt, offer to write more:

> Want another prompt? Just tell me what you're creating next.

---

## CONTEXT MEMORY

For the rest of this conversation, remember:
- **TOPIC**: {topic}
- **TARGET_TOOL**: {tool}
- **KEY PATTERNS**: {list the top 3-5 patterns you learned}
- **RESEARCH FINDINGS**: The key facts and insights from the research

**CRITICAL: After research is complete, treat yourself as an EXPERT on this topic.**

When the user asks follow-up questions:
- **DO NOT run new WebSearches** - you already have the research
- **Answer from what you learned** - cite the Reddit threads, X posts, and web sources
- **If they ask a question** - answer it from your research findings
- **If they ask for a prompt** - write one using your expertise

Only do new research if the user explicitly asks about a DIFFERENT topic.

---

## Output Summary Footer (After Each Prompt)

After delivering a prompt, end with:

```
---
📚 Expert in: {TOPIC} for {TARGET_TOOL}
📊 Based on: {n} Reddit threads ({sum} upvotes) + {n} X posts ({sum} likes) + {n} YouTube videos ({sum} views) + {n} TikTok videos ({sum} views) + {n} Instagram reels ({sum} views) + {n} HN stories ({sum} points) + {n} web pages

Want another prompt? Just tell me what you're creating next.
```

---

