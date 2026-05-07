# Meta Ads Analysis Checklist

Step-by-step template for analyzing Meta Ads performance. Follow in order.

## Step 1: Data Collection

### Required Data Points

| Metric | Where to Find | Period |
|--------|--------------|--------|
| Campaign spend | Ads Manager → Columns: Performance | Last 7d, 14d, 30d |
| Conversions by type | Ads Manager → Columns: Conversions | Same periods |
| CPA by campaign | Calculated: Spend / Conversions | Same periods |
| Frequency | Ads Manager → Columns: Delivery | Last 7d |
| CTR (all) | Ads Manager → Columns: Performance | Last 7d, 14d |
| CPM | Ads Manager → Columns: Performance | Last 7d, 14d |
| ROAS | Ads Manager → Columns: Conversions | Last 7d, 14d, 30d |
| Breakdown data | Ads Manager → Breakdown menu | Last 7d |

### Data Format

User should provide as CSV export or screenshot. For CSV:
```
Campaign Name, Spend, Impressions, Clicks, CTR, CPC, Conversions, CPA, ROAS
```

## Step 2: Health Check

### 2.1 Budget Efficiency

| Check | Green | Yellow | Red |
|-------|-------|--------|-----|
| Budget utilization | >90% spent | 70-90% spent | <70% spent |
| CPA vs target | <100% target | 100-130% target | >130% target |
| ROAS vs target | >100% target | 70-100% target | <70% target |
| Frequency (7d) | <2 | 2-4 | >4 |

### 2.2 Learning Phase Status

For each ad set:
- [ ] Has exited learning phase (50+ conversions/week)?
- [ ] If learning limited — identify cause (see core_concepts.md)
- [ ] Any recent edits that reset learning?

### 2.3 Account-Level Metrics

| Metric | Benchmark | Your Value | Status |
|--------|-----------|------------|--------|
| Account CPM | Industry-specific | ___ | |
| Account CTR | 1-3% (varies) | ___ | |
| Account CVR | 2-10% (varies) | ___ | |
| Overall ROAS | Business-specific | ___ | |

## Step 3: Breakdown Analysis (CAREFUL — Breakdown Effect!)

### MANDATORY: Read breakdown_effect.md before this step

### 3.1 Evaluate Each Breakdown

For each dimension (age, gender, placement, device):

| Question | If YES | If NO |
|----------|--------|-------|
| Is sample size sufficient (>30 conversions per segment)? | Proceed | Do not draw conclusions |
| Are CPA differences >20% between segments? | Investigate further | Normal variance, skip |
| Has this pattern persisted >2 weeks? | Likely real pattern | May be noise |

### 3.2 Breakdown Evaluation Table

Fill in for each dimension analyzed:

| Dimension | Segments | Conv/Segment | CPA Range | Spread | Verdict |
|-----------|----------|-------------|-----------|--------|---------|
| Age | 18-24, 25-34, 35-44, 45+ | ___each | $___-$___ | ___% | |
| Gender | M, F | ___each | $___-$___ | ___% | |
| Placement | Feed, Stories, Reels, etc. | ___each | $___-$___ | ___% | |
| Device | Mobile, Desktop | ___each | $___-$___ | ___% | |

**Spread** = (Max CPA - Min CPA) / Average CPA × 100

**Verdict options**:
- **No action**: Spread <20% or insufficient data
- **Monitor**: Spread 20-50%, sufficient data, pattern <2 weeks
- **Test**: Spread >50%, sufficient data, pattern >2 weeks → run scale test

### 3.3 Scale Test Protocol

Before any audience changes:
1. Increase budget to "best" segment by 20%
2. Run for 7 days
3. Compare marginal CPA (not average CPA)
4. If marginal CPA rises significantly → Breakdown Effect confirmed → revert

## Step 4: Creative Analysis

### 4.1 Creative Performance Matrix

| Creative | Spend Share | Conv Share | CPA | CTR | Thumb-stop | Hook Rate |
|----------|-----------|-----------|-----|-----|------------|-----------|
| Ad 1 | ___% | ___% | $___ | ___% | ___% | ___% |
| Ad 2 | ___% | ___% | $___ | ___% | ___% | ___% |
| ... | | | | | | |

**Thumb-stop rate** = 3-second video views / Impressions
**Hook rate** = Video watches past 25% / Impressions

### 4.2 Creative Decisions

| Creative Status | Action |
|----------------|--------|
| High spend, high conversions, low CPA | Keep, scale |
| High spend, low conversions, high CPA | Replace |
| Low spend, any performance | Insufficient data, needs more budget |
| Declining CTR over time | Creative fatigue, prepare replacement |

## Step 5: Recommendations

### Priority Framework

| Priority | Criteria | Examples |
|----------|----------|---------|
| **P0 (Immediate)** | Losing money, critical errors | Broken tracking, wrong audience, budget overspend |
| **P1 (This week)** | Significant inefficiency | High-CPA ad sets, learning limited resolution |
| **P2 (Next sprint)** | Optimization opportunities | Creative refresh, audience expansion |
| **P3 (Backlog)** | Nice-to-have improvements | Testing new formats, attribution model changes |

### Recommendation Template

For each recommendation:

```
**Issue**: [What's wrong]
**Evidence**: [Data points supporting this]
**Recommendation**: [Specific action]
**Expected Impact**: [CPA reduction %, ROAS improvement %, etc.]
**Risk**: [What could go wrong]
**Timeline**: [When to implement and when to evaluate]
```

## Step 6: Report Rules (MANDATORY)

1. **Always state the Breakdown Effect caveat** when presenting segment data
2. **Never recommend audience exclusions** based solely on breakdown CPA
3. **Include confidence levels**: High (>100 conversions), Medium (30-100), Low (<30)
4. **Show period comparisons**: WoW, MoM trends, not just snapshots
5. **Separate correlation from causation**: "Segment X has higher CPA" ≠ "Segment X causes high CPA"
6. **Provide action items, not just observations**: Every insight must have a recommended action
