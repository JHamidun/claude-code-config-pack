# HeyGen LiveAvatar — Realtime Video Avatar API

> Reverse-engineered from OpenAPI spec (187KB, `api.liveavatar.com/openapi.json`) + SDK source (`github.com/heygen-com/liveavatar-web-sdk`, `packages/js-sdk/src/`).
> Verified 2026-06-09.

## Overview

LiveAvatar = realtime talking-head avatar. User speaks → avatar animates lip-sync + gestures in real time. Two modes:

| Mode | Cost | What HeyGen does | What YOU provide |
|------|------|-------------------|------------------|
| **FULL** | 2 credits/min | STT + LLM + TTS + avatar render | Nothing (just configure) |
| **LITE** | 1 credits/min | Avatar render only | STT + LLM + TTS pipeline |

**Base URL:** `https://api.liveavatar.com`
**Auth:** `X-API-KEY: <key>` header (same as HeyGen main API, but SEPARATE service)
**SDK:** `@heygen/liveavatar-web-sdk` (npm), built on **LiveKit** (WebRTC rooms)
**Creds:** `HEYGEN_LIVE_AVATAR_API_KEY` in `.credentials.master.env`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LiveAvatar Service                     │
│                                                          │
│  ┌──────────┐   ┌─────────┐   ┌──────────────────────┐ │
│  │  LiveKit  │   │  Agent  │   │  Avatar Renderer     │ │
│  │  Room     │◄──│ (FULL)  │──►│  (Video + Audio out) │ │
│  └────┬─────┘   └─────────┘   └──────────────────────┘ │
│       │                                                  │
│       │  WebSocket (LITE mode)                           │
│  ┌────┴──────────────────────┐                           │
│  │  WS: agent.speak/interrupt │                          │
│  │  Events: speak_started/end │                          │
│  └───────────────────────────┘                           │
└─────────────────────────────────────────────────────────┘
         ▲                    │
         │ Audio/Data in      │ Video + Audio out
         │                    ▼
    ┌─────────┐         ┌──────────┐
    │  Client  │         │  Client  │
    │ (mic/TTS)│         │ (display)│
    └─────────┘         └──────────┘
```

### Transport layers

**LiveKit Room** (both modes):
- HeyGen participant (`identity: "heygen"`) publishes **video + audio** tracks
- In FULL mode: agent participant (`liveavatar-agent-{session_id}`) handles STT/LLM/TTS
- Client publishes local audio track (microphone) for VAD/STT
- DataChannel topics: `agent-control` (client→server commands), `agent-response` (server→client events)

**WebSocket** (LITE mode only):
- URL returned in `session.start()` response as `ws_url`
- Commands: `agent.speak` (audio chunks), `agent.speak_end`, `agent.interrupt`, `agent.start_listening`, `agent.stop_listening`
- Events: `agent.speak_started`, `agent.speak_ended`
- Audio format: **PCM 24kHz 16-bit mono, base64-encoded string**

## API Endpoints (24 total, OpenAPI 3.1.0)

### Sessions
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/sessions/token` | Generate session token (FULL or LITE) |
| POST | `/v1/sessions/start` | Start session (called by SDK internally) |
| POST | `/v1/sessions/stop` | Stop session |
| POST | `/v1/sessions/keep-alive` | Heartbeat |
| GET | `/v1/sessions` | List sessions (paginated, filter by avatar/embed/context) |
| GET | `/v1/sessions/{session_id}` | Session details |
| GET | `/v1/sessions/{session_id}/transcript` | Conversation transcript (timestamp range filter) |
| DELETE | `/v1/sessions/{session_id}/events` | Hard delete all events |

### Avatars (LiveAvatar-specific, separate from main HeyGen /v3/avatars)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/avatars` | List avatars (paginated) |
| GET | `/v1/avatars/public` | Public avatar gallery |
| GET | `/v1/avatars/{avatar_id}` | Avatar details |
| PATCH | `/v1/avatars/{avatar_id}` | Update config (persona, voice, context, STT) |
| DELETE | `/v1/avatars/{avatar_id}` | Soft delete |

### Voices
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/voices` | List (filter: public/custom) |
| POST | `/v1/voices/third_party` | Bind ElevenLabs/Fish voice |
| GET | `/v1/voices/{voice_id}` | Metadata |
| PATCH | `/v1/voices/{voice_id}` | Update |
| DELETE | `/v1/voices/{voice_id}` | Remove |
| GET | `/v1/voices/{voice_id}/preview` | Audio preview URL |

### Context (system prompt)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/contexts` | Create context (prompt, opening_text, variables) |
| GET | `/v1/contexts` | List |
| GET | `/v1/contexts/{context_id}` | Details with links |
| PATCH | `/v1/contexts/{context_id}` | Update |
| DELETE | `/v1/contexts/{context_id}` | Remove |

