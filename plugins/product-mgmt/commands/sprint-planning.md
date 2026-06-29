---
description: Планирование спринта с использованием Linear/Jira через MCP
argument-hint: [sprint name/number]
---

# Sprint Planning: $ARGUMENTS

## 1. Подготовка (Pre-Planning)

### Собери данные из Linear
- Velocity последних 3 спринтов
- Количество завершённых story points
- Незавершённые задачи из прошлого спринта

### Team Capacity
**Команда:**
- Количество разработчиков: [число]
- Доступные часы в спринте: [число]
- Отпуска/больничные: [перечисли]

**Расчёт capacity:**
```
Доступные часы = (Разработчики × Дни в спринте × 6 часов) - Отпуска
```

## 2. Sprint Goal

**Главная цель спринта:**
> [Сформулируй одним предложением - что мы хотим достичь?]

**Критерии успеха:**
1. [Измеримый результат 1]
2. [Измеримый результат 2]
3. [Измеримый результат 3]

## 3. Backlog Grooming

### Приоритизация (используя MCP Linear)

#### 🔴 Must Have (P0)
Критичные задачи, которые ДОЛЖНЫ быть в спринте:
- [ ] [Task 1] - [Story Points] - @owner
- [ ] [Task 2] - [Story Points] - @owner

#### 🟡 Should Have (P1)
Важные, но не блокирующие:
- [ ] [Task 3] - [Story Points] - @owner
- [ ] [Task 4] - [Story Points] - @owner

#### 🟢 Could Have (P2)
Желательные, если останется время:
- [ ] [Task 5] - [Story Points] - @owner

#### ⚪ Won't Have
Откладываем на следующий спринт:
- [ ] [Task 6] - [Reason]

## 4. Task Breakdown

Для каждой фичи создай подзадачи:

### Фича: [Название]

**User Story:**
> As a [role], I want [feature] so that [benefit]

**Acceptance Criteria:**
1. Given [context], When [action], Then [result]
2. Given [context], When [action], Then [result]

**Technical Tasks:**
- [ ] Design API endpoints - [hours] - @backend-dev
- [ ] Implement database schema - [hours] - @backend-dev
- [ ] Create UI components - [hours] - @frontend-dev
- [ ] Write tests - [hours] - @qa
- [ ] Documentation - [hours] - @tech-writer

**Dependencies:**
- Блокируется: [другие задачи]
- Блокирует: [другие задачи]

**Story Points:** [число]

## 5. Capacity Planning

### Распределение по разработчикам

**@developer1:**
- Capacity: [hours]
- Assigned: [hours]
- Tasks:
  - [Task 1] - [hours]
  - [Task 2] - [hours]

**@developer2:**
- Capacity: [hours]
- Assigned: [hours]
- Tasks:
  - [Task 3] - [hours]
  - [Task 4] - [hours]

### Загрузка команды
```
Total Capacity: [hours]
Total Assigned: [hours]
Buffer: [hours] ([%])
```

**Рекомендация:** Оставляй 20% buffer для unplanned work.

## 6. Risks & Mitigations

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | High/Medium/Low | High/Medium/Low | [Action plan] |
| [Risk 2] | High/Medium/Low | High/Medium/Low | [Action plan] |

### Dependencies на другие команды
- [ ] [Team A] - [что нужно] - by [date]
- [ ] [Team B] - [что нужно] - by [date]

## 7. Sprint Schedule

### Key Dates
- **Sprint Start:** [date]
- **Sprint End:** [date]
- **Mid-Sprint Check-in:** [date]
- **Code Freeze:** [date]
- **Deploy to Staging:** [date]
- **Deploy to Production:** [date]

### Ceremonies
- **Daily Standup:** Every day at [time]
- **Mid-Sprint Review:** [date] at [time]
- **Sprint Demo:** [date] at [time]
- **Retrospective:** [date] at [time]

## 8. Success Metrics

### Velocity
- **Target:** [story points]
- **Committed:** [story points]
- **Buffer:** [story points]

### Quality Metrics
- Code coverage: >80%
- Bug count: <5 critical
- Customer satisfaction: >4.5/5

### Delivery
- On-time delivery: 100%
- Scope creep: <10%

## 9. Action Items

**Before Sprint Start:**
- [ ] Все задачи в Linear с story points
- [ ] Owners назначены
- [ ] Dependencies проверены
- [ ] Design review завершён
- [ ] Tech spec одобрен

**During Sprint:**
- [ ] Ежедневные standups
- [ ] Update Linear daily
- [ ] Mid-sprint check-in
- [ ] Unblock задачи быстро

**Sprint Review:**
- [ ] Demo готово
- [ ] Metrics собраны
- [ ] Feedback от stakeholders
- [ ] Retrospective notes

## 10. Create Tasks in Linear

```bash
# После завершения планирования, создай задачи автоматически
# через Linear MCP
```

Для каждой задачи:
- Title
- Description с acceptance criteria
- Story points
- Priority
- Owner
- Labels
- Sprint assignment

---

**Sprint Planning Completed:** [date]
**Participants:** [список]
**Next Planning:** [date]
