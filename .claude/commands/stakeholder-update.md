---
description: Generate a stakeholder update tailored to audience and cadence
argument-hint: "<update type and audience>"
---

# Stakeholder Update

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Generate a stakeholder update tailored to the audience and cadence.

## Usage

```
/stakeholder-update $ARGUMENTS
```

## Workflow

### 1. Determine Update Type

Ask the user what kind of update:
- **Weekly**: Regular cadence update on progress, blockers, and next steps
- **Monthly**: Higher-level summary with trends, milestones, and strategic alignment
- **Launch**: Announcement of a feature or product launch with details and impact
- **Ad-hoc**: One-off update for a specific situation (escalation, pivot, major decision)

### 2. Determine Audience

Ask who the update is for:
- **Executives / leadership**: High-level, outcome-focused, strategic framing, brief
- **Engineering team**: Technical detail, implementation context, blockers, decisions needed
- **Cross-functional partners**: Context-appropriate detail, focus on shared goals and dependencies
- **Customers / external**: Benefits-focused, clear timelines, no internal jargon
- **Board**: Metrics-driven, strategic, risk-focused, very concise

### 3. Pull Context from Connected Tools

If **project tracker** is connected:
- Pull status of roadmap items and milestones
- Identify completed items since last update
- Surface items that are at risk or blocked
- Pull sprint or iteration progress

If **chat** is connected:
- Search for relevant team discussions and decisions
- Find blockers or issues raised in channels
- Identify key decisions made asynchronously

If **meeting transcription** is connected:
- Pull recent meeting notes and discussion summaries
- Find decisions and action items from relevant meetings

If **knowledge base** is connected:
- Search for recent meeting notes
- Find decision documents or design reviews

If no tools are connected, ask the user to provide:
- What was accomplished since the last update
- Current blockers or risks
- Key decisions made or needed
- What is coming next

### 4. Generate the Update

Structure the update for the target audience. See the **stakeholder-comms** skill for detailed templates, G/Y/R status definitions, and the ROAM risk communication framework.

**For executives**: TL;DR, status color (G/Y/R), key progress tied to goals, decisions made, risks with mitigation, specific asks, and next milestones. Keep it under 300 words.

**For engineering**: What shipped (with links), what is in progress (with owners), blockers, decisions needed (with options and recommendation), and what is coming next.

**For cross-functional partners**: What is coming that affects them, what you need from them (with deadlines), decisions that impact their team, and areas open for input.

**For customers**: What is new (framed as benefits), what is coming soon, known issues with workarounds, and how to provide feedback. No internal jargon.

**For launch announcements**: What launched, why it matters, key details (scope, availability, limitations), success metrics, rollout plan, and feedback channels.

### 5. Review and Deliver

After generating the update:
- Ask if the user wants to adjust tone, detail level, or emphasis
- Offer to format for the delivery channel (email, chat post, doc, slides)
- If **chat** is connected, offer to draft the message for sending

## Output Format

Keep updates scannable. Use bold for key points, bullets for lists. Executive updates should be under 300 words. Engineering updates can be longer but should still be structured for skimming.

## Tips

- The most common mistake in stakeholder updates is burying the lead. Start with the most important thing.
- Status colors (Green/Yellow/Red) should reflect reality, not optimism. Yellow is not a failure — it is good risk communication.
- Asks should be specific and actionable. "We need help" is not an ask. "We need a decision on X by Friday" is.
- For executives, frame everything in terms of outcomes and goals, not activities and tasks.
- If there is bad news, lead with it. Do not hide it after good news.
- Match the length to the audience's attention. Executives get a few bullets. Engineering gets the details they need.

## Auto-Pull Context

Sources checked automatically, in order of priority:

```text
# Sources (checked in order):
1. Linear MCP → open issues, sprint progress, blockers
2. Slack MCP → recent channel activity, mentions of blockers
3. GitHub MCP → PR status, deployment status
4. Git log → recent commits summary
5. Memory → saved project milestones
```

If a source is unavailable (MCP not connected), skip it silently and move to the next. If none are available, fall back to asking the user directly (see Workflow step 3).

## Status Indicators

Use the G/Y/R (Green/Yellow/Red) system consistently across all updates:

