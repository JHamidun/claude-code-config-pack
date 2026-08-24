# Custom Sales Bot Patterns (Grammy + MCP + PostgreSQL)

> Patterns extracted from a production TypeScript sales agent (names and ids replaced with placeholders).
> Custom TypeScript stack — NOT Hermes/OpenClaw. Use when you need full DB + CRM + calendar + video conferencing integration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Docker Compose (the VPS)                 │
│                                                 │
│  ┌──────────┐    ┌───────────────────────────┐  │
│  │ postgres  │    │  sales-agent  │  │
│  │ :5437     │◄───│  Grammy TG bot            │  │
│  └──────────┘    │  MCP tool server (stdio)   │  │
│                  │  node-cron scheduler       │  │
│                  │  Anthropic streaming client │  │
│                  └──────────┬────────────────┘  │
│                             │                   │
│  ┌──────────────┐          │                   │
│  │ ai-gateway   │◄─────────┘                   │
│  │ :8080        │  Claude via gateway           │
│  └──────────────┘                               │
│                                                 │
│  ┌──────────────┐  ┌───────────────────────┐    │
│  │ Pinecone KB  │  │ OpenClaw Friend bot   │    │
│  │ (external)   │  │ Admin notifications   │    │
│  └──────────────┘  └───────────────────────┘    │
└─────────────────────────────────────────────────┘
```

Key components:
- **Grammy** — Telegram bot framework (lightweight, TypeScript-first)
- **MCP tool server** — StdioServerTransport, 14 tools exposed to Claude as function calls
- **PostgreSQL** — users, leads, conversations, meetings, proactive_log, kv_store
- **AI Gateway** — routes Claude requests through shared Docker network
- **Pinecone** — vector knowledge base for RAG search
- **node-cron** — 6 scheduled jobs (follow-ups, digest, hot alerts, zoom reminders, value nurture, cleanup)

---

## Config Validation with Zod (MUST HAVE)

Raw `process.env` access scatters across files and fails at runtime with cryptic errors. Centralize ALL env vars through Zod validation at startup.

```typescript
// config.ts
import { z } from 'zod';

const envSchema = z.object({
  TELEGRAM_BOT_TOKEN: z.string().min(1),
  ADMIN_TG_ID: z.string().transform(Number),
  ADMIN_TG_IDS: z.string().optional(),

  AI_GATEWAY_URL: z.string().url(),
  AI_GATEWAY_API_KEY: z.string().min(1),
  CLAUDE_MODEL: z.string().default('opus'),

  DATABASE_URL: z.string().min(1),

  PINECONE_API_KEY: z.string().min(1),
  PINECONE_INDEX: z.string().default('sales-kb'),
  PINECONE_NAMESPACE: z.string().default('mastermind-v1'),
  OPENAI_API_KEY: z.string().min(1),

  // Google Calendar OAuth2
  GOOGLE_CLIENT_ID: z.string().min(1),
  GOOGLE_CLIENT_SECRET: z.string().min(1),
  GOOGLE_REFRESH_TOKEN: z.string().min(1),

  // Zoom S2S OAuth
  ZOOM_ACCOUNT_ID: z.string().min(1),
  ZOOM_CLIENT_ID: z.string().min(1),
  ZOOM_CLIENT_SECRET: z.string().min(1),

  // Separate bot for admin notifications (optional, degrades gracefully)
  OPENCLAW_FRIEND_BOT_TOKEN: z.string().min(1).optional(),

  DEEPGRAM_API_KEY: z.string().optional(),
  NODE_ENV: z.enum(['development', 'production']).default('production'),
  LOG_LEVEL: z.enum(['trace', 'debug', 'info', 'warn', 'error']).default('info'),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('Invalid environment variables:');
  for (const issue of parsed.error.issues) {
    console.error(`  ${issue.path.join('.')}: ${issue.message}`);
  }
  process.exit(1);
}

const env = parsed.data;

export const config = {
  telegram: {
    token: env.TELEGRAM_BOT_TOKEN,
    adminTgId: env.ADMIN_TG_ID,
    adminTgIds: env.ADMIN_TG_IDS
      ? env.ADMIN_TG_IDS.split(',').map(Number).filter(Boolean)
      : [env.ADMIN_TG_ID],
  },
  // ... structured sections for each integration
} as const;
```

**Why this matters:** Without Zod, a missing `ZOOM_CLIENT_SECRET` only crashes when someone tries to schedule a Zoom — maybe days after deploy. With Zod, the container refuses to start and logs exactly which var is missing.

---

## Dual-Bot Notification Pattern

**Problem:** The sales bot can't message the admin because they never pressed /start on it. Telegram requires users to initiate contact.

**Solution:** Route ALL admin notifications through a separate bot (`@<notifier_bot>`) that the admin has already started.

```typescript
// utils/notify-admin-helper.ts
export async function sendToAdmin(message: string): Promise<boolean> {
  const botToken = config.openclawFriendToken;
  if (!botToken) {
    log.warn("OPENCLAW_FRIEND_BOT_TOKEN not set, cannot notify admin");
    return false;  // degrade gracefully, don't crash
  }

  const res = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: config.telegram.adminTgId,
      text: message,
      parse_mode: "HTML",
    }),
  });
  return res.ok;
}
```

**Where to use:** Hot lead alerts, daily digest, zoom reminders to admin, error notifications.

**Key design choices:**
- Optional token (`z.string().optional()`) — bot works without it, just doesn't notify admin
- Direct Telegram Bot API call (no Grammy instance needed for the friend bot)
- HTML parse_mode for rich formatting

---

## Proactive Message Dedup System

**Problem:** Cron jobs run periodically. Without dedup, a hot lead gets the same "Горячий лид!" alert every hour.

**Solution:** `proactive_log` table + `wasProactiveSentToday()` check.

```sql
CREATE TABLE proactive_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  event_type TEXT NOT NULL,       -- 'follow_up', 'hot_alert', 'value_nudge'
  sent_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_proactive_log_user_event
  ON proactive_log(user_id, event_type, sent_at);
