---
description: Систематическая обработка и приоритизация багов
argument-hint: [bug ID или описание]
---

# Bug Triage: $ARGUMENTS

## 1. Сбор информации

### Базовая информация
- **Bug ID:** [если есть]
- **Reporter:** [кто нашёл]
- **Date Reported:** [когда]
- **Environment:** [production/staging/development]

### Воспроизведение
**Шаги для воспроизведения:**
1. [Шаг 1]
2. [Шаг 2]
3. [Шаг 3]

**Ожидаемое поведение:**
> [Что должно происходить]

**Фактическое поведение:**
> [Что происходит на самом деле]

**Частота:**
- [ ] Всегда (100%)
- [ ] Часто (>50%)
- [ ] Иногда (<50%)
- [ ] Редко (<10%)
- [ ] Не воспроизводится

## 2. Severity Classification

### Critical (P0) - Немедленное исправление
**Критерии:**
- [ ] Production полностью down
- [ ] Data loss или corruption
- [ ] Security breach
- [ ] Блокирует всех пользователей

**SLA:** Исправить в течение 1 часа

### High (P1) - Срочное исправление
**Критерии:**
- [ ] Основная функциональность не работает
- [ ] Блокирует большую часть пользователей
- [ ] Workaround сложный или невозможен
- [ ] Revenue impact

**SLA:** Исправить в течение 24 часов

### Medium (P2) - Планируемое исправление
**Критерии:**
- [ ] Функциональность работает с ограничениями
- [ ] Есть простой workaround
- [ ] Затрагивает малую часть пользователей
- [ ] Minor UI issues

**SLA:** Исправить в текущем спринте

### Low (P3) - Backlog
**Критерии:**
- [ ] Косметические проблемы
- [ ] Edge cases
- [ ] Nice-to-have improvements
- [ ] Минимальный impact

**SLA:** Когда будет время

## 3. Impact Analysis

### Пользователи
- **Затронуто пользователей:** [число или %]
- **User segments:** [какие сегменты]
- **User complaints:** [сколько тикетов]

### Бизнес
- **Revenue impact:** $[amount] / [%]
- **Conversion impact:** [%]
- **Customer satisfaction:** [rating drop]

### Техническая
- **Affected components:** [список]
- **Data integrity:** [OK / At Risk]
- **Security implications:** [None / Low / High]

## 4. Root Cause Investigation

### Проверь логи
```bash
# Application logs
tail -f /var/log/app.log | grep "$ARGUMENTS"

# Error tracking (Sentry/etc)
# Проверь error count и stack traces

# Database logs
# Проверь slow queries, locks
```

### Code Analysis
```bash
# Найди связанный код
git log --all --grep="$ARGUMENTS"

# Проверь последние изменения
git log -p --since="1 week ago" -- [affected-file]

# Blame
git blame [affected-file]
```

### Возможная причина
> [Твоя гипотеза о причине бага]

### Affected code locations
- File: [path/to/file.py:123]
- Function: [function_name]
- Recent changes: [commit hash]

## 5. Triage Decision

### Priority: [P0/P1/P2/P3]
**Обоснование:**
> [Почему выбран именно этот приоритет]

### Assignment
- **Owner:** @[developer]
- **Reviewer:** @[reviewer]
- **QA:** @[qa-specialist]

### Timeline
- **ETA for Fix:** [date/time]
- **Target Release:** [version/sprint]

### Workaround (если есть)
**Временное решение для пользователей:**
```
[Шаги workaround]
```

## 6. Fix Strategy

### Quick Fix vs Proper Fix
- [ ] **Hot patch** - быстрое исправление для production
- [ ] **Proper fix** - полноценное решение проблемы
- [ ] **Refactoring** - нужна более глубокая переработка

### Testing Strategy
**Тесты, которые нужно добавить:**
- [ ] Unit test для воспроизведения
- [ ] Integration test
- [ ] E2E test для regression
- [ ] Performance test (если нужно)

### Rollout Plan
1. Fix в development
2. QA testing в staging
3. Deploy to production (canary/blue-green)
4. Monitor metrics
5. Rollback plan готов

## 7. Communication

### Notify Stakeholders
**Internal:**
- [ ] Team в Slack
- [ ] Product Manager
- [ ] Engineering Lead

**External (если P0/P1):**
- [ ] Status page update
- [ ] Customer support notification
- [ ] Affected customers email

### Status Updates
**Шаблон для Slack:**
```
🐛 Bug Update: $ARGUMENTS
Severity: [P0/P1/P2/P3]
Status: [Investigating / Fix in Progress / Testing / Deployed]
ETA: [time]
Workaround: [если есть]
Owner: @[developer]
```

## 8. Prevention

### Root Cause
> [Глубинная причина, почему баг возник]

### Prevention Measures
**Что нужно сделать, чтобы такое не повторилось:**
- [ ] Add monitoring/alerting
- [ ] Improve test coverage
- [ ] Update documentation
- [ ] Code review process improvement
- [ ] Architecture change needed

### Action Items
1. [Action item 1] - @owner - [deadline]
2. [Action item 2] - @owner - [deadline]

## 9. Post-Mortem (для P0/P1)

### Timeline
- **Bug introduced:** [date/commit]
- **Bug detected:** [date]
- **Time to fix:** [hours/days]
- **Time to deploy:** [hours/days]

### What Went Well
- [Положительный момент 1]
- [Положительный момент 2]

### What Went Wrong
- [Проблема 1]
- [Проблема 2]

### Lessons Learned
- [Урок 1]
- [Урок 2]

### Action Items for Improvement
- [ ] [Improvement 1] - @owner
- [ ] [Improvement 2] - @owner

---

**Triage Completed By:** [your name]
**Date:** [date]
**Time Spent:** [hours]

**Next Steps:**
1. [Immediate action]
2. [Follow-up action]
3. [Long-term improvement]
