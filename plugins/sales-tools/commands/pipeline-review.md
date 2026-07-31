---
description: Analyze pipeline health — prioritize deals, flag risks, get a weekly action plan
argument-hint: "<segment or rep>"
---

# /pipeline-review

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Analyze your pipeline health, prioritize deals, and get actionable recommendations for where to focus.

## Usage

```
/pipeline-review [segment or rep]
```

Review pipeline for: $ARGUMENTS

If a file is referenced: @$1

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE REVIEW                              │
├─────────────────────────────────────────────────────────────────┤
│  STANDALONE (always works)                                       │
│  ✓ Upload CSV export from your CRM                              │
│  ✓ Or paste/describe your deals                                 │
│  ✓ Health check: flag stale, stuck, and at-risk deals          │
│  ✓ Prioritization: rank deals by impact and closability        │
│  ✓ Hygiene audit: missing data, bad close dates, single-thread │
│  ✓ Weekly action plan: what to focus on                        │
├─────────────────────────────────────────────────────────────────┤
│  SUPERCHARGED (when you connect your tools)                      │
│  + CRM: Pull pipeline automatically, update records             │
│  + Activity data for engagement scoring                         │
│  + Historical patterns for risk prediction                      │
│  + Calendar: See upcoming meetings per deal                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## What I Need From You

**Option A: Upload a CSV**
Export your pipeline from your CRM (e.g. Salesforce, HubSpot). Helpful fields:
- Deal/Opportunity name
- Account name
- Amount
- Stage
- Close date
- Created date
- Last activity date
- Owner (if reviewing a team)
- Primary contact

**Option B: Paste your deals**
```
Acme Corp - $50K - Negotiation - closes MMM DD - last activity Jan 20
TechStart - $25K - Demo scheduled - closes Feb 15 - no activity in 3 weeks
BigCo - $100K - Discovery - closes Mar 30 - created last week
```

**Option C: Describe your pipeline**
"I have 12 deals. Two big ones in negotiation that I'm confident about. Three stuck in discovery for over a month. The rest are mid-stage but I haven't talked to some of them in a while."

---

## Output

