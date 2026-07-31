---
description: Generate a full campaign brief with objectives, channels, content calendar, and success metrics
argument-hint: "<campaign objective or product>"
---

# Campaign Plan

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Generate a comprehensive marketing campaign brief with objectives, audience, messaging, channel strategy, content calendar, and success metrics.

## Trigger

User runs `/campaign-plan` or asks to plan, design, or build a marketing campaign.

## Inputs

Gather the following from the user. If not provided, ask before proceeding:

1. **Campaign goal** — the primary objective (e.g., drive signups, increase awareness, launch a product, generate leads, re-engage churned users)

2. **Target audience** — who the campaign is aimed at (demographics, roles, industries, pain points, buying stage)

3. **Timeline** — campaign duration and any fixed dates (launch date, event date, seasonal deadline)

4. **Budget range** — approximate budget or budget tier (optional; if not provided, generate a channel-agnostic plan and note where budget allocation would matter)

5. **Additional context** (optional):
   - Product or service being promoted
   - Key differentiators or value propositions
   - Previous campaign performance or learnings
   - Brand guidelines or constraints
   - Geographic focus

## Campaign Brief Structure

Generate a campaign brief with the following sections:

### 1. Campaign Overview
- Campaign name suggestion
- One-sentence campaign summary
- Primary objective with a specific, measurable goal
- Secondary objectives (if applicable)

### 2. Target Audience
- Primary audience segment with description
- Secondary audience segment (if applicable)
- Audience pain points and motivations
- Where they spend time (channels, communities, publications)
- Buying stage alignment (awareness, consideration, decision)

### 3. Key Messages
- Core campaign message (one sentence)
- 3-4 supporting messages tailored to audience pain points
- Message variations by channel (if different tones are needed)
- Proof points or evidence to support each message

### 4. Channel Strategy
Recommend channels based on audience and goal. For each channel, include:
- Why this channel fits the audience and objective
- Content format recommendations
- Estimated effort level (low, medium, high)
- Budget allocation suggestion (if budget was provided)

Consider channels from:
- Owned: blog, email, website, social media profiles
- Earned: PR, influencer partnerships, guest posts, community engagement
- Paid: search ads, social ads, display, sponsored content, events

### 5. Content Calendar
Create a week-by-week (or day-by-day for short campaigns) content calendar:
- What content to produce each week
- Which channel each piece targets
- Key milestones and deadlines
- Dependencies between pieces (e.g., "landing page must be live before paid ads launch")

Format as a table:

| Week | Content Piece | Channel | Owner/Notes | Status |
|------|--------------|---------|-------------|--------|

### 6. Content Pieces Needed
List every content asset required for the campaign:
- Asset name and type (blog post, email, social post, ad creative, landing page, etc.)
- Brief description of what it should contain
- Priority (must-have vs. nice-to-have)
- Suggested timeline for creation

### 7. Success Metrics
Define KPIs aligned to the campaign objective:
- Primary KPI with target number
- Secondary KPIs (3-5)
- How each metric will be tracked
- Reporting cadence recommendation

If product analytics is connected, reference any available historical performance benchmarks to inform targets.

### 8. Budget Allocation (if budget provided)
- Breakdown by channel or activity
- Production costs vs. distribution costs
- Contingency recommendation (typically 10-15%)

### 9. Risks and Mitigations
- 2-3 potential risks (timeline, audience mismatch, channel underperformance)
- Mitigation strategy for each

### 10. Next Steps
- Immediate action items to kick off the campaign
- Stakeholder approvals needed
- Key decision points

## Output

Present the full campaign brief with clear headings and formatting. After the brief, ask:

"Would you like me to:
- Dive deeper into any section?
- Draft specific content pieces from the calendar?
- Create a competitive analysis to inform the messaging?
- Adjust the plan for a different budget or timeline?"

---

## Budget Allocation Calculator

Use the following framework to allocate campaign budget across channels. Adjust splits based on campaign type and historical performance data.

### Default Channel Splits

| Channel Group | Sub-Channel | Default % | Awareness | Conversion | Retention |
|---------------|-------------|-----------|-----------|------------|-----------|
| **Digital** | **Total** | **60%** | **65%** | **55%** | **50%** |
| | Paid (Search + Social Ads) | 30% | 35% | 30% | 10% |
| | Organic (SEO, Social, Content) | 20% | 20% | 15% | 20% |
| | Email (Sequences, Newsletters) | 10% | 10% | 10% | 20% |
| **Events** | Webinars, Conferences, Meetups | **20%** | **15%** | **25%** | **20%** |
| **PR** | Media, Influencers, Guest Posts | **10%** | **15%** | **5%** | **5%** |
| **Other** | Contingency, Tools, Creative | **10%** | **5%** | **15%** | **25%** |

