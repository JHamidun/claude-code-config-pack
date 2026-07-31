# CRASH-SAFE PROTOCOL — вставка в COMMON каждой Workflow-волны

> Канонический блок. Вставлять ДОСЛОВНО в template-literal COMMON каждого workflow-скрипта
> (после архитектурных правил, перед "Report honestly"). Плейсхолдер `<WAVE>` заменить
> на имя волны (например, `news-w6`). Стоимость: ~200 токенов на агента, окупается
> первым же обрывом (session limit, крэш, kill).

```text
CRASH-SAFE PROTOCOL (mandatory):
- Progress file: ${HOME}/.claude/workflows-progress/<WAVE>/<your-agent-label>.progress.md (create dirs if needed).
- FIRST ACTION on start: read your progress file. If it exists, you are a RESUMED run: trust its RECON summary (do not redo discovery), quickly re-verify claimed EDITs (grep/md5 the target files — cheap), then continue from the first unfinished step.
- APPEND one line to the file after EVERY completed step, immediately, via Bash append (echo '...' >> file):
  [HH:MM] RECON: <3-6 lines of key facts: live paths, topology, anchors, gotchas — enough for a resumed run to skip discovery>
  [HH:MM] EDIT <file>: <what landed> (backup: <path>)
  [HH:MM] VERIFY <what>: <result>
  [HH:MM] DONE: <final one-line summary>
- Write the RECON line the moment discovery is complete — it is the most valuable checkpoint.
- Long generation/backfill loops must checkpoint into their durable target (DB UPSERT / skip-if-done), not into memory.
```

## Почему так
- Session limit / крэш убивает агента с контекстом — всё, что не на диске, потеряно
  (прецедент: волна 5 news.your-domain.com, 2026-07-03, 345K токенов разведки).
- `resumeFromRunId` кэширует только завершённые agent()-вызовы — прогресс-файл закрывает
  дыру для убитых in-flight.
- Путь стабильный (не session-scratchpad!) — резюм из НОВОЙ сессии тоже найдёт файлы.

## Оркестратору (не агентам)
- Мельче нарезай агентов — кэш resume работает поагентно.
- Перед ре-раном переименуй чистые бэкапы (`.pre-crash-clean`) — иначе ре-ран заклобберит их полуправкой.
- При фейлах `session limit · resets 7am` — ScheduleWakeup на ~07:05 МСК с resumeFromRunId.
- После успеха волны: удалить ${HOME}/.claude/workflows-progress/<WAVE>/ (мусор не копим).
