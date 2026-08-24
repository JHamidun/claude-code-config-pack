# Telethon Autonomous Smoke Test Loop

When fixing a frozen or misbehaving bot, do NOT loop "send test → ask user → wait → repeat". You can drive Telegram yourself via `~/.claude/tools/tg_client.py` as the user account (Telethon), then read replies, parse them, and iterate fixes autonomously.

This document is the canonical pattern for autonomous bot debugging from inside Claude Code.

## Prerequisites

- `tg_client.py` set up on Windows side (already done — uses your Telethon session)
- Bot username (NOT bot token) — e.g. `<BotName>`, `SecondBot_bot`

## Single-bot smoke loop

```bash
# 1. Send a test message
python ~/.claude/tools/tg_client.py send <BotName>_bot "тест N"

# 2. Wait for a REAL agent reply (not an error/retry/system message)
until python ~/.claude/tools/tg_client.py read-chat <BotName>_bot --limit 1 2>&1 \
        | grep -E '<BotName>.*\] ' \
        | grep -vE 'тест N|API call failed|⏳|⚠|Gateway shutting|Retrying'; do
  sleep 5
done

# 3. Show final reply
python ~/.claude/tools/tg_client.py read-chat <BotName>_bot --limit 4
```

Key trick: the `grep -vE` filter EXCLUDES sentinel messages from Hermes:
- `тест N` — your own outgoing message (echo)
- `API call failed` — provider error fallback
- `⏳ Retrying in Xs (attempt Y/3)` — Hermes retry-warmup notice
- `⚠ Max retries exhausted — trying fallback` — Hermes failover notice
- `⚠ Gateway shutting down` — Hermes shutdown notice
- `⚡ Interrupting current task` — Hermes interrupt-during-busy notice

Only when ALL filters fail and a real agent message lands, the loop exits.

## Multi-bot fleet smoke (parallel)

```bash
# Send to ALL bots
for bot in <BotName> SecondBot_bot AnotherBot_bot; do
  python ~/.claude/tools/tg_client.py send "${bot}" "тест fleet" &
done
wait

# Then poll each for real reply
for bot in <BotName> SecondBot_bot AnotherBot_bot; do
  echo "=== ${bot} ==="
  until python ~/.claude/tools/tg_client.py read-chat "${bot}" --limit 1 2>&1 \
          | grep -E "${bot}.*\] " \
          | grep -vE 'тест fleet|API call|⏳|⚠|Gateway'; do
    sleep 5
  done
  python ~/.claude/tools/tg_client.py read-chat "${bot}" --limit 3 | tail -10
done
```

## Increment test number across iterations

When you cycle through fixes (rebuild → restart → test → fail → fix → restart → test → fail → ...), use incrementing test numbers:

- Iteration 1: send "тест 1"
- Iteration 2: send "тест 2"
- ...

This lets you parse `[reply to #935199]` ids in the response stream and correlate which reply matches which send. Telegram message_id assignment is monotonic per chat.

## Combining with server-side log inspection

While Telethon waits for TG reply, you can in parallel watch Hermes logs on the VPS:

```bash
# In one shell: send + poll TG
python ~/.claude/tools/tg_client.py send <BotName> "тест 7"

# In another shell: watch logs flow
ssh "$SERVER" "docker exec hermes-<bot> tail -f /opt/data/logs/agent.log" \
  | grep -E 'inbound|response ready|API call failed|HTTP'
```

You see:
1. `inbound message: platform=telegram user=... msg='тест 7'`
2. `OpenAI client created` (gateway picks provider)
3. `chat_completion_stream_request`
4. `API call #1: model=X provider=Y in=N out=M latency=Zs`
5. `response ready: api_calls=1 response=68 chars`
6. `Sending response (68 chars) to <chat_id>`

If step 4 has `provider=openai-codex` when you expected `gemini`, you missed a cascade layer — see `hermes-provider-resolution-cascade.md`.

## Anti-pattern: stop polling once you "know" it works

Do NOT mark the task complete after a single 200 OK reply. Send 3 different messages and verify all 3 get coherent agent replies:

```bash
for msg in "привет" "сколько 2+2" "расскажи короткую шутку"; do
  python ~/.claude/tools/tg_client.py send <BotName> "${msg}"
  until python ~/.claude/tools/tg_client.py read-chat <BotName> --limit 1 2>&1 \
          | grep -E '<BotName>.*\] ' \
          | grep -vE "${msg}|API call|⏳|⚠|Gateway"; do
    sleep 4
  done
done

# Then dump last 6 messages to see all 3 replies
python ~/.claude/tools/tg_client.py read-chat <BotName> --limit 6
```

This catches intermittent failures: provider working once → cron-fire reuses old session pinning → fails. Send multiple variations across timing windows.

## Sending voice / file / photo

```bash
# Voice memo (transcribed via faster-whisper inside Hermes)
python ~/.claude/tools/tg_client.py send-file <BotName> /path/to/voice.ogg

# Document
python ~/.claude/tools/tg_client.py send-file <BotName> /path/to/budget.xlsx

# Photo (Hermes routes through vision_analyze)
python ~/.claude/tools/tg_client.py send-file <BotName> /path/to/test.jpg
```

After send, the same `read-chat` polling works. Hermes uses faster-whisper for voice (locally, no API call). Vision uses primary provider (Gemini Flash native vision) for image understanding.

## When to escalate to user

You don't need user intervention for:
- Send/receive/parse TG messages
- Container restart, config edit, log inspect
- Provider cascade fix
- Volume rebuild

You DO need user for:
- API key rotation (the owner has to paste fresh keys into their own env file)
- ChatGPT subscription `codex login` (interactive browser OAuth)
- Decision: which model to use, what persona changes to make, etc.
- Confirming critical destructive ops (`docker volume rm`)

In autonomous fix mode, surface the bug + proposed fix + ask permission ONLY when stuck on one of the above. Otherwise just keep iterating.

## Common Telethon gotchas

- **Bot username vs bot @-handle** — Telethon takes username (no @) or numeric chat_id. `<BotName>` works. `@<BotName>` also works (Telethon strips @).
- **No reply to your test for >60s** — bot may be processing OR may be silent due to a different cascade issue. Look at the server logs to confirm `inbound message` is received but no `response ready` is sent.
- **Reply with 269 chars exactly** — Hermes serves a stock error message at 269 chars. That's the "Provider authentication failed" template. `api_calls=0` in logs confirms it.
- **Multiple replies for one test message** — Hermes can stream multiple replies: typing indicator → first chunk → final chunk. Read with `--limit 5` to see all of them.

## tg_client.py exit codes

- 0 — success (message sent or read)
- 1 — auth issue (session file missing, etc.)
- 2 — network / Telegram API error
- 3 — bot not found / no permission

Always check exit code in scripted loops to bail early on infrastructure failures, not bot misconfig.
