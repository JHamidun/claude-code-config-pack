---
description: Оценка сложности и времени разработки фичи
argument-hint: [описание фичи или Linear issue ID]
---

# ⏱️ Estimate: $ARGUMENTS

Оцени сложность и время для: **$ARGUMENTS**

## Process:

### 1. Feature Analysis
**Разбей на компоненты:**
- Frontend tasks
- Backend tasks
- Database changes
- API integrations
- Testing requirements
- Documentation

### 2. Complexity Assessment

**Оцени каждый компонент:**
- 🟢 Simple (1-2 часа)
- 🟡 Medium (0.5-1 день)
- 🟠 Complex (1-3 дня)
- 🔴 Very Complex (3+ дня)

**Факторы сложности:**
- Technical unknowns
- Dependencies
- Breaking changes
- Performance impact
- Security considerations

### 3. Estimation Breakdown

**По типам работ:**
```
📋 Requirements & Design: X hours
💻 Implementation: X hours
🧪 Testing: X hours
📝 Documentation: X hours
🔄 Code Review: X hours
---
Total: X hours (X days)
```

### 4. Risk Assessment

**Potential blockers:**
- [ ] Technical dependencies
- [ ] External API availability
- [ ] Database migration complexity
- [ ] Performance optimization needed
- [ ] Security review required

### 5. Resource Planning

**Recommended team:**
- Backend: X developers
- Frontend: X developers
- QA: X testers
- DevOps: X engineers

## Output Format:

```
⏱️ Оценка: $ARGUMENTS

**Сложность:** [Simple/Medium/Complex/Very Complex]

**Время разработки:** X days (Y hours)

**Разбивка:**
- Design: X hours
- Implementation: Y hours
- Testing: Z hours

**Риски:**
1. [Risk 1]
2. [Risk 2]

**Рекомендации:**
- [Recommendation 1]
- [Recommendation 2]

**Обновлено в Linear:** [Issue link]
```

## Examples:

```
/estimate Добавить WebSocket поддержку для real-time уведомлений
```

```
/estimate PROJ-123
```

```
/estimate Migration с SQLite на PostgreSQL
```

**Начинаю оценку! ⏱️**