# Workflow: Research

> Глубокое исследование темы, компании, человека или технологии

## Keywords
`research`, `найти`, `изучить`, `analyze`, `investigate`, `dig into`

## Inputs
- **task**: описание задачи из Todoist
- **target**: что исследуем (topic | company | person | technology)
- **depth**: quick (5 min) | standard (15 min) | deep (30+ min)
- **output**: summary | report | decision_brief | competitive_analysis

## Steps

### 1. Define Research Scope
```
Questions to answer:
- What specifically do I need to know?
- What decisions will this inform?
- What's the minimum viable answer?
- What depth is actually needed?
```

### 2. Source Selection
```
By target type:

## Person Research
- LinkedIn (career, connections)
- Twitter/X (opinions, interests)
- Google (articles, talks)
- Crunchbase (if entrepreneur)
- YouTube (talks, interviews)
- Podcast appearances

## Company Research
- Official site
- Crunchbase (funding, team)
- LinkedIn (employees, growth)
- G2/Capterra (if SaaS)
- News (recent events)
- Glassdoor (culture)
- SEC filings (if public)

## Topic Research
- Perplexity (overview + citations)
- Academic papers (if technical)
- Industry reports
- Expert blogs
- Reddit/communities
- YouTube explainers

## Technology Research
- Official docs
- GitHub (stars, activity, issues)
- Stack Overflow (problems, adoption)
- Hacker News (opinions)
- Comparison articles
- Case studies
```

### 3. Execute Research (Parallel)
```
Tool: Perplexity + WebFetch + Memory search

Run in parallel:
- Primary source search
- Secondary source search
- Memory MCP for existing knowledge
```

### 4. Synthesize Findings
```
Template:

# Research: [Target]
Date: [date]
Depth: [quick|standard|deep]

## TL;DR
[2-3 sentence summary]

## Key Findings
1. [Finding 1 + source]
2. [Finding 2 + source]
3. [Finding 3 + source]

## Implications
- [What this means for our goals]

## Gaps / Unknowns
- [What we still don't know]
- [Where to look next]

## Sources
- [Source 1]
- [Source 2]

## Raw Notes
[Optional: detailed notes]
```

### 5. Save to Memory
```
Tool: Memory MCP
Save:
- Key facts
- Relationships discovered
- Insights for future reference
```

## Quality Checks
- [ ] Scope чётко определён
- [ ] Minimum 3 sources использовано
- [ ] Findings отвечают на изначальный вопрос
- [ ] Bias checked (не только one-sided info)
- [ ] Sources credible и recent
- [ ] Saved to Memory для future use

## Completion Criteria
- Research document создан
- Key findings summarized
- Saved to Memory MCP
- Todoist task updated

## Time Estimate by Depth
- **Quick**: 5-10 minutes (overview only)
- **Standard**: 15-20 minutes (solid understanding)
- **Deep**: 30-60 minutes (comprehensive)

## Research Depth Guide

### Quick (5 min)
- 1-2 sources
- Top-level overview
- Good for: quick decisions, context

### Standard (15 min)
- 3-5 sources
- Key facts + implications
- Good for: most business decisions

### Deep (30+ min)
- 5-10+ sources
- Multiple perspectives
- Counter-arguments explored
- Good for: major decisions, investments

## Output Formats

### Summary (1 page)
For: quick reference, sharing

### Report (3-5 pages)
For: team alignment, documentation

### Decision Brief (1-2 pages)
For: specific decision support
```
## Decision: [question]

### Option A: [name]
Pros: ...
Cons: ...
Risk: ...

### Option B: [name]
Pros: ...
Cons: ...
Risk: ...

### Recommendation
[What and why]
```

### Competitive Analysis
For: market positioning
```
## Competitor: [name]

Strengths: ...
Weaknesses: ...
Positioning: ...
Pricing: ...
Our advantage: ...
```

## Tools Integration

### Perplexity (Primary)
- Quick answers with citations
- Good for: overview, fact-checking
- Use: /ai-search или /deep-research

### Memory MCP
- Past research recall
- Connection discovery
- Use: Check before new research

### WebFetch
- Specific page analysis
- Use: When Perplexity insufficient

## Notes
- Always check Memory first (may have relevant past research)
- Cite sources for credibility
- Note confidence level (high/medium/low)
- Update Memory with new findings
- Set expiry for time-sensitive info
