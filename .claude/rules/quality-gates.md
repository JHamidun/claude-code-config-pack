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

## Prime Directives (inspired by garrytan/gstack)

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

## Anti-Claim-Fabrication (self-check перед заявлениями)

| Вид | Проверка перед заявлением |
| --- | --- |
| **UNFULFILLED** («создал X») | X реально на диске / в результатах последнего tool call? Не изобретай — перечитай, а не вспоминай. |
| **MISREPORTED** («тесты прошли») | Последний РЕАЛЬНО увиденный вывод тест-раннера — зелёный? Не пересказывай ожидаемое как случившееся. |
| **HOLLOWED** (тест/чек ослаблен) | Не подменил ли я строгую проверку (`==`) на мягкую (`startswith`), не замаскировал ли exit code (`\|\| true`), не выхолостил ли тело чекера (`return True`/`pass`)? |
| **SELF-CONTRADICTING** | Не противоречит ли это заявление открытому todo/обещанию из этой же сессии? |
| **BYPASSED** | Не отключил ли я гейт/хук/линт, чтобы протолкнуть блокировку, вместо того чтобы её устранить? |
| **FABRICATED ACTION** («я запустил X») | Был ли реальный tool call за этим заявлением в этом ходе, или это пересказ намерения? |
| **PHANTOM CITATION** (URL/SHA/цитата) | Видел ли я это РЕАЛЬНО в выводе tool call этой сессии, или подставил по памяти/правдоподобию? |

Сторонние hook-инструменты проверки заявлений (например, Makoto) в пак намеренно не включены: конфликт с Co-Authored-By трейлером + ~500мс на каждый tool call.

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

## Position-Bias Guard для LLM-as-Judge (auto-improve)

Когда судья-LLM выбирает лучший из 2 вариантов (копирайт/дизайн/КП/фикс/ревью, «оставить или откатить»):
- LLM систематически предпочитает ПЕРВЫЙ вариант. Прогоняй ОБА порядка: A-vs-B и B-vs-A.
- Keep кандидата ТОЛЬКО при перевесе голосов (2:0); ничья → держится текущий чемпион.
- Решение по голосам двустороннего сравнения, НЕ по самоотчётной цифре автора.
- Генератор НИКОГДА не судит свою работу — оценщик в отдельном контексте. Промпт судьи: «Judge quality only; do not favor a version because it appears first; if equivalent, tie.»
- Полный паттерн: `skills/verifier/references/gan-adversarial-improve.md`.

## Adversarial Role Gate (SHARP)

Для дорогих/необратимых артефактов (публикуемые посты, оферы, КП, shipping-код, направления рисёрча) — гейт отдельной ролью **Critic**, оценка SHARP (Sharpness/Horizon/Asymmetry/Resistance/Parsimony, каждая 1-5, /25). **Pass ≥18**; ниже — вернуть автору с 3 самыми жёсткими критиками. Варьирует *позицию* (одна модель ок) — дополняет cross-*model* validation. Дешёвый обратимый вывод НЕ гейтить. См. `skills/autonomous-agent-creator/references/adversarial-agent-pairs-pattern.md`.

## YAGNI-иерархия (ponytail)

Перед написанием кода — пройди лестницу, остановись на первой ступени, которая держит:

1. **Нужно ли это вообще?** Спекулятивная потребность = скип, скажи об этом одной строкой.
2. **Уже есть в кодбазе?** Helper/util/паттерн рядом → переиспользуй. Сначала ищи, потом пиши.
3. **Stdlib умеет?** Используй stdlib.
4. **Нативная фича платформы?** `<input type="date">` вместо picker-либы, CSS вместо JS, DB constraint вместо кода.
5. **Уже установленная зависимость решает?** Используй её. Новую не добавляй ради пары строк.
6. **Можно одной строкой?** Одна строка.
7. **Только потом** — минимальный работающий код.

Правила: никаких абстракций «на будущее» (interface с одной имплементацией, factory для одного продукта); удаление лучше добавления; скучное лучше умного. Лестница сокращает РЕШЕНИЕ, не ПОНИМАНИЕ — сначала прочитай задачу и код полностью, потом ленись. НЕ упрощать: валидацию на trust boundaries, error handling от потери данных, security, явно запрошенное.
