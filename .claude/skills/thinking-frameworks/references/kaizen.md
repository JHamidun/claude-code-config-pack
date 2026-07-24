# Kaizen / PDCA — Continuous Improvement (reference)

> [MERGED 2026-07-18] Бывший отдельный скилл `kaizen`, влит в `thinking-frameworks` (режим 7).
> Тело сохранено целиком: PDCA-цикл, 7 типов muda, Gemba, Kaizen Event, Value Stream Mapping,
> A3 Report, Daily/Personal Kaizen, метрики.
> NB: секция «5 Whys Analysis» ниже дублирует фреймворк 5 в SKILL.md — канон шагов там,
> здесь остаются расширенный шаблон и разобранный пример (Customer complaints → restocking SOP).

## Overview

Kaizen - философия непрерывного улучшения через маленькие инкрементальные изменения.

## When to Use

- Оптимизация процессов
- Повышение качества
- Устранение waste (потерь)
- Повышение эффективности
- Культура улучшений

## Core Principles

### 1. Continuous Improvement

```
Сегодня лучше чем вчера
Завтра лучше чем сегодня
Маленькие шаги каждый день
```

### 2. Good Processes = Good Results

```
Фокус на ПРОЦЕССЕ, не только на результате
Улучши процесс → результат улучшится
```

### 3. Go to Gemba

```
Gemba = "реальное место" (где происходит работа)
- Наблюдай процесс на месте
- Говори с людьми, которые делают работу
- Данные из первоисточника
```

### 4. Eliminate Waste (Muda)

```
7 типов потерь:
1. Перепроизводство - делаем больше чем нужно
2. Ожидание - простои
3. Транспортировка - ненужное перемещение
4. Излишняя обработка - делаем больше чем требуется
5. Запасы - лишние запасы
6. Движение - ненужные движения
7. Дефекты - брак, переделки
```

## Kaizen Cycle (PDCA)

```
    ┌─────────────────────────────────────┐
    │                                     │
    │   ┌─────────┐     ┌─────────┐      │
    │   │  PLAN   │ ──► │   DO    │      │
    │   └─────────┘     └─────────┘      │
    │        ▲               │           │
    │        │               ▼           │
    │   ┌─────────┐     ┌─────────┐      │
    │   │   ACT   │ ◄── │  CHECK  │      │
    │   └─────────┘     └─────────┘      │
    │                                     │
    └─────────────────────────────────────┘

PLAN  - Определи проблему, проанализируй, спланируй изменение
DO    - Реализуй изменение (small scale test)
CHECK - Измерь результат, сравни с ожиданием
ACT   - Стандартизируй или корректируй
```

## Kaizen Event Template

```markdown
# Kaizen Event: [Problem/Opportunity]

## Current State
- **Process:** [Description]
- **Problem:** [What's wrong]
- **Impact:** [Metrics, cost, time]
- **Root Cause:** [5 Whys analysis]

## Goal
- **Target State:** [What we want]
- **Metrics:** [How we'll measure]
- **Scope:** [Boundaries]

## Team
- Champion: [Name]
- Team Lead: [Name]
- Members: [Names]

## Timeline
- Day 1: Current state mapping
- Day 2-3: Analysis & ideation
- Day 4: Implementation
- Day 5: Measure & document

## Actions

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| [Action] | [Name] | [Date] | [Status] |

## Results
- Before: [Metric] = [Value]
- After: [Metric] = [Value]
- Improvement: [X]%

## Standardization
- [ ] Document new process
- [ ] Train team
- [ ] Update procedures
- [ ] Schedule follow-up
```

## 5 Whys Analysis

```markdown
## Problem: [Statement]

### Why 1?
Q: Why did [problem] happen?
A: Because [cause 1]

### Why 2?
Q: Why did [cause 1] happen?
A: Because [cause 2]

### Why 3?
Q: Why did [cause 2] happen?
A: Because [cause 3]

### Why 4?
Q: Why did [cause 3] happen?
A: Because [cause 4]

### Why 5?
Q: Why did [cause 4] happen?
A: Because [ROOT CAUSE]

### Solution
Address [ROOT CAUSE] by [action]
```

### Example

```markdown
## Problem: Customer complaints increased 30%

### Why 1?
Q: Why are customers complaining?
A: Orders arriving late

### Why 2?
Q: Why are orders late?
A: Shipping takes longer than promised

### Why 3?
Q: Why does shipping take longer?
A: Warehouse picking is slow

### Why 4?
Q: Why is picking slow?
A: Items not in expected locations

### Why 5?
Q: Why are items not in locations?
A: No standard restocking process

### ROOT CAUSE: Missing restocking SOP

### Solution: Create and train standard restocking procedure
```

## Value Stream Mapping