```markdown
# Pipeline Review: [Date]

**Data Source:** [CSV upload / Manual input / CRM]
**Deals Analyzed:** [X]
**Total Pipeline Value:** $[X]

---

## Pipeline Health Score: [X/100]

| Dimension | Score | Issue |
|-----------|-------|-------|
| **Stage Progression** | [X]/25 | [X] deals stuck in same stage 30+ days |
| **Activity Recency** | [X]/25 | [X] deals with no activity in 14+ days |
| **Close Date Accuracy** | [X]/25 | [X] deals with close date in past |
| **Contact Coverage** | [X]/25 | [X] deals single-threaded |

---

## Priority Actions This Week

### 1. [Highest Priority Deal]
**Why:** [Reason — large, closing soon, at risk, etc.]
**Action:** [Specific next step]
**Impact:** $[X] if you close it

### 2. [Second Priority]
**Why:** [Reason]
**Action:** [Next step]

### 3. [Third Priority]
**Why:** [Reason]
**Action:** [Next step]

---

## Deal Prioritization Matrix

### Close This Week (Focus Time Here)
| Deal | Amount | Stage | Close Date | Next Action |
|------|--------|-------|------------|-------------|
| [Deal] | $[X] | [Stage] | [Date] | [Action] |

### Close This Month (Keep Warm)
| Deal | Amount | Stage | Close Date | Status |
|------|--------|-------|------------|--------|
| [Deal] | $[X] | [Stage] | [Date] | [Status] |

### Nurture (Check-in Periodically)
| Deal | Amount | Stage | Close Date | Status |
|------|--------|-------|------------|--------|
| [Deal] | $[X] | [Stage] | [Date] | [Status] |

---

## Risk Flags

### Stale Deals (No Activity 14+ Days)
| Deal | Amount | Last Activity | Days Silent | Recommendation |
|------|--------|---------------|-------------|----------------|
| [Deal] | $[X] | [Date] | [X] | [Re-engage / Downgrade / Remove] |

### Stuck Deals (Same Stage 30+ Days)
| Deal | Amount | Stage | Days in Stage | Recommendation |
|------|--------|-------|---------------|----------------|
| [Deal] | $[X] | [Stage] | [X] | [Push / Multi-thread / Qualify out] |

### Past Close Date
| Deal | Amount | Close Date | Days Overdue | Recommendation |
|------|--------|------------|--------------|----------------|
| [Deal] | $[X] | [Date] | [X] | [Update date / Push to next quarter / Close lost] |

### Single-Threaded (Only One Contact)
| Deal | Amount | Contact | Risk | Recommendation |
|------|--------|---------|------|----------------|
| [Deal] | $[X] | [Name] | Champion leaves = deal dies | [Identify additional stakeholders] |

---

## Hygiene Issues

| Issue | Count | Deals | Action |
|-------|-------|-------|--------|
| Missing close date | [X] | [List] | Add realistic close dates |
| Missing amount | [X] | [List] | Estimate or qualify |
| Missing next step | [X] | [List] | Define next action |
| No primary contact | [X] | [List] | Assign contact |

---

## Pipeline Shape

### By Stage
| Stage | # Deals | Value | % of Pipeline |
|-------|---------|-------|---------------|
| [Stage] | [X] | $[X] | [X]% |

### By Close Month
| Month | # Deals | Value |
|-------|---------|-------|
| [Month] | [X] | $[X] |

### By Deal Size
| Size | # Deals | Value |
|------|---------|-------|
| $100K+ | [X] | $[X] |
| $50K-100K | [X] | $[X] |
| $25K-50K | [X] | $[X] |
| <$25K | [X] | $[X] |

---

## Recommendations

### This Week
1. [ ] [Specific action for priority deal 1]
2. [ ] [Action for at-risk deal]
3. [ ] [Hygiene task]

### This Month
1. [ ] [Strategic action]
2. [ ] [Pipeline building if needed]

---

## Deals to Consider Removing

These deals may be dead weight:

| Deal | Amount | Reason | Recommendation |
|------|--------|--------|----------------|
| [Deal] | $[X] | [No activity 60+ days, no response] | Mark closed-lost |
| [Deal] | $[X] | [Pushed 3+ times, no champion] | Qualify out |
```

---

## Prioritization Framework

I'll rank your deals using this framework:

| Factor | Weight | What I Look For |
|--------|--------|-----------------|
| **Close Date** | 30% | Deals closing soonest get priority |
| **Deal Size** | 25% | Bigger deals = more focus |
| **Stage** | 20% | Later stage = more focus |
| **Activity** | 15% | Active deals get prioritized |
| **Risk** | 10% | Lower risk = safer bet |

You can tell me to weight differently: "Focus on big deals over soon deals" or "I need quick wins, prioritize close dates."

---

## If CRM Connected

- I'll pull your pipeline automatically
- Update records with new close dates, stages, next steps
- Create follow-up tasks
- Track hygiene improvements over time

---

## Health Scoring Algorithm

Each deal receives a **Health Score (0-100)** calculated from four dimensions:

```
Health Score = Stage Age Score (30%) + Activity Recency Score (30%)
             + Deal Size Score (20%) + Next Steps Score (20%)
```

### Dimension Formulas

| Dimension | Formula | Max Points |
|-----------|---------|------------|
| **Stage Age** | `max(0, 30 - (days_in_stage / avg_stage_duration) * 15)` | 30 |
| **Activity Recency** | `max(0, 30 - (days_since_last_activity * 2))` | 30 |
| **Deal Size** | `20 * (deal_amount / pipeline_median_amount)` capped at 20 | 20 |
| **Next Steps Defined** | 20 if next step exists with date, 10 if next step without date, 0 if none | 20 |

### Stage Age Score Details

