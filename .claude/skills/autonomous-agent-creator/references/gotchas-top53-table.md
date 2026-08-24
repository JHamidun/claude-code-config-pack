# 53 грабли Hermes/OpenClaw — таблица «симптом → починка»

Полная таблица известных отказов с короткой починкой. Читай, когда бот сломался или ведёт себя странно: сначала ищи симптом здесь, разборы 15 самых частых — в `gotchas-and-fixes.md`.

## Common Gotchas (TOP-53)

See `references/gotchas-and-fixes.md` for detailed solutions.

| # | Problem | Fix |
|---|---------|-----|
| 1 | "Unknown model: openai/gpt-5.4-mini" | Model not in v2026.2.18 registry. Use gpt-5.2 max |
| 2 | "401 Unauthorized" on Telegram | Bot token revoked. Get new from @BotFather |
| 3 | Container disappears after reboot | Missing `--restart unless-stopped` |
| 4 | "No API key found for provider" | Env var not passed to container. Check docker run -e |
| 5 | Volume permissions denied | `chown -R 1000:1000` (OpenClaw) or set HERMES_UID (Hermes) |
| 6 | Python packages lost on restart | Use bootstrap.sh with `uv pip install` at start |
| 7 | Images not sending via Telegram | Use `curl -F photo=@file` via Bot API, NOT [PHOTO:] prefix |
| 8 | Hermes "model": must be object | OpenClaw needs `{"primary": "...", "fallbacks": [...]}` not string |
| 9 | Agent silent after model change | Telegram needs offset reset. Restart container |
| 10 | Cron job not firing | Check timezone in schedule config. Use tz: "Europe/Moscow" |
| 11 | OpenClaw "baseUrl" error | v2026.2.18 doesn't support baseUrl in auth profiles |
| 12 | Docker image tag lost after prune | Re-tag: `docker tag <image-id> openclaw:local` |
| 13 | Context compression losing context | protect_last_n=20, increase if agent forgets recent messages |
| 14 | Plugin tools not appearing | Check plugin.yaml provides_tools matches schema function names |
| 15 | Browser automation rate-limited | Add random delays 3-8s between actions, max 20/hour |
| 16 | ALL MODELS EXHAUSTED — every provider failed over | Illustrative chain: Gemini skipped (tool_results), OpenAI CB tripped, Vertex 429. Fix: restart `<your-gateway>` + fix credentials |
| 17 | OpenAI circuit breaker CLOSED | codex-1 refresh_token expired (401). Get new OAuth token or use direct API keys |
| 18 | Vertex AI 429 quota exceeded | Increase `online_prediction_input_tokens_per_minute` in Google Cloud Console |
| 19 | `/start` mangled to `C:/Program Files/Git/start` | Windows Git Bash MSYS path conversion. Use `MSYS_NO_PATHCONV=1` before command |
| 20 | Cron jobs all failing same time | Root cause is AI Gateway, not individual bots. Fix gateway first, crons will recover |
| 21 | Hermes config says Gemini but bot still uses Codex | 5-layer cascade — see "Hermes Provider Resolution Cascade" section. Usually `.env` file has stale `HERMES_INFERENCE_PROVIDER` value that overrides docker-compose env |
| 22 | `Gemini returned HTTP 404` on `gemini-3-flash` | `gemini-3-flash` without `-preview` does NOT exist on public API. Use `gemini-3.5-flash` or `gemini-3-flash-preview`. Verify with `curl /v1beta/models?key=...` before hardcoding |
| 23 | Codex `refresh_token consumed` error after second-bot adds | ChatGPT subscription rotates refresh on every use. 2+ clients = constant collision. Single client only, or switch to Gemini direct API |
| 24 | `Provider authentication failed: No Codex credentials stored` after I disabled Codex | Hermes runtime cascades to fallback that still tries Codex. Need to ALSO clear `providers.openai-codex` from `/opt/data/auth.json` and set `active_provider: gemini` |
| 25 | Hermes Docker container `exec: not found` on entrypoint.sh | Repo cloned on Windows with CRLF line endings. Fix: `find /opt/hermes -name '*.sh' -exec sed -i 's/\r$//' {} \;` then rebuild |
| 26 | Migrated Hermes bot lost workspace files (budgets, scripts) | `hermes claw migrate` only imports SOUL.md, USER.md, config, secrets. Workspace files need MANUAL `cp -r .../workspace/_data/. /opt/data/workspace/` |
| 27 | Google Sheets/Drive tool returns auth errors after migration | OAuth JSON `credentials/google-oauth-*.json` was excluded from `claw migrate` for security. Manually copy back to `/opt/data/workspace/credentials/`, chmod 600 |
| 28 | Hermes onboarding `/sethome` prompt nags every user first time | Set `TELEGRAM_HOME_CHANNEL=<admin_id>` env var. Suppresses 184-char notice on first message |
| 29 | Session pinning ignores config switch | `state.db sessions.billing_provider` and `sessions/*.jsonl session_meta.model` hold old values. Wipe with UPDATE + sed (see Provider Cascade section) |
| 30 | `hermes claw migrate` cron jobs report "skipped — no cron configuration found" | OpenClaw `cron/jobs.json` format ≠ Hermes cron format. Recreate via `hermes cron create` CLI. Convert tz to UTC (Hermes parse_schedule doesn't take tz suffix) |
| 31 | Anthropic API "organization has been disabled" | Whole org dead. Need new account or another provider. Sonnet path is unreliable for prod bot fleet |
| 32 | All API keys revoked simultaneously | Probably exposed in a public repo or leaked log. Rotate ALL keys + audit log access. Держи ключи в одном env-файле как единственном источнике правды, никогда не коммить |
| 33 | Bot answers with the model's name instead of its persona name | SOUL.md was loaded but persona instructions buried. Put persona rules in FIRST 1000 chars of SOUL.md. Hermes streams the file as system prompt |
| 34 | Hermes cron-job answer goes to wrong chat (no thread) | Cron `deliver` argument must be `platform:chat_id:thread_id` for topics, NOT `platform:chat_id`. Without thread_id, replies go to General topic |
| 35 | First user message after restart silently dropped | Telegram polling needs 5-10s after `gateway run` start to be ready. Wait for "Gateway running with 1 platform(s)" before testing |
| 36 | OAuth ChatGPT account_id missing in JWT — Cloudflare 403 | Need `ChatGPT-Account-ID` header in Codex requests, extracted from JWT `chatgpt_account_id` claim. Hermes `auxiliary_client.py` does this correctly; custom code must too |
| 37 | session_id collisions during migration | UNIQUE constraint on `sessions.title` in Hermes state.db. Make titles unique by appending session_id prefix: `title = base_title + ' #' + sess_id[:8]` |
| 38 | `gemini-3.5-flash` returns `completion_tokens: 0` despite 200 OK | Model spent all max_tokens on reasoning. Bump `max_tokens` in your config or set `reasoning_effort: low` in config.yaml |
| 39 | Proactive notification fires every hour for same lead | `lead.id` (PK) passed instead of `lead.user_id` (FK to users). Dedup lookup always misses. Use `entity.user_id` consistently |
| 40 | SQL injection via dynamic column name in `SET ${field}` | Parameterized queries protect values, NOT identifiers. Use allowlist: `ALLOWED_FIELDS.has(field)` before interpolation |
| 41 | Grammy typing indicator shows "typing..." forever after error | `setInterval` for typing without `try/finally { clearInterval }`. Always wrap in try/finally |
| 42 | SCP deploy missed new file, Docker built with stale code | Verify critical files on server after SCP: `ssh "$SERVER" "ls -la /opt/bot/src/scheduler/index.ts"` |
| 43 | Bot crashes on rare feature because env var missing | Raw `process.env` access fails at call time, not startup. Centralize all vars through Zod schema with `safeParse` at import |
| 44 | Voice messages not transcribed (or inconsistent) | Auto-detect picks OpenAI Whisper when OPENAI_API_KEY is set (order: openai→groq→deepgram→google). Fix: explicitly set `tools.media.audio.models: [{"type":"provider","provider":"deepgram","model":"nova-3"}]` in openclaw.json |
| 45 | `web_search` fails with "SUBSCRIPTION_TOKEN_INVALID" | Brave Search API key expired. Fix: switch `tools.web.search.provider` to `"perplexity"` (needs PERPLEXITY_API_KEY) |
| 46 | Cron can't find Telegram channel (private, no username) | Private channels have no public @username. Use numeric channel ID via Telethon: `await client.get_entity(-100XXXXXXXXXX)`. Put ID in fetch script, not cron prompt |
| 47 | SQLite "attempt to write a readonly database" for Telethon session | Workspace directory owned by root — SQLite can't create WAL file. Fix: `chown 1000:1000` on the workspace volume directory (not just the .session file) |
| 48 | Telethon script "API_ID cannot be empty" but .env has values | Env var naming mismatch: .env has `TELEGRAM_API_ID` but script reads `API_ID`. Always match `os.getenv()` key to actual .env key |
| 49 | Pip packages lost after `docker rm + docker run` (not restart) | `docker restart` preserves container layer; `docker rm + run` rebuilds from image. Fix: create `setup_deps.sh` in workspace volume + host-level `@reboot` crontab that runs it after container start |
| 50 | Cron "announce delivery failed" — message never arrives | `delivery.to` format wrong or target unresolvable. Use `"telegram:USER_ID"` (numeric). Check `state.lastError` in cron/jobs.json |
| 51 | VPS lockout after SSH hardening | Password disabled before key login was verified. Always confirm `KEY_OK` by key BEFORE turning password off; recovery only via provider VNC. See `references/vps-ssh-hardening.md` |
| 52 | Password auth won't turn off despite editing sshd_config | Ubuntu cloud images keep `PasswordAuthentication yes` in `/etc/ssh/sshd_config.d/50-cloud-init.conf`; drop-ins read lexicographically, first match wins → add `00-hardening.conf`. Verify `sshd -T \| grep passwordauth` |
| 53 | Cut own SSH session when enabling firewall | `ufw enable` without allowing SSH first → always `ufw allow OpenSSH` BEFORE `ufw --force enable` |

---