### Memory (cross-session)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/memory` | Store record |
| GET | `/v1/memory` | List (filter by type) |
| GET | `/v1/memory/{memory_id}` | Record with episodes |
| DELETE | `/v1/memory/{memory_id}` | Delete (204) |

### Secrets & LLM Config
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/secrets` | Store encrypted secret (KMS-backed) |
| GET | `/v1/secrets` | List metadata (values never exposed) |
| DELETE | `/v1/secrets/{secret_id}` | Delete |
| POST | `/v1/llm-configurations` | Create LLM config (references secret) |
| GET | `/v1/llm-configurations` | List |
| GET | `/v1/llm-configurations/{config_id}` | Details |
| PATCH | `/v1/llm-configurations/{config_id}` | Update |
| DELETE | `/v1/llm-configurations/{config_id}` | Delete |

### Other
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v2/embeddings` | Create embed (sandbox support) |
| GET | `/v1/users/credits` | Credit balance |
| GET | `/v1/languages` | Supported languages |

## Session Token — `POST /v1/sessions/token`

### FULL mode
```json
{
  "mode": "FULL",
  "avatar_id": "<liveavatar avatar_id>",
  "voice_id": "<voice_id>",
  "context_id": "<context_id>",
  "language": "ru",
  "video": {
    "encoding": "H264",
    "quality": "high"
  },
  "stt": {
    "provider": "deepgram",
    "language": "ru"
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "llm_configuration_id": "<stored config>"
  }
}
```

### LITE mode
```json
{
  "mode": "LITE",
  "avatar_id": "<liveavatar avatar_id>",
  "video": {
    "encoding": "H264",
    "quality": "high"
  }
}
```

**Video settings:**
- `encoding`: `H264` (default) or `VP8`
- `quality`: `very_high` / `high` / `medium` / `low`

**FULL mode voice providers:** ElevenLabs (Flash v2.5), Fish Audio (S1/S2)
**FULL mode STT providers:** Deepgram, AssemblyAI, Gladia, ElevenLabs
**FULL mode LLM integrations:** OpenAI Realtime, Gemini Realtime, ElevenLabs Agent

**Response:** JWT token string — decoded payload contains `start_session_data` with mode, configs

## SDK Internals (from source code)

### Session lifecycle
```
new LiveAvatarSession(token, config?)
  → session.start()
    → POST /v1/sessions/start (Bearer token)
    → Returns: { session_id, livekit_url, livekit_client_token, ws_url, max_session_duration }
    → Connect to LiveKit room
    → (FULL mode only) Wait for "heygen" + "liveavatar-agent-{id}" participants (30s timeout)
    → Connect to WebSocket if ws_url provided (LITE mode)
    → Configure voice chat (mic → local audio track)
  → session.stop()
    → Cleanup all tracks + room + WebSocket
    → POST /v1/sessions/stop
```

### Enums & types
```typescript
enum SessionMode { FULL = "FULL", LITE = "LITE" }
enum AgentType { FULL, OPENAI_REALTIME, ELEVENLABS_AGENT, GEMINI_REALTIME, UNKNOWN }
enum SessionState { INACTIVE, CONNECTING, CONNECTED, DISCONNECTING, DISCONNECTED }
enum SessionDisconnectReason { UNKNOWN_REASON, CLIENT_INITIATED, SESSION_START_FAILED, SERVER_INITIATED }
enum SessionInteractivityMode { CONVERSATIONAL, PUSH_TO_TALK }
enum VoiceChatState { INACTIVE, STARTING, ACTIVE }
```

### Session events (inbound from server)
```
session.state_changed      → SessionState
session.stream_ready       → (video + audio tracks both subscribed)
session.connection_quality_changed → ConnectionQuality
session.disconnected       → SessionDisconnectReason

user.speak_started         → { event_id }
user.speak_ended           → { event_id }
user.transcription         → { event_id, text }
user.transcription.chunk   → { event_id, text }
avatar.transcription       → { event_id, text }
avatar.transcription.chunk → { event_id, text }
avatar.speak_started       → { event_id }
avatar.speak_ended         → { event_id }
session.stopped            → { stop_reason }
elevenlabs_agent_event     → { elevenlabs_event_type, data }
```

### Command methods (outbound from client)
```typescript
// FULL mode — text commands via LiveKit DataChannel
session.message(text)       → AVATAR_SPEAK_RESPONSE (LLM generates response, avatar speaks)
session.repeat(text)        → AVATAR_SPEAK_TEXT (avatar speaks this exact text, no LLM)

// LITE mode — audio via WebSocket
session.repeatAudio(base64pcm24k) → agent.speak chunks + agent.speak_end
  // Audio: PCM 24kHz 16-bit mono, base64 string
  // Chunked: first 400ms (19200 bytes), then 1s chunks (48000 bytes)

// Both modes
session.interrupt()         → AVATAR_INTERRUPT
session.startListening()    → AVATAR_START_LISTENING
session.stopListening()     → AVATAR_STOP_LISTENING
session.keepAlive()         → POST /v1/sessions/keep-alive
session.attach(element)     → Attach video+audio to HTMLMediaElement
```