```
Customer Order → Order Entry → Picking → Packing → Shipping → Delivery
     │              │            │          │          │          │
   START         Process      Process    Process    Process      END
     │           Time: 5m     Time: 15m  Time: 10m  Time: 5m      │
     │                                                             │
     └─────────────── Lead Time: 2 days ──────────────────────────┘

Process Time: 35 minutes
Wait Time: 1 day 23 hours 25 minutes
Efficiency: 35min / 2880min = 1.2%

WASTE IDENTIFIED:
- Wait between order and picking: 8 hours
- Searching for items: 10 minutes
- Rework from errors: 5 minutes
```

## Gemba Walk Checklist

```markdown
## Gemba Walk: [Area/Process]
**Date:** [Date]
**Observer:** [Name]

### Observations

| Category | Observation | Type | Priority |
|----------|-------------|------|----------|
| Safety | [Observation] | [Issue/Good] | [H/M/L] |
| Quality | [Observation] | [Issue/Good] | [H/M/L] |
| Efficiency | [Observation] | [Issue/Good] | [H/M/L] |
| Morale | [Observation] | [Issue/Good] | [H/M/L] |

### Questions Asked
1. Q: [Question to worker]
   A: [Their answer]

2. Q: [Question]
   A: [Answer]

### Ideas for Improvement
1. [Idea from observation]
2. [Idea from conversation]

### Follow-up Actions
- [ ] [Action 1]
- [ ] [Action 2]
```

## Daily Kaizen

### Standup Format

```markdown
## Daily Improvement Meeting (10 min)

1. **Yesterday's improvement** (2 min)
   - What small improvement did we make?
   - Result?

2. **Today's focus** (3 min)
   - One thing to improve today
   - Who/What/How

3. **Blockers** (3 min)
   - What's preventing improvements?
   - Who can help?

4. **Ideas** (2 min)
   - Quick share of improvement ideas
   - Add to backlog
```

### Personal Kaizen

```markdown
## My Daily Kaizen

### Morning (1 min)
- [ ] What one thing will I improve today?

### Evening (2 min)
- [ ] Did I make the improvement?
- [ ] What did I learn?
- [ ] What will I improve tomorrow?

### Weekly Review (10 min)
- Improvements made this week: [count]
- Time saved: [estimate]
- Next week's focus: [area]
```

## Kaizen Metrics

```python
def track_kaizen_metrics(improvements: list) -> dict:
    """Track kaizen initiative metrics"""

    return {
        "total_improvements": len(improvements),
        "improvements_per_person": len(improvements) / team_size,
        "time_saved_hours": sum(i['time_saved'] for i in improvements),
        "cost_saved": sum(i['cost_saved'] for i in improvements),
        "quality_impact": count_quality_improvements(improvements),
        "implementation_rate": implemented / proposed * 100,
        "average_cycle_time": avg_days_to_implement(improvements),
    }
```

## Common Kaizen Tools

| Tool | Purpose |
|------|---------|
| **5S** | Workplace organization |
| **Kanban** | Visual workflow |
| **Poka-yoke** | Error-proofing |
| **Andon** | Visual signals |
| **Standardized Work** | Best practices |
| **Visual Management** | Information display |
| **A3 Report** | Problem solving |

## A3 Report Template

```
┌─────────────────────────────────────────────────────────────────┐
│ A3 REPORT: [Title]                              Date: [Date]    │
├────────────────────────────────┬────────────────────────────────┤
│ 1. BACKGROUND                  │ 5. COUNTERMEASURES             │
│ [Context and importance]       │ [Actions to address root cause]│
│                                │                                │
├────────────────────────────────┼────────────────────────────────┤
│ 2. CURRENT CONDITION           │ 6. IMPLEMENTATION PLAN         │
│ [Data, metrics, facts]         │ [Who, What, When]              │
│                                │                                │
├────────────────────────────────┼────────────────────────────────┤
│ 3. GOAL/TARGET                 │ 7. FOLLOW-UP                   │
│ [Specific, measurable]         │ [Check points, metrics]        │
│                                │                                │
├────────────────────────────────┼────────────────────────────────┤
│ 4. ROOT CAUSE ANALYSIS         │ 8. RESULTS                     │
│ [5 Whys, Fishbone]             │ [Actual vs Target]             │
│                                │                                │
└────────────────────────────────┴────────────────────────────────┘
```

## Tips

1. **Start small** - маленькие изменения каждый день
2. **Everyone participates** - идеи от всех
3. **No blame** - фокус на процессе, не на людях
4. **Measure** - без метрик нет улучшения
5. **Standardize** - закрепляй успешные изменения
6. **Respect** - уважай тех, кто делает работу
7. **Never stop** - улучшение бесконечно
