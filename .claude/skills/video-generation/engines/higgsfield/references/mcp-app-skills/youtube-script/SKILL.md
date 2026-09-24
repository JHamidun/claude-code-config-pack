---
name: youtube-script
description: >
  Write a complete YouTube script with a full spoken body in one of six genres:
  business/finance, tech review, commentary, documentary, true crime or explainer.
  Includes hook options, timestamps, production cues and a retention map.
  Use for full scripts, not hook-only requests, ad copy or finished video production;
  ai-host-video may call this skill for its script-writing stage.
metadata:
  source_revision: "5073f3a09d3f6b0469db9ff7e8a9df0d339f743a"
---

# YouTube Script

Write a complete YouTube script by routing the request to exactly one genre guide.
This root router is mandatory: load and apply this file before opening any genre
reference. Never open or apply a genre reference as a standalone skill.

## Scope boundaries

Use this skill for complete YouTube scripts, including the writing stage of an
AI-hosted episode. Hook-only or retention-outline requests do not require the full
genre workflow. Ad/commercial scripts and cinematic scene writing are outside this
skill's scope; do not assume an unavailable sibling skill is installed.

## Shared truth policy

Never invent first-person experience, tests, purchases or spending, revenue,
confessions, expertise, credentials, or audience/channel history. When genre craft
calls for personal proof, ask the user for receipts. If receipts are unavailable,
use named sourced evidence or neutral analyst framing and remove the unsupported
first-person claim. Never turn illustrative formulas in the references into facts.

For factual subjects, distinguish verified facts from uncertainty. Use user-supplied
sources or available read-only research tools; ask only when required evidence is
unavailable. Attribute evidence by name and mark unverified details for confirmation.
Do not invent dialogue, quotations, events, statistics, or interior thoughts.

## Monetization policy

Never invent a sponsor read, affiliate mention, product or course plug, merch beat,
brand integration, or other monetization. If the user explicitly requests a
specific monetization integration, honor it without fabricating claims and place it
where it does not break the selected genre's story, test, reveal, or payoff.

## Route to exactly one genre

Choose one guide only. Do not blend genre guides. Route by the promised viewer
experience and the structure that carries it—not by topic nouns. A company, AI,
economics, work, money, history, or productivity topic can enter several genres.

Before choosing, diagnose these five fields:

- **subject** — the person, product, event, artifact, case, or mechanism discussed;
- **viewer promise** — what the viewer can understand, decide, feel, or do afterward;
- **narrative engine** — advice, verdict, stance, chronology, case reveal, or causal
  explanation;
- **evidence spine** — receipts/framework, test/demo, concrete artifact, event
  timeline, case record, or mechanism/analogy;
- **host stance** — coach/operator, reviewer, critic, narrator, case guide, or teacher.

The narrative engine and evidence spine are decisive. Subject words are supporting
evidence only.

### Affirmative entry gates

Select a guide only when its complete entry gate is satisfied:

- `references/business-finance.md` — the viewer promise is an actionable personal,
  career, entrepreneurial, productivity, self-improvement, or financial outcome, and
  the spine is advice, a framework, operator evidence, or a decision. Do not select it
  merely because the subject mentions a company, AI, economics, work, productivity,
  money, “lessons,” or “how to.” A company chronology is documentary; a product
  verdict or tutorial is tech review; a system mechanism is explainer.
- `references/tech-review.md` — a concrete product or tool is evaluated, tested,
  compared, ranked, demonstrated, reported as news, or taught through product use.
  The payoff is a verdict, purchasing/usage decision, observed result, or completed
  product task—not general career or business advice.
- `references/commentary.md` — a concrete artifact, work, creator output, claim, or
  cultural trend is examined through an explicit host stance. The spine is reaction,
  critique, satire, or close reading—not neutral mechanism teaching or chronology.
- `references/storytelling-documentary.md` — verified real events, a challenge, or a
  person/company/history arc unfolds through chronology, conflict, investigation, and
  reveals. The payoff is what happened and why it mattered—not primarily a list of
  takeaways.
- `references/true-crime.md` — a specific crime, disappearance, interrogation,
  court/bodycam record, scam case, or dark legal case is reconstructed with
  case-specific evidence and ethical/legal discipline. General scam prevention or
  fraud mechanics without a case belongs elsewhere.
- `references/explainer.md` — one central how/why question is answered through a
  causal mechanism, misconception correction, demonstration, or analogy. Science,
  history, economics, geography, companies, and technology route here only when
  understanding the mechanism is the payoff.

No guide is a fallback. In particular, `business-finance` is never the default for an
unclear advice-shaped brief.

### Resolve overlaps by outcome

Explicit user intent and title-promise verbs override domain nouns:

- “which should I use/buy?” or “I tested/compared” → tech review;
- “what is wrong/brilliant about this?” → commentary;
- “what happened next/how did they rise or fall?” → storytelling/documentary;
- “how was this case solved?” → true crime;
- “how/why does this work?” → explainer;
- “what should I do to improve/earn/build/decide?” → business/finance.

For example, an AI subject routes to tech review for a tool comparison, business for
an income method, explainer for model mechanics, commentary for a critique of an AI
trend, and documentary for a company chronology.

Identify the closest competing guide and state why its entry gate loses. If two entry
gates remain genuinely satisfied and the run is interactive, ask one outcome question
with concrete choices, such as story versus mechanism versus operator takeaways.
If the caller explicitly authorizes autonomous resolution, infer from the requested
outcome, title promise, available evidence, and intended payoff. Never resolve
ambiguity by defaulting to `business-finance`.

## Loading order

1. Apply this root router and its shared truth and monetization policies.
2. Select exactly one genre.
3. Read that genre guide in full.
4. Read its paired `*-patterns.md` file only when deeper examples or pattern detail
   are useful.
5. Follow the genre guide, with this root policy taking precedence if wording
   conflicts.

Callers such as `ai-host-video` may override the presentation format, headings,
cue syntax, or surrounding workflow contract. Preserve the selected genre's craft:
hook logic, beat structure, voice, evidence discipline, retention devices, and
ending behavior.

## Direct-use output contract

When this skill is used directly and no caller supplies another presentation
contract, preserve the selected guide's output format:

1. Three distinct hook options.
2. One complete timestamped script with actionable production cues.
3. One timestamped retention map.

Use the requested language and target length. At roughly 140–150 spoken words per
minute unless the selected guide specifies another pace, write to the runtime
rather than merely describing it.
