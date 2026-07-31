---
description: Автоматическая оркестрация разработки фичи с координацией всех агентов
argument-hint: [описание фичи или задачи]
---

# 🎯 Оркестрация: $ARGUMENTS

**Создай и выполни полный workflow для разработки: $ARGUMENTS**

## Твоя задача:

1. **ANALYZE** - Проанализируй задачу, оцени сложность и требования
2. **PLAN** - Используй `Task(subagent_type="Plan")` для детального плана
3. **EXECUTE** - Используй `Task(subagent_type="general-purpose")` для реализации
4. **MONITOR** - Отслеживай прогресс через TodoWrite
5. **AGGREGATE** - Собери все результаты
6. **DELIVER** - Финальный deliverable со всеми артефактами

## Execution Strategy:

- **Используй parallel execution** где возможно (frontend || backend || integration)
- **Quality gates**: code-reviewer перед merge, security-engineer для auth/integrations
- **Context management**: используй Memory MCP для передачи контекста между агентами
- **Tracking**: создавай Linear issues для каждой подзадачи
- **Communication**: отправляй updates в Slack о ключевых milestone
- **Version control**: создай git branch, потом PR через GitHub MCP

## Standard Workflow для фичи:

### Подход 1: Multi-Agent Orchestration (для сложных задач)

**Используй кастомных агентов когда:**
- Задача сложная (>1 день работы)
- Нужна экспертиза в специфичных областях (security, architecture)
- Можно делать параллельно (frontend + backend + testing одновременно)

```
# Phase 1: Analysis (sequential)
Use the orchestrator subagent to create execution plan for $ARGUMENTS with architecture, phases, and task decomposition
Use the business-analyst subagent to analyze business requirements and stakeholders for $ARGUMENTS
Use the software-architect subagent to design architecture for $ARGUMENTS

# Phase 2: Development (parallel)
Use the backend-dev subagent to implement backend for $ARGUMENTS
Use the frontend-dev subagent to implement frontend for $ARGUMENTS
Use the integration-dev subagent to integrate external APIs for $ARGUMENTS

# Phase 3: Quality (sequential)
Use the code-reviewer subagent to review code quality and security
Use the qa-specialist subagent to create test suite
Use the security-engineer subagent to review security implications

# Phase 4: Deployment
Use the devops-engineer subagent to set up CI/CD and deploy to staging
```

### Подход 2: Built-in Subagents (для простых задач)

**Используй встроенные типы когда:**
- Задача простая (<1 день)
- Не нужна глубокая экспертиза
- Быстрое прототипирование

```python
# 1. Research (проактивно!)
/deep-research "best practices для [feature]"

# 2. Planning через Plan субагента
Task(
  subagent_type="Plan",
  prompt="План разработки $ARGUMENTS с архитектурой, компонентами и шагами реализации",
  description="Plan feature"
)

# 3. Реализация через general-purpose
Task(
  subagent_type="general-purpose",
  prompt="Реализуй $ARGUMENTS по плану. Включи backend, frontend, tests и документацию",
  description="Implement feature"
)
```

### Phase 3: Quality
```bash
# Code review
/code-review src/feature/

# Frontend testing
/test-frontend http://localhost:3000 e2e

# Security review если нужно
/kimi-reasoning "Security implications of [feature]"
```

### Phase 4: Deployment
```bash
# Quick deploy
/quick-deploy staging
```

## Важные правила:

- ✅ ВСЕГДА создавай execution plan в JSON формате
- ✅ ВСЕГДА делай security scan для auth и API integrations
- ✅ ВСЕГДА проверяй test coverage >80%
- ✅ НЕ пропускай этапы для ускорения - качество важнее
- ✅ Сохраняй все промежуточные результаты в `docs/features/[feature-name]/`

## Output Format:

Верни JSON execution plan:

