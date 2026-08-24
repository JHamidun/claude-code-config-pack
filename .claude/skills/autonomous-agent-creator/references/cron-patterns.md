# Cron Job Patterns

> Scheduled tasks for Hermes and OpenClaw engines.

---

## Hermes: cronjob Tool

The `cronjob` tool is part of the standard toolset. It provides 7 actions:

| Action | Description |
|--------|-------------|
| `create` | Create a new scheduled job |
| `list` | List all active jobs |
| `update` | Modify an existing job |
| `pause` | Temporarily disable a job |
| `resume` | Re-enable a paused job |
| `remove` | Delete a job permanently |
| `run` | Execute a job immediately (one-shot) |

### Schedule Formats

```
"30m"                   # Relative: every 30 minutes
"2h"                    # Relative: every 2 hours
"1d"                    # Relative: every day
"0 9 * * *"            # Cron: daily at 9:00
"*/15 * * * *"         # Cron: every 15 minutes
"0 9 * * 1-5"          # Cron: weekdays at 9:00
"2026-06-15T10:00:00"  # ISO: one-shot at specific time
```

### Delivery Options

| Mode | Behavior |
|------|----------|
| `origin` | Reply in the chat that created the job |
| `local` | Reply in the current chat |
| `all` | Broadcast to all active chats |
| `specific` | Target a specific chat_id |

### Script-Only Mode (no_agent)

When `no_agent=True`, the job runs a script directly without invoking the agent.
Output is delivered as plain text. Empty stdout = silent (no message sent).

```json
{
  "action": "create",
  "name": "health-check",
  "schedule": "*/5 * * * *",
  "no_agent": true,
  "script": "curl -s http://localhost:8080/health | jq .status",
  "delivery": "origin",
  "silent_on_empty": true
}
```

### Context Chaining

Inject output from an upstream job as context for the current job:

```json
{
  "action": "create",
  "name": "morning-summary",
  "schedule": "0 9 * * *",
  "timezone": "Europe/Moscow",
  "message": "Summarize today's tasks and send a motivational message.",
  "context_from": ["daily-stats"],
  "delivery": "origin"
}
```

The output of the `daily-stats` job is prepended to the agent's context before executing `morning-summary`.

### Hermes Cron Examples

**Daily reminder:**
```json
{
  "action": "create",
  "name": "water-reminder",
  "schedule": "0 10,14,18 * * *",
  "timezone": "Europe/Moscow",
  "message": "Remind user to drink water. Be brief and encouraging.",
  "delivery": "origin"
}
```

**Weekly report:**
```json
{
  "action": "create",
  "name": "weekly-report",
  "schedule": "0 18 * * 5",
  "timezone": "Europe/Moscow",
  "message": "Generate a weekly progress report. Use memory_search to find this week's entries. Format as bullet points with totals.",
  "delivery": "origin"
}
```

**Script-only monitoring:**
```json
{
  "action": "create",
  "name": "disk-check",
  "schedule": "0 */6 * * *",
  "no_agent": true,
  "script": "df -h / | awk 'NR==2 {if ($5+0 > 80) print \"Disk usage: \" $5}'",
  "delivery": "origin",
  "silent_on_empty": true
}
```

---

## OpenClaw: Cron Config

Cron jobs are declared in `openclaw.json` under the `cron` key.

### Structure

```json
{
  "cron": {
    "enabled": true,
    "jobs": [
      {
        "name": "job-name",
        "enabled": true,
        "schedule": { ... },
        "sessionTarget": "main" | "isolated",
        "wakeMode": "now" | "queue",
        "payload": { ... },
        "delivery": { ... }
      }
    ]
  }
}
```

### Schedule Types

```json
// Standard cron expression
{ "kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow" }

// Fixed interval in milliseconds
{ "kind": "every", "everyMs": 60000 }

// One-shot at specific time
{ "kind": "at", "iso": "2026-06-15T10:00:00+03:00" }
```

### Payload

```json
{
  "kind": "agentTurn",
  "message": "The prompt the agent receives when the job fires",
  "toolsAllow": ["memory_search", "web_fetch"],
  "toolsDeny": ["browser"]
}
```

- `toolsAllow`: whitelist of tools available during this job (empty = all)
- `toolsDeny`: blacklist of tools (takes precedence over allow)
- `message`: the user-turn text injected into the agent session

### Session Target

| Value | Behavior |
|-------|----------|
| `main` | Runs in the existing conversation context |
| `isolated` | Creates a fresh session (no history pollution) |

Use `isolated` for repetitive scanning jobs that don't need conversation context.

