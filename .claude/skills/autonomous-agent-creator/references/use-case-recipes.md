# Рецепты под типовые задачи

Готовые сборки агентов под конкретные задачи (продажи, контент, фитнес, поддержка и т.п.): что включить, какие инструменты, какой крон. Читай, когда клиент описал задачу и надо быстро предложить состав бота.

## Use Case Recipes

### 1. Fitness Trainer (Hermes + Plugin)
- **Engine:** Hermes
- **Plugin:** Custom (PostgreSQL for clients, macros calculations, video library, menu image generation)
- **Key patterns:** description-as-instructions in tool schemas, parallel flow (text + image), brand prompts for image gen
- **Toolsets:** web, vision, image_gen, file, memory
- **Cron:** Weekly progress check, daily menu reminder
- **Personality:** Strict but supportive coach, uses emojis, celebrates wins
- **See:** examples/hermes-fitness-trainer.yaml

### 2. Booking Assistant (OpenClaw Skill)
- **Engine:** OpenClaw
- **Implementation:** Pure SKILL.md (no code needed)
- **Key patterns:** Memory as database (BOOKING|date|time|name|phone|type|notes|status), cron reminders
- **Cron:** Daily 9:00 check for today's bookings, send reminders
- **Personality:** Polite receptionist, confirms every detail twice
- **See:** examples/openclaw-booking.json

### 3. Trading Signals (OpenClaw Skill + Cron)
- **Engine:** OpenClaw
- **Implementation:** SKILL.md + cron jobs (quick every 60s + swing every 15m)
- **Key patterns:** web_fetch to Binance API, signal strength scoring (1-5), memory for performance tracking
- **Cron:** quick (1m scalping BTC/ETH), swing (15m top-10 pairs)
- **Personality:** Analytical, numbers-first, no hype
- **See:** examples/openclaw-trading.json

### 4. LinkedIn Autopilot (OpenClaw Extension)
- **Engine:** OpenClaw
- **Implementation:** TypeScript extension with browser automation
- **Key patterns:** Rate limiter (20/hour, 100/day), instruction-emitting tools (agent executes via browser tool), random delays 3-8s
- **Sandbox:** sandbox-browser with CDP + Playwright
- **Personality:** Professional networker, warm but brief
- **See:** references/openclaw-extension-howto.md

### 5. E2E Desktop Testing (OpenClaw Extension)
- **Engine:** OpenClaw
- **Implementation:** TypeScript extension with YAML scenario parser + screenshot diff
- **Key patterns:** Zero-dep PNG decoder, pixel-level RGBA comparison, HTML reporter
- **Personality:** QA engineer, reports bugs precisely with steps-to-reproduce
- **See:** references/openclaw-extension-howto.md

### 6. Children's Tutor (Hermes)
- **Engine:** Hermes
- **Key patterns:** Child-safe toolsets (NO terminal), Socratic method (never give answers directly), star gamification, emoji-rich personality
- **Safety:** Soft refusal + alert on dangerous topics, no external links
- **Allowed users:** Only child's Telegram ID
- **Personality:** Enthusiastic teacher, uses stories and analogies, celebrates effort
- **See:** examples/hermes-child-tutor.yaml

### 7. Sales Agent (Custom Stack)
- **Engine:** Custom TypeScript (Grammy + MCP tool server + PostgreSQL)
- **Architecture:** Grammy bot → Claude via AI Gateway → MCP tools (14 tools: CRM, Zoom, Calendar, KB search, tripwires)
- **Key patterns:**
  - **Zod config validation** — ALL env vars validated at startup, fail-fast on missing credentials
  - **Dual-bot notifications** — admin gets alerts via separate "friend" bot (because admin never /started the sales bot)
  - **Proactive dedup** — `proactive_log` table prevents cron spam (GOTCHA: always use `lead.user_id`, not `lead.id`)
  - **Tripwire tools** — free AI Diagnostic (5 questions → report) and EQ Test as engagement hooks
  - **Value nurture cron** — periodic useful micro-content (5 rotating themes, Claude haiku-composed, max 1 per 2 days)
  - **Tool-hint injection** — `workspace/AGENTS.md` loaded into system prompt tells Claude when to call each tool
  - **6 cron jobs** — follow-ups (tiered 24h/3d/7d), digest, hot alerts, zoom reminders, value nurture, log cleanup
  - **Security hardening** — SQL injection allowlist, admin auth on tools, input length limit, typing interval cleanup
- **Docker:** Compose with postgres + agent + ai-gateway-network
- **Not Hermes/OpenClaw** — standalone when you need full relational DB + CRM + calendar + video integration
- **Personality:** Consultative seller, asks questions before pitching, never pushy
- **See:** `references/custom-sales-bot-patterns.md` (full architecture, code examples, gotchas)

### 8. Personal Assistant (Hermes)
- **Engine:** Hermes
- **Key patterns:** Full toolset (hermes-telegram = everything), direct no-fluff personality, opinions allowed
- **Allowed users:** Only the owner
- **Personality:** Direct, informal, like a trusted colleague who remembers everything
- **See:** examples/hermes-personal-assistant.yaml

### 9. Multi-tenant Content Agent (Custom Stack)
- **Engine:** Custom Python (long-poll Bot API + LLM agent loop + Docker compose × 3 контейнера: bot / scheduler / video-worker)
- **Use case:** Публичный бот где много юзеров параллельно ведут свои контент-темы (мониторинг каналов, drafts, медиапланы)
- **Key patterns:**
  - **Per-user data isolation** — `data/users/<tg_id>/topics/<slug>/...`, никаких глобальных таблиц с user_id-колонкой. Удалить юзера = `rm -rf user_dir`
  - **Fernet BYOK sidechannel** — `/byok` команды обходят LLM context, юзерские API ключи валидируются и шифруются на диске. **Никогда не попадают в history.jsonl**
  - **Multi-provider LLM** routing by model prefix + orphan-tool-message filter + fallback chain (см. `multi-model-gateway` skill §1–6)
  - **Staged content pipeline** — voiceover → storyboard → references → render с per-stage approval (см. `mcp-builder/reference/agent-tool-design-examples.md` §11.3–11.5)
  - **Per-user rate limiting на shared quota** — Default-budget с upgrade через `/byok` (свой ключ снимает лимит)
  - **Reply keyboard как NL-shortcuts** — кнопки `📋 Темы / ✍️ Черновик` отправляют свой текст, агент роутит на tools (см. `telegram-bot-toolkit` §3)
  - **Scheduler container** — отдельно от bot, тикает каждую минуту, обрабатывает медиаплан-слоты и cron мониторинга
  - **Whitelist для беты** — `data/whitelist.txt`, простой text file
- **Docker:** Compose с bot + scheduler + video-worker (+ optional MCP sidecar для OpenClaw-интеграции)
- **Не Hermes/OpenClaw** — standalone когда нужна тонкая разработка собственного UX (staged approval, custom reply keyboards, FSM sidechannels)
- **See:** `references/multi-tenant-content-agent.md` (полный architectural reference)

---