```json
{
  "task": "краткое описание",
  "complexity": "simple|medium|complex",
  "estimated_time": "X hours",
  "phases": [
    {
      "phase_number": 1,
      "name": "Research & Planning",
      "type": "sequential",
      "steps": [
        {
          "step": "/deep-research best practices",
          "estimated_time": "5 min"
        },
        {
          "step": "Task(subagent_type='Plan', prompt='детальный план')",
          "output_location": "docs/features/X/plan.md",
          "estimated_time": "30 min"
        }
      ]
    },
    {
      "phase_number": 2,
      "name": "Implementation",
      "type": "sequential",
      "steps": [
        {
          "step": "Task(subagent_type='general-purpose', prompt='реализация')",
          "output_location": "src/features/X/",
          "estimated_time": "2-4 hours"
        }
      ]
    },
    {
      "phase_number": 3,
      "name": "Quality",
      "type": "sequential",
      "steps": [
        {
          "step": "/code-review src/features/X/",
          "estimated_time": "15 min"
        },
        {
          "step": "/test-frontend http://localhost:3000 e2e",
          "estimated_time": "10 min"
        }
      ]
    }
  ],
  "success_criteria": [
    "все тесты проходят",
    "code review чист",
    "code coverage >80%"
  ],
  "deliverables": [
    "working code",
    "tests",
    "documentation"
  ]
}
```

## Автоматизация:

### Pre-Development (Setup)
1. **Linear Issue** (если Linear MCP доступен):
   - Создай issue с title и description
   - Assign to developer
   - Add labels: feature, priority
   - Set estimate

2. **Git Branch**:
   ```bash
   BRANCH="feature/$(echo "$ARGUMENTS" | tr '[:upper:] ' '[:lower:]-')"
   git checkout -b "$BRANCH"
   git push -u origin "$BRANCH"
   ```

3. **Project Structure**:
   ```bash
   mkdir -p docs/features/[feature-name]
   mkdir -p tests/features/[feature-name]
   ```

4. **Memory MCP**:
   - Store execution plan
   - Store context для agents
   - Track progress

### During Development (Tracking)
1. **Regular Commits**:
   - Conventional commit format
   - Link to Linear issue: `feat: Add feature (LINEAR-123)`
   - Atomic commits (one logical change per commit)

2. **Progress Updates**:
   - Update Linear issue comments each phase
   - Slack notification на key milestones
   - Memory MCP для sharing context between agents

3. **Code Quality**:
   - Run pre-commit hooks автоматически
   - Fix linting issues immediately
   - Maintain test coverage >80%

### Post-Development (PR & Deployment)

#### 1. Final Code Review
```bash
# Comprehensive review
/code-review src/features/X/

# Проверяет:
# - Code quality и style
# - Test coverage
# - Performance
# - Security issues
# - Documentation
```

#### 2. Security Scan (if applicable)
```bash
# Deep security reasoning
/kimi-reasoning "Security analysis of [feature]: Authentication, Input validation, SQL injection, XSS, Sensitive data handling, API rate limiting"

# Или используй Context7 для security best practices
Context7: "OWASP security guidelines for [technology]"
```

#### 3. Fix Issues
```bash
# Auto-fix через агента
Use the bug-fixer subagent to fix issues from the review in src/features/X/

# Или manual fixes
- Address review comments
- Update tests
- Commit fixes
```

#### 4. Create Pull Request (GitHub MCP)

**PR Title Format:**
```
feat: [Feature name] (LINEAR-123)
```

**PR Description (auto-generated):**
```markdown
## What
Implements [feature description]

## Why
[Business value и user impact]

## How
[Technical approach - key changes]

## Changes
- Component A: [description]
- Component B: [description]
- Tests: [description]

## Testing
- [x] Unit tests (coverage: X%)
- [x] Integration tests
- [x] E2E tests (if applicable)
- [x] Manual testing checklist:
  - [ ] Happy path
  - [ ] Error cases
  - [ ] Edge cases

## Screenshots/Demo
[If UI changes]

## Performance Impact
- Bundle size: +/- X KB
- API latency: X ms
- Database queries: optimized

## Rollout Plan
1. Deploy to staging
2. QA sign-off
3. Enable feature flag (if applicable)
4. Monitor metrics
5. Gradual rollout: 10% → 50% → 100%

## Related
- Linear: [LINEAR-123]
- Docs: docs/features/X/
- Depends on: [other PRs]
- Blocks: [other issues]

## Checklist
- [x] Tests passing (coverage >80%)
- [x] Linter clean
- [x] Documentation updated
- [x] No console errors/warnings
- [x] Accessibility checked
- [x] Security reviewed
- [x] Performance tested
- [x] Database migrations (if any)
- [x] Feature flags configured (if any)

## Post-Merge Tasks
- [ ] Update Linear issue → Done
- [ ] Notify stakeholders в Slack
- [ ] Update roadmap
- [ ] Schedule monitoring review
```