### Allocation Formula

For each channel, calculate the adjusted allocation:

```
channel_budget = total_budget * base_split * performance_modifier

where:
  performance_modifier = (1 / channel_CAC) / sum(1 / all_channel_CACs)
```

If historical CAC data is available per channel:
1. Rank channels by CAC (lowest = most efficient)
2. Weight allocation inversely proportional to CAC
3. Cap any single channel at 40% to avoid over-concentration
4. Ensure minimum 5% for testing new/unproven channels

If no historical data is available, use the default splits above based on campaign type.

### Budget Output Table

| Channel | Base % | Adjusted % | Budget | Expected CAC | Expected Conversions |
|---------|--------|------------|--------|--------------|---------------------|
| ... | ... | ... | ... | ... | ... |

---

## ROI Modeling

Project campaign ROI using the funnel model below. Fill in known values; estimate unknowns from industry benchmarks or historical data.

### Funnel Calculations

```
Expected Reach       = budget / CPM * 1000
Expected Clicks      = reach * CTR
Expected Conversions = clicks * conversion_rate
Expected Revenue     = conversions * avg_deal_size
Campaign ROI         = (revenue - budget) / budget * 100%
```

### Benchmark Defaults (adjust per industry)

| Metric | B2B SaaS | E-commerce | Education | Events |
|--------|----------|------------|-----------|--------|
| CPM | $15-30 | $8-20 | $10-25 | $20-40 |
| CTR | 1.5-3% | 2-4% | 2-5% | 1-2% |
| Conversion Rate | 2-5% | 1-3% | 3-7% | 5-10% |
| Avg Deal Size | $500-5000 | $50-200 | $100-1000 | $200-2000 |

### ROI Projection Table

Generate for each channel and total:

| Channel | Budget | CPM | Reach | CTR | Clicks | Conv % | Conversions | Avg Deal | Revenue | ROI % |
|---------|--------|-----|-------|-----|--------|--------|-------------|----------|---------|-------|
| Paid Search | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Social Ads | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Email | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **Total** | ... | | ... | | ... | | ... | | ... | ... |

### Scenario Analysis

Always model three scenarios:
- **Conservative**: use lower-bound benchmarks (25th percentile)
- **Base**: use median benchmarks
- **Optimistic**: use upper-bound benchmarks (75th percentile)

Present as:

| Scenario | Conversions | Revenue | ROI % | Payback Period |
|----------|-------------|---------|-------|----------------|
| Conservative | ... | ... | ... | ... |
| Base | ... | ... | ... | ... |
| Optimistic | ... | ... | ... | ... |

---

## Calendar Export

Generate a structured timeline for the campaign and offer export options.

### Milestone Timeline Table

| # | Milestone | Date | Owner | Dependencies | Status |
|---|-----------|------|-------|--------------|--------|
| 1 | Campaign kickoff | ... | ... | — | ... |
| 2 | Creative assets ready | ... | ... | #1 | ... |
| 3 | Landing page live | ... | ... | #2 | ... |
| 4 | Paid ads launch | ... | ... | #3 | ... |
| 5 | Mid-campaign review | ... | ... | #4 | ... |
| 6 | Campaign wrap-up | ... | ... | #5 | ... |
| 7 | Post-mortem & report | ... | ... | #6 | ... |

### ICS Calendar Export

For each milestone, generate an ICS event block:

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Campaign Plan//EN
BEGIN:VEVENT
DTSTART:YYYYMMDDTHHMMSSZ
DTEND:YYYYMMDDTHHMMSSZ
SUMMARY:[Campaign Name] - Milestone Name
DESCRIPTION:Details and dependencies
STATUS:TENTATIVE
END:VEVENT
END:VCALENDAR
```

Save as `campaign-<name>-milestones.ics` in the working directory.

### Google Calendar Integration

If the user wants calendar sync, use:

```
/gcalendar create-event --title "[Campaign] Milestone" --date YYYY-MM-DD --description "..."
```

Offer to batch-create all milestones as Google Calendar events.

### Gantt-Style Markdown Visualization

For visual overview, render a text-based Gantt chart:

```
Week        1    2    3    4    5    6    7    8
Creative   [====]
Landing         [===]
Paid Ads             [=================]
Email            [==]      [==]      [==]
Review                          [=]
Wrap-up                                   [==]
```

Adjust granularity (days/weeks) based on campaign duration.
