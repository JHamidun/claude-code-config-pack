---
description: Начать работу над feature из Linear issue с полной автоматизацией
argument-hint: [Linear issue ID, e.g., PROJ-123]
---

# 🚀 Start Feature: $ARGUMENTS

Автоматизирую весь workflow для issue: **$ARGUMENTS**

> ⚠️ **Плагин `linear` выключен** — инструментов `mcp__linear__*` в сессии нет,
> и шаг 1 взять требования оттуда не сможет. Либо включи плагин (`/plugin`),
> либо работай от локального трекера: `bd show <id>` (если beads установлен). Если
> ни того ни другого — попроси текст задачи у владельца; выдуманные критерии
> приёмки хуже отсутствующих.

## Process:

### 1. Fetch Issue (Linear MCP)
Get requirements, acceptance criteria

### 2. Technical Planning
Use @software-architect для design (режим ANALYSIS → DESIGN)

### 3. Estimation
Use /estimate command

### 4. Git Setup
Create feature branch

### 5. Implementation
Execute plan с agents

### 6. Testing
Run tests, check coverage

### 7. PR Creation
Create PR via GitHub MCP, link to issue

### 8. Post-PR
Update Linear, notify team

