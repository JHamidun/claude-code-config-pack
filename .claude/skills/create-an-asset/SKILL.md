---
name: create-an-asset
description: "Продажные материалы под сделку: лендинг, дек. Триггеры: «sales deck», «материал для клиента»."
---

# Create an Asset

Builds a customer-facing sales asset — interactive landing page, deck, one-pager, or
workflow/architecture demo — tailored to one prospect at one deal stage.

## Phase 0 — Four inputs

Nothing gets built before all four are known. An asset built without them reads as
templated, and looking templated defeats the only thing the asset is for: showing this
prospect that someone did the homework.

| | Input | Required | Also ask for |
|---|---|---|---|
| (a) | **Prospect** | company, deal stage | contacts + roles, pain points, transcripts / emails / call notes |
| (b) | **Audience** | who is viewing, their primary concern | specific titles, known objections |
| (c) | **Purpose** | goal of the asset, desired next action | — |
| (d) | **Format** | landing page / deck / one-pager / workflow demo | — |

- Deal stages: intro → discovery → evaluation → POC → negotiation → close.
- Audience types: executive · technical · operations · mixed.
- Primary concerns: ROI · technical depth · strategic alignment · risk & security · implementation timeline.
- Goals: intro · discovery follow-up · technical deep-dive · exec alignment · POC proposal · close.

**Seller context** — what the *user* sells. Derive it from their email domain
(`"[domain]" company products services site:linkedin.com OR site:crunchbase.com`), then
confirm. If the domain belongs to a multi-product company, a consultancy, or a generic
mailbox, ask which product this asset is for — guessing here poisons every section that
follows. Persist company, product, value props, differentiators, pricing model; on later
invocations confirm instead of re-asking: "Still selling [Product] at [Company]?"

**Workflow demo only** — also establish the components involved, the step-by-step flow,
where a human touches it, and one concrete example scenario. Parse these from the user's
description first and ask only about the gaps.

## Phase 1 — Research, scaled to what you were given

| Context supplied | Depth |
|---|---|
| Transcripts + detailed pain points | fill gaps only |
| Some context, no transcripts | company + industry |
| Just a company name | full pass: company, leadership, industry, tech stack, competitors |

Always establish: recent annual report or investor deck, publicly stated CEO/CTO
priorities, **current** leadership names, and brand colors from the company site. A
stale exec name destroys credibility faster than a weak argument does, so verify names
against something dated this year.

If transcripts were uploaded, mine them for exact wording — their terminology, acronyms,
internal project names, stated decision criteria. Quoting their own language back is the
strongest available signal that this was built for them and not pulled off a shelf.

## Phase 2 — Structure

### Landing page and deck sections, by purpose

| Purpose | Sections |
|---------|----------|
| Intro | Company Fit → Solution Overview → Key Use Cases → Why Us → Next Steps |
| Discovery follow-up | Their Priorities → How We Help → Relevant Examples → ROI Framework → Next Steps |
| Technical deep-dive | Architecture → Security & Compliance → Integration → Performance → Support |
| Exec alignment | Strategic Fit → Business Impact → ROI Calculator → Risk Mitigation → Partnership |
| POC proposal | Scope → Success Criteria → Timeline → Team → Investment → Next Steps |
| Deal close | Value Summary → Pricing → Implementation Plan → Terms → Sign-off |

Lead with what the audience is accountable for: business impact and ROI for executives,
architecture and integration depth for technical, workflow impact and change management
for operations. For mixed audiences use tabs to separate depth levels rather than
averaging the depth — an averaged asset satisfies neither half of the room.

**Deck** — same sections as linear slides: title (both logos, partnership framing),
agenda, one section per slide, summary, next steps, optional appendix. One message per
slide, visual over text, speaker notes included.

**One-pager** — single scroll: hero headline → three key points with icons → one proof
point (metric, quote, or case study) → CTA with contact info.

**Workflow demo** — canvas structure, component and step schemas, and a worked scenario
narrative are in `references/workflow-demos.md`.

## Phase 3 — Content

Every section must reference specific pain points from the input, use the prospect's own
terminology, map the seller's product explicitly onto their stated needs, and carry a
proof point where one exists.

For each pain point, the pattern is: their challenge in their words → how the product
addresses it → proof or example → the outcome.

The **ROI calculator**, when included, takes inputs drawn from research (user counts,
current spend or time, expected improvement) and outputs annual value, cost, net ROI,
and payback period. State every assumption on screen and make it editable — a hidden
assumption gets discovered in the meeting and takes the whole model down with it.

The **CTA** names a specific next step with a date, not "let's chat", plus contact
details and what happens after they act.

## Phase 4 — Visual design

Dark base, prospect's brand color as the accent. Full token set, typography scale,
card/button/animation rules, workflow-demo node and arrow styles, component icons, and
industry fallback palettes → `references/visual-design.md`.

Default to the **prospect's** brand, not the seller's — the asset should read as built
for them. The seller can switch to their own brand or a neutral palette after the first
build.

## Phase 5 — Confirm before building (required)

Never skip straight to the build. These assets take real effort and a wrong read of the
audience wastes all of it, so state the plan back first:

```
Asset:       [Format] for [Prospect]
Audience:    [Type] — specifically [roles]
Goal:        [Purpose] → driving toward [action]
Key themes:  [2-3 points to emphasize]
[workflow demos] Components: [...]  Flow: [step] → [step] → [step]
```

Then ask, for any format:
- Does this match your vision?
- What is the ONE thing this must nail?
- Tone: bold and confident / consultative / technical and precise?
- Focused and concise, or comprehensive?

Format-specific follow-ups: which sections matter most and whether to include an ROI
calculator (landing page); presentation length and live vs. leave-behind (deck); the
single most important message and print vs. digital (one-pager); component list and flow
confirmation, realistic sample data vs. abstract, click-through vs. auto-play (workflow
demo).

**Cap at two rounds of questions.** Past that, make a reasonable call and flag it:
"I went with X — easy to change if you prefer Y." More rounds cost more goodwill than the
remaining uncertainty is worth.

## Phase 6 — Build and deliver

Output is always a **self-contained HTML file** — CSS in `<style>`, JS in `<script>`, no
external dependencies except Google Fonts. Self-contained is what makes it forwardable:
the prospect opens it from an email attachment with no hosting involved.

File name: `[ProspectName]-[format]-[date].html`, e.g.
`CentricBrands-workflow-demo-2026-01-28.html`.

In the delivery message give the file link, a four-line summary (format, audience,
purpose, sections), and note the sharing options: any static host (Netlify, Vercel,
GitHub Pages, S3), password protection via the host, or sending the file directly.

Before delivering, verify:
- prospect company and leadership names spelled correctly and current
- pain points match what was actually said in the input or transcripts
- no placeholder text left anywhere
- proof points are real and sourced
- interactive elements actually work — tabs, calculator, workflow steps, CTA
- contrast is readable and the layout survives a narrow viewport

On iteration requests, change only what was asked and keep the rest — restyling and
restructuring at the same time makes it impossible to tell which change fixed what.
