# Hermes Provider Resolution Cascade

The single most frustrating Hermes phenomenon: you change `config.yaml` from one provider to another, restart the container, and the bot **still uses the old provider**. This happens because Hermes resolves the active provider+model from **five independent state locations**, each of which can override the others.

This document is the source-code-level forensic guide.

## The 5 Layers

When a Telegram message arrives at the gateway, `_resolve_runtime_agent_kwargs()` in `gateway/run.py` is called. It in turn calls `resolve_runtime_provider()` from `hermes_cli/runtime_provider.py`:

```python
runtime = resolve_runtime_provider(
    requested=os.getenv("HERMES_INFERENCE_PROVIDER"),
)
```

The `requested` argument can be ANY of:
- `None` → resolver falls through to config / state / auth_json
- `"gemini"` / `"openai-codex"` / `"anthropic"` etc. → explicit override

Then `resolve_requested_provider()` resolves the requested:

```python
# Layer 1: explicit argument (already includes env HERMES_INFERENCE_PROVIDER from above)
if requested and requested.strip():
    return requested.strip().lower()

# Layer 2: config.yaml model.provider
model_cfg = _get_model_config()
cfg_provider = model_cfg.get("provider")
if isinstance(cfg_provider, str) and cfg_provider.strip():
    return cfg_provider.strip().lower()

# Layer 3: env again (fallback if config empty)
env_provider = os.getenv("HERMES_INFERENCE_PROVIDER", "").strip().lower()
if env_provider:
    return env_provider

return "auto"
```

After provider name resolved, `resolve_runtime_provider()` then:
- Looks up `model_cfg.get("default")` for model name
- Looks up `model_cfg.get("base_url")` for endpoint
- Returns dict `{provider, model, base_url, api_mode, api_key, source}`

But — **per-session pinning overrides the above** in the runtime layer of `run_agent.py`. Each Telegram DM has a session in `state.db` with `billing_provider` field. If non-NULL, that wins over config.

And — for **continuation** of in-flight conversations, `gateway/session.py` reads `session_meta.model` from the FIRST line of `sessions/<sess_id>.jsonl`. That model name is used to look up provider via `models_dev.py` mapping.

So the cascade order, top to bottom, is:

| Layer | Source | When read | How to override |
|---|---|---|---|
| 1 | `HERMES_INFERENCE_PROVIDER` env var | Every gateway message | Set via compose `environment:` or in `/opt/data/.env` |
| 2 | `/opt/data/.env` file | Every gateway message (loaded at session start) | `sed -i 's/^HERMES_INFERENCE_PROVIDER=.*/HERMES_INFERENCE_PROVIDER=gemini/' /opt/data/.env` |
| 3 | `config.yaml` `model:` block | Every gateway message | Edit `default` + `provider` + `base_url`. Use `hermes config set` CLI for safety |
| 4 | `state.db sessions.billing_provider` per session | When existing session is found for inbound user | `UPDATE sessions SET billing_provider=NULL, model=NULL, billing_base_url=NULL` |
| 5 | `/opt/data/sessions/<sess_id>.jsonl` first line `session_meta.model` | When session.jsonl exists for continuation | `sed -i 's/old-model/new-model/g' /opt/data/sessions/*.jsonl` |

## Counterintuitive: `.env` file overrides docker-compose env

**This was the killer bug in our May 31 outage.** Hermes runtime loads `/opt/data/.env` via `dotenv` library, and that loader runs AFTER docker container env is set. So `.env` file vars override docker-compose `environment:` for `HERMES_INFERENCE_PROVIDER` and friends.

Real example from our outage:
- docker-compose.yml: `HERMES_INFERENCE_PROVIDER: "gemini"`
- /opt/data/.env: `HERMES_INFERENCE_PROVIDER=openai-codex` (leftover from earlier migration)
- Result: bot uses openai-codex → fails because Codex creds revoked → "Provider authentication failed"
- Even though `docker exec bot env | grep PROVIDER` shows `gemini` (env var IS set), the runtime reads `.env` file at session start and that overrides.

Fix: always sed both files in lockstep.

## Auth JSON: another override path

There's a 6th half-layer — `/opt/data/auth.json`:

```json
{
  "providers": {
    "openai-codex": { "tokens": {...}, "auth_mode": "chatgpt" },
    "anthropic": { "api_key": "..." },
    "gemini": { "api_key": "..." }
  },
  "active_provider": "gemini"
}
```

`active_provider` is set by `hermes model` interactive CLI and read by `hermes_cli/auth.py:resolve_provider()`. If the provider listed in `providers` doesn't match the requested provider, certain code paths in `credential_pool.py` will re-seed it. Specifically `providers.openai-codex` is auto-seeded from `~/.codex/auth.json` AND from the in-container auth.json — so even if you delete openai-codex from auth.json, it can be reseeded if a chatgpt session token exists anywhere.

To fully eliminate Codex as a fallback:
```python
# /opt/data/auth.json
import json
fp = "/opt/data/auth.json"
d = json.load(open(fp))
d.get("providers", {}).pop("openai-codex", None)
d["active_provider"] = "gemini"
json.dump(d, open(fp, "w"), indent=2)
```

