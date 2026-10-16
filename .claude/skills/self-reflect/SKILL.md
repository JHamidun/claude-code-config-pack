---
name: self-reflect
description: "Разбор недавних ошибок и паттернов, генерация правок для rules/skills. Триггеры: «проанализируй себя», «какие ошибки повторяются»."
---

# Self-Reflect: Continuous Improvement

Analyze past sessions and errors to generate actionable improvements.

## Process

### Phase 1: Gather Data

> Пустой ответ источника — это НЕ «ошибок не было». Если источник вернул ноль строк
> или его данные старше запрошенного периода, пиши в отчёт строку
> `источник недоступен: <источник> — <причина>` и не заполняй по нему раздел.
> `tools/vector_memory.py` не использовать: хранилище (Qdrant в `~/.claude/vector-memory/`)
> не пополняется с 30.01.2026. Опаснее пустоты: поиск отвечает exit 0 и НЕПУСТЫМ
> списком — свежими на вид записями февраля, которые легко принять за текущие
> (проверено запуском 06.09.2026).

1. **Recent errors from memory**:
```bash
python ~/.claude/scripts/memory_find.py "ошибка баг что чинили"
python ~/.claude/scripts/memory_vec.py search "ошибка баг что чинили"
```

2. **Recent decisions**:
```bash
python ~/.claude/scripts/memory_find.py "решение почему выбрали"
```

3. **Recent learnings**:
```bash
python ~/.claude/scripts/memory_find.py "паттерн грабли научился"
```

4. **Subagent usage patterns**:
```bash
# ВНИМАНИЕ: logs/subagents.log не пополняется с 01.02.2026 — сначала проверь дату,
# и если файл не новее разбираемого периода, пиши «источник недоступен» вместо выборки.
powershell -c "(Get-Item $env:USERPROFILE\.claude\logs\subagents.log).LastWriteTime"
powershell -c "Get-Content $env:USERPROFILE\.claude\logs\subagents.log -Tail 50"
```

### Phase 2: Analyze Patterns

For each error/issue found:
1. Has this type of error occurred before?
2. What was the root cause?
3. Could a rule/skill/hook have prevented it?
4. What's the fix pattern?

### Phase 3: Generate Improvements

Categories:
- **New rule** -> add to `~/.claude/rules/`
- **Updated routing** -> modify `routing.md`
- **New skill** -> add to `~/.claude/skills/`
- **Hook adjustment** -> modify `settings.json`
- **Memory entry** -> заметка в `~/.claude/projects/<project>/memory/` + указатель в `MEMORY.md`

### Phase 4: Apply & Save

For each improvement:
```bash
python ~/.claude/tools/search_chats.py learn "[improvement description]" "self-improvement"
```

## Report Format

```markdown
# Self-Reflection Report

## Errors Analyzed
1. [Error] -> [Root cause] -> [Fix applied]

## Recurring Patterns
- Pattern: [description]
  - Frequency: N times
  - Improvement: [what to change]

## Improvements Generated
- [ ] [Rule/skill/hook change description]

## Metrics
- Errors analyzed: N
- Patterns found: N
- Improvements proposed: N

## Источники
- <источник>: N записей за период | источник недоступен: <причина>
```

## Rules
- Be honest about mistakes
- Focus on systemic fixes, not one-off patches
- Prioritize by frequency x impact
- Save findings to memory (`search_chats.py learn` + заметка в `memory/`)
- Пустой источник называй пустым: «источник недоступен», а не «паттернов не найдено»
