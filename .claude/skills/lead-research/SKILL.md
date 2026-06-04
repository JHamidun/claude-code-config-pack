---
name: lead-research
description: Identify and qualify high-quality leads, prospect research, ICP matching
---

# Lead Research Skill

## Overview

Идентификация и квалификация лидов, исследование потенциальных клиентов, соответствие ICP.

## When to Use

- Поиск потенциальных клиентов
- Квалификация лидов
- Account research
- ICP (Ideal Customer Profile) matching
- Sales intelligence

## ICP Definition Template

```markdown
# Ideal Customer Profile

## Company Characteristics
- **Industry:** [e.g., SaaS, E-commerce, Fintech]
- **Company Size:** [e.g., 50-500 employees]
- **Revenue:** [e.g., $5M-$50M ARR]
- **Funding Stage:** [e.g., Series A-C]
- **Location:** [e.g., US, Europe, Global]
- **Tech Stack:** [e.g., Uses AWS, Python, React]

## Buyer Persona
- **Title:** [e.g., VP of Engineering, CTO]
- **Department:** [e.g., Engineering, Product]
- **Reports to:** [e.g., CEO, COO]
- **Team Size:** [e.g., 10-50 engineers]

## Pain Points
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

## Buying Triggers
- [Trigger 1: e.g., Just raised funding]
- [Trigger 2: e.g., Hiring rapidly]
- [Trigger 3: e.g., Announced new product]

## Disqualifiers
- [Red flag 1]
- [Red flag 2]
```

## Lead Scoring Model

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Lead:
    company_name: str
    industry: str
    employee_count: int
    revenue: Optional[float]
    funding_stage: str
    tech_stack: list
    contact_title: str
    contact_email: str

class LeadScorer:
    def __init__(self, icp: dict):
        self.icp = icp

    def score(self, lead: Lead) -> dict:
        """Score lead against ICP (0-100)"""
        scores = {}
        total_weight = 0

        # Industry match (weight: 25)
        if lead.industry in self.icp['industries']:
            scores['industry'] = 25
        else:
            scores['industry'] = 0
        total_weight += 25

        # Company size (weight: 20)
        min_size, max_size = self.icp['employee_range']
        if min_size <= lead.employee_count <= max_size:
            scores['size'] = 20
        elif lead.employee_count < min_size * 0.5 or lead.employee_count > max_size * 2:
            scores['size'] = 0
        else:
            scores['size'] = 10
        total_weight += 20

        # Funding stage (weight: 15)
        if lead.funding_stage in self.icp['funding_stages']:
            scores['funding'] = 15
        else:
            scores['funding'] = 5
        total_weight += 15

        # Tech stack match (weight: 20)
        tech_overlap = len(set(lead.tech_stack) & set(self.icp['tech_stack']))
        scores['tech'] = min(20, tech_overlap * 5)
        total_weight += 20

        # Title match (weight: 20)
        if any(title.lower() in lead.contact_title.lower()
               for title in self.icp['target_titles']):
            scores['title'] = 20
        else:
            scores['title'] = 5
        total_weight += 20

        # Calculate total
        total = sum(scores.values())
        grade = 'A' if total >= 80 else 'B' if total >= 60 else 'C' if total >= 40 else 'D'

        return {
            'scores': scores,
            'total': total,
            'grade': grade,
            'qualified': total >= 60
        }
```

## Research Sources

### Public Data

| Source | Data Type | Access |
|--------|-----------|--------|
| LinkedIn | Company info, employees | Free/Premium |
| Crunchbase | Funding, investors | Free/Paid |
| BuiltWith | Tech stack | Free/Paid |
| SimilarWeb | Traffic, competitors | Free/Paid |
| Glassdoor | Culture, reviews | Free |
| G2/Capterra | Product reviews | Free |
| Press releases | News, announcements | Free |

### Data Enrichment APIs

```python
import requests

