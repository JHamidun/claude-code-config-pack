---
description: Run a comprehensive SEO audit — keyword research, on-page analysis, content gaps, technical checks, and competitor comparison
argument-hint: "<url or topic> [audit type]"
---

# /seo-audit

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Audit a website's SEO health, research keyword opportunities, identify content gaps, and benchmark against competitors. Produces a prioritized action plan a marketer can execute immediately.

## Trigger

User runs `/seo-audit` or asks for an SEO audit, keyword research, content gap analysis, technical SEO check, or competitor SEO comparison.

## Inputs

Gather the following from the user. If not provided, ask before proceeding:

1. **URL or domain** — the site to audit, or a topic/keyword if running in keyword research mode

2. **Audit type** — one of:
   - **Full site audit** — end-to-end SEO review covering all sections below
   - **Keyword research** — identify keyword opportunities for a topic or domain
   - **Content gap analysis** — find topics competitors rank for that you don't
   - **Technical SEO check** — crawlability, speed, structured data, and infrastructure issues
   - **Competitor SEO comparison** — head-to-head SEO benchmarking against specific competitors

   If not specified, default to **full site audit**.

3. **Target keywords or topics** (optional) — specific keywords the user is already targeting or wants to rank for

4. **Competitors** (optional) — domains or companies to compare against. If not provided and the audit type requires competitor data, use web search to identify 2-3 likely competitors based on the user's domain and keyword space.

## Process

### 1. Keyword Research

Research keywords related to the user's domain, topic, or target keywords.

**If SEO tools are connected:**
- Pull keyword data, search volume, keyword difficulty scores, and ranking positions automatically
- Identify keywords the site currently ranks for and where it's gaining or losing ground

**If product analytics are connected:**
- Cross-reference keyword targets with actual organic traffic data to validate which keywords are driving visits and conversions

**If tools are not connected:**
- Use web search to research the keyword landscape
- Note: "For more precise volume and difficulty data, connect an SEO tool like Ahrefs or Semrush via MCP. The audit will auto-populate with ranking data."

For each keyword opportunity, assess:
- **Primary keywords** — high-intent terms directly tied to the user's product or service
- **Secondary keywords** — supporting terms and variations
- **Search volume signals** — relative demand (high, medium, low) based on available data
- **Keyword difficulty** — how competitive the term is (easy, moderate, hard)
- **Long-tail opportunities** — specific, lower-competition phrases with clear intent
- **Question-based keywords** — "how to", "what is", "why does" queries that mirror People Also Ask results
- **Intent classification** — informational, navigational, commercial, or transactional

### 2. On-Page SEO Audit

For each key page (homepage, top landing pages, recent blog posts), evaluate:

- **Title tags** — present, unique, within 50-60 characters, includes target keyword
- **Meta descriptions** — present, compelling, within 150-160 characters, includes a call to action
- **H1 tags** — exactly one per page, includes primary keyword
- **H2/H3 structure** — logical hierarchy, uses secondary keywords where natural
- **Keyword usage** — primary keyword appears in the first 100 words, used naturally throughout, not over-stuffed
- **Internal linking** — pages link to related content, orphan pages identified, anchor text is descriptive
- **Image alt text** — all images have descriptive alt attributes, keywords included where relevant
- **URL structure** — clean, readable, includes keywords, no excessive parameters or depth

### 3. Content Gap Analysis

Identify what's missing from the user's content strategy:

- **Competitor topic coverage** — topics and keywords competitors rank for that the user's site does not cover
- **Content freshness** — pages that haven't been updated in 12+ months and may be losing rankings
- **Thin content** — pages with insufficient depth to rank (under 300 words for informational queries, lacking substance)
- **Missing content types** — formats competitors use that the user doesn't (guides, comparison pages, glossaries, tools, templates)
- **Funnel gaps** — missing content at specific buyer journey stages (awareness, consideration, decision)
- **Topic clusters** — opportunities to build pillar pages with supporting content

### 4. Technical SEO Checklist

Evaluate technical foundations that affect crawlability and rankings:

- **Page speed** — identify slow-loading pages and likely causes (large images, render-blocking scripts, excessive redirects)
- **Mobile-friendliness** — responsive design, tap targets, font sizes, viewport configuration
- **Structured data** — opportunities for schema markup (FAQ, HowTo, Product, Article, Organization, Breadcrumb)
- **Crawlability** — robots.txt configuration, XML sitemap presence and accuracy, canonical tags, noindex/nofollow usage
- **Broken links** — internal and external 404s, redirect chains
- **HTTPS** — secure connection, mixed content issues
- **Core Web Vitals signals** — LCP, FID/INP, CLS indicators based on observable page behavior
- **Indexation** — pages that should be indexed but may not be, duplicate content risks

