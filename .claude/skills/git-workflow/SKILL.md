---
name: git-workflow
description: "Git operations: commits, branches, PRs, merge conflicts, history analysis. Triggers: «merge conflict», «create a branch», «open a PR»."
---

# Git Workflow Skill

## Overview

Навык для работы с Git: коммиты, ветки, PR, разрешение конфликтов, анализ истории.

## When to Use

- Создание осмысленных commit messages
- Работа с ветками и merge
- Разрешение конфликтов
- Анализ истории изменений
- Code review через git

## Commit Message Format

### Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Описание |
|------|----------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `docs` | Документация |
| `style` | Форматирование (не влияет на код) |
| `refactor` | Рефакторинг |
| `perf` | Оптимизация производительности |
| `test` | Добавление тестов |
| `chore` | Обслуживание (build, deps) |
| `ci` | CI/CD изменения |

### Примеры

```bash
# Фича
feat(auth): add OAuth2 login with Google

# Баг-фикс
fix(api): handle null response in user endpoint

# Рефакторинг
refactor(db): extract connection pool to separate module

# Breaking change
feat(api)!: change response format for /users endpoint

BREAKING CHANGE: Response now returns array instead of object
```

## Branch Strategy

### Git Flow

```
main          ─────●─────────●─────────●─────
                   ↑         ↑         ↑
release      ────●─┴───●───●─┴───●───●─┴────
                 ↑     ↑       ↑
develop    ────●─┴──●──┴──●──●─┴──●──●──────
               ↑    ↑     ↑      ↑
feature   ───●─┴──●─┘   ●─┴────●─┘
```

### Naming

```bash
# Features
feature/add-user-auth
feature/JIRA-123-payment-integration

# Bugfixes
bugfix/fix-login-redirect
hotfix/critical-security-patch

# Other
release/v1.2.0
chore/update-dependencies
```

## Common Operations

### Branches

```bash
# Создать и переключиться
git checkout -b feature/new-feature

# Список веток
git branch -a

# Удалить ветку
git branch -d feature/old-feature
git push origin --delete feature/old-feature

# Переименовать
git branch -m old-name new-name
```

### Commits

```bash
# Staged changes
git add -p  # интерактивно

# Commit
git commit -m "feat: add feature"

# Amend последний коммит
git commit --amend -m "new message"

# Squash коммиты
git rebase -i HEAD~3
```

### Merge & Rebase

```bash
# Merge с сохранением истории
git merge --no-ff feature/branch

# Rebase (линейная история)
git rebase main

# Интерактивный rebase
git rebase -i HEAD~5
```

### Stash

```bash
# Сохранить изменения
git stash
git stash push -m "work in progress"

# Список
git stash list

# Применить
git stash pop
git stash apply stash@{0}

# Удалить
git stash drop stash@{0}
```

## Conflict Resolution

### Процесс

```bash
# 1. Увидели конфликт
git merge feature/branch
# CONFLICT (content): Merge conflict in file.py

# 2. Смотрим статус
git status

# 3. Открываем файл, ищем маркеры
<<<<<<< HEAD
current changes
=======
incoming changes
>>>>>>> feature/branch

# 4. Редактируем, убираем маркеры

# 5. Добавляем и коммитим
git add file.py
git commit -m "fix: resolve merge conflict in file.py"
```

### Стратегии

```bash
# Принять наши изменения
git checkout --ours file.py

# Принять их изменения
git checkout --theirs file.py

# Отменить merge
git merge --abort
```

## History Analysis

```bash
# Красивый лог
git log --oneline --graph --all

# Поиск по сообщению
git log --grep="fix"

# Поиск по автору
git log --author="name"

# Изменения в файле
git log -p -- path/to/file

# Кто менял строку
git blame file.py

# Поиск когда появился баг
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# тестируем... git bisect good/bad
git bisect reset
```

## Pull Request Best Practices

### Checklist

- [ ] Понятный заголовок PR
- [ ] Описание что и зачем
- [ ] Связь с issue/task
- [ ] Все тесты проходят
- [ ] Код проверен линтером
- [ ] Нет конфликтов с main
- [ ] Self-review проведён

### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Test Plan
- [ ] Unit tests pass
- [ ] Manual testing done

## Screenshots (if UI)

## Related Issues
Closes #123
```

## Tips

1. **Коммиты атомарные** - один коммит = одно логическое изменение
2. **Сообщения в imperative** - "add feature" не "added feature"
3. **Rebase перед merge** - чистая история
4. **Не force push в main** - никогда
5. **Squash перед PR** - если много мелких коммитов
6. **git stash** - для быстрого переключения контекста
