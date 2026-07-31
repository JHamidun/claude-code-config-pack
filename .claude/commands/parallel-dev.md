---
description: Параллельная разработка фичи используя git worktrees
argument-hint: [название фичи]
---

# Параллельная разработка: $ARGUMENTS

Создай 3 параллельные имплементации используя git worktrees:

## Фаза 1: Подготовка
1. Создай worktrees для каждого подхода:
   - `git worktree add ../feature-performance feature/$ARGUMENTS-performance`
   - `git worktree add ../feature-ux feature/$ARGUMENTS-ux`
   - `git worktree add ../feature-maintainable feature/$ARGUMENTS-maintainable`

## Фаза 2: Параллельная разработка
2. Назначь специализированных агентов:
   - @software-architect: Подход A (performance-focused) в worktree feature-performance
   - @frontend-dev: Подход B (UX-focused) в worktree feature-ux
   - @backend-dev: Подход C (maintainability-focused) в worktree feature-maintainable

3. Каждый агент работает независимо в своём worktree

## Фаза 3: Сравнение и выбор
4. Сравни результаты всех подходов:
   - Производительность (benchmarks)
   - User experience (простота использования)
   - Поддерживаемость кода (читаемость, тестирование)

5. Выбери лучший подход или объедини лучшие части

## Фаза 4: Очистка
6. Удали неиспользованные worktrees:
   - `git worktree remove ../feature-performance`
   - `git worktree remove ../feature-ux`
   - `git worktree remove ../feature-maintainable`

Каждый agent сохраняет результаты в `docs/features/$ARGUMENTS/[agent-name].md`
