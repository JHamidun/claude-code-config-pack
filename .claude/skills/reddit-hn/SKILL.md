---
name: reddit-hn
description: Search Reddit and Hacker News for technology opinions, trends, and discussions. Use for social research on tech topics.
---

# Reddit & Hacker News Research

Search developer communities for opinions, trends, and discussions.

## Sources

### Reddit
Use WebSearch with site filter:
```
WebSearch: "site:reddit.com [topic] [year]"
```

Key subreddits:
- r/programming, r/webdev, r/javascript, r/python
- r/devops, r/sysadmin, r/selfhosted
- r/MachineLearning, r/artificial
- r/startups, r/SaaS, r/Entrepreneur

### Hacker News
Use Algolia HN Search API:
```
WebFetch: https://hn.algolia.com/api/v1/search?query=[topic]&tags=story
Prompt: "Extract top discussions about [topic] with scores and comment counts"
```

Or via WebSearch:
```
WebSearch: "site:news.ycombinator.com [topic]"
```

## Research Templates

### Technology Comparison
```
1. Search: "[tech A] vs [tech B] site:reddit.com 2025 2026"
2. Search HN: same query
3. Aggregate: pros/cons from community
4. Output: balanced comparison with sources
```

### Problem/Bug Research
```
1. Search: "[error message] site:reddit.com"
2. Search: "[error message] site:news.ycombinator.com"
3. Search: "[error message] site:stackoverflow.com"
4. Synthesize solutions
```

### Trend Analysis
```
1. Search: "[technology] site:reddit.com" (sort by relevance)
2. HN API: tags=story, sorted by points
3. Analyze sentiment over time
4. Report: trending up/down/stable
```

## Output Format

```markdown
# Community Research: [topic]

## Summary
[2-3 sentence overview of community sentiment]

## Key Opinions

### Positive
- [opinion + source link]

### Negative/Concerns
- [concern + source link]

### Neutral/Nuanced
- [balanced view + source link]

## Recommendations
[Based on community consensus]

## Sources
- [links to discussions]
```

## Notes
- Always include source links
- Distinguish between popular opinion and expert opinion
- Note recency of discussions (old opinions may be outdated)
- Reddit/HN can be biased — note potential biases
