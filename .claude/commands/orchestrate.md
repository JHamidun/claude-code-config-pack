---
description: Автоматическая оркестрация разработки фичи с координацией всех агентов
argument-hint: [описание фичи или задачи]
---

# Оркестрация: $ARGUMENTS

Собери и выполни полный workflow разработки. Прогресс веди через TodoWrite,
промежуточные артефакты складывай в `docs/features/[feature-name]/` — иначе
следующий агент не найдёт контекст предыдущего.

## Выбор подхода

**Кастомные агенты** — задача >1 дня, нужна узкая экспертиза (security,
архитектура) или части делаются параллельно.
**Встроенные субагенты** (`Plan` → `general-purpose`) — задача <1 дня, прототип.

## Фазы (кастомные агенты)

| Фаза | Режим | Агенты |
|------|-------|--------|
| 1. Анализ | последовательно | `orchestrator` → `business-analyst` → `software-architect` |
| 2. Разработка | **параллельно** | `backend-dev` ‖ `frontend-dev` ‖ `integration-dev` |
| 3. Качество | последовательно | `code-reviewer` → `test-writer` → `security-engineer` |
| 4. Деплой | последовательно | `devops-engineer` (CI/CD + staging) |

Фаза 2 параллелится только если агенты не трогают одни файлы — иначе правки
затрут друг друга.

## Слэш-команды по ходу

- `/deep-research "best practices для [feature]"` — до планирования
- `/code-review src/features/X/` — после реализации
- `/test-frontend http://localhost:3000 e2e` — если есть UI
- `/kimi-reasoning "Security implications of …"` — auth, платежи, внешние API
- `/deploy staging` — с проверками и rollback

## Правила

- Security-скан обязателен для auth и интеграций с внешними API — там цена
  пропущенной дыры несопоставима со временем скана.
- Test coverage >80% перед PR.
- Этапы не пропускать ради скорости.
- Ветка: `feature/<kebab-case-задачи>`, коммиты Conventional + ссылка на Linear
  (`feat: Add X (LINEAR-123)`), атомарные.
- Linear issue и Slack-уведомления — только если соответствующий MCP доступен;
  недоступен — молча пропусти, не имитируй отправку.

## Формат отдачи

Верни execution plan в JSON:

```json
{
  "task": "краткое описание",
  "complexity": "simple|medium|complex",
  "estimated_time": "X hours",
  "phases": [
    {
      "phase_number": 1,
      "name": "Research & Planning",
      "type": "sequential|parallel",
      "steps": [
        {"step": "/deep-research …", "output_location": "docs/features/X/research.md", "estimated_time": "5 min"}
      ]
    }
  ],
  "success_criteria": ["тесты зелёные", "review чист", "coverage >80%"],
  "deliverables": ["working code", "tests", "documentation"]
}
```

Дошёл до PR и пост-мержа — формат описания PR, лестница feature-flag и список
пост-мерж действий в `commands/references/orchestrate.md`.
