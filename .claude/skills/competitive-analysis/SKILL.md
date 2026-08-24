---
name: competitive-analysis
description: "Продуктовый анализ конкурентов: рынок, позиционирование, цены. Триггеры: «конкуренты», «конкурентная разведка». Реклама конкурентов → ad-spy."
---

# Competitive Analysis Skill

## Overview

Анализ конкурентов: исследование рынка, рекламная разведка, позиционирование.

## When to Use

- Запуск нового продукта
- Анализ конкурентной рекламы
- Стратегическое планирование
- Ценообразование
- Поиск рыночных возможностей

<!-- no-key-block -->
## Ключа SerpAPI нет — что тогда

Сам фреймворк ниже ключа не требует: это порядок работы, а не скрипт. Ключ
`SERPAPI_API_KEY` нужен ровно двум блокам кода в конце файла — сбору выдачи и
разбору чужой рекламы.

Без ключа `os.getenv("SERPAPI_API_KEY")` вернёт `None`, SerpAPI ответит
`401 Invalid API key` — из этого текста не видно, что ключа просто нет.

Чем заменить, по убыванию точности:

| Вместо | Чем | Что теряешь |
|--------|-----|-------------|
| SERP-выдача | `openserp` в Docker (`127.0.0.1:7000`, 0 кредитов) — рецепт в навыке `serpapi`, раздел «Локальная бесплатная альтернатива» | carousels, Maps, Shopping, Trends |
| SERP-выдача | встроенный в Claude Code веб-поиск | структурированные поля, позиции |
| реклама конкурентов | навык `ad-spy` (Ad Library Meta/Google/LinkedIn — свои источники, не SerpAPI) | ничего: это отдельный источник |
| позиции своего сайта | навыки `yandex` (Вебмастер) и команда `/gsearch-console` — по своим сайтам данные точнее любой выдачи | чужие сайты |

Остальные разделы навыка — позиционирование, матрица сравнения, ценовой анализ —
работают целиком без ключа.

## Competitor Research Framework

### 1. Identify Competitors

```markdown
## Direct Competitors
Компании с похожим продуктом для той же аудитории
- [Competitor 1]
- [Competitor 2]

## Indirect Competitors
Альтернативные решения той же проблемы
- [Competitor 3]
- [Competitor 4]

## Potential Competitors
Компании, которые могут войти на рынок
- [Company 5]
```

### 2. Competitor Profile Template

```markdown
# [Competitor Name]

## Overview
- Website: [URL]
- Founded: [Year]
- Employees: [Number]
- Funding: [Amount]
- HQ: [Location]

## Product
- Main product: [Description]
- Key features: [List]
- Pricing: [Tiers]
- Target market: [Segments]

## Strengths
- [Strength 1]
- [Strength 2]

## Weaknesses
- [Weakness 1]
- [Weakness 2]

## Recent News
- [News 1]
- [News 2]
```

## Ad Intelligence

> **Анализ рекламы конкурентов**: для разведки рекламных кампаний/креативов конкурентов используй `ad-spy` (Facebook/Google/LinkedIn ad libraries + российские каналы Яндекс/VK/TG + Atria для Meta-креативов с оценкой бюджета). Этот скилл — про продуктовую/рыночную конкурентную разведку, ad-spy — про рекламную.

### Sources

| Platform | How to Access |
|----------|---------------|
| **Meta Ad Library** | facebook.com/ads/library |
| **Google Ads Transparency** | adstransparency.google.com |
| **LinkedIn Ad Library** | linkedin.com/ad-library |
| **TikTok Ad Library** | library.tiktok.com |
| **Twitter/X Ads** | ads.twitter.com/transparency |

### Ad Analysis Template

```markdown
## Ad Analysis: [Competitor]

### Ad Creative
- Format: [Image/Video/Carousel]
- Visual style: [Description]
- Call-to-action: [CTA text]

### Messaging
- Headline: "[Actual headline]"
- Value proposition: [What they promise]
- Pain points addressed: [List]
- Social proof: [If any]

### Targeting (Estimated)
- Audience: [Demographics]
- Interests: [Categories]
- Stage: [Awareness/Consideration/Conversion]

### Effectiveness Signals
- Running since: [Date]
- Estimated spend: [Range]
- Multiple variations: [Yes/No]
```

## Market Positioning

### Positioning Map

```
                    High Price
                        │
          Premium       │      Luxury
        Enterprise      │      Boutique
                        │
    ────────────────────┼──────────────────
    Low Features        │      High Features
                        │
        Budget          │      Value
         Basic          │      Best Bang
                        │
                    Low Price
```

### Positioning Statement

```
For [target customer]
who [statement of need/opportunity]
our [product/service name] is a [product category]
that [statement of key benefit]
unlike [primary competitive alternative]
our product [statement of primary differentiation]
```

**Example:**
```
For busy professionals
who need to stay organized across devices
our TaskFlow is a productivity app
that syncs instantly everywhere
unlike Notion
our product is simple and focused on tasks only
```

