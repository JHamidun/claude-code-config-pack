# Quality gates — справочник (читается ПО ТРЕБОВАНИЮ)

Вынесено из `rules/quality-gates.md` 06.09.2026. Здесь то, что нужно не в каждой
задаче, а в конкретном режиме: архитектурное ревью, судейство двух вариантов,
гейт дорогого артефакта. Ядро правила («что делать всегда») осталось в `rules/`.

---

## Error & Rescue Map — для архитектурных ревью

При ревью нового кода заполняй таблицу целиком, а не «на глаз»:

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

Любая строка с `RESCUED=N` + `TEST=N` + `USER SEES=Silent` → **CRITICAL GAP**.
Смысл таблицы в том, что она заставляет назвать КЛАСС исключения: «обработать
ошибки» — это не решение, а обещание.

---

## Position-Bias Guard для LLM-as-Judge

Когда судья-LLM выбирает лучший из двух вариантов (копирайт, дизайн, КП, фикс,
ревью, «оставить или откатить»):

* LLM систематически предпочитает **ПЕРВЫЙ** вариант. Прогоняй ОБА порядка:
  A-vs-B и B-vs-A.
* Keep кандидата ТОЛЬКО при перевесе голосов (2:0); ничья → держится текущий
  чемпион.
* Решение принимается по голосам двустороннего сравнения, а **не** по
  самоотчётной цифре автора.
* Генератор НИКОГДА не судит свою работу — оценщик в отдельном контексте.
  Промпт судьи: «Judge quality only; do not favor a version because it appears
  first; if equivalent, tie.»

Полный паттерн — `skills/verifier/references/gan-adversarial-improve.md`.

---

## Adversarial Role Gate (SHARP)

Для дорогих и необратимых артефактов — публикуемые посты, оферы, КП,
shipping-код, направления рисёрча — гейт отдельной ролью **Critic**.

Оценка SHARP: Sharpness / Horizon / Asymmetry / Resistance / Parsimony, каждая
1–5, итого /25. **Pass ≥18**; ниже — вернуть автору с тремя самыми жёсткими
критиками.

Варьирует *позицию*, а не модель (одной модели достаточно) — поэтому дополняет
cross-*model* validation, а не заменяет её. Дешёвый обратимый вывод гейтить
не надо: цена гейта тогда выше цены ошибки.

Разбор — `skills/autonomous-agent-creator/references/adversarial-agent-pairs-pattern.md`.

---

## Типичные ошибки среды

| Ошибка | Решение |
|--------|---------|
| API key not found | Читай из `~/.claude/.credentials.master.env` |
| Image format mismatch | Определяй формат перед сохранением (см. `rules/security.md`) |
| Model not found (Gemini) | Сверься с `config/models.md` |
| Rate limit exceeded | Добавь задержки между запросами |
| Connection refused | `ssh your-server "docker ps"` |

---

## Почему Makoto не установлен

Конфликт с трейлером `Co-Authored-By` плюс ~500 мс на каждом вызове инструмента.
