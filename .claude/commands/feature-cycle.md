---
description: Полный цикл разработки фичи с параллельными агентами
argument-hint: [описание фичи]
---

# Цикл разработки фичи: $ARGUMENTS

## Phase 1: Discovery (Parallel)
Запускаем параллельно:
- @business-analyst: User research, market analysis, competitive analysis
- @product-designer: User flows, wireframes, прототипы

Каждый работает в своём Task одновременно.

## Phase 2: Planning (Sequential)
После завершения Phase 1:
- @system-analyst читает результаты Phase 1 → Technical feasibility analysis
- @software-architect читает результаты → Architecture design, tech stack выбор

## Phase 3: Implementation (Parallel)
Все работают параллельно в изолированных файлах:
- @frontend-dev: UI components, state management
- @backend-dev: API endpoints, database schema
- @integration-dev: Third-party services integration
- @qa-specialist: Test suites (unit, integration, E2E)

## Phase 4: Quality Assurance (Sequential)
Последовательная проверка всех результатов Phase 3:
- @qa-specialist: Manual testing, exploratory testing
- @security-engineer: Security review, vulnerability scanning
- Финальный code review

## Phase 5: Deployment
- @devops-engineer: CI/CD pipeline, deployment, monitoring setup

## Структура документации
Каждый agent сохраняет output в:
`docs/features/[feature-name]/[agent-name].md`

## Метрики успеха
- Time to market: сколько времени от идеи до production
- Quality score: coverage, security issues, performance
- Team efficiency: параллельная работа vs последовательная
