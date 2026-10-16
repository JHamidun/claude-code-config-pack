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
> перепроверил собственную работу сессии** — доки про это прямо. Проверка
> работы ДРУГОГО остаётся.

| Задача | Субагент | Почему |
|--------|----------|--------|
| Код-ревью | Agent `code-reviewer` | Специализированный чеклист |
| Поиск багов | Agent `bug-hunter` → `bug-fixer` | Systematic debugging |
| Написание тестов | Agent `test-writer` | Mocking, coverage |
| Security-аудит | Agent `security-scanner` | OWASP Top 10 |
| Поиск по кодбазе | Task(subagent_type="Explore") | Экономия контекста |
| Performance | Agent `performance-optimizer` | Core Web Vitals |
| Dead code | Agent `dead-code-hunter` | Knip, точное детектирование |
| Баги / security / мёртвый код / дубли / зависимости — с фиксом, без отдельных агентов | `/health bugs\|security\|cleanup\|reuse\|deps` (Skill `health-inline`) | Детект→фикс→верификация, откат по changes-log; фикс отдельным воркером |
| Аудит/ревью/разбор, где **нужно несколько точек зрения** и выводу надо верить | Skill `agent-swarm` | Как собрать рой, которому можно верить: калибровка каждой линзы (пустой результат говорит о ПРОВЕРКЕ, а не о предмете), опровержение вместо подтверждения, CRASH-SAFE-PROTOCOL дословно, подключение Кодекса и Ox воркерами. Механику `Workflow` не дублирует |

## Масштаб: несколько волн разом — это норма, а не риск

Кап `min(16, ядер − 2)` действует **внутри одного Workflow** и настройкой не
обходится. Поэтому путь к сотням агентов один: **запускать несколько волн
параллельно**. Ограничивать их числом не нужно.

`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` в `settings.json` держать выше суммарной
потребности (десять волн ≈ 160 одновременных), иначе он станет узким местом.

**Обрыв роя ≠ поломка механизма.** Самая частая причина, когда агенты умирают
разом и исчезают из списка задач, — **упёрлись в лимит подписки**. Лечится не
уменьшением параллелизма, а сменой подписки и восстановлением:

1. **Не перезапускать с нуля.** `Workflow({scriptPath, resumeFromRunId})` —
   завершённые `agent()` возвращаются из кэша мгновенно, живыми пойдут только
   недоделанные.
2. Перед ре-раном переименовать чистые бэкапы в `.pre-crash-clean` — иначе
   повтор заклобберит их полуправкой.
3. Проверить `workflows-progress/<волна>/` — то, что агенты успели записать по
   ходу, уцелело и часто закрывает бóльшую часть работы.

Именно поэтому CRASH-SAFE PROTOCOL обязателен: он делает обрыв дешёвым, и тогда
масштаб можно не ограничивать вовсе.

| Anti-pattern | Why it fails | Fix |
|--------------|-------------|-----|
| Ре-ран упавшего роя с нуля | Теряется всё, что уже сделано и закэшировано | `Workflow({scriptPath, resumeFromRunId})` — готовые вернутся из кэша мгновенно |
| Урезать параллелизм после обрыва | Обрыв обычно от лимита подписки, а не от числа агентов — урезание лечит не то | Сменить подписку, восстановиться через resume; масштаб не трогать |