### 5. Competitor SEO Comparison

For each competitor, compare:

- **Keyword overlap** — keywords both sites rank for, and where each site ranks higher
- **Keyword gaps** — terms the competitor ranks for that the user does not
- **Domain authority signals** — relative site strength based on backlink profiles, referring domains, and content depth
- **Content depth** — average content length, topic coverage breadth, publishing frequency
- **Backlink profile observations** — types of sites linking to competitors, link-worthy content they've produced
- **SERP feature ownership** — which competitor appears in featured snippets, People Also Ask, image packs, or knowledge panels
- **Technical advantages** — site speed differences, mobile experience, structured data usage

## Output

### Executive Summary

Open with a 3-5 sentence summary of overall SEO health. Highlight:
- The site's biggest strength
- The top 3 priorities that will have the most impact
- An overall assessment: strong foundation, needs work, or critical issues

### Keyword Opportunity Table

| Keyword | Est. Difficulty | Opportunity Score | Current Ranking | Intent | Recommended Content Type |
|---------|----------------|-------------------|-----------------|--------|--------------------------|

Opportunity score: high, medium, or low — based on the combination of search demand, difficulty, and relevance to the user's business.

Include 15-25 keyword opportunities, sorted by opportunity score.

### On-Page Issues Table

| Page | Issue | Severity | Recommended Fix |
|------|-------|----------|-----------------|

Severity levels:
- **Critical** — directly hurting rankings or preventing indexation
- **High** — significant impact on SEO performance
- **Medium** — best practice violation, moderate impact
- **Low** — minor optimization opportunity

### Content Gap Recommendations

For each content gap identified, provide:
- **Topic or keyword** to target
- **Why it matters** — search demand, competitor coverage, funnel stage
- **Recommended format** — blog post, landing page, guide, comparison page, etc.
- **Priority** — high, medium, or low
- **Estimated effort** — quick win (1-2 hours), moderate (half day), substantial (multi-day)

### Technical SEO Checklist

| Check | Status | Details |
|-------|--------|---------|

Status: Pass, Fail, or Warning.

### Competitor Comparison Summary

| Dimension | Your Site | Competitor A | Competitor B | Winner |
|-----------|-----------|--------------|--------------|--------|

Include rows for: keyword count, content depth, publishing frequency, backlink signals, technical score, SERP feature presence.

### Prioritized Action Plan

Split recommendations into two categories:

**Quick Wins (do this week):**
- Actions that take under 2 hours and have immediate impact
- Examples: fix title tags, add meta descriptions, fix broken links, add alt text

**Strategic Investments (plan for this quarter):**
- Actions that require more effort but drive long-term growth
- Examples: build a topic cluster, create a pillar page, launch a link-building campaign, overhaul site structure

For each action item, include:
- What to do (specific and concrete)
- Expected impact (high, medium, low)
- Effort estimate
- Dependencies (if any)

## Technical SEO Automation

When MCP tools are available, automate data collection before manual analysis.

### Site Crawl via Firecrawl

Use Firecrawl MCP to crawl the target site and extract on-page SEO elements:

```
mcp__firecrawl__crawl({url: "https://example.com", limit: 50})
```

From the crawl results, automatically extract and tabulate:
- **Title tags** — presence, length, uniqueness across pages
- **Meta descriptions** — presence, length, duplicate detection
- **H1 tags** — count per page, missing H1s, duplicate H1s across pages
- **Broken links** — internal 404s, external dead links, redirect chains (3xx)
- **Image alt text** — missing alt attributes, empty alt on non-decorative images
- **Canonical tags** — missing, self-referencing, conflicting canonicals
- **Hreflang tags** — presence and correctness for multilingual sites
- **Open Graph / Twitter cards** — missing social meta tags

If Firecrawl is unavailable, fall back to `mcp__firecrawl__scrape` on individual pages (homepage, top 5 landing pages) or use web search to gather publicly available data.

### Lighthouse Audit via Chrome DevTools

Run a Lighthouse audit for comprehensive performance and SEO scoring:

```
mcp__chrome-devtools__lighthouse_audit({url: "https://example.com"})
```

Extract from Lighthouse results:
- **SEO score** (0-100) — overall on-page SEO health
- **Performance score** (0-100) — page speed and rendering
- **Accessibility score** (0-100) — a11y issues that also affect SEO
- **Best Practices score** (0-100) — security, modern web standards
- **Specific audits**: missing meta description, invalid hreflang, non-crawlable links, illegible font sizes, tap targets too small

Run Lighthouse for both **mobile** and **desktop** configurations. Mobile results take priority since Google uses mobile-first indexing.

### Automated Data Aggregation