```

```typescript
export async function wasProactiveSentToday(
  userId: number,
  eventType: string,
): Promise<boolean> {
  const result = await getPool().query(
    `SELECT 1 FROM proactive_log
     WHERE user_id = $1 AND event_type = $2
       AND sent_at > NOW() - INTERVAL '1 day'
     LIMIT 1`,
    [userId, eventType],
  );
  return (result.rowCount ?? 0) > 0;
}

export async function logProactive(
  userId: number,
  eventType: string,
): Promise<void> {
  await getPool().query(
    `INSERT INTO proactive_log (user_id, event_type) VALUES ($1, $2)`,
    [userId, eventType],
  );
}
```

### CRITICAL GOTCHA: user_id vs entity.id

The #1 bug we hit in production: `sendHotLeadAlert()` was passing `lead.id` (primary key from leads table) instead of `lead.user_id` (foreign key to users table). Result:
- `proactive_log` INSERT with wrong user_id → FK constraint might fail silently or reference wrong user
- `wasProactiveSentToday()` lookup with wrong user_id → never finds existing record
- **Alert fires EVERY HOUR** for the same lead

**Fix:** Always use `lead.user_id` (or `entity.user_id`) when interacting with `proactive_log`. The `user_id` column references `users.id`, not any other table's PK.

```typescript
// WRONG:
await logProactive(lead.id, "hot_alert");

// CORRECT:
await logProactive(lead.user_id, "hot_alert");
```

### Cleanup cron (prevent unbounded growth)

```typescript
cron.schedule("0 3 * * *", async () => {
  const result = await getPool().query(
    "DELETE FROM proactive_log WHERE sent_at < NOW() - INTERVAL '30 days'",
  );
  if (result.rowCount && result.rowCount > 0) {
    log.info({ deleted: result.rowCount }, "proactive_log cleanup done");
  }
});
```

---

## Tripwire Tools Pattern

Free micro-assessments that give immediate value to the user while generating qualified data for the sales team. The user answers 5 questions → gets a personalized report.

### AI Business Diagnostic

```typescript
const DIAGNOSTIC_SYSTEM = [
  "Ты эксперт по AI-автоматизации бизнеса.",
  "На основе ответов пользователя составь КРАТКИЙ персональный отчёт (до 500 слов).",
  "Формат: 1) Профиль бизнеса, 2) 3 процесса для AI, 3) Экономия часов/неделю, 4) Первый шаг.",
  "В конце НЕ предлагай zoom — это сделает бот сам.",
].join("\n");

