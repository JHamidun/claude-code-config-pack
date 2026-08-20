---
name: manus
description: "Автономная облачная задача в Manus (REST API v2, manus_helper.py): research, browsing, код. Триггеры: «запусти в Manus». НЕ слайды→manus-slides. Слэш-запуск→команда /manus."
---

# Manus AI (API v2)

Manus (manus.im) is a cloud autonomous-agent platform. You hand it a natural-language
task; a Manus agent plans and runs it asynchronously (browser, code sandbox, files,
connectors) and returns messages/artifacts. This skill drives it through the official
REST API v2 via `scripts/manus_helper.py`.

## When to use

- A self-planning, multi-step job that runs unattended for minutes: deep web research,
  scraping + structuring, "go to X, download report, summarize", generate a document.
- You want the work done in Manus's own cloud sandbox, not in this session.

**When NOT to use:**

- Slides/decks "in the style of Manus" → skill `manus-slides`.
- Simple/local browser clicks or scraping you control step-by-step → `dev-browser`,
  `playwright-automation`, `apify-scraping`.
- Quick web answer with citations → `deep-research` (Perplexity).

## Verified facts (checked against open.manus.im/docs + live calls, 2026-07-22)

- Base URL: `https://api.manus.ai`
- Auth header: `x-manus-api-key: <MANUS_API_KEY>` (OAuth2 Bearer also supported).
  Key is in `~/.claude/.credentials.master.env` as `MANUS_API_KEY`.
- **v2 is current; v1 (`/v1/tasks`, header `API_KEY`) is deprecated** — do not use it.
- Create is `POST /v2/task.create`; the task runs **async**. You poll for progress.
- `agent_profile` values: `manus-1.6` (default), `manus-1.6-lite` (fast/cheap),
  `manus-1.6-max` (best quality).
- Lifecycle `agent_status`: `running` → `stopped` (success) | `error` (failed) |
  `waiting` (needs your input). Field lives at `messages[].status_update.agent_status`.
- Final answer text is at `messages[].assistant_message.content` (newest first when
  `order=desc`). Structured output at `structured_output_result` if a schema was passed.

Endpoints (see `references/api-v2.md` for the full map): `task.create` (POST),
`task.listMessages` (GET, query params), `task.detail` (GET), `task.sendMessage` (POST),
`task.stop` (POST), `task.list`, `task.delete`, `file.upload`.

> Honest note: only the endpoints exercised by `manus_helper.py` (create / listMessages /
> status / sendMessage / stop) have been run live from here. `file.upload`, connectors and
> skills are documented by Manus but **not yet tested in this skill** — treat as reference.

## Procedure

Prefer the helper over hand-rolled `requests` — it handles the async poll loop and the
nested `status_update` / `assistant_message` field parsing correctly.

```bash
# one-shot: create + poll until done, prints JSON with .answer
python ~/.claude/skills/manus/scripts/manus_helper.py run \
  "Research the top 5 Russian EdTech AI products in 2026; output a comparison table" \
  --profile manus-1.6 --timeout 1800 --poll 8

# fire-and-forget (returns task_id + task_url immediately)
python ~/.claude/skills/manus/scripts/manus_helper.py create "…prompt…" --profile manus-1.6-lite

# poll a task you started earlier
python ~/.claude/skills/manus/scripts/manus_helper.py status   <task_id>
python ~/.claude/skills/manus/scripts/manus_helper.py messages <task_id> --limit 20

# answer a task that went agent_status=waiting, or add a follow-up
python ~/.claude/skills/manus/scripts/manus_helper.py reply <task_id> "yes, proceed"

# stop a runaway task
python ~/.claude/skills/manus/scripts/manus_helper.py stop <task_id>
```

The key must be in the environment. In bash:
`set -a; source ~/.claude/.credentials.master.env; set +a` before the call.

## Output

`run` prints JSON to stdout:

```json
{
  "task_id": "REumuUf3XoZBGMgUZF7yad",
  "task_url": "https://manus.im/app/REumuUf3XoZBGMgUZF7yad",
  "agent_status": "stopped",
  "answer": "…the agent's final message text…",
  "messages": { "messages": [ … full event log … ] }
}
```

Exit codes: `0` stopped/waiting, `2` error, `3` timeout. Progress (`task_id`,
`agent_status`) is streamed to **stderr** so stdout stays parseable.

## Example

```bash
$ set -a; source ~/.claude/.credentials.master.env; set +a
$ python ~/.claude/skills/manus/scripts/manus_helper.py run \
    "Reply with exactly the word PONG and nothing else." --profile manus-1.6-lite
# stderr: task_id=… / agent_status=running / agent_status=stopped
# stdout: {"agent_status":"stopped","answer":"PONG", …}
```

## Checklist

- [ ] `MANUS_API_KEY` exported before calling the helper.
- [ ] Chose profile: `manus-1.6-lite` for cheap/fast, `manus-1.6` default, `manus-1.6-max` for hard jobs.
- [ ] Long jobs: set `--timeout` generously (default 1800s) — Manus runs can take many minutes.
- [ ] If result is `agent_status=waiting`, use `reply` to unblock; if `error`, read `messages` for `error_message`.
- [ ] Autonomy ≠ correctness — verify the returned artifact/answer before shipping.

## Tips

1. Detailed prompt = better run. Spell out inputs, steps, and the exact output format.
2. Break very large jobs into a few smaller tasks rather than one mega-prompt.
3. Pass `--locale ru` (via `create`/`run` code path) to force Russian output.
4. For structured extraction, call `create_task(..., structured_schema=<JSON Schema>)`
   in Python and read `structured_output_result`.
5. Manus API billing is metered per task/usage on the Manus account — prefer `-lite`
   for drafts and cheap iterations.
