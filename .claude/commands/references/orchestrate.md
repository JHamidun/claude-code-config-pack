---
description: "Справочник к /orchestrate (не вызывать напрямую): формат PR, пост-мерж, feature flags"
---

# orchestrate — справочник

Читать, когда дошёл до создания PR или пост-мерж автоматизации и нужен принятый
здесь формат (Linear + Slack + docs/features), а не свой.

## PR description (шаблон)

Title: `feat: [Feature name] (LINEAR-123)`

```markdown
## What / Why / How
[что реализовано] / [бизнес-ценность] / [технический подход]

## Changes
- Component A: …
- Tests: …

## Testing
- [x] Unit (coverage: X%) / Integration / E2E
- Manual: happy path, error cases, edge cases

## Performance Impact
Bundle size ±X KB · API latency X ms · DB queries

## Rollout Plan
staging → QA sign-off → feature flag → мониторинг → 10% → 50% → 100%

## Related
Beads: bd-123 · Docs: docs/features/X/ · Depends on / Blocks

## Post-Merge
- [ ] `bd close bd-123`
- [ ] Анонс команде (канал, которым команда пользуется)
- [ ] Roadmap обновлён
```

Создание: `gh pr create --title … --body-file PR_DESCRIPTION.md --base main --head "$BRANCH" --reviewer team-leads --label "feature,needs-review"`

## Пост-мерж

1. `git branch -d "$BRANCH"; git push origin --delete "$BRANCH"`
2. `bd close <id>` (в комментарии — время мержа и деплоя).
3. `changelog-generator` → CHANGELOG.md.
4. Deploy staging + smoke tests, уведомить QA.
5. Алерты и метрики на новую фичу.
6. Доки: API (если менялся контракт), user-facing, вики.

## Feature flags — лестница выката

Внутренняя команда (allowlist) → 10% (день 3) → 50% (день 7) → 100% (день 14).
Первый деплой ВСЕГДА с `enabled: false`: флаг включается отдельным действием,
иначе выкат и деплой нельзя откатить по отдельности.