export async function generateAiDiagnostic(params: {
  businessType: string;
  teamSize: string;
  mainPain: string;
  currentTools: string;
  timeWaster: string;
}): Promise<string> {
  const userMessage = [
    `Сфера: ${params.businessType}`,
    `Команда: ${params.teamSize}`,
    `Боль: ${params.mainPain}`,
    `Инструменты: ${params.currentTools}`,
    `Пожиратель времени: ${params.timeWaster}`,
  ].join("\n");

  return callClaude({ systemPrompt: DIAGNOSTIC_SYSTEM, userMessage, model: "haiku" });
}
```

### EQ Profile Test

Same pattern: 5 answers → archetype classification → personalized report. Use haiku model for speed and cost efficiency.

### Key design principles for tripwire tools:

1. **5 questions max** — enough for personalization, not enough to bore
2. **Immediate value** — user gets useful report, not just "thanks, we'll call you"
3. **Cheap model** (haiku) — tripwires fire often, keep cost per interaction low
4. **No CTA in the report** — the bot adds zoom/meeting suggestion separately, keeping the report valuable on its own
5. **Fallback on error** — always return a human-readable message, never crash

---

## Value Nurture Cron

Periodic useful content for leads who haven't reached zoom_scheduled yet. NOT a "hey, still interested?" nag — actual micro-content.

```typescript
const NURTURE_THEMES = [
  "ai_tip",              // practical AI automation tip
  "eq_insight",          // emotional intelligence insight
  "exercise",            // quick self-reflection exercise
  "mini_case",           // real business case study (2-3 sentences)
  "provocative_question" // thought-provoking question about their business
] as const;

// Rotate through themes using persisted counter
const themeIndex = nudgeCounter % NURTURE_THEMES.length;
const theme = NURTURE_THEMES[themeIndex];
```

**Frequency:** Max 1 message per 2 days per user (via `wasProactiveSentToday` with 2-day window).

**Claude generates** the actual content each time — no static templates. This keeps messages fresh and contextual.

**Filtering:** Only targets leads in early stages (new, contacted) who haven't scheduled a zoom yet. Never targets converted or lost leads.

---

## Tool-Hint Injection via AGENTS.md

When using Claude as the brain, it needs guidance on WHEN to call each tool. The `workspace/AGENTS.md` file is loaded into the system prompt and contains tool-selection hints.

```markdown
# Tool Usage Rules

## Mandatory hints
- When user asks about the program → call `send_program_info`
- When user shows interest in meeting → call `schedule_zoom`
- When user asks to cancel/reschedule → call `cancel_zoom` or `reschedule_zoom`
- When user wants a diagnostic → call `generate_ai_diagnostic`
- When user mentions emotions/EQ → call `generate_eq_profile`

## Fuzzy matching
- "блог" (blog) and "блок" (block) are DIFFERENT words. "Блок" likely means "module/block of the program"
- Interpret based on context, not just keyword

## What NOT to do
- Never call `get_lead_stats` unless user is admin
- Never call `notify_admin` directly — the scheduler handles it
```

This pattern works with any LLM tool-calling setup: inject tool-selection rules into the system prompt so the model knows when each tool is appropriate.

---

## Security Hardening Checklist (Custom Bots)

### 1. SQL Injection via Dynamic Column Names

**Problem:** Parameterized queries protect values (`$1`, `$2`), but column/table names CAN'T be parameterized. If you interpolate user-influenced strings into column names:

```typescript
// VULNERABLE:
const query = `UPDATE meetings SET ${reminderField} = true WHERE id = $1`;
```

**Fix:** Allowlist pattern — only accept known column names:

```typescript
const ALLOWED_REMINDER_FIELDS = new Set(["reminder_24h_sent", "reminder_1h_sent"]);

if (!ALLOWED_REMINDER_FIELDS.has(reminderField)) {
  throw new Error(`Invalid reminder field: ${reminderField}`);
}
```

Also applies to `make_interval()` — use `make_interval(hours => $1)` instead of string interpolation.

### 2. Admin Auth on Sensitive Tools

```typescript
function createToolExecutor(telegramId: number, isAdmin: boolean) {
  return async (toolName: string, toolInput: Record<string, unknown>) => {
    // Admin-only tools
    if (toolName === "get_lead_stats" && !isAdmin) {
      return { error: "Эта функция доступна только администраторам" };
    }
    // ... execute tool
  };
}
```

### 3. Input Length Limit

Prevent abuse and token waste:

```typescript
const MAX_INPUT_LENGTH = 5000;

