> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Context Management Strategy

## Context Window Sizes

| Model | Window | Effective (after system prompt) |
|-------|--------|-------------------------------|
| Opus 5 | 1M tokens | ~900K usable |
| Sonnet 5 | 200K tokens | ~180K usable |
| Haiku 4.5 | 200K tokens | ~180K usable |

## When to /compact

- Context is >60% full (Claude will suggest this)
- After completing a major task before starting a new one
- When responses start losing earlier context
- After large file reads that are no longer needed
- **What it does:** Summarizes conversation, reduces token count by ~70%
- **Preserves:** Task progress, key decisions, file paths discussed

## When to /clear

- Starting a completely new, unrelated task
- Context is polluted with irrelevant information
- After a failed approach — fresh start is faster
- Debugging loops with no progress after 3+ attempts
- **What it does:** Wipes conversation history entirely
- **Before clearing:** Save any learnings to memory files

## When to Use Subagents (Agent tool)

- Task requires reading many files (saves main context)
- Independent research that doesn't need conversation history
- Parallel tasks that can run simultaneously
- Heavy exploration (Explore agent type)
- Code review, test writing, bug hunting (see delegation.md)
- **Key:** Subagent results are summarized back, not full context
- **Cost:** Each subagent has its own context window (usually Haiku/Sonnet)

## When to Use Plan Mode

- Complex multi-step implementation (5+ files)
- Need user alignment before execution
- Architecture decisions with tradeoffs
- Refactoring across multiple modules
- **Key:** Plan file persists across compacts

## Context-Saving Patterns

1. **Front-load critical info** — put key context at start of conversation
2. **Use CLAUDE.md** — persistent instructions loaded every session
3. **Use rules/** — auto-loaded every session, no context cost per message
4. **Use Memory** — save important learnings for future sessions
5. **Use TodoWrite** — track progress across compacts
6. **Reference files by path** — don't paste large files, read them on demand
7. **Batch related questions** — one conversation per topic area
8. **Summarize before compact** — ask Claude to list key findings first

## Дисциплина чтения больших источников

Книга/отчёт/лог целиком в контекст — самый дорогой способ узнать один факт. Skill-listing уже
съедает ~39.7% авто-загрузки; чтение книги на каждую главу стоит миллионы входных токенов.
Порядок: **сначала измерь, потом найди оффсет, потом читай срез.**

```bash
wc -w book.txt                      # 1. сколько там вообще (слова ≈ токены ×1.3)
grep -n "^#\|^Глава\|^Chapter" f    # 2. оффсеты заголовков — карта, а не текст
grep -c "конкретное утверждение" f  # 3. оно вообще есть? 0 → не читай, отвечай "нет в тексте"
sed -n "1200,1450p" book.txt        # 4. один срез
```

Затем `Read(file_path, offset=1200, limit=250)` вместо голого `Read` — голый Read большого
файла допустим, только когда действительно нужен весь файл.

- Проверка утверждения (`grep -c` = 0) стоит ~50 токенов вместо ~200K на чтение книги.
- Одна глава = один `sed`-срез; не тяни соседние «на всякий случай».
- Для длинных структурированных PDF есть дерево-индекс (PageIndex) — см. skill `research-docs`.
- Тот же порядок для логов: `grep -n ERROR` → `sed -n` вокруг найденной строки.

## Anti-Patterns

- Pasting entire files into chat (use Read tool instead)
- Голый `Read` книги/лога ради одного факта (см. «Дисциплина чтения больших источников»)
- Keeping stale context from completed tasks
- Running many sequential searches in main context (use Explore agent)
- Not compacting before starting new work
- Re-reading the same file multiple times in one session
- Asking Claude to "remember" things (use memory files instead)
- Long conversations spanning multiple unrelated topics
- Requesting verbose explanations when a code snippet suffices

## Token Budget Rules of Thumb

| Content | Approximate tokens |
|---------|--------------------|
| 1 line of code | ~10 tokens |
| 100-line file | ~1,000 tokens |
| 1,000-line file | ~10,000 tokens |
| Typical tool call + response | ~500-2,000 tokens |
| System prompt + rules | ~30,000-50,000 tokens |

## Session Lifecycle

1. **Start** — CLAUDE.md + rules auto-loaded (~40K tokens)
2. **Work** — read files, make changes, run commands
3. **Monitor** — watch for context warnings
4. **Compact** — when switching tasks or >60% full
5. **Save** — persist learnings to memory before /clear
6. **End** — update memory files with session findings