- `ratio = days_in_stage / avg_days_for_this_stage`
- ratio <= 1.0: full 30 points (on track)
- ratio 1.0-2.0: linear decay from 30 to 15
- ratio 2.0-3.0: linear decay from 15 to 0
- ratio > 3.0: 0 points (stuck)

### Activity Recency Score Details

- 0 days ago: 30 points
- 1-7 days: 28-16 points (linear decay)
- 8-14 days: 15-2 points (linear decay)
- 15+ days: 0 points (stale)

### Color Coding

| Score | Color | Label | Meaning |
|-------|-------|-------|---------|
| 70-100 | Green | Healthy | Deal is progressing well |
| 40-69 | Yellow | At Risk | Needs attention this week |
| 0-39 | Red | Critical | Immediate intervention required |

### Aggregate Pipeline Health

```
Pipeline Health = weighted_avg(deal_scores, weights=deal_amounts)
```

Weighted by deal size so large at-risk deals pull the score down more than small ones.

---

## Deal Velocity Metrics

### Average Days Per Stage

Track how long deals typically spend in each stage to establish baselines:

| Stage | Avg Days | Median Days | P90 Days | Deals Measured |
|-------|----------|-------------|----------|----------------|
| Discovery | [X] | [X] | [X] | [X] |
| Demo/Evaluation | [X] | [X] | [X] | [X] |
| Proposal | [X] | [X] | [X] | [X] |
| Negotiation | [X] | [X] | [X] | [X] |
| Closed Won | [X] | [X] | [X] | [X] |

### Conversion Rates Between Stages

```
Stage Conversion Rate = deals_exiting_to_next_stage / deals_entering_stage
```

| Transition | Conversion Rate | Trend (vs last quarter) |
|------------|----------------|------------------------|
| Lead -> Discovery | [X]% | [up/down/flat] |
| Discovery -> Demo | [X]% | [up/down/flat] |
| Demo -> Proposal | [X]% | [up/down/flat] |
| Proposal -> Negotiation | [X]% | [up/down/flat] |
| Negotiation -> Closed Won | [X]% | [up/down/flat] |
| **Overall Win Rate** | [X]% | [up/down/flat] |

### Deal Velocity Formula

```
Deal Velocity = (number_of_deals * avg_deal_size * win_rate) / avg_sales_cycle_days
```

This tells you how much revenue your pipeline generates per day.

### Stuck Deals Detection

A deal is **stuck** when it exceeds **2x the average time** for its current stage:

```
is_stuck = days_in_current_stage > (2 * avg_days_for_stage)
severity = days_in_current_stage / avg_days_for_stage  # 2.0 = stuck, 3.0+ = critical
```

| Severity | Multiplier | Action |
|----------|-----------|--------|
| Warning | 1.5x - 2.0x | Check in, verify deal is alive |
| Stuck | 2.0x - 3.0x | Escalate, multi-thread, reassess |
| Dead weight | 3.0x+ | Qualify out or close lost |

---

## Risk Flags

Automatic detection rules applied to every deal in the pipeline. Each flag adds to a **Risk Score** that feeds into prioritization.

### Flag Definitions

| # | Risk Flag | Detection Rule | Severity | Points |
|---|-----------|---------------|----------|--------|
| 1 | **No activity 14+ days** | `last_activity_date < today - 14` | High | +25 |
| 2 | **No next steps defined** | `next_step IS NULL OR next_step = ''` | High | +20 |
| 3 | **Champion left the company** | LinkedIn/CRM shows contact departed, or email bounced | Critical | +30 |
| 4 | **Budget not confirmed** | Stage >= Proposal AND `budget_confirmed = false` | Medium | +15 |
| 5 | **Decision date pushed >2 times** | `close_date_change_count > 2` | High | +25 |
| 6 | **Single-threaded** | Only 1 contact associated with deal | Medium | +15 |
| 7 | **No meeting scheduled** | No calendar event in next 14 days for deal contacts | Medium | +10 |
| 8 | **Ghosted after proposal** | Stage = Proposal AND no reply to last 2+ outreach | Critical | +30 |
| 9 | **Competitor mentioned** | Notes contain competitor names with no counter-strategy | Low | +10 |
| 10 | **Close date in the past** | `expected_close_date < today` | High | +20 |

