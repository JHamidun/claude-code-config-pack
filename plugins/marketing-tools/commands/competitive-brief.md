---
description: Create a competitive analysis brief for one or more competitors or a feature area
argument-hint: "<competitor or feature area>"
---

# Competitive Brief

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Create a competitive analysis brief for one or more competitors or a feature area.

## Usage

```text
/competitive-brief $ARGUMENTS
```

## Workflow

### 1. Scope the Analysis

Ask the user:

- **Competitor(s)**: Which specific competitor(s) to analyze? Or a feature area to compare across competitors?
- **Focus**: Full product comparison, specific feature area, pricing/packaging, go-to-market, or positioning?
- **Context**: What decision will this inform? (product strategy, sales enablement, investor/board materials, feature prioritization)

### 2. Research

**Via web search**:

- Product pages and feature lists
- Pricing pages and packaging
- Recent product launches, blog posts, and changelogs
- Press coverage and analyst reports
- Customer reviews and ratings (G2, Capterra, TrustRadius)
- Job postings (signal of strategic direction)
- Social media and community discussions

If **knowledge base** is connected:

- Search for existing competitive analysis documents
- Find win/loss reports or sales battle cards
- Pull prior competitive research

If **chat** is connected:

- Search for competitive mentions in sales or product channels
- Find recent deal feedback involving competitors

### 3. Generate the Brief

#### Competitor Overview

For each competitor:

- Company summary: founding, size, funding/revenue if public, target market
- Product positioning: how they describe themselves, who they target
- Recent momentum: launches, funding, partnerships, customer wins

#### Feature Comparison

Compare capabilities across key areas relevant to the analysis. See the **competitive-analysis** skill for rating frameworks and comparison matrix templates.

#### Positioning Analysis

Analyze how each competitor positions themselves — target customer, category claim, key differentiator, and value proposition. See the **competitive-analysis** skill for positioning analysis frameworks.

#### Strengths and Weaknesses

For each competitor:

- **Strengths**: Where they genuinely excel. What customers praise.
- **Weaknesses**: Where they fall short. What customers complain about.
- Be honest and evidence-based — do not dismiss competitors or inflate their weaknesses.

#### Opportunities

Based on the analysis:

- Where are there gaps in competitor offerings we could exploit?
- What are customers asking for that no one provides well?
- Where are competitors making bets we disagree with?
- What market shifts could advantage our approach?

#### Threats

- Where are competitors investing heavily?
- What competitive moves could disrupt our position?
- Where are we most vulnerable?
- What would a "nightmare scenario" competitive move look like?

#### Strategic Implications

Tie the analysis back to product strategy:

- What should we build, accelerate, or deprioritize based on this analysis?
- Where should we differentiate vs. achieve parity?
- How should we adjust positioning or messaging?
- What should we monitor going forward?

### 4. Follow Up

After generating the brief:

- Ask if the user wants to dive deeper on any section
- Offer to create a one-page summary for executives
- Offer to create sales battle cards for competitive deals
- Offer to draft a "how to win against [competitor]" guide
- Offer to set up a monitoring plan for competitive moves

## Output Format

Use tables for feature comparisons. Use clear headers for each section. Keep the strategic implications section concise and actionable — this is where the value is for the reader.

## Tips

- Be honest about competitor strengths. Dismissing competitors makes the analysis useless.
- Focus on what matters to customers, not what matters to product teams. Customers do not care about architecture elegance.
- Pricing is hard to compare fairly. Note the caveats (different packaging, usage-based vs seat-based, enterprise custom pricing).
- Job postings are underrated competitive intelligence. A competitor hiring ML engineers signals a strategic direction.
- Customer reviews are gold. They reveal what real users love and hate, unfiltered by marketing.
- The most valuable part of competitive analysis is the "so what" — the strategic implications. Do not skip this.
- Competitive analysis has a shelf life. Note the date and flag areas that change quickly.

## Live Research Automation

Automate data collection before manual analysis begins.

### Firecrawl MCP (website scraping)

Use `mcp__firecrawl__*` tools to extract structured data from competitor websites:

- **Pricing page**: scrape tiers, prices, feature gates, trial/freemium details
- **Features page**: extract feature lists, compare with our capabilities
- **About/positioning**: founding story, mission statement, target audience language
- **Changelog/blog**: recent launches, feature velocity, strategic bets

```text
mcp__firecrawl__firecrawl_scrape_url → competitor pricing/features pages
mcp__firecrawl__firecrawl_extract → structured extraction (pricing tiers, feature lists)
```

### Web Search (news & signals)

Use brave-search MCP or web search for real-time intelligence:

- `"[competitor name]" funding OR acquisition OR partnership` — recent deals
- `"[competitor name]" launch OR release OR announce` — product launches (last 90 days)
- `"[competitor name]" careers OR hiring` — job postings as strategic signals
- `site:g2.com "[competitor name]" reviews` — aggregate G2 sentiment
- `site:capterra.com "[competitor name]"` — Capterra ratings and complaints

### Review Aggregation

For G2/Capterra/TrustRadius reviews, extract:

- Overall rating and number of reviews
- Top 3 praised features (what they do well)
- Top 3 complaints (where they fail)
- Recent review trend (improving or declining?)
- Enterprise vs SMB sentiment split if visible

### Job Postings Analysis

Search `"[competitor] careers"` or `site:linkedin.com/jobs "[competitor]"`:

- Count roles by department (Engineering, Sales, Marketing, ML/AI)
- Identify new teams being built (signals new product lines)
- Note seniority distribution (leadership hires = strategic shift)
- Tech stack mentions in job descriptions (architecture signals)

## Knowledge Base Integration

Leverage existing knowledge before starting from scratch.

### Memory Search

```bash
# Search vector memory for prior competitive intel
/memory-search [competitor name]
/memory-search "[competitor] pricing"
/memory-search "[competitor] weaknesses"
```

### Notion MCP

If Notion MCP is connected (`mcp__notion__*`):

- Search for existing competitive analysis docs
- Find win/loss reports from sales
- Pull prior battle cards or feature comparisons
- Check if there is a competitive intelligence workspace/database

### Save Findings

After completing the brief, persist key findings:

```bash
# Save to vector memory for future reference
python ~/.claude/tools/vector_memory.py learn "[competitor]: [key finding]" "project"
```

Save these data points specifically:

- Pricing tiers and changes (with date)
- Feature gaps we identified
- Strategic direction signals
- Win/loss insights

## Signal Detection

Track these competitive signals as leading indicators of strategy changes.

### Hiring Signals

- **ML/AI engineers**: building AI features or infrastructure
- **Enterprise sales**: moving upmarket
- **Developer relations**: building ecosystem/community play
- **Compliance/security**: targeting regulated industries
- **International roles**: geographic expansion

### Pricing Changes

- Price increase → monetization pressure or premium positioning
- Price decrease → market share grab or competitive response
- New free tier → land-and-expand strategy shift
- Usage-based pivot → aligning with consumption trends

### Feature Launches

- Core product improvements → defending existing position
- Adjacent features → platform expansion strategy
- API/integrations → ecosystem play
- AI features → following market trend vs. genuine differentiation

### Leadership Changes

- New CEO → potential strategy pivot
- New CTO → technical direction shift
- New VP Sales → go-to-market change
- Departures → potential instability or disagreement

### Funding Rounds

- Seed/Series A → early, still finding PMF
- Series B/C → scaling, product-market fit validated
- Late stage/PE → optimizing for profitability
- Down round → trouble, possible fire sale or pivot
- No new funding in 2+ years → bootstrapped/profitable OR struggling

## Output Enhancement

Generate actionable deliverables beyond the analysis brief.

### Battlecard (1-pager for sales)

| Section                | Content                                                   |
| ---------------------- | --------------------------------------------------------- |
| **Who they are**       | 2-3 sentence overview                                     |
| **Their strengths**    | Top 3 genuine advantages                                  |
| **Their weaknesses**   | Top 3 exploitable gaps                                    |
| **Our advantages**     | Top 3 differentiators vs this competitor                   |
| **Landmines to set**   | Questions to ask prospects that highlight their weaknesses |
| **Objection handling** | "They say X, we say Y" for top 3 objections               |
| **When we lose**       | Honest assessment of deals we lose and why                 |
| **When we win**        | Patterns in deals we win against them                      |

### Feature Comparison Matrix

Generate a clear comparison table:

```markdown
| Feature Area | Us | Competitor A | Competitor B |
| --- | --- | --- | --- |
| Feature 1 | ✅ | ✅ | ❌ |
| Feature 2 | ✅ | ⚠️ (partial) | ✅ |
| Feature 3 | ❌ | ✅ | ✅ |
```

Legend: ✅ = fully supported, ⚠️ = partial/limited, ❌ = not available

Include notes column for important caveats (e.g., "requires Enterprise plan", "beta only", "via integration").

### Win/Loss Talking Points

Prepare for sales team:

**When competing against [Competitor]:**

- **Lead with**: our top 2-3 differentiators relevant to this competitor
- **Avoid**: areas where they are genuinely stronger (do not invite comparison)
- **Ask the prospect**: discovery questions that expose competitor weaknesses
- **Proof points**: customer stories, case studies, or data that support our position
- **Pricing response**: how to handle "they are cheaper" or "they offer more for less"
