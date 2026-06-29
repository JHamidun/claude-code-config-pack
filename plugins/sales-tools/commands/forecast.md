---
description: Generate a weighted sales forecast with best/likely/worst scenarios, commit vs. upside breakdown, and gap analysis
argument-hint: "<period>"
---

# /forecast

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../CONNECTORS.md).

Generate a weighted sales forecast with risk analysis and commit recommendations.

## Usage

```
/forecast [period]
```

Generate a forecast for: $ARGUMENTS

If a file is referenced: @$1

---

## Execution Mode

### CSV Pipeline Parser

When a CSV file is provided, parse it automatically:

```bash
python -c "
import csv, json, sys, io

# Stage probability defaults
STAGE_PROBS = {
    'discovery': 0.10,
    'qualification': 0.25,
    'qualified': 0.25,
    'proposal': 0.50,
    'quote': 0.50,
    'negotiation': 0.75,
    'contract': 0.75,
    'closed won': 1.00,
    'won': 1.00,
    'closed lost': 0.00,
    'lost': 0.00,
    'prospecting': 0.05,
    'lead': 0.05,
    'demo': 0.35,
    'evaluation': 0.35,
}

def normalize_stage(stage):
    s = stage.strip().lower()
    for key in STAGE_PROBS:
        if key in s:
            return key, STAGE_PROBS[key]
    return s, 0.20  # fallback 20%

def parse_pipeline(csv_path):
    deals = []
    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Normalize headers (lowercase, strip)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        for row in reader:
            # Find amount column (amount, value, deal_value, sum, сумма)
            amount = 0
            for col in ['amount', 'value', 'deal_value', 'sum', 'сумма', 'opportunity_amount']:
                if col in row and row[col]:
                    amount = float(row[col].replace(',', '').replace(' ', '').replace('$', '').replace('₽', ''))
                    break
            # Find stage column
            stage_raw = ''
            for col in ['stage', 'status', 'deal_stage', 'стадия', 'этап']:
                if col in row and row[col]:
                    stage_raw = row[col]
                    break
            stage_name, prob = normalize_stage(stage_raw)
            # Find deal name
            name = ''
            for col in ['deal', 'name', 'opportunity', 'deal_name', 'company', 'название', 'сделка']:
                if col in row and row[col]:
                    name = row[col]
                    break
            # Find close date
            close_date = ''
            for col in ['close_date', 'close date', 'expected_close', 'дата_закрытия', 'closedate']:
                if col in row and row[col]:
                    close_date = row[col]
                    break
            deals.append({
                'name': name,
                'amount': amount,
                'stage': stage_name,
                'probability': prob,
                'weighted': amount * prob,
                'close_date': close_date,
            })
    return deals

deals = parse_pipeline(sys.argv[1])
total_value = sum(d['amount'] for d in deals)
weighted_total = sum(d['weighted'] for d in deals)

# Group by stage
stages = {}
for d in deals:
    s = d['stage']
    if s not in stages:
        stages[s] = {'count': 0, 'total': 0, 'weighted': 0, 'prob': d['probability']}
    stages[s]['count'] += 1
    stages[s]['total'] += d['amount']
    stages[s]['weighted'] += d['weighted']

print(json.dumps({
    'deals': deals,
    'stages': stages,
    'total_pipeline': total_value,
    'weighted_forecast': weighted_total,
    'deal_count': len(deals),
}, indent=2, ensure_ascii=False))
" "$CSV_FILE"
```

### Weighted Pipeline Formula

```
Weighted Value = Deal Amount x Stage Probability

Best Case  = Sum of all open deals (100% close rate)
Likely Case = Sum of weighted values (stage probabilities)
Worst Case = Sum of Negotiation + Closed Won only (commit deals)

Coverage Ratio = Total Pipeline / Quota
Gap to Quota = Quota - Closed to Date - Weighted Forecast
```

### Stage Probability Defaults (for calculations)

| Stage | Probability | Classification |
|-------|-------------|----------------|
| Prospecting / Lead | 5% | Pipeline |
| Discovery | 10% | Pipeline |
| Qualification | 25% | Pipeline |
| Demo / Evaluation | 35% | Upside |
| Proposal / Quote | 50% | Upside |
| Negotiation / Contract | 75% | Commit |
| Closed Won | 100% | Closed |
| Closed Lost | 0% | Lost |

---

## MCP Integration

### Your CRM (if available)

When Your CRM skill is connected, pull deals automatically instead of CSV:

```
1. Use skill `crm` to fetch open deals:
   - crm.deal.list with FILTER[CLOSED]=N, FILTER[CATEGORY_ID]=0
   - Fields: TITLE, OPPORTUNITY, STAGE_ID, CLOSEDATE, ASSIGNED_BY_ID, COMPANY_ID
2. Map Your CRM stages to probabilities:
   - NEW → Discovery (10%)
   - PREPARATION → Qualification (25%)
   - PREPAYMENT_INVOICE → Proposal (50%)
   - EXECUTING → Negotiation (75%)
   - WON → Closed Won (100%)
   - LOSE → Closed Lost (0%)
   - Custom stages: ask user or use 20% default
3. Pull deal history for activity-based risk scoring:
   - crm.activity.list per deal
   - Flag deals with no activity > 14 days
4. Fetch previous period closed deals for win-rate calibration:
   - crm.deal.list with FILTER[CLOSED]=Y, FILTER[>=CLOSEDATE]=period_start
```