### Delivery

```json
// Announce to Telegram
{ "mode": "announce", "channel": "telegram" }

// Silent (no delivery, just execute)
{ "mode": "silent" }

// Conditional (only deliver if agent produces output)
{ "mode": "announce", "channel": "telegram", "onlyIfOutput": true }
```

### OpenClaw Cron Examples

**Daily morning briefing:**
```json
{
  "name": "morning-briefing",
  "enabled": true,
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow" },
  "sessionTarget": "main",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Good morning! Check today's schedule and pending tasks. Send a brief summary.",
    "toolsAllow": ["memory_search"]
  },
  "delivery": { "mode": "announce", "channel": "telegram" }
}
```

**Every-15m market scanner:**
```json
{
  "name": "market-scan",
  "enabled": true,
  "schedule": { "kind": "every", "everyMs": 900000 },
  "sessionTarget": "isolated",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Scan BTC/USDT on 15m chart. Only report if signal strength >= 3.",
    "toolsAllow": ["web_fetch", "memory_search"]
  },
  "delivery": { "mode": "announce", "channel": "telegram", "onlyIfOutput": true }
}
```

**Weekly digest:**
```json
{
  "name": "weekly-digest",
  "enabled": true,
  "schedule": { "kind": "cron", "expr": "0 18 * * 5", "tz": "Europe/Moscow" },
  "sessionTarget": "main",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "Generate a weekly summary of all conversations and key decisions. Format with headers and bullet points.",
    "toolsAllow": ["memory_search", "session_search"]
  },
  "delivery": { "mode": "announce", "channel": "telegram" }
}
```

---

## Custom Stack: node-cron Patterns (TypeScript Sales Bots)

For custom bots (not Hermes/OpenClaw) using `node-cron` directly. Key difference: YOU own the cron handler code, including dedup logic, DB access, and error handling.

### Tiered follow-up (24h / 3d / 7d)

Process tiers highest-first so a 7-day stale lead gets a level-2 message, not level-0:

```typescript
import cron from "node-cron";

const FOLLOW_UP_TIERS = [
  { hoursStale: 24, level: 0 },
  { hoursStale: 72, level: 1 },
  { hoursStale: 168, level: 2 },
] as const;

cron.schedule("0 */6 * * *", async () => {
  const processed = new Set<number>();

  for (const tier of [...FOLLOW_UP_TIERS].reverse()) {
    const leads = await getStaleLeads(tier.hoursStale);
    for (const lead of leads) {
      if (processed.has(lead.user_id)) continue;
      if (lead.follow_up_count >= 3) continue;

      const alreadySent = await wasProactiveSentToday(lead.user_id, "follow_up");
      if (alreadySent) { processed.add(lead.user_id); continue; }

      await sendFollowUp(lead, tier.level);
      await logProactive(lead.user_id, "follow_up");
      processed.add(lead.user_id);
      await delay(2000);  // Telegram rate limit
    }
  }
});
```

### Value nurture with rotating themes

```typescript
const THEMES = ["ai_tip", "eq_insight", "exercise", "mini_case", "provocative_question"];

cron.schedule("0 9 * * *", async () => {
  let counter = (await getKV("nudge_counter")) ?? 0;
  const leads = await getLeadsForNurture();  // early-stage, no zoom scheduled

  for (const lead of leads) {
    const theme = THEMES[counter % THEMES.length];
    // Claude haiku composes the actual content each time — keeps it fresh
    const sent = await sendValueNudge(lead, theme);
    if (sent) {
      await logProactive(lead.user_id, "value_nudge");
      counter++;
    }
    await delay(2000);
  }
  await setKV("nudge_counter", counter);
});
```

### Proactive log cleanup

```typescript
cron.schedule("0 3 * * *", async () => {
  const result = await pool.query(
    "DELETE FROM proactive_log WHERE sent_at < NOW() - INTERVAL '30 days'",
  );
  if (result.rowCount > 0) {
    log.info({ deleted: result.rowCount }, "proactive_log cleanup done");
  }
});
```

### Key differences from Hermes/OpenClaw cron

| Aspect | Hermes/OpenClaw | Custom node-cron |
| ------ | --------------- | ---------------- |
| Dedup | Manual (memory-based or agent prompt) | DB-backed `proactive_log` table |
| Error handling | Platform catches + retries | You handle try/catch per job |
| Delivery | Platform manages channel routing | You call `sendMessage()` directly |
| State | Agent memory or config | PostgreSQL + KV store |
| Rate limiting | Platform may throttle | You add `delay()` between sends |
