---
name: run-quality-gate
description: "Прогон quality gate: type-check, build, tests, lint со структурным отчётом. Служебный. Триггеры: «прогони проверки», «проверь перед мержем»."
allowed-tools: Bash, Read
---

# Run Quality Gate

Execute validation commands as quality gates with structured error reporting.

## When to Use

- Type-check, build, test, lint validation
- Orchestrator phase validation
- Worker self-validation

## Input

```json
{
  "gate": "type-check|build|tests|lint|custom",
  "blocking": true,
  "custom_command": "pnpm custom-validate"
}
```

## Gate Commands

**Единый источник команд, таймаута, кодов возврата и регэкспов ошибок —
`gate-mappings.json` рядом с этим файлом.** Таблица ниже — его выжимка для чтения;
при расхождении верна JSON, править надо её.

| Gate | Command (при pnpm-репозитории) |
|------|---------|
| type-check | `pnpm type-check` |
| build | `pnpm build` |
| tests | `pnpm test` |
| lint | `pnpm lint` |
| custom | `custom_command` value |

**Пакетный менеджер сначала определи, а не подставляй `pnpm` вслепую.** Команды в
`gate-mappings.json` записаны под pnpm, потому что так устроены рабочие репозитории
владельца, но навык объявлен общим. На npm/yarn/bun-репозитории `pnpm …` вернёт
`exit_code=127`, а это по таблице ниже «failed» — блокирующий гейт остановит работу
не из-за качества кода, а из-за отсутствия pnpm. Развилка:

- есть `pnpm-lock.yaml` → `pnpm <gate>`;
- есть `yarn.lock` → `yarn <gate>`;
- есть `bun.lockb` → `bun run <gate>`;
- иначе `npm run <gate>` (у npm нужен именно `run`: `npm test` работает, `npm type-check` нет);
- скрипта с таким именем нет в `package.json` → это не «failed», а «гейт не настроен» —
  так и доложи, не выдавай за провал качества.

То же различие проговаривает всегда загруженное `rules/quality-gates.md`
(«`pnpm type-check` **или** `npm run type-check`»), а сосед `health-inline` честно
сузил себя в описании до «Только pnpm+TypeScript-репо».

## Process

1. **Map gate to command** - возьми `gates.<gate>.command` из `gate-mappings.json`,
   подставь пакетный менеджер репозитория (развилка выше). Validate custom_command if gate="custom"
2. **Execute via Bash** - Timeout: `timeout.milliseconds` из `gate-mappings.json` (5 минут),
   capture stdout/stderr
3. **Parse result** - по `exit_codes` из `gate-mappings.json`: 0 = passed, 1 = general error,
   127 = command not found, -1 = timeout
4. **Extract errors** - по `gates.<gate>.error_patterns` из `gate-mappings.json`
   (напр. type-check: `error TS\d+`, `Type '.+' is not assignable`, `Cannot find`;
   build: `ERROR in`, `Module not found`, `Build failed`). Файл не читается → грубый
   фолбэк: строки со словами "error", "failed", коды TS####
5. **Determine action**:
   - Passed → action="continue"
   - Failed + blocking → action="stop"
   - Failed + non-blocking → action="warn"

## Output

```json
{
  "gate": "type-check",
  "passed": true,
  "blocking": true,
  "action": "continue",
  "errors": [],
  "exit_code": 0,
  "duration_ms": 2345,
  "command": "pnpm type-check",
  "timestamp": "2025-10-18T14:30:00Z"
}
```

## Examples

**Blocking gate passes**:
```json
{ "gate": "type-check", "blocking": true }
→ { "passed": true, "action": "continue", "errors": [] }
```

**Blocking gate fails** (stops workflow):
```json
{ "gate": "build", "blocking": true }
→ { "passed": false, "action": "stop", "errors": ["Module not found: missing-module"] }
```

**Non-blocking gate fails** (warns only):
```json
{ "gate": "lint", "blocking": false }
→ { "passed": false, "action": "warn", "errors": ["Missing semicolon"] }
```

## Error Handling

- **Timeout (5 min)**: Return failed with timeout error
- **Missing custom_command**: Return error
- **Command not found**: Return failed with exit_code=127 — и в `errors` напиши, что не
  найден сам инструмент (чаще всего `pnpm` в не-pnpm репозитории), а не что код плохой.
  Это повод сменить пакетный менеджер и перезапустить гейт, а не останавливать работу.

## Notes

- Exit code 0 always = success regardless of output
- Blocking flag only affects action, not passed status
- Error extraction is best-effort
