# Eve Pattern — Agent-as-File-Layout (vercel/eve, 3.8k★)

> Distilled from github.com/vercel/eve (2026-07-20). NOT an engine we install — a
> **structural pattern** to borrow ideas from when designing Hermes plugins / OpenClaw
> extensions / custom-stack bots. Compare against our two live engines below.

## The core idea

Eve treats **the filesystem itself as the agent's authoring interface**. An agent is not
a YAML blob or a database row — it's a directory. Every capability lives in a
conventional location, so a human (or another LLM) can `ls` an agent and understand it
without reading framework internals:

```
my-agent/
├── instructions.md   # always-on system prompt — WHO the agent is
├── agent.ts          # optional: model choice, runtime settings
├── tools/            # typed functions the model can call directly
│   └── get_weather.ts
├── skills/           # procedures loaded ON DEMAND (markdown, not always in context)
├── channels/         # message integrations — http, slack, discord, ...
└── schedules/         # recurring cron jobs
```

**Tools** are typed with Zod at the boundary:

```ts
export const getWeather = tool({
  inputSchema: z.object({ city: z.string().min(1) }),
  execute: async ({ city }) => { /* ... */ },
});
```

**Philosophy in one line:** agent capability = file you can point to. Extending the
agent = adding a file in the right directory, not editing a monolithic config object.
Debugging = "which file handles this" is always a `find`/`ls`, never a grep through
framework source.

## Why this matters here

This is a genuinely different axis from how our two engines encode an agent:

| | Eve | Hermes (ours, primary) | OpenClaw (ours, legacy) |
|---|---|---|---|
| Agent definition unit | **directory of files**, each file = one capability | **single `config.yaml`** + `SOUL.md` personality file | **single `openclaw.json`** + `SKILL.md` files |
| Tools | one `.ts` file per tool, Zod schema inline | Python plugin (`plugin.yaml` + `tools.py` + `schemas.py`), registered via `TOOL_BINDINGS` | TypeScript extension (`src/tools/*.ts`), TypeBox schema, `definePluginEntry()` |
| On-demand procedures | `skills/` dir, markdown, loaded lazily | not a first-class concept — everything in SOUL.md context budget (2200 char memory cap) or plugin tools | `SKILL.md` loaded as system-prompt context (this is literally how OpenClaw personality works) |
| Scheduled jobs | `schedules/` dir, one file per job | `cronjob` tool (create/list/update/pause/resume/remove/run), config lives in state, not a file per job | `cron.jobs[]` array inside `openclaw.json` |
| Channels | `channels/` dir, one file per integration | adapter list in `config.yaml` `platforms:` | `channels.telegram` block in `openclaw.json` |
| Inspectability | `ls agent/` tells you everything | must read `config.yaml` + `SOUL.md` + plugin dirs separately | must read `openclaw.json` + skill dirs separately |

**What we already do that matches Eve's instinct:** OpenClaw's `SKILL.md`-as-personality
and our own top-level `~/.claude/skills/<name>/SKILL.md` + `references/` + `scripts/`
convention (used across this entire skill library) is functionally the same pattern —
one directory per capability, lazy-loaded references, explicit script files instead of
inline logic. Eve just applies that same idea *inside a single running agent's own
capability set* (tools/skills/channels/schedules as sibling dirs), where our engines
keep tools in a plugin package and schedule/channel config inside one JSON/YAML blob.

**Concrete takeaway for new Hermes plugins / OpenClaw extensions:**

- When a plugin/extension grows past ~3-4 tools, mirror Eve's `tools/` convention:
  one file per tool (we already do this loosely via `schemas.py`/`tools.py` split, but
  Eve's "one tool = one file" is stricter and greps faster in a big plugin).
- For **schedule-heavy** bots (Recipe #3 Trading Signals, #9 Multi-tenant Content
  Agent), consider a `schedules/<job-name>.md` doc per cron job (one paragraph: what it
  does, why this cadence, last-known-good) even though the actual cron entry still
  lives in `config.yaml`/`openclaw.json` — solves "which cron job does X" faster than
  grepping the JSON array.
- Eve's directory-per-capability instinct is *why* our own skill library (this whole
  `~/.claude/skills/` tree) works well — it's independent validation of the pattern we
  already use one level up (Claude Code skills), not a reason to migrate Hermes/OpenClaw
  configs to a new file layout.

## Verdict — not adopted as a framework, pattern noted

Eve itself is not installed and not recommended for adoption: we already have two
production engines (Hermes primary, OpenClaw legacy) with live bots, migration tooling,
and a hard-won gotcha catalog (`references/gotchas-and-fixes.md`, 53 entries). Swapping
either for a third framework is not justified by "nicer file layout" alone. The value
extracted here is the **architectural idea** — filesystem-as-authoring-interface — filed
for future plugin/extension design, not a new engine option in the Decision Tree.