### ElevenLabsAgentSession (extends LiveAvatarSession)
For LITE+ElevenLabs Agent mode. Additional commands:
```typescript
session.sendUserMessage(text)       → EL user_message
session.sendContextualUpdate(text)  → EL contextual_update (silent context)
session.sendUserActivity()          → EL keepalive/typing indicator
session.sendClientToolResult({toolCallId, result, isError}) → EL client_tool_result
```

### VoiceChat (microphone handling)
```typescript
session.voiceChat.start({ defaultMuted?, deviceId?, mode? })
session.voiceChat.stop()
session.voiceChat.mute() / unmute()
session.voiceChat.setDevice(deviceId)
session.voiceChat.startPushToTalk() / stopPushToTalk()
// Push-to-talk: sends command on LiveKit agent-control, waits for server ack
```

## Integration with Telegram Voice Calls (pytgcalls)

### Architecture for LITE mode (recommended for custom pipeline)

```
Telegram Call (pytgcalls)
  │
  │ PCM 48kHz s16le
  ▼
┌─────────────┐    ┌──────────────────────────────────────────────┐
│ Resample    │    │         Your Pipeline (Pipecat/custom)       │
│ 48k → 16k  │───►│  STT (Deepgram/GigaAM) → LLM → TTS          │
└─────────────┘    │  (GPT-RT / Gemini / ElevenLabs / Cartesia)   │
                   └──────────────────┬───────────────────────────┘
                                      │ PCM 24kHz base64
                                      ▼
                   ┌──────────────────────────────────────────────┐
                   │  LiveAvatar WebSocket                         │
                   │  agent.speak(audio chunks) → avatar renders   │
                   └──────────────────┬───────────────────────────┘
                                      │
                                      ▼
                   ┌──────────────────────────────────────────────┐
                   │  LiveKit Room (video + audio tracks)          │
                   │  → aiortc / livekit-python-sdk                │
                   └──────────────────┬───────────────────────────┘
                                      │ H264/VP8 video + PCM audio
                                      ▼
                   ┌──────────────────────────────────────────────┐
                   │  Decode → YUV420p frames + PCM 48kHz         │
                   │  → pytgcalls VideoStream + AudioStream       │
                   └──────────────────────────────────────────────┘
                                      │
                                      ▼
                              Telegram Call (outgoing video+audio)
```

### Architecture for FULL mode (simpler, more expensive)

```
Telegram Call (pytgcalls)
  │
  │ PCM 48kHz s16le
  ▼
┌──────────────────┐
│ Resample 48k→48k │    ┌────────────────────────────────┐
│ Publish as local  │───►│ LiveKit Room                    │
│ audio track       │    │ (HeyGen manages STT+LLM+TTS+   │
└──────────────────┘    │  avatar rendering)               │
                        └───────────────┬────────────────┘
                                        │ Video + Audio tracks
                                        ▼
                        ┌────────────────────────────────┐
                        │ Decode → YUV420p + PCM 48kHz   │
                        │ → pytgcalls streams             │
                        └────────────────────────────────┘
```

### Key technical details for Python integration

1. **LiveKit Python SDK** (`livekit` on PyPI) for room connection
2. **WebSocket** (`websockets` or `aiohttp`) for LITE mode commands
3. **Audio format conversion:**
   - pytgcalls → LiveAvatar: resample 48kHz → 24kHz, base64 encode
   - LiveAvatar audio track → pytgcalls: resample if needed (LiveKit delivers at negotiated rate)
4. **Video decoding:** LiveKit track → raw frames → YUV420p → pytgcalls `VideoStream`
5. **Session token** obtained server-side via REST API, NOT from SDK