### Risk Score Interpretation

```
Total Risk = sum(applicable_flag_points)
```

| Risk Score | Level | Action Required |
|------------|-------|-----------------|
| 0-15 | Low | No immediate action |
| 16-35 | Medium | Review this week |
| 36-55 | High | Action within 48 hours |
| 56+ | Critical | Same-day intervention |

### Champion Left Detection

When detected (via bounced email, LinkedIn change, or CRM update):
1. Identify new stakeholders immediately
2. Request warm intro from other contacts
3. If no path to new champion within 7 days, downgrade deal stage
4. Flag for potential close-lost if no engagement in 14 days

### Decision Date Push Tracking

```
push_count = number_of_times close_date was moved forward
avg_push_days = total_days_pushed / push_count
```

- 1 push: normal, things happen
- 2 pushes: yellow flag, verify commitment
- 3+ pushes: red flag, deal may be dead or deprioritized by buyer

---

## Integration

### Your CRM: Pull Pipeline Data

Use the `crm` skill to automatically pull deal data:

```bash
# Pull all deals from a specific pipeline/category
# Skill: your-crm-skill (custom)

# Key Your CRM CRM methods:
# crm.deal.list     — fetch deals with filters (STAGE_ID, ASSIGNED_BY_ID, etc.)
# crm.deal.get      — single deal details
# crm.status.list   — pipeline stages and their semantics
# crm.activity.list — activities (calls, emails, meetings) linked to deals
# crm.contact.list  — contacts associated with deals
# crm.timeline.comment.list — deal timeline/history
```

**Data mapping (Your CRM -> Pipeline Review):**

| Pipeline Review Field | CRM Field |
|----------------------|----------------|
| Deal name | `TITLE` |
| Amount | `OPPORTUNITY` |
| Stage | `STAGE_ID` (resolve via `crm.status.list`) |
| Close date | `CLOSEDATE` |
| Created date | `DATE_CREATE` |
| Last activity | `LAST_ACTIVITY_TIME` or latest from `crm.activity.list` |
| Owner | `ASSIGNED_BY_ID` (resolve via `user.get`) |
| Primary contact | `CONTACT_ID` (resolve via `crm.contact.get`) |

**Refresh cadence:** Pull fresh data at the start of each `/pipeline-review` run. Cache for 15 minutes if running multiple analyses.

### Linear: Create Action Items for At-Risk Deals

When deals are flagged as **High** or **Critical** risk, automatically create Linear issues:

```
# Linear issue creation for at-risk deals:
# - Project: "Sales Ops" or user-specified
# - Label: "pipeline-risk"
# - Priority: maps from risk level (Critical -> Urgent, High -> High)
# - Assignee: deal owner
# - Due date: 48h for Critical, 7d for High
```

**Issue template:**

```markdown
Title: [PIPELINE] {Deal Name} — {Primary Risk Flag}

**Deal:** {Deal Name}
**Amount:** ${Amount}
**Stage:** {Stage}
**Health Score:** {Score}/100 ({Color})
**Risk Flags:** {comma-separated list of triggered flags}

**Required Actions:**
- [ ] {Action based on primary risk flag}
- [ ] {Action based on secondary risk flag}
- [ ] Update deal status in CRM after action

**Context:** Auto-generated by /pipeline-review on {date}
```

**Escalation flow:**
1. Critical risk -> Linear issue (Urgent) + Slack DM to deal owner
2. High risk -> Linear issue (High priority)
3. Medium risk -> Noted in review, no auto-creation (unless user opts in)

---

## Tips

1. **Review weekly** — Pipeline health decays fast. Weekly reviews catch issues early.
2. **Kill dead deals** — Stale opportunities inflate your pipeline and distort forecasts. Be ruthless.
3. **Multi-thread everything** — If one person goes dark, you need a backup contact.
4. **Close dates should mean something** — A close date is when you expect signature, not when you hope for one.
