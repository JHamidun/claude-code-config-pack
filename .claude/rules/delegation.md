# Делегирование и масштабирование

## Уровни
- **Level 0** (делай сам): 1 файл, typo, простой import
- **Level 1** (1 агент): Feature в 2-5 файлов
- **Level 2** (orchestrator): Epic, 5+ файлов, несколько систем
- **Level 3** (полный workflow): Проект, planning + agents + QA

## Key Principle: Synthesize Before Delegating (from Claude Code source)

When writing prompts for workers, avoid delegating understanding — delegate work:
- "Based on your findings, fix the bug" 
- "Based on the research, implement it"
- "The worker found an issue, please fix it"

Эти фразы **делегируют понимание** вместо работы. Всегда **синтезируй** результаты research'а сам, затем давай worker'у конкретную спецификацию с file paths, line numbers, и что именно менять.

**Хороший промпт:** "Fix null pointer in src/auth/validate.ts:42. The user field is undefined when session expires. Add null check before user.id access — if null, return 401."

**Плохой промпт:** "Based on your findings, fix the auth bug."

## Continue vs Spawn Decision

| Ситуация | Механизм | Почему |
|----------|----------|--------|
| Research нашёл файлы для редактирования | **Continue** (SendMessage) | Worker уже имеет файлы в контексте |
| Research широкий, implementation узкий | **Spawn fresh** | Чистый контекст эффективнее |
| Исправление ошибки worker'а | **Continue** | Worker знает контекст ошибки |
| Верификация кода другого worker'а | **Spawn fresh** | Верификатор должен смотреть свежими глазами |
| Полностью неправильный подход | **Spawn fresh** | Старый контекст заякорит на провальном пути |

## Purpose Statement в промптах

Всегда включай цель в промпт worker'а:
- "This research will inform a PR description — focus on user-facing changes."
- "I need this to plan implementation — report file paths, line numbers, type signatures."
- "Quick check before merge — just verify the happy path."

## Куда какая задача идёт

> Карта, а не приказ делегировать. Тривиальный однофайловый случай (Level 0,
> меньше 5 вызовов инструментов) делается сам — накладные расходы на спавн там
> больше самой работы.
>
> ⚠️ Порог поднялся: Opus 5 делегирует **охотнее** прежних моделей
> («delegates more readily than earlier models»), поэтому сдерживать надо не
> число воркеров, а поводы. И отдельно: **не спавнить субагента, чтобы он
> перепроверил собственную работу сессии** — доки про это прямо.

| Задача | Субагент | Почему |
|--------|----------|--------|
| Код-ревью | Agent `code-reviewer` | Специализированный чеклист |
| Поиск багов | Agent `bug-hunter` → `bug-fixer` | Systematic debugging |
| Написание тестов | Agent `test-writer` | Mocking, coverage |
| Security-аудит | Agent `security-scanner` | OWASP Top 10 |
| Поиск по кодбазе | Task(subagent_type="Explore") | Экономия контекста |
| Performance | Agent `performance-optimizer` | Core Web Vitals |
| Dead code | Agent `dead-code-hunter` | Knip, точное детектирование |