## SWOT Analysis Template

```markdown
## SWOT: [Company Name]

### Strengths (Internal, Positive)
- [What do they do well?]
- [What resources do they have?]
- [What's their competitive advantage?]

### Weaknesses (Internal, Negative)
- [What do they do poorly?]
- [What resources do they lack?]
- [What do customers complain about?]

### Opportunities (External, Positive)
- [Market trends in their favor?]
- [Gaps they could fill?]
- [New markets they could enter?]

### Threats (External, Negative)
- [New competitors?]
- [Regulatory changes?]
- [Technology shifts?]
```

## Feature Comparison Matrix

```markdown
| Feature | Us | Competitor A | Competitor B | Competitor C |
|---------|:--:|:------------:|:------------:|:------------:|
| Feature 1 | ✅ | ✅ | ❌ | ✅ |
| Feature 2 | ✅ | ❌ | ✅ | ❌ |
| Feature 3 | ✅ | ✅ | ✅ | ❌ |
| Feature 4 | ❌ | ✅ | ❌ | ✅ |
| Pricing | $$ | $$$ | $ | $$ |
| Support | 24/7 | Business | Email | 24/7 |
```

## Pricing Intelligence

### Pricing Strategy Analysis

```markdown
## [Competitor] Pricing

### Model
- [ ] Freemium
- [ ] Free trial
- [ ] Subscription
- [ ] One-time purchase
- [ ] Usage-based
- [ ] Per-seat

### Tiers
| Tier | Price | Key Limits |
|------|-------|------------|
| Free | $0 | [Limits] |
| Basic | $X/mo | [Limits] |
| Pro | $Y/mo | [Limits] |
| Enterprise | Custom | Unlimited |

### Observations
- Anchor price: [Highest tier]
- Most pushed tier: [Which one]
- Hidden costs: [If any]
- Discounts: [Annual, etc.]
```

## Traffic & SEO Analysis

### Tools to Use

| Tool | Free Tier | Data |
|------|-----------|------|
| SimilarWeb | Yes | Traffic estimates |
| SEMrush | Limited | Keywords, traffic |
| Ahrefs | No | Backlinks, keywords |
| SpyFu | Limited | PPC keywords |
| BuiltWith | Yes | Tech stack |

### SEO Competitive Analysis

```markdown
## SEO Analysis: [Competitor]

### Domain Metrics
- Domain Authority: [Score]
- Estimated monthly traffic: [Number]
- Top traffic countries: [List]

### Top Keywords (Organic)
| Keyword | Position | Volume |
|---------|----------|--------|
| [kw1] | #[X] | [N] |
| [kw2] | #[X] | [N] |

### Content Strategy
- Blog frequency: [Posts/month]
- Top performing content: [URLs]
- Content types: [Blog, guides, tools]

### Backlink Profile
- Total backlinks: [Number]
- Referring domains: [Number]
- Top referring sites: [List]
```

## Social Listening

### Metrics to Track

```markdown
## Social Presence: [Competitor]

### Followers
| Platform | Followers | Growth |
|----------|-----------|--------|
| Twitter/X | [N] | [%/mo] |
| LinkedIn | [N] | [%/mo] |
| Instagram | [N] | [%/mo] |
| YouTube | [N] | [%/mo] |

### Engagement
- Avg likes: [N]
- Avg comments: [N]
- Posting frequency: [X/week]

### Content Themes
- [Theme 1] - [Frequency]
- [Theme 2] - [Frequency]

### Sentiment
- Positive: [%]
- Neutral: [%]
- Negative: [%]
```

## Automation with APIs

```python
# SerpAPI для SERP данных
import os
from serpapi import GoogleSearch

def analyze_competitor_seo(domain):
    params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google",
        "q": f"site:{domain}",
        "num": 100
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("organic_results", [])

# Анализ рекламы через SerpAPI
def get_competitor_ads(keyword):
    params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google",
        "q": keyword,
        "google_domain": "google.com"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("ads", [])
```

## Competitive Report Template

```markdown
# Competitive Intelligence Report

**Date:** [Date]
**Analyst:** [Name]
**Focus:** [Market/Product]

## Executive Summary
[2-3 sentences on key findings]

## Market Overview
- TAM: $[X]B
- Growth rate: [X]% CAGR
- Key trends: [List]

## Competitor Landscape
[Summary table or positioning map]

## Detailed Analysis
### [Competitor 1]
[Profile]

### [Competitor 2]
[Profile]

## Opportunities
1. [Gap they're missing]
2. [Underserved segment]
3. [Weak feature area]

## Threats
1. [Strong competitor moves]
2. [Market shifts]

## Recommendations
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]
```

## Tips

1. **Регулярность** - анализируй постоянно, не разово
2. **Первоисточники** - не полагайся только на инструменты
3. **Отзывы** - G2, Capterra, TrustPilot - голос клиентов
4. **Job postings** - вакансии показывают стратегию
5. **Не копируй** - анализируй, но делай по-своему
6. **Документируй** - веди базу конкурентной разведки