if (messageText.length > MAX_INPUT_LENGTH) {
  messageText = messageText.slice(0, MAX_INPUT_LENGTH);
}
```

### 4. Typing Indicator Cleanup

Grammy's `ctx.replyWithChatAction("typing")` + `setInterval` pattern leaks if the handler throws:

```typescript
const typingInterval = setInterval(() => {
  ctx.replyWithChatAction("typing").catch(() => {});
}, 4000);

try {
  // ... process message with Claude
} finally {
  clearInterval(typingInterval);  // ALWAYS clean up
}
```

### 5. Dead Code Removal

Audit for unused imports and files. We deleted `telegram-media.ts` (264 lines) that was never imported. Dead code:
- Creates false complexity in reviews
- May contain outdated patterns that get copy-pasted
- Inflates Docker image

---

## MCP Tool Server Pattern

The sales bot uses Grammy for Telegram + a separate MCP tool server (StdioServerTransport) so Claude can call tools via standard function-calling.

```
Claude ←→ [anthropic-client.ts] ←→ AI Gateway ←→ Claude API
  ↑                                                    ↓
  └── tool_use response ←── JSON tool calls ←──────────┘
  ↓
[telegram.ts createToolExecutor]
  ↓
tool handler (schedule-zoom.ts, ai-diagnostic.ts, etc.)
  ↓
tool_result → back to Claude for next iteration
```

Each tool is a separate `.ts` file in `src/mcp-server/tools/`:

```
tools/
├── calendar-api.ts       # Google Calendar OAuth2
├── zoom-api.ts           # Zoom S2S OAuth
├── schedule-zoom.ts      # Orchestrates calendar + zoom
├── cancel-zoom.ts
├── reschedule-zoom.ts
├── send-calendar-invite.ts
├── ai-diagnostic.ts      # Tripwire: AI business diagnostic
├── eq-test.ts            # Tripwire: EQ profile
├── pinecone-search.ts    # RAG knowledge base search
├── send-program-info.ts  # Static program info
├── send-testimonial.ts   # Client testimonials
├── user-profile.ts       # CRUD for user data
├── lead-ops.ts           # Lead stage management
└── notify-admin.ts     # Admin notification
```

The tool schemas (JSON) are defined in `telegram.ts` as `SALES_TOOLS[]` array and passed to Claude in each API call. Claude sees all tool descriptions and decides which to call.

---

## Cron Job Architecture

6 jobs with clear separation of concerns:

| Job | Schedule | Purpose | Dedup |
|-----|----------|---------|-------|
| follow_up_check | `0 */6 * * *` | Nudge stale leads (24h/3d/7d tiers) | proactive_log `follow_up` |
| daily_digest | `0 7 * * *` (10:00 MSK) | Pipeline summary to admin | None (1x/day by design) |
| hot_lead_alerts | `0 * * * *` | Alert admin on hot leads | proactive_log `hot_alert` |
| zoom_reminders | `*/15 * * * *` | 24h and 1h meeting reminders | DB flag on meetings row |
| value_nurture | `0 9 * * *` (12:00 MSK) | Useful micro-content to cold leads | proactive_log `value_nudge` (2-day window) |
| proactive_log_cleanup | `0 3 * * *` | Delete records >30 days | N/A |

**Design principles:**
- Each job is independent — failure of one doesn't block others
- All Claude-composed messages use haiku model (cheap, fast)
- Rate limit respect: 2s delay between messages per user
- Follow-ups process tiers highest-first (7d before 24h) with Set tracking to avoid double-sends
- MAX_FOLLOW_UPS = 3 per lead lifetime

---

## When to Use Custom Stack vs Hermes/OpenClaw

**Choose custom stack when:**
- Need PostgreSQL with relational data model (users → leads → conversations → meetings)
- Need calendar + video conferencing integration (Google Calendar OAuth2, Zoom S2S)
- Need complex cron logic (tiered follow-ups, dedup, cross-entity coordination)
- Need dual-bot notification pattern
- Need full control over the agentic loop (streaming, tool execution order, retry logic)
- Team knows TypeScript and wants type safety end-to-end

**Choose Hermes/OpenClaw when:**
- Personality-driven bot (coach, tutor, assistant) without heavy DB logic
- Standard toolsets cover your needs (web, vision, memory, file)
- Don't need relational data — simple key-value or memory is enough
- Want faster time-to-deploy (hours, not days)
- Don't need custom cron dedup logic
