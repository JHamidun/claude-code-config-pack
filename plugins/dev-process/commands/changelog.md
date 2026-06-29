---
description: Автоматическая генерация changelog из git commits и PRs
argument-hint: [version number, e.g., v2.1.0]
---

# 📝 Changelog Generator: $ARGUMENTS

Создай changelog для версии: **$ARGUMENTS**

## Process:

### 1. Git Analysis
Fetch commits since last release, group by type (Conventional Commits)

### 2. GitHub Integration
Fetch PR details, closed issues

### 3. Format CHANGELOG.md
Based on Keep a Changelog format

### 4. Generate Release Notes
Create GitHub Release

### 5. Distribution
- Commit changelog
- Create git tag
- Notify team

