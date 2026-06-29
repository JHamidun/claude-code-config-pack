---
name: plan-my-day
description: Generate an optimized daily plan from tasks, calendar, and priorities. Use with /plan-my-day or "спланируй день".
---

# Plan My Day

Generate an optimized daily plan based on tasks and energy levels.

## Data Sources

### 1. Calendar Events (if available)
```
Use gcalendar skill to fetch today's events
```

### 2. Current Tasks
Ask user or check:
- Linear issues assigned to me
- Todoist tasks for today
- Any explicit priorities mentioned

### 3. Recent Context
```bash
python ${WORKSPACE}/tools/vector_memory.py recall-recent 1
```

## Energy-Based Scheduling

```
MORNING (9:00-12:00) — Peak energy
  -> Complex coding tasks
  -> Architecture decisions
  -> Deep research
  -> Writing/creative work

AFTERNOON (13:00-16:00) — Moderate energy
  -> Code reviews
  -> Meetings
  -> Bug fixes
  -> Testing

EVENING (16:00-19:00) — Low energy
  -> Emails and messages
  -> Documentation
  -> Planning for tomorrow
  -> Routine maintenance
```

## Output Format

```markdown
# Daily Plan: [date]

## Top 3 Priorities
1. [Most important task]
2. [Second priority]
3. [Third priority]

## Schedule

### Morning (high energy)
- [ ] 09:00 - [task]
- [ ] 10:30 - [task]

### Afternoon (moderate energy)
- [ ] 13:00 - [task/meeting]
- [ ] 14:30 - [task]

### Evening (wind down)
- [ ] 16:00 - [task]
- [ ] 17:00 - [review/docs]

## Blocked/Waiting
- [Items waiting on others]

## Tomorrow Preview
- [Key items for tomorrow]
```

## Process

1. Gather tasks from all sources
2. Prioritize by urgency x importance (Eisenhower)
3. Map to energy-appropriate time slots
4. Account for calendar events (fixed blocks)
5. Add buffer time between deep work blocks
6. Output the plan