### Python session token example
```python
import os, requests

LA_KEY = os.environ['HEYGEN_LIVE_AVATAR_API_KEY']
LA_BASE = 'https://api.liveavatar.com'

def get_session_token(*, avatar_id, mode='LITE', video_quality='high', video_encoding='H264'):
    body = {
        'mode': mode,
        'avatar_id': avatar_id,
        'video': {'encoding': video_encoding, 'quality': video_quality},
    }
    r = requests.post(f'{LA_BASE}/v1/sessions/token',
                      headers={'X-API-KEY': LA_KEY, 'Content-Type': 'application/json'},
                      json=body, timeout=30)
    r.raise_for_status()
    return r.json()['data']['token']  # JWT string


def start_session(token):
    r = requests.post(f'{LA_BASE}/v1/sessions/start',
                      headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                      timeout=30)
    r.raise_for_status()
    return r.json()['data']
    # Returns: { session_id, livekit_url, livekit_client_token, ws_url, max_session_duration }


def stop_session(token):
    requests.post(f'{LA_BASE}/v1/sessions/stop',
                  headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                  timeout=10)


def check_credits():
    r = requests.get(f'{LA_BASE}/v1/users/credits',
                     headers={'X-API-KEY': LA_KEY}, timeout=10)
    r.raise_for_status()
    return r.json()['data']


def list_avatars():
    r = requests.get(f'{LA_BASE}/v1/avatars',
                     headers={'X-API-KEY': LA_KEY}, timeout=10)
    r.raise_for_status()
    return r.json()['data']


def list_public_avatars():
    r = requests.get(f'{LA_BASE}/v1/avatars/public',
                     headers={'X-API-KEY': LA_KEY}, timeout=10)
    r.raise_for_status()
    return r.json()['data']
```

### LITE mode WebSocket protocol
```python
import asyncio, json, base64, struct, websockets

async def lite_session(ws_url, tts_audio_pcm24k_bytes):
    async with websockets.connect(ws_url) as ws:
        # Send audio in chunks (first 400ms, then 1s)
        FIRST_CHUNK = 24000 * 2 * 0.4   # 19200 bytes
        NEXT_CHUNK = 24000 * 2 * 1.0    # 48000 bytes
        event_id = str(uuid.uuid4())

        # Chunk and send
        audio_b64 = base64.b64encode(tts_audio_pcm24k_bytes).decode()
        pos = 0
        chunk_size = int(FIRST_CHUNK * 4/3 + 4)  # base64 expansion
        # Actually work with raw bytes, encode per chunk:
        pos = 0
        first = True
        while pos < len(tts_audio_pcm24k_bytes):
            sz = int(FIRST_CHUNK) if first else int(NEXT_CHUNK)
            first = False
            chunk = tts_audio_pcm24k_bytes[pos:pos+sz]
            pos += sz
            chunk_b64 = base64.b64encode(chunk).decode()
            await ws.send(json.dumps({
                'type': 'agent.speak',
                'event_id': event_id,
                'audio': chunk_b64,
            }))

        # Signal end
        await ws.send(json.dumps({
            'type': 'agent.speak_end',
            'event_id': event_id,
        }))

        # Listen for events
        async for msg in ws:
            data = json.loads(msg)
            if data.get('type') == 'agent.speak_started':
                print(f"Avatar started speaking (event {data['event_id']})")
            elif data.get('type') == 'agent.speak_ended':
                print(f"Avatar finished speaking (event {data['event_id']})")
```

## Pricing

| Item | Cost |
|------|------|
| FULL mode session | 2 credits/min |
| LITE mode session | 1 credit/min |
| Credit purchase | varies by plan |

Check: `GET /v1/users/credits` → remaining balance.

## Gotchas

1. **LiveAvatar API is SEPARATE from main HeyGen API** — different base URL (`api.liveavatar.com` vs `api.heygen.com`), different auth header (`X-API-KEY` vs `x-api-key`), different avatar IDs
2. **LITE mode only supports `repeatAudio()`** — `message()` and `repeat()` throw "Not permitted in LITE mode"
3. **Audio must be PCM 24kHz 16-bit mono** — not 48kHz like pytgcalls. Resampling required.
4. **First audio chunk = 400ms (19200 bytes)** to minimize time-to-first-audio, then 1s chunks (48000 bytes)
5. **WebSocket is for commands only** — video/audio OUTPUT comes via LiveKit tracks
6. **FULL mode waits 30s for required participants** (`heygen` + `liveavatar-agent-{session_id}`). Timeout = session start failure.
7. **Session token is a JWT** — decoded payload contains `start_session_data` with mode, agent_type, configs. SDK parses mode and agent type from it.
8. **Video encoding options**: H264 (default, wide compat) or VP8 (WebM/transparency). Quality: very_high/high/medium/low.
9. **Keep-alive required** — sessions timeout without periodic `POST /v1/sessions/keep-alive`
10. **WebSocket close = session cleanup** — if WS disconnects unexpectedly, entire session tears down
11. **Secrets for LLM keys** — in FULL mode, store your OpenAI/Gemini key via `POST /v1/secrets`, reference in LLM config. Never sent in plain text after creation.
12. **Push-to-talk** — only in CONVERSATIONAL vs PUSH_TO_TALK interactivity modes. PTT sends command on LiveKit, waits for server ACK.
13. **ElevenLabsAgentSession** — specialized subclass for EL Agent integration. Adds `sendUserMessage`, `sendContextualUpdate`, `sendClientToolResult`. Disables `message()`/`repeat()`/`repeatAudio()`.