def enrich_company(domain: str, api_key: str) -> dict:
    """Enrich company data using Clearbit-like API"""
    response = requests.get(
        f"https://api.your-enrichment.example/v2/companies/find",
        params={"domain": domain},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.json()

def enrich_person(email: str, api_key: str) -> dict:
    """Enrich person data"""
    response = requests.get(
        f"https://api.your-enrichment.example/v2/people/find",
        params={"email": email},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.json()
```

## Research Template

```markdown
# Company Research: [Company Name]

## Basic Info
- **Website:** [URL]
- **Industry:** [Industry]
- **Founded:** [Year]
- **HQ:** [Location]
- **Employees:** [Count]
- **LinkedIn:** [URL]

## Financials
- **Revenue (est.):** $[X]M
- **Funding:** $[X]M total
- **Latest Round:** [Stage] - $[X]M ([Date])
- **Investors:** [List]

## Tech Stack
- **Frontend:** [Technologies]
- **Backend:** [Technologies]
- **Cloud:** [AWS/GCP/Azure]
- **Other:** [Tools]

## Key People
| Name | Title | LinkedIn |
|------|-------|----------|
| [Name] | [Title] | [URL] |

## Recent News
- [Date]: [News item]
- [Date]: [News item]

## Hiring Signals
- Open roles: [Number]
- Key hires: [Recent notable hires]
- Growing teams: [Departments]

## Pain Points (Inferred)
1. [Based on job postings]
2. [Based on tech stack]
3. [Based on company stage]

## Competitive Landscape
- **Main Competitors:** [List]
- **Differentiation:** [How they position]

## Qualification
- **ICP Match:** [Score]/100
- **Fit Grade:** [A/B/C/D]
- **Buying Stage:** [Awareness/Consideration/Decision]
- **Priority:** [High/Medium/Low]

## Outreach Strategy
- **Best Contact:** [Name, Title]
- **Hook:** [Relevant pain point]
- **Personalization:** [Specific detail to reference]
```

## Lead List Building

```python
import csv
from dataclasses import asdict

def build_lead_list(leads: list[Lead], scorer: LeadScorer, output_file: str):
    """Build and score lead list"""

    scored_leads = []
    for lead in leads:
        score_result = scorer.score(lead)
        scored_leads.append({
            **asdict(lead),
            'score': score_result['total'],
            'grade': score_result['grade'],
            'qualified': score_result['qualified']
        })

    # Sort by score
    scored_leads.sort(key=lambda x: x['score'], reverse=True)

    # Export to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=scored_leads[0].keys())
        writer.writeheader()
        writer.writerows(scored_leads)

    # Summary
    qualified = [l for l in scored_leads if l['qualified']]
    print(f"Total leads: {len(scored_leads)}")
    print(f"Qualified leads: {len(qualified)}")
    print(f"A-grade: {len([l for l in scored_leads if l['grade'] == 'A'])}")

    return scored_leads
```

## Outreach Personalization

```python
def generate_personalization(research: dict) -> dict:
    """Generate personalization points for outreach"""

    hooks = []

    # Recent funding
    if research.get('recent_funding'):
        hooks.append(f"Congrats on the {research['recent_funding']} raise!")

    # Recent news
    if research.get('recent_news'):
        hooks.append(f"Saw the news about {research['recent_news']}")

    # Hiring signals
    if research.get('hiring_roles'):
        hooks.append(f"Noticed you're hiring {research['hiring_roles']}")

    # Mutual connections
    if research.get('mutual_connections'):
        hooks.append(f"We're both connected with {research['mutual_connections'][0]}")

    # Tech stack match
    if research.get('uses_tech'):
        hooks.append(f"Saw you're using {research['uses_tech']}")

    return {
        'hooks': hooks,
        'best_hook': hooks[0] if hooks else None,
        'pain_point': research.get('inferred_pain_point'),
        'value_prop': generate_value_prop(research)
    }
```

## CRM Integration

```python
def sync_to_crm(leads: list, crm_api_key: str):
    """Sync qualified leads to CRM"""
    import requests

    for lead in leads:
        if not lead['qualified']:
            continue

        # Create/update in CRM
        response = requests.post(
            "https://api.your-crm.example/leads",
            headers={"Authorization": f"Bearer {crm_api_key}"},
            json={
                "company": lead['company_name'],
                "contact_email": lead['contact_email'],
                "contact_title": lead['contact_title'],
                "lead_score": lead['score'],
                "source": "research",
                "status": "new"
            }
        )

        print(f"Synced: {lead['company_name']} - {response.status_code}")
```

## Tips

1. **Quality > Quantity** - лучше 10 хороших лидов чем 100 плохих
2. **Update ICP** - регулярно обновляй профиль идеального клиента
3. **Multi-source** - используй несколько источников данных
4. **Personalize** - generic outreach не работает
5. **Track signals** - следи за сигналами покупки
6. **Automate research** - автоматизируй сбор базовых данных
7. **Score consistently** - используй единую систему скоринга
