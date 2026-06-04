# Quality Gates

## Обязательные проверки после изменений
```bash
pnpm type-check   # или npm run type-check
pnpm build         # production build СТРОЖЕ чем tsc
pnpm test          # опционально
pnpm lint          # опционально
```

## Systematic Debugging (ОБЯЗАТЕЛЬНО при багах)
4 фазы:
1. Root Cause Investigation — воспроизведи, проследи данные
2. Pattern Analysis — сравни с работающим кодом
3. Hypothesis Testing — одна гипотеза, минимальное изменение
4. Implementation — failing test → fix → verify

Always find root cause before fixing. If you can't find it — say so honestly, don't guess.

## Prime Directives (inspired by <owner>/<repo>)

1. **Make failures visible.** Every failure mode should be surfaced — to the system, the team, and the user. Silent failures are the hardest bugs to diagnose, so ensure all error paths are logged or exposed.
2. **Every error has a name.** Don't say "handle errors." Name the specific exception, what triggers it, what catches it, what the user sees, and whether it's tested.
3. **Data flows have shadow paths.** Every data flow has: happy path, nil input, empty input, upstream error. Trace all four for every new flow.

## Error & Rescue Map (для архитектурных ревью)

При ревью нового кода — заполняй таблицу:
```
METHOD/CODEPATH      | WHAT CAN GO WRONG     | EXCEPTION CLASS
---------------------|----------------------|------------------
Service#call         | API timeout          | TimeoutError
                     | API 429              | RateLimitError
                     | Malformed response   | ParseError

EXCEPTION CLASS      | RESCUED? | ACTION          | USER SEES
---------------------|----------|-----------------|----------
TimeoutError         | Y        | Retry 2x        | "Retry later"
RateLimitError       | Y        | Backoff          | Transparent
ParseError           | N ← GAP  | —                | 500 ← BAD
```
Любая строка с RESCUED=N + TEST=N + USER SEES=Silent → **CRITICAL GAP**.

## LLM Output Trust Boundary

LLM-generated values (emails, URLs, names) ДОЛЖНЫ валидироваться перед:
- Записью в БД
- Отправкой по email/webhook
- Использованием как параметры запросов

Добавляй guards: `EMAIL_REGEXP`, `URI.parse`, `.strip`, type/shape checks.

## What Real Verification Looks Like (from Claude Code source)

Verification means **proving the code works**, not confirming it exists.

- Run tests **with the feature enabled** — not just "tests pass"
- Run typechecks and **investigate errors** — don't dismiss as "unrelated"
- Be skeptical — if something looks off, dig in
- **Test independently** — prove the change works, don't rubber-stamp
- Try **edge cases and error paths** — don't just re-run what the implementation ran
- **Investigate failures** — don't dismiss as unrelated without evidence
- For implementation: "Fix the root cause, not the symptom"

A verifier that rubber-stamps weak work undermines everything.

## Cross-Model Validation (Advisor Pattern)

For architectural decisions and complex tradeoffs:
- Request "second opinion" via `gpt-agent` or `gemini-agent`
- Compare approaches before committing to implementation
- Use when: system design, API design, security boundaries, data model choices

## Типичные ошибки
| Ошибка | Решение |
|--------|---------|
| API key not found | Читай из ~/.claude/.credentials.master.env |
| Image format mismatch | Определяй формат перед сохранением |
| Model not found (Gemini) | Используй config/models.md |
| Rate limit exceeded | Добавь delays между запросами |
| Connection refused | ssh your-server "docker ps" |
