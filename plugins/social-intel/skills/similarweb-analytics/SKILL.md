---
name: similarweb-analytics
description: "Analyze website traffic and engagement metrics using web search and public SimilarWeb data — traffic estimates, rankings, engagement stats, traffic sources, geographic distribution. Use for domain analysis and competitive web analytics."
type: actionable
---

# SimilarWeb Analytics

Website traffic and engagement analysis using web search + public SimilarWeb data.

## Strategy

Manus uses internal SimilarWeb API. We adapt by:
1. **WebSearch** for SimilarWeb data on target domain
2. **WebFetch** to scrape public SimilarWeb pages
3. **Fallback**: alternative free tools (Semrush, Ahrefs free tier)

## Quick Start

```bash
# Run analysis script
python ~/.claude/skills/similarweb-analytics/scripts/similarweb.py analyze example.com

# Compare domains
python ~/.claude/skills/similarweb-analytics/scripts/similarweb.py compare example.com,competitor.com
```

## Core Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| Total Visits | Monthly traffic estimate | SimilarWeb public page |
| Unique Visitors | Deduplicated visitor count | SimilarWeb / search |
| Bounce Rate | % single-page sessions | SimilarWeb public page |
| Pages per Visit | Average depth | SimilarWeb public page |
| Avg Visit Duration | Time on site | SimilarWeb public page |
| Global Rank | Worldwide ranking | SimilarWeb public page |
| Country Rank | Country-specific ranking | SimilarWeb public page |

## Traffic Sources

| Channel | Description |
|---------|-------------|
| Direct | Type-in traffic |
| Organic Search | SEO traffic |
| Paid Search | PPC advertising |
| Social | Social media referrals |
| Referral | Links from other sites |
| Display | Banner ads |
| Email | Email marketing |

## Analysis Workflow

### Step 1: Gather Data

```python
# Use WebSearch to find SimilarWeb data
search_query = f"similarweb {domain} traffic 2026"

# Use WebFetch on public SimilarWeb page
url = f"https://www.similarweb.com/website/{domain}/"
```

### Step 2: Parse Key Metrics

Extract from search results and web pages:
- Monthly visits (with trend)
- Bounce rate
- Pages per visit
- Visit duration
- Traffic sources breakdown
- Top countries

### Step 3: Competitive Analysis

Compare against competitors:
- Relative traffic share
- Source mix differences
- Geographic overlap
- Engagement comparison

### Step 4: Report

Create structured report with:
- Executive summary
- Traffic overview (trend chart data)
- Source breakdown
- Geographic distribution
- Competitive comparison
- Recommendations

## When to Use

**Trigger words:** "similarweb", "website traffic", "domain analysis", "how popular is", "traffic sources", "посещаемость", "трафик сайта", "аналитика сайта", "конкуренты"

## Limitations

- Public SimilarWeb data may be limited (requires paid plan for full API)
- Traffic estimates are approximations
- Data freshness: typically 1-2 months lag
- Small sites (<50K monthly visits) may have limited data

## Alternative Data Sources

If SimilarWeb data is unavailable:
- **Semrush** (free tier): domain overview, traffic analytics
- **Ahrefs** (free tier): backlink data, organic keywords
- **Google Trends**: relative search interest
- **BuiltWith**: technology stack analysis
