# Manus API v2 — reference

Source: https://open.manus.im/docs (API v2). Verified 2026-07-22. v1 is deprecated.

- Base URL: `https://api.manus.ai`
- Auth: header `x-manus-api-key: <key>` **or** `Authorization: Bearer <oauth_token>`
- Content type: `application/json`
- Get an API key: Manus web app → Settings → Integration → "Build with Manus API" → Create New.

Legend: ✅ = exercised live via `manus_helper.py`; 📄 = documented by Manus, not yet tested here.

## Endpoints

| Endpoint | Method | Purpose | Status |
|---|---|---|---|
| `/v2/task.create` | POST | Create an async agent task | ✅ |
| `/v2/task.listMessages` | GET (query params) | Poll event/message history, read `agent_status` | ✅ |
| `/v2/task.detail` | GET | Task metadata | 📄 |
| `/v2/task.sendMessage` | POST | Follow-up / answer a `waiting` task | ✅ (create path) |
| `/v2/task.stop` | POST | Halt a running task | 📄 |
| `/v2/task.list` | GET | List tasks (filter/paginate) | 📄 |
| `/v2/task.update` | POST | Edit task metadata | 📄 |
| `/v2/task.delete` | POST | Delete task | 📄 |
| `/v2/task.confirmAction` | POST | Approve a pending action to resume | 📄 |
| `/v2/file.upload` | POST | Create file record + presigned PUT upload URL (≤512MB) | 📄 |
| `/v2/file.detail`, `/v2/file.delete` | GET/POST | File metadata / delete (auto-deleted after 48h) | 📄 |
| `/v2/connector.list`, `/v2/skill.list`, `/v2/project.list`, `/v2/agent.list` | GET | List connectors / skills / projects / agents | 📄 |

## task.create — request body

```json
{
  "message": {
    "content": "string OR array of ContentPart",
    "connectors": ["<connector_id>"],
    "enable_skills": ["<skill_id>"],
    "force_skills": ["<skill_id>"]
  },
  "agent_profile": "manus-1.6 | manus-1.6-lite | manus-1.6-max",
  "locale": "en | ru | zh-CN | ja | …",
  "interactive_mode": false,
  "hide_in_task_list": false,
  "share_visibility": "private | team | public",
  "project_id": "…",
  "title": "…",
  "structured_output_schema": { "...JSON Schema..." }
}
```

Only `message.content` is required. `agent_profile` defaults to `manus-1.6`.

ContentPart types: `text` (`{type,text}`), `file` (`{type:"file", file_id|file_url|file_data}`),
`voice` (`{type:"voice", file_id|file_url|file_data}`). Limits: `file_id` ≤512MB,
`file_url`/`file_data` ≤20MB.

### task.create — success response

```json
{ "ok": true, "request_id": "…", "task_id": "…",
  "task_title": "…", "task_url": "https://manus.im/app/<id>",
  "share_url": "… (if not private)", "share_visibility": "private" }
```

### Error response (any endpoint)

```json
{ "ok": false, "request_id": "…",
  "error": { "code": "invalid_argument|not_found|permission_denied|rate_limited", "message": "…" } }
```

## task.listMessages — poll

`GET /v2/task.listMessages?task_id=<id>&order=desc&limit=20[&cursor=<c>]`

Response: `{ ok, task_id, has_more, messages: [ event, … ] }`. Each event has a `type`:

- `type: "user_message"` → `user_message.content`
- `type: "assistant_message"` → `assistant_message.content` (the agent's answer text)
- `type: "status_update"` → `status_update.agent_status` in
  `running | stopped | error | waiting`, plus `brief`/`description`.

**Completion:** task is done when the newest `status_update.agent_status` is `stopped`
(success) or `error`. `waiting` means it needs input — the waiting reason is in
`status_detail.waiting_for_event_type` (e.g. `messageAskUser`, `needConnectMyBrowser`,
`gmailSendAction`, `deployAction`, `terminalExecute`, …); resume via `task.sendMessage`
or `task.confirmAction`.

Structured output (when `structured_output_schema` was given) is returned as
`structured_output_result`.

## Live-verified example (2026-07-22)

`task.create` with `agent_profile=manus-1.6-lite`, prompt "Reply with exactly PONG" →
task ran `running` → `stopped`, `assistant_message.content == "PONG"`. Full create→poll→
answer loop works through `manus_helper.py run`.
