---
description: "Codebase health: /health bugs|cleanup|deps|reuse|security — детекция→фикс→верификация инлайн. Заменяет пять команд /health-bugs … /health-security."
argument-hint: "bugs | cleanup | deps | reuse | security"
---

# Health Check — `/health <mode>`

Единая точка входа в codebase health. Аргумент: `$ARGUMENTS`.

**Ты САМ оркестратор.** Отдельного orchestrator-агента не спавнить.
Task-tool — только под воркеров. Quality gates — инлайн через Bash.

## Режимы

| Режим | Файл режима (`skills/health-inline/references/modes/`) | Бриф детекции | Бриф фикса | Что делает |
|---|---|---|---|---|
| `bugs` (= `bug`) | `bug.md` | Bug Hunter | Bug Fixer | Баги: type-check/build, уязвимости, мёртвый код, debug-стейтменты |
| `cleanup` | `cleanup.md` | Dead Code Hunter | Dead Code Remover | Мёртвый код: неиспользуемые импорты/экспорты, закомментированные блоки, Knip |
| `deps` | `deps.md` | Dependency Auditor | Dependency Updater | Зависимости: аудит и обновление по одной, с откатом package.json + lockfile |
| `reuse` | `reuse.md` | Reuse Hunter | Reuse Fixer | Дубли кода: консолидация в Single Source of Truth (приоритеты high/medium/low, critical нет) |
| `security` | `security.md` | Security Scanner | Vulnerability Fixer | Уязвимости: SQLi, XSS, auth/authz, RLS, хардкод секретов |

Колонки «бриф» — это заголовки секций внутри
`skills/health-inline/references/worker-prompts/<mode>.md`, а не типы агентов:
`subagent_type: "bug-hunter"` упадёт с `Agent type not found`. Воркер спавнится
как `subagent_type: "general-purpose"`, `model: "fable"`, а текст брифа
вставляется в промпт целиком.

## Вызов без аргумента

Если `$ARGUMENTS` пуст — **НЕ выбирать режим за пользователя и НЕ запускать
ничего**. Вывести список пяти режимов с одной строкой описания каждого (колонка
«Что делает» выше) и спросить, какой запускать. Ждать ответа.

Если аргумент есть, но это не один из `bugs|bug|cleanup|deps|reuse|security` —
сказать, что режим неизвестен, показать тот же список, не угадывать.

## Что делать с валидным режимом

1. Прочитать `skills/health-inline/SKILL.md` — таблица режимов и общий скелет.
2. Прочитать `skills/health-inline/references/modes/<файл режима из таблицы>` —
   полный воркфлоу. Для `bugs` файл называется `bug.md`.
3. Выполнить фазы напрямую.

```
Pre-flight → Detect → [Fix/Remove/Update/Consolidate by Priority] → Verify → Report
```

**Quality gates**: `pnpm type-check && pnpm build` (инлайн, после каждого приоритета)
**Max iterations**: 3
**Откат при падении гейта**: бэкапы в `.tmp/current/backups/` + changes-log режима
(либо скилл `rollback-changes`).
