# Hermes on Bare-Metal VPS (systemd, no Docker)

> Verified preset: Ubuntu 24.04 (2 CPU / ~4 GB), Hermes v0.17.0, model `kimi-k2.5` via AITUNNEL.
> Complements `deployment-docker.md` (our primary path). Use bare-metal when: cheap single-bot VPS,
> client/student deploys without Docker, or RU-hosted servers where a Docker registry pull is flaky.
> Source: adapted from a field-tested community preset (2026-07); commands below are what actually worked.

---

## When bare-metal vs Docker

| Factor | Bare-metal systemd | Docker (our default) |
|--------|--------------------|----------------------|
| Setup speed on fresh VPS | Faster (one installer) | Needs Docker + image build |
| Fleet on one host | Poor isolation | Clean (volumes, networks) |
| Upgrades | `install.sh` re-run | Rebuild/pull image |
| Client handoff (RU students) | Simplest | Requires Docker literacy |

## Prerequisites (do IN THIS ORDER)

```bash
apt update && apt -y upgrade
apt -y install curl git
timedatectl set-timezone Europe/Moscow   # BEFORE any cron jobs, otherwise deliveries shift by 3h
free -m                                   # need >=2 GB RAM — agent OOM-crashes on 1 GB
```

**Host timezone BEFORE cron.** For Docker we solve this with per-cron `tz:`; on bare VPS the
scheduler inherits the host TZ at job-creation time — set it first or deliveries drift.

## Install (official installer, non-interactive)

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --non-interactive --skip-setup
```

`--skip-setup` skips the interactive wizard — we place the config ourselves. Resulting layout:

| Path | What |
|------|------|
| `/usr/local/bin/hermes` | CLI binary |
| `/usr/local/lib/hermes-agent` | code + venv |
| `/root/.hermes/` | working dir: `config.yaml`, `.env`, `logs/`, `sessions/`, `cron/`, `skills/`, `memories/` |

If the installer output differs (newer version) — check `hermes --help` and the generated
`config.yaml`, keep the SEMANTICS: custom provider + base_url + exact model id + systemd service.

## Model config — `/root/.hermes/config.yaml`

Any OpenAI-compatible endpoint works as `provider: custom`; only `base_url`/`model`/`api_key` differ.
Provider base_urls (incl. AITUNNEL for RU deploys): see the "Custom OpenAI-compatible providers"
table in `hermes-config-reference.md`.

**Don't guess the model id** — pull the exact id from the provider catalog first:

```bash
curl -s <BASE_URL>/models -H "Authorization: Bearer <MODEL_API_KEY>" | python3 -m json.tool
```

If this isn't HTTP 200 — fix key/balance/region access BEFORE continuing.

```yaml
model:
  provider: custom
  base_url: https://api.aitunnel.ru/v1   # or api.moonshot.ai/v1 / api.deepseek.com/v1
  model: kimi-k2.5                        # exact id from GET /v1/models
  api_key: "<MODEL_API_KEY>"
```

```bash
chmod 600 /root/.hermes/config.yaml
```

**Rule:** keep the operator's key in ONE place — your own env file (образец имён —
`.claude/templates/.credentials.master.env.example`) — and inject it into the server config from there.
Never hardcode keys in scripts and never commit them.

## Telegram secrets — `/root/.hermes/.env`

```bash
TELEGRAM_BOT_TOKEN=<BOT_TOKEN>
TELEGRAM_ALLOWED_USERS=<TELEGRAM_USER_ID>
TELEGRAM_HOME_CHANNEL=<TELEGRAM_USER_ID>   # cron deliveries to owner
GATEWAY_ALLOW_ALL_USERS=false              # MANDATORY: bot answers allowlist only
```

```bash
chmod 600 /root/.hermes/.env
```

`GATEWAY_ALLOW_ALL_USERS=false` is an env flag NOT covered by the Docker env table in
`hermes-config-reference.md` — without it (or with an empty `TELEGRAM_ALLOWED_USERS`) the bot is
open to anyone.

## systemd service (24/7)

```bash
hermes gateway install --system --run-as-user root
systemctl enable --now hermes-gateway.service
```

Expect: unit `/etc/systemd/system/hermes-gateway.service`, `enabled`, `active (running)`,
`Restart=always`.

**Root caveat (our canon: non-root for prod).** `--run-as-user root` is the quick-test path; the
agent's tool access then equals full root. For production create a dedicated unprivileged user, chown
its `~/.hermes/`, and pass `--run-as-user <user>` — same flow, tighter blast radius. Tell the client
explicitly which mode they got.

## Verification (drive to green)

```bash
systemctl status hermes-gateway.service --no-pager
journalctl -u hermes-gateway.service -n 40 --no-pager   # look for '✓ telegram connected (polling mode)'
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getMe"   # "ok": true + bot username
# one-shot POST <base_url>/chat/completions with the key+model → HTTP 200
```

Then `/start` the bot in Telegram and ask a question.

## Hardening (mandatory after the bot works)

Full playbook with lockout gotchas: `vps-ssh-hardening.md` (keys → fail2ban → ufw → password off).
Telegram polling and model APIs are OUTBOUND — no inbound ports needed beyond SSH.

## Bare-metal gotchas (delta vs Docker table)

| Symptom | Fix |
|---------|-----|
| Agent starts then dies immediately | <2 GB RAM → resize VPS |
| Cron deliveries shifted by 3h | TZ set after jobs were created → `timedatectl set-timezone` first, recreate jobs |
| Model not found | Guessed id → take exact id from `GET /v1/models` |
| `chat/completions` 401/402 | Bad key or zero balance (AITUNNEL — top up; direct Moonshot/DeepSeek — key/region) |
| `chat/completions` 404 model / conn error | base_url ↔ model id mismatch for the provider |
| Bot answers strangers | `GATEWAY_ALLOW_ALL_USERS` not `false` or empty `TELEGRAM_ALLOWED_USERS` |
| Re-entry after hardening fails with password | By design — connect by key: `ssh -i ~/.ssh/id_ed25519 root@<VPS_IP>` |