| Status | Color | Criteria |
| --- | --- | --- |
| **Green** | On Track | On track, no blockers, milestones hit on schedule, metrics within targets |
| **Yellow** | At Risk | Minor delays (< 1 week), risks identified but mitigation plan exists, needs monitoring |
| **Red** | Blocked | Blocked or behind schedule (> 1 week), needs escalation, no clear path to resolution without help |

Rules for status assignment:

- Default to Yellow if unsure — it signals awareness without alarm
- Never use Green if there are unresolved blockers, even minor ones
- Red requires a specific ask: what is needed, from whom, by when
- Status should reflect the overall project health, not just the last sprint
- If multiple workstreams exist, provide per-workstream status AND an overall roll-up

## Export Formats

After generating the update, offer to export in the appropriate format:

| Format | Use Case | Details |
| --- | --- | --- |
| **Email** | Formal distribution | Markdown converted to HTML, includes subject line suggestion, CC recommendations |
| **Slack message** | Team channels | Formatted with Slack mrkdwn syntax (`*bold*`, `>` quotes, `:emoji:` status icons) |
| **Presentation slide** | Exec review meetings | Single-slide summary: title, G/Y/R badge, 3-5 bullet points, key metric, one ask |
| **Notion page** | Documentation / async review | Structured page via Notion MCP with database properties (Status, Date, Author, Audience) |

When exporting:

- Email: wrap in clean HTML, add "Reply with questions" CTA
- Slack: use `:large_green_circle:` / `:large_yellow_circle:` / `:red_circle:` for status
- Slides: keep to ONE slide, max 6 lines, font size readable from 3 meters
- Notion: tag with project name, date, and audience for future searchability

## Cadence Templates

### Weekly (Team-Focused)

Target audience: engineering team, direct managers, cross-functional partners.

```markdown
Subject: [Project] Weekly Update — {date} — {G/Y/R}

## TL;DR
{1-2 sentence summary}

## Status: {GREEN/YELLOW/RED}

## Completed This Week
- {item 1} (owner, link)
- {item 2} (owner, link)

## In Progress
- {item 1} — {% complete, ETA}
- {item 2} — {% complete, ETA}

## Blockers / Risks
- {blocker} — impact: {what}, needed: {action from whom by when}

## Decisions Made
- {decision} — rationale: {why}

## Next Week Plan
- {item 1} (owner)
- {item 2} (owner)

## Asks
- {specific ask with deadline}
```

### Bi-Weekly (Milestone-Focused)

Target audience: managers, project sponsors, adjacent team leads.

```markdown
Subject: [Project] Bi-Weekly Update — {date range} — {G/Y/R}

## Executive Summary
{3-4 sentences: where we are vs. plan, key wins, key risks}

## Milestone Progress
| Milestone | Target Date | Status | Notes |
|-----------|-------------|--------|-------|
| {name}    | {date}      | {G/Y/R}| {1-liner} |

## Key Accomplishments (2 weeks)
- {accomplishment tied to a milestone or OKR}

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| {risk} | H/M/L | H/M/L | {plan} |

## Upcoming Milestones (next 2 weeks)
- {milestone} — {date} — {owner}

## Decisions Needed
- {decision} — options: {A vs B} — recommend: {X} — needed by: {date}
```

### Monthly (Strategic / Executive)

Target audience: executives, board members, C-suite stakeholders.

```markdown
Subject: [Project] Monthly Report — {month year} — {G/Y/R}

## Status: {GREEN/YELLOW/RED}

## One-Line Summary
{Single sentence: are we on track to hit the quarterly goal?}

## Key Metrics
| Metric | Target | Actual | Trend |
|--------|--------|--------|-------|
| {metric} | {target} | {actual} | {up/down/flat} |

## Strategic Highlights
- {win tied to company goal}
- {win tied to company goal}

## Risks Requiring Attention
- {risk} — ask: {what is needed from leadership}

## Budget / Resource Status
{On budget / Over by X% / Need additional {resource}}

## Next Month Outlook
- {key milestone or deliverable}
- {key milestone or deliverable}

## One Ask
{The single most important thing you need from this audience}
```

Choose the template based on cadence. Adapt sections as needed — not every section is required every time. Remove empty sections rather than writing "N/A".
