---
description: Standup-отчёт — daily за сутки (без аргумента) или сводный за период
argument-hint: "[период: пусто=сутки | week | last week | this month | Q4 2026]"
---

# 📊 Standup Report: $ARGUMENTS

**Период:** $ARGUMENTS (пусто → daily за вчера/сегодня).

## Режим DAILY (без аргумента или "today")

Generate concise daily report:

### ✅ Completed Yesterday
- What was finished
- PRs merged
- Issues closed

### 🔄 In Progress Today
- Current work
- Focus areas
- Expected completion

### 🚧 Blockers
- Issues or dependencies
- Need help with
- Waiting on

Check recent git commits, open files, and project status.
Keep it brief and actionable.

## Режим PERIOD (week / last week / this month / Q4 …)

Создай сводный отчёт за указанный период.

### 1. Collect Data

**Git Activity:**
```bash
git log --since="1 week ago" --pretty=format:"%h - %an: %s"
git shortlog -s -n --since="1 week ago"
```
(Подставь период из $ARGUMENTS в --since.)

**Pull requests** — `gh pr list --state merged --search "merged:>=<дата>"`,
`gh pr list --state open`, `gh pr list --search "reviewed-by:@me"`:
- Merged PRs
- Open PRs
- PR reviews

**Задачи** — Beads (`bd list --status closed`, `bd list --status in_progress`,
`bd blocked`):
- Completed issues
- In progress issues
- Blocked issues

### 2. Aggregate Metrics

**Velocity:**
- Story points completed
- Issues closed
- PRs merged

**Quality:**
- Bug count (opened vs closed)
- Code review turnaround time
- Test coverage changes

**Blockers:**
- Current blockers
- Resolved blockers
- Dependencies

### 3. Create Report

**Используй xlsx skill** для dashboard:

**Sheet 1: Summary**
| Metric | This Period | Last Period | Change |
|--------|-------------|-------------|--------|
| Story Points | 34 | 28 | +21% ✅ |
| PRs Merged | 12 | 15 | -20% ⚠️ |
| Bugs Fixed | 8 | 5 | +60% ✅ |

**Sheet 2: Team Activity**
| Member | Commits | PRs | Issues | Status |
|--------|---------|-----|--------|--------|
| Developer 1 | 45 | 3 | 5 | ✅ On track |
| Developer 2 | 32 | 2 | 4 | ✅ On track |

**Sheet 3: Completed Features**
- Feature A (PROJ-123) - Deployed ✅
- Feature B (PROJ-124) - In review 🔍
- Feature C (PROJ-125) - Blocked ⚠️

### 4. Executive Summary (pptx skill)

**Slide 1: Highlights**
- Top achievements
- Key metrics
- Important decisions

**Slide 2: Team Progress**
- Velocity trend (chart)
- Completed features
- Upcoming work

**Slide 3: Issues & Blockers**
- Current blockers
- Mitigation plans
- Help needed

### 5. Distribution

**Email format:**
```
Subject: Weekly Update - [Date Range]

Hi team,

Here's our weekly summary:

🎯 HIGHLIGHTS:
- Shipped feature X to production
- Resolved 8 bugs
- Completed Sprint 23 with 34 points

📊 METRICS:
- Velocity: 34 pts (+21% vs last week)
- PRs Merged: 12
- Test Coverage: 85% (+2%)

⚠️ BLOCKERS:
- Waiting for API access from Partner team
- Database migration pending approval

📋 NEXT WEEK:
- Start Sprint 24
- Focus on Feature Y
- Tech debt cleanup

Dashboard: [link to Excel]

Best,
[Your name]
```

**Slack post** (#general or #updates):
```
📊 *Weekly Update - Week 45*

*Highlights:*
✅ Shipped feature X
✅ 34 story points completed
✅ 8 bugs resolved

*Metrics:* Velocity +21%, Coverage 85%
*Next:* Sprint 24, Feature Y

📈 Full dashboard: [link]
```

### Output (period-режим):

1. **Excel Dashboard** (detailed metrics)
2. **PowerPoint Summary** (exec-ready)
3. **Email/Slack formatted** update (текст для копирования)

## Examples:

```
/daily                  # daily standup за сутки
/daily week
/daily last week
/daily this month
/daily Q4 2026
```
