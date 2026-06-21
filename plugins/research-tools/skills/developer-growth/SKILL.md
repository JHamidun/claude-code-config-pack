---
name: developer-growth
description: Analyze coding patterns and track developer skill progression
---

# Developer Growth Analysis Skill

## Overview

Анализ паттернов кодирования, отслеживание роста навыков, персональное развитие.

## When to Use

- Самооценка навыков
- Планирование развития
- Code review insights
- Performance review prep
- Mentoring developers

## Skills Assessment Framework

### Technical Skills Matrix

```markdown
## Technical Skills Assessment

Rate each skill 1-5:
1 = Beginner (learning)
2 = Junior (can do with guidance)
3 = Mid (independent work)
4 = Senior (can teach others)
5 = Expert (industry leader)

### Languages
| Skill | Current | Target | Gap |
|-------|---------|--------|-----|
| Python | [X] | [Y] | [Y-X] |
| JavaScript | [X] | [Y] | [Y-X] |
| TypeScript | [X] | [Y] | [Y-X] |
| Go | [X] | [Y] | [Y-X] |
| SQL | [X] | [Y] | [Y-X] |

### Frameworks
| Skill | Current | Target | Gap |
|-------|---------|--------|-----|
| React | [X] | [Y] | [Y-X] |
| Node.js | [X] | [Y] | [Y-X] |
| FastAPI | [X] | [Y] | [Y-X] |
| Django | [X] | [Y] | [Y-X] |

### Infrastructure
| Skill | Current | Target | Gap |
|-------|---------|--------|-----|
| Docker | [X] | [Y] | [Y-X] |
| Kubernetes | [X] | [Y] | [Y-X] |
| AWS | [X] | [Y] | [Y-X] |
| CI/CD | [X] | [Y] | [Y-X] |

### Practices
| Skill | Current | Target | Gap |
|-------|---------|--------|-----|
| TDD | [X] | [Y] | [Y-X] |
| Code Review | [X] | [Y] | [Y-X] |
| System Design | [X] | [Y] | [Y-X] |
| Documentation | [X] | [Y] | [Y-X] |
```

## Git Analytics

### Contribution Patterns

```python
import subprocess
from collections import defaultdict
from datetime import datetime

def analyze_git_contributions(repo_path: str, author: str = None) -> dict:
    """Analyze git contribution patterns"""

    # Get commit stats
    cmd = "git log --pretty=format:'%H|%an|%ae|%ad|%s' --date=short"
    if author:
        cmd += f" --author='{author}'"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=repo_path)

    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            commits.append({
                'hash': parts[0],
                'author': parts[1],
                'email': parts[2],
                'date': parts[3],
                'message': parts[4]
            })

    # Analyze patterns
    by_weekday = defaultdict(int)
    by_month = defaultdict(int)
    by_type = defaultdict(int)

    for commit in commits:
        date = datetime.strptime(commit['date'], '%Y-%m-%d')
        by_weekday[date.strftime('%A')] += 1
        by_month[date.strftime('%Y-%m')] += 1

        # Categorize by conventional commit
        msg = commit['message'].lower()
        if msg.startswith('feat'):
            by_type['features'] += 1
        elif msg.startswith('fix'):
            by_type['fixes'] += 1
        elif msg.startswith('refactor'):
            by_type['refactors'] += 1
        elif msg.startswith('test'):
            by_type['tests'] += 1
        elif msg.startswith('docs'):
            by_type['docs'] += 1
        else:
            by_type['other'] += 1

    return {
        'total_commits': len(commits),
        'by_weekday': dict(by_weekday),
        'by_month': dict(by_month),
        'by_type': dict(by_type),
        'commits': commits[:50]  # Last 50
    }
```

### Code Complexity Trends

```python
import subprocess
import json

def analyze_complexity_trends(repo_path: str) -> dict:
    """Track code complexity over time"""

    # Using radon for Python
    result = subprocess.run(
        "radon cc . -a -j",
        shell=True,
        capture_output=True,
        text=True,
        cwd=repo_path
    )

    complexity = json.loads(result.stdout)

    summary = {
        'A': 0,  # Low complexity
        'B': 0,  # Low
        'C': 0,  # Moderate
        'D': 0,  # High
        'E': 0,  # Very high
        'F': 0   # Extreme
    }

    for file_data in complexity.values():
        for func in file_data:
            rank = func.get('rank', 'A')
            summary[rank] += 1

    return summary
```

## Growth Metrics

### Productivity Metrics

```markdown
## Developer Productivity Dashboard

### Code Output (Monthly)
| Metric | Value | Trend |
|--------|-------|-------|
| Commits | [X] | [↑/↓/→] |
| Lines Changed | [X] | [↑/↓/→] |
| PRs Merged | [X] | [↑/↓/→] |
| PRs Reviewed | [X] | [↑/↓/→] |

### Quality Metrics
| Metric | Value | Target |
|--------|-------|--------|
| Bug Rate | [X per 1K LOC] | <[Y] |
| PR Approval Time | [X hours] | <[Y] |
| Test Coverage | [X]% | >[Y]% |
| Doc Coverage | [X]% | >[Y]% |

### Learning & Growth
| Activity | Count |
|----------|-------|
| New technologies used | [X] |
| Technical articles read | [X] |
| Courses completed | [X] |
| Talks/presentations given | [X] |
```