### Google Sheets Export (if available)

After forecast generation, offer to export results:

```
1. Use command `gsheets` to create/update a forecast spreadsheet
2. Sheet structure:
   - Tab "Forecast Summary": quota, closed, weighted, gap, coverage
   - Tab "Pipeline Detail": all deals with stage, amount, weighted, risk flags
   - Tab "Stage Analysis": grouped by stage with counts and totals
   - Tab "Scenarios": best/likely/worst with assumptions
3. Include conditional formatting:
   - Red: deals with close date passed or no activity 14+ days
   - Yellow: deals closing this week still in early stages
   - Green: commit deals (Negotiation+)
4. Update existing sheet if forecast was previously generated (match by period name)
```

### Salesforce / HubSpot (manual CSV)

If no CRM MCP is connected but user has CRM access:

```
Salesforce: Reports → Opportunities → Export to CSV
HubSpot: Deals → All Deals → Export → CSV
Your CRM: Deals → Export → CSV
Then pass CSV path to the parser above.
```

---

## Automated Output

After parsing pipeline data (from CSV, Your CRM, or manual input), generate this structured output automatically:

### Forecast Summary Table

```markdown
## Forecast: [Period]

| Metric | Value | vs Quota |
|--------|-------|----------|
| Quota | $[target] | — |
| Closed to Date | $[closed] | [X]% |
| Open Pipeline | $[total_pipeline] | [X]x coverage |
| Weighted Forecast | $[weighted] | — |
| Projected Total | $[closed + weighted] | [X]% |
| Gap to Quota | $[gap] | — |
| Coverage Ratio | [pipeline/quota]x | [healthy/risky/critical] |
```

Coverage health: >= 3x = healthy, 2-3x = adequate, < 2x = risky, < 1x = critical.

### Scenario Calculations

```python
# Best Case: all deals close at face value
best_case = closed_to_date + sum(deal.amount for deal in open_deals)

# Likely Case: stage-weighted probabilities
likely_case = closed_to_date + sum(deal.amount * deal.probability for deal in open_deals)

# Worst Case: only commit-level deals (Negotiation + Contract, prob >= 0.75)
worst_case = closed_to_date + sum(deal.amount for deal in open_deals if deal.probability >= 0.75)

# Scenarios table
scenarios = {
    'Best':   {'amount': best_case,   'pct': best_case / quota * 100},
    'Likely': {'amount': likely_case,  'pct': likely_case / quota * 100},
    'Worst':  {'amount': worst_case,   'pct': worst_case / quota * 100},
}
```

### Gap Analysis (automated)

```markdown
## Gap Analysis

**Target:** $[quota]
**Current trajectory (Likely):** $[likely_case]
**Gap:** $[quota - likely_case]

### To Close the Gap:

| Option | Deals Needed | Total Value | Feasibility |
|--------|-------------|-------------|-------------|
| Accelerate existing | [N] deals from Proposal→Negotiation | $[X] | High |
| Revive stalled | [N] deals inactive 14+ days | $[X] | Medium |
| New pipeline | [N] new deals at [avg_deal_size] | $[X] at 3x coverage | Low (time) |

### Timeline Risk:
- [N] deals closing this month: $[X] weighted
- [N] deals closing next month: $[X] weighted
- [N] deals with passed close dates: $[X] — UPDATE THESE
```

### Risk Scoring (automated per deal)

Each deal gets a risk score 0-100 based on:

```
risk_score = 0
if days_since_last_activity > 14: risk_score += 30
if days_since_last_activity > 30: risk_score += 20  # additional
if close_date < today: risk_score += 40              # overdue
if close_date < today + 7 and prob < 0.50: risk_score += 25  # closing soon, early stage
if days_in_current_stage > 30: risk_score += 15      # stuck
if amount > avg_deal_size * 3: risk_score += 10       # unusually large

# Classification:
# 0-20: Low risk (green)
# 21-50: Medium risk (yellow)
# 51+: High risk (red)
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        FORECAST                                  │
├─────────────────────────────────────────────────────────────────┤
│  STANDALONE (always works)                                       │
│  ✓ Upload CSV export from your CRM                              │
│  ✓ Or paste/describe your pipeline deals                        │
│  ✓ Set your quota and timeline                                  │
│  ✓ Get weighted forecast with stage probabilities               │
│  ✓ Risk-adjusted projections (best/likely/worst case)           │
│  ✓ Commit vs. upside breakdown                                  │
│  ✓ Gap analysis and recommendations                             │
├─────────────────────────────────────────────────────────────────┤
│  SUPERCHARGED (when you connect your tools)                      │
│  + CRM: Pull pipeline automatically, real-time data             │
│  + Historical win rates by stage, segment, deal size            │
│  + Activity signals for risk scoring                            │
│  + Automatic refresh and tracking over time                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## What I Need From You

### Step 1: Your Pipeline Data

**Option A: Upload a CSV**
Export your pipeline from your CRM (e.g. Salesforce, HubSpot). I need at minimum:
- Deal/Opportunity name
- Amount
- Stage
- Close date

Helpful if you have:
- Owner (if team forecast)
- Last activity date
- Created date
- Account name

**Option B: Paste your deals**
```
Acme Corp - $50K - Negotiation - closes MMM DD
TechStart - $25K - Demo scheduled - closes Feb 15
BigCo - $100K - Discovery - closes Mar 30
```

**Option C: Describe your territory**
"I have 8 deals in pipeline totaling $400K. Two are in negotiation ($120K), three in evaluation ($180K), three in discovery ($100K)."

### Step 2: Your Targets

- **Quota**: What's your number? (e.g., "$500K this quarter")
- **Timeline**: When does the period end? (e.g., "Q1 ends March 31")
- **Already closed**: How much have you already booked this period?

---

## Output

```markdown
# Sales Forecast: [Period]

**Generated:** [Date]
**Data Source:** [CSV upload / Manual input / CRM]

---

## Summary

| Metric | Value |
|--------|-------|
| **Quota** | $[X] |
| **Closed to Date** | $[X] ([X]% of quota) |
| **Open Pipeline** | $[X] |
| **Weighted Forecast** | $[X] |
| **Gap to Quota** | $[X] |
| **Coverage Ratio** | [X]x |

---

## Forecast Scenarios

| Scenario | Amount | % of Quota | Assumptions |
|----------|--------|------------|-------------|
| **Best Case** | $[X] | [X]% | All deals close as expected |
| **Likely Case** | $[X] | [X]% | Stage-weighted probabilities |
| **Worst Case** | $[X] | [X]% | Only commit deals close |

---

## Pipeline by Stage

| Stage | # Deals | Total Value | Probability | Weighted Value |
|-------|---------|-------------|-------------|----------------|
| Negotiation | [X] | $[X] | 80% | $[X] |
| Proposal | [X] | $[X] | 60% | $[X] |
| Evaluation | [X] | $[X] | 40% | $[X] |
| Discovery | [X] | $[X] | 20% | $[X] |
| **Total** | [X] | $[X] | — | $[X] |

---

## Commit vs. Upside

### Commit (High Confidence)
Deals you'd stake your forecast on:

| Deal | Amount | Stage | Close Date | Why Commit |
|------|--------|-------|------------|------------|
| [Deal] | $[X] | [Stage] | [Date] | [Reason] |

**Total Commit:** $[X]

### Upside (Lower Confidence)
Deals that could close but have risk:

| Deal | Amount | Stage | Close Date | Risk Factor |
|------|--------|-------|------------|-------------|
| [Deal] | $[X] | [Stage] | [Date] | [Risk] |

**Total Upside:** $[X]

---

## Risk Flags

| Deal | Amount | Risk | Recommendation |
|------|--------|------|----------------|
| [Deal] | $[X] | Close date passed | Update close date or move to lost |
| [Deal] | $[X] | No activity in 14+ days | Re-engage or downgrade stage |
| [Deal] | $[X] | Close date this week, still in discovery | Unlikely to close — push out |

---

## Gap Analysis

**To hit quota, you need:** $[X] more

**Options to close the gap:**
1. **Accelerate [Deal]** — Currently [stage], worth $[X]. If you can close by [date], you're at [X]% of quota.
2. **Revive [Stalled Deal]** — Last active [date]. Worth $[X]. Reach out to [contact].
3. **New pipeline needed** — You need $[X] in new opportunities at [X]x coverage to be safe.

---

## Recommendations

1. [ ] [Specific action for highest-impact deal]
2. [ ] [Action for at-risk deal]
3. [ ] [Pipeline generation recommendation if gap exists]
```

---

## Stage Probabilities (Default)

If you don't provide custom probabilities, I'll use:

| Stage | Default Probability |
|-------|---------------------|
| Closed Won | 100% |
| Negotiation / Contract | 80% |
| Proposal / Quote | 60% |
| Evaluation / Demo | 40% |
| Discovery / Qualification | 20% |
| Prospecting / Lead | 10% |

Tell me if your stages or probabilities are different.

---

## If CRM Connected

- I'll pull your pipeline automatically
- Use your actual historical win rates
- Factor in activity recency for risk scoring
- Track forecast changes over time
- Compare to previous forecasts

---

## Tips

1. **Be honest about commit** — Only commit deals you'd bet on. Upside is for everything else.
2. **Update close dates** — Stale close dates kill forecast accuracy. Push out deals that won't close in time.
3. **Coverage matters** — 3x pipeline coverage is healthy. Below 2x is risky.
4. **Activity = signal** — Deals with no recent activity are at higher risk than stage suggests.