Combine crawl + Lighthouse data into a unified table before analysis:

| Page URL | Title (len) | Meta Desc (len) | H1 Count | Broken Links | Missing Alt | Lighthouse SEO | Lighthouse Perf |
|----------|-------------|-----------------|----------|--------------|-------------|----------------|-----------------|

Flag any page where:
- Title is missing or > 60 chars
- Meta description is missing or > 160 chars
- H1 count != 1
- Broken links > 0
- Lighthouse SEO < 90
- Lighthouse Performance < 50

## Keyword Analysis

### Current Rankings Check

Use web search and Firecrawl to assess current keyword positions:

1. **Site search query**: `site:example.com` — estimate indexed page count
2. **Brand search**: search the brand name — check if the site owns Position 1
3. **Target keyword searches**: for each provided keyword, check if the site appears in top 20 results
4. **SERP feature presence**: note featured snippets, People Also Ask, knowledge panels, image/video packs

```
# Check indexation
mcp__firecrawl__scrape({url: "https://www.google.com/search?q=site:example.com"})

# Check keyword ranking
mcp__firecrawl__scrape({url: "https://www.google.com/search?q=target+keyword"})
```

If scraping SERPs is blocked, use web search tool as fallback and note approximate positions.

### Competitor Keyword Gap Analysis

For each identified competitor:

1. **Crawl competitor site** (limit: 20 pages) to extract their title tags and H1s — these reveal their target keywords
2. **Compare keyword sets**: your site's target keywords vs competitor's target keywords
3. **Identify gaps**: keywords competitors target that you do not cover at all
4. **Identify overlaps**: keywords both target — who ranks higher and why

Present as a gap matrix:

| Keyword | Your Site | Competitor A | Competitor B | Gap Type |
|---------|-----------|--------------|--------------|----------|
| keyword1 | Ranks #8 | Ranks #3 | Not ranking | Improvement |
| keyword2 | Not ranking | Ranks #5 | Ranks #2 | New opportunity |
| keyword3 | Ranks #1 | Ranks #4 | Ranks #7 | Defend |

Gap types:
- **New opportunity** — you don't target it, competitors do (high priority)
- **Improvement** — you rank but competitors rank higher (medium priority)
- **Defend** — you rank higher, monitor for competitor gains (low priority)

### Content Opportunity Scoring

Score each keyword opportunity on a 1-10 scale using three factors:

| Factor | Weight | How to Assess |
|--------|--------|---------------|
| **Relevance** | 40% | How closely the keyword matches the user's product/service/audience |
| **Difficulty** | 30% | Inverse: easy keywords score higher. Based on SERP competition, domain authority of ranking sites |
| **Potential traffic** | 30% | Based on search volume signals, SERP click-through likelihood, seasonal trends |

**Opportunity Score** = (Relevance x 0.4) + (Inverse Difficulty x 0.3) + (Traffic Potential x 0.3)

Classify:
- **8-10**: High priority — create content immediately
- **5-7**: Medium priority — plan for next quarter
- **1-4**: Low priority — backlog, revisit later

## Core Web Vitals Check

### Thresholds (Google's Standards)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | <= 2.5s | 2.5s - 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | <= 200ms | 200ms - 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | <= 0.1 | 0.1 - 0.25 | > 0.25 |

> Note: INP replaced FID (First Input Delay) as of March 2024. If tools still report FID, note that INP is the current standard. Good FID threshold was <= 100ms.

### Performance Trace via Chrome DevTools

Run a performance trace to measure Core Web Vitals precisely:

```
mcp__chrome-devtools__lighthouse_audit({url: "https://example.com"})
```

From the performance results, extract:
- **LCP element** — identify which element is the LCP (hero image, heading, video). Common fixes: optimize image format/size, preload LCP resource, reduce server response time
- **INP contributors** — long tasks blocking the main thread. Common fixes: defer non-critical JS, break up long tasks, use web workers
- **CLS sources** — elements shifting during load. Common fixes: set explicit width/height on images/embeds, avoid inserting content above existing content, use `font-display: swap`

### Mobile vs Desktop Comparison

Run audits for BOTH viewports and compare:

| Metric | Mobile | Desktop | Delta | Status |
|--------|--------|---------|-------|--------|
| LCP | | | | |
| INP | | | | |
| CLS | | | | |
| Performance Score | | | | |
| Speed Index | | | | |
| Time to Interactive | | | | |
| Total Blocking Time | | | | |

Flag any metric where:
- Mobile is significantly worse than desktop (delta > 30%)
- Mobile falls into "Poor" while desktop is "Good"
- Mobile Performance Score < 50

**Mobile takes priority** — Google uses mobile-first indexing. If mobile scores are poor, this is a critical issue regardless of desktop scores.