## Code Review Analysis

```python
def analyze_code_reviews(pr_data: list) -> dict:
    """Analyze code review patterns"""

    review_stats = {
        'reviews_given': 0,
        'reviews_received': 0,
        'avg_review_time_hours': 0,
        'comments_given': 0,
        'comments_received': 0,
        'approval_rate': 0,
        'common_feedback': []
    }

    # Analyze patterns
    feedback_categories = defaultdict(int)

    for pr in pr_data:
        # Count reviews
        review_stats['reviews_given'] += len(pr.get('reviews_given', []))
        review_stats['reviews_received'] += len(pr.get('reviews_received', []))

        # Categorize feedback
        for comment in pr.get('comments', []):
            text = comment['body'].lower()
            if 'style' in text or 'format' in text:
                feedback_categories['style'] += 1
            elif 'test' in text:
                feedback_categories['testing'] += 1
            elif 'performance' in text:
                feedback_categories['performance'] += 1
            elif 'security' in text:
                feedback_categories['security'] += 1
            else:
                feedback_categories['logic'] += 1

    review_stats['common_feedback'] = sorted(
        feedback_categories.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return review_stats
```

## Personal Development Plan

```markdown
# Personal Development Plan: [Name]

**Period:** [Q1 2024]
**Role:** [Current Role]
**Target Role:** [Desired Role]

## Goals

### Technical Goals
1. **[Goal 1]**
   - Current state: [Description]
   - Target state: [Description]
   - Actions: [List of actions]
   - Success criteria: [Measurable outcome]
   - Resources: [Courses, books, projects]

2. **[Goal 2]**
   ...

### Soft Skills Goals
1. **[Goal 1]**
   ...

## Learning Plan

### Q1 Focus Areas
| Area | Resource | Time/Week | Deadline |
|------|----------|-----------|----------|
| [Skill 1] | [Course/Book] | [X hours] | [Date] |
| [Skill 2] | [Resource] | [X hours] | [Date] |

### Projects
| Project | Skills Developed | Status |
|---------|-----------------|--------|
| [Project 1] | [Skills] | [Status] |
| [Project 2] | [Skills] | [Status] |

## Milestones

- [ ] **Week 4:** [Milestone 1]
- [ ] **Week 8:** [Milestone 2]
- [ ] **Week 12:** [Milestone 3]

## Check-in Schedule
- Weekly: Self-reflection
- Bi-weekly: Mentor 1:1
- Monthly: Progress review
- Quarterly: Goal adjustment

## Resources
- Mentor: [Name]
- Buddy: [Name]
- Learning budget: $[Amount]
```

## Career Ladder

### IC Track

```markdown
## Individual Contributor Levels

### Junior Engineer (L1)
**Scope:** Task-level
**Skills:**
- [ ] Writes clean, functional code
- [ ] Follows team standards
- [ ] Completes assigned tasks
- [ ] Asks for help when stuck

### Mid Engineer (L2)
**Scope:** Feature-level
**Skills:**
- [ ] Designs and implements features
- [ ] Writes tests
- [ ] Reviews code
- [ ] Mentors juniors

### Senior Engineer (L3)
**Scope:** Project-level
**Skills:**
- [ ] Leads technical projects
- [ ] Makes architectural decisions
- [ ] Influences team practices
- [ ] Debugs complex issues

### Staff Engineer (L4)
**Scope:** Org-level
**Skills:**
- [ ] Sets technical direction
- [ ] Solves cross-team problems
- [ ] Drives major initiatives
- [ ] Mentors seniors

### Principal Engineer (L5)
**Scope:** Company-level
**Skills:**
- [ ] Industry-recognized expertise
- [ ] Shapes company tech strategy
- [ ] External thought leadership
```

## 1:1 Template

```markdown
# 1:1 Meeting: [Date]

## Since Last Time
- **Accomplished:** [List]
- **Learned:** [List]
- **Struggled with:** [List]

## Discussion Topics
1. [Topic 1]
2. [Topic 2]

## Feedback
- **What's going well:**
- **Areas for improvement:**
- **Support needed:**

## Action Items
- [ ] [Action] - Due: [Date]

## Notes
[Meeting notes]
```

## Tips

1. **Measure consistently** - track the same metrics over time
2. **Quality > quantity** - LOC isn't productivity
3. **Seek feedback** - ask for specific feedback
4. **Reflect weekly** - what did you learn?
5. **Set SMART goals** - specific, measurable
6. **Learn in public** - blog, speak, contribute
7. **Find mentors** - accelerate growth