**Create PR:**
```bash
# Via GitHub MCP
gh pr create \
  --title "feat: Feature name (LINEAR-123)" \
  --body "$(cat PR_DESCRIPTION.md)" \
  --base main \
  --head "$BRANCH" \
  --reviewer team-leads \
  --label "feature,needs-review"
```

#### 5. Update Linear Issue
```
Status: In Review
PR: [link]
Comment: "PR #XXX created and ready for review

Code: [lines changed]
Tests: [coverage %]
Review: Assigned to @reviewer"
```

#### 6. Slack Notification
```
🚀 Feature PR Ready: $ARGUMENTS

👤 Author: @developer
📋 PR: #XXX [link]
🔍 Reviewers: @team-leads
📊 Stats:
  • Code: +XXX -YYY lines
  • Tests: ZZ% coverage
  • Files: N changed

✅ All checks passed
⏰ ETA for review: 1-2 days
```

#### 7. Post-Merge Automation

**After PR merged:**

1. **Delete Branch**:
   ```bash
   git branch -d "$BRANCH"
   git push origin --delete "$BRANCH"
   ```

2. **Update Linear Issue**:
   ```
   Status: Done
   Merged: [timestamp]
   Deployed: [environment]
   ```

3. **Generate Changelog Entry**:
   ```
   Use /changelog command to update CHANGELOG.md
   ```

4. **Deploy to Staging**:
   ```
   Trigger CI/CD pipeline
   Run smoke tests
   Notify QA team
   ```

5. **Monitoring Setup**:
   ```
   - Setup alerts для new feature
   - Track key metrics
   - Monitor error rates
   ```

6. **Documentation Updates**:
   ```
   - Update API docs (if API changes)
   - Update user docs (if user-facing)
   - Update team wiki в Notion
   ```

7. **Stakeholder Communication**:
   ```
   Slack #announcements:
   "✅ Feature shipped: [name]

   What's new:
   • [benefit 1]
   • [benefit 2]

   Docs: [link]
   Feedback: [channel]"
   ```

### Optional: Feature Flag Management

**If using feature flags:**

```javascript
// Initial deployment - disabled
featureFlags.set('new-feature', {
  enabled: false,
  rollout: 0
});

// Gradual rollout
// Day 1: Internal team only
featureFlags.set('new-feature', {
  enabled: true,
  rollout: 0,
  allowlist: ['internal-users']
});

// Day 3: 10% of users
featureFlags.set('new-feature', {
  enabled: true,
  rollout: 10
});

// Day 7: 50% of users
featureFlags.set('new-feature', {
  enabled: true,
  rollout: 50
});

// Day 14: 100% (full launch)
featureFlags.set('new-feature', {
  enabled: true,
  rollout: 100
});
```

## Execution Checklist:

**Pre-Development:**
- [ ] Linear issue created
- [ ] Git branch created
- [ ] Project structure setup
- [ ] Execution plan documented

**Development:**
- [ ] Code implemented
- [ ] Tests written (>80% coverage)
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Regular commits

**Quality:**
- [ ] Code review completed
- [ ] Security review (if applicable)
- [ ] All issues addressed
- [ ] Tests passing

**PR & Deploy:**
- [ ] PR created with comprehensive description
- [ ] Linear issue updated
- [ ] Team notified
- [ ] CI/CD passing
- [ ] Deployed to staging
- [ ] QA sign-off
- [ ] Production deploy
- [ ] Monitoring configured

**Post-Launch:**
- [ ] Metrics tracked
- [ ] Stakeholders informed
- [ ] Documentation published
- [ ] Roadmap updated
- [ ] Retrospective scheduled

---

**Начинай оркестрацию! 🚀**