### Common CWV Issues and Fixes

| Issue | Metric Affected | Fix | Effort |
|-------|----------------|-----|--------|
| Unoptimized images (no WebP/AVIF) | LCP | Convert to modern formats, add srcset | Low |
| No image dimensions | CLS | Add width/height attributes | Low |
| Render-blocking CSS/JS | LCP, TBT | Defer non-critical resources | Medium |
| Third-party scripts (analytics, ads) | INP, TBT | Lazy-load, use Partytown | Medium |
| No font preloading | CLS, LCP | Preload critical fonts, use font-display | Low |
| Large DOM size (>1500 nodes) | INP | Simplify layout, virtualize lists | High |
| No CDN | LCP | Deploy static assets to CDN | Medium |
| Server response time > 600ms | LCP | Optimize backend, add caching | High |

## Output Format

The final SEO audit report MUST follow this structured format:

### Report Structure

```markdown
# SEO Audit Report: [domain]
**Date:** [YYYY-MM-DD]
**Audit Type:** [Full / Technical / Keywords / Content Gap / Competitor]
**Auditor:** Claude Code (automated)

---

## 1. Executive Summary
[3-5 sentences, biggest strength, top 3 priorities, overall health]

## 2. Technical SEO
### 2.1 Crawl Results
[Firecrawl/Lighthouse data tables]
### 2.2 Core Web Vitals
[Mobile + Desktop comparison table]
### 2.3 Technical Issues
[Issues table with severity]

## 3. Content Analysis
### 3.1 On-Page SEO
[Title tags, meta descriptions, H1s, content quality]
### 3.2 Content Gaps
[Missing topics, thin pages, freshness issues]
### 3.3 Content Recommendations
[New content to create, updates to make]

## 4. Keyword Opportunities
### 4.1 Current Rankings
[What the site ranks for now]
### 4.2 Keyword Gap Analysis
[What competitors rank for that you don't]
### 4.3 Opportunity Table
[Full keyword table with scores]

## 5. Performance
### 5.1 Core Web Vitals (Mobile)
[LCP, INP, CLS with status]
### 5.2 Core Web Vitals (Desktop)
[LCP, INP, CLS with status]
### 5.3 Performance Recommendations
[Specific fixes with expected impact]

## 6. Priority Matrix
[Impact vs Effort grid]

## 7. Action Items
[Ordered list with estimated impact]
```

### Priority Matrix (Impact vs Effort)

Categorize every recommendation into this 2x2 matrix:

| | Low Effort | High Effort |
|---|---|---|
| **High Impact** | **DO FIRST** (quick wins) | **PLAN** (strategic investments) |
| **Low Impact** | **BATCH** (do when convenient) | **SKIP** (not worth it now) |

Present as a table:

| Action | Impact | Effort | Quadrant | Est. Time |
|--------|--------|--------|----------|-----------|
| Fix missing meta descriptions | High | Low | DO FIRST | 1-2 hours |
| Build topic cluster for [keyword] | High | High | PLAN | 2-3 weeks |
| Add alt text to blog images | Low | Low | BATCH | 30 min |
| Rebuild site architecture | Low | High | SKIP | 1+ month |

### Action Items with Estimated Impact

Every action item MUST include:

1. **What**: specific, concrete action (not vague advice)
2. **Why**: which metric or ranking it improves
3. **Impact**: High / Medium / Low — with reasoning
4. **Effort**: time estimate (hours or days)
5. **Priority**: 1 (do now) through 5 (backlog)
6. **Dependencies**: what needs to happen first (if any)

Example:

| # | Action | Impact | Effort | Priority | Dependencies |
|---|--------|--------|--------|----------|-------------|
| 1 | Compress hero images to WebP, add width/height | High — fixes LCP + CLS on 80% of pages | 2 hours | 1 | None |
| 2 | Write meta descriptions for top 10 landing pages | High — improves CTR from SERPs | 3 hours | 1 | Keyword research |
| 3 | Create pillar page for "[main keyword]" | High — captures 5K+ monthly searches | 3-5 days | 2 | Content brief |
| 4 | Add FAQ schema to product pages | Medium — may win FAQ snippets | 4 hours | 3 | None |
| 5 | Set up 301 redirects for 12 broken URLs | Medium — recovers link equity | 1 hour | 1 | Access to server/CMS |

## Follow-Up

After presenting the audit, ask:

"Would you like me to:
- Draft content briefs for the top keyword opportunities?
- Create optimized title tags and meta descriptions for your key pages?
- Build a content calendar based on the gap analysis?
- Dive deeper into any specific section of the audit?
- Run this same analysis for a different competitor or domain?"