## The full bot-reset sequence (when nothing else works)

When a bot stubbornly uses the wrong provider despite all your edits, run this nuclear option:

```bash
BOT=<bot>   # имя своего контейнера
NEW_PROVIDER=gemini
NEW_MODEL=gemini-3.5-flash
NEW_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"

ssh "$SERVER" "
docker exec -u 0 hermes-${BOT} bash -c '
  # 1. .env file
  sed -i \"s|^HERMES_INFERENCE_PROVIDER=.*|HERMES_INFERENCE_PROVIDER=${NEW_PROVIDER}|\" /opt/data/.env
  sed -i \"s|^HERMES_DEFAULT_MODEL=.*|HERMES_DEFAULT_MODEL=${NEW_MODEL}|\" /opt/data/.env

  # 2. config.yaml — rewrite model: block
  python3 -c \"
import re
fp = \\\"/opt/data/config.yaml\\\"
src = open(fp).read()
src = re.sub(r\\\"^model:.*?(?=^[a-zA-Z])\\\", \\\"model:\\\\n  default: ${NEW_MODEL}\\\\n  provider: ${NEW_PROVIDER}\\\\n  base_url: ${NEW_BASE_URL}\\\\n\\\\n\\\", src, count=1, flags=re.MULTILINE | re.DOTALL)
open(fp, \\\"w\\\").write(src)
\"

  # 3. auth.json — remove old provider, set active
  python3 -c \"
import json
fp = \\\"/opt/data/auth.json\\\"
d = json.load(open(fp))
for stale in [\\\"openai-codex\\\", \\\"anthropic\\\"]:
    d.get(\\\"providers\\\", {}).pop(stale, None)
d[\\\"active_provider\\\"] = \\\"${NEW_PROVIDER}\\\"
json.dump(d, open(fp, \\\"w\\\"), indent=2)
\"

  # 4. state.db — wipe session pinning
  python3 -c \"
import sqlite3
c = sqlite3.connect(\\\"/opt/data/state.db\\\")
c.execute(\\\"UPDATE sessions SET billing_provider=NULL, model=NULL, billing_base_url=NULL\\\")
c.commit()
c.close()
\"

  # 5. sessions/*.jsonl — replace pinned model in session_meta
  for f in /opt/data/sessions/*.jsonl; do
    sed -i \"s|openai-codex/gpt-5.4|${NEW_PROVIDER}/${NEW_MODEL}|g; s|openai-codex|${NEW_PROVIDER}|g; s|gpt-5.4|${NEW_MODEL}|g; s|chatgpt.com/backend-api/codex|${NEW_BASE_URL}|g\" \"\$f\"
  done

  # 6. sessions.json cache
  rm -f /opt/data/sessions/sessions.json
'

# 7. force restart
cd /opt/hermes-${BOT} && docker compose up -d --force-recreate
"
```

After this every layer of cascade points at the new provider. Restart picks it up cleanly.

## Verification

After fix, before testing via Telegram:

```bash
ssh "$SERVER" "
docker exec -u 1000 hermes-${BOT} /opt/hermes/.venv/bin/python3 -c '
from hermes_cli.runtime_provider import resolve_requested_provider, resolve_runtime_provider
print(\"requested:\", resolve_requested_provider())
r = resolve_runtime_provider()
print(\"runtime provider:\", r.get(\"provider\"))
print(\"runtime api_mode:\", r.get(\"api_mode\"))
print(\"runtime base_url:\", r.get(\"base_url\"))
'
"
```

Should print:
```
requested: gemini
runtime provider: gemini
runtime api_mode: chat_completions
runtime base_url: https://generativelanguage.googleapis.com/v1beta/openai
```

If any line doesn't match, you missed a layer. Re-check the cascade above.

## Why this architecture

It's not malicious — each layer was added for a legitimate reason:
- `config.yaml` — persistent default, edit-friendly
- `.env` — secret-friendly per-env overrides (recommended pattern in 12-factor apps)
- `auth.json` — runtime cache so re-auth flows don't keep prompting
- `state.db sessions.billing_provider` — multi-tenant billing audit. When a user upgrades from free→paid mid-conversation, future turns should bill against new provider, but historical turns still attributed to original
- `sessions/*.jsonl` session_meta — supports session resumption after server restart with consistent model behavior

The pain is that all five can independently drift, especially across migrations. Fix order: env → config → auth → state.db → jsonl, in that priority. Verify with the resolver test above.

## Source-code references

- `gateway/run.py:_resolve_runtime_agent_kwargs()` — entry point
- `hermes_cli/runtime_provider.py:resolve_requested_provider()` — provider name resolution
- `hermes_cli/runtime_provider.py:resolve_runtime_provider()` — full runtime dict construction
- `hermes_cli/runtime_provider.py:_get_model_config()` — reads config.yaml model: block
- `hermes_cli/auth.py:resolve_provider()` — auth.json reader
- `gateway/session.py:load_session()` — reads jsonl session_meta
- `hermes_state.py SCHEMA_SQL.sessions` — billing_provider column definition
- `agent/credential_pool.py:_load_pool()` — auto-seeding from auth.json + ~/.codex/auth.json
