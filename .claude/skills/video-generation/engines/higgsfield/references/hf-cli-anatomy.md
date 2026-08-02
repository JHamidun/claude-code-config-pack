# hf.exe — полная анатомия (разобрано на запчасти, 2026-06-07)

`~/.claude/skills/video-generation/engines/higgsfield/bin/hf.exe` — **8.66 МБ, Go-бинарь** (Cobra CLI), статически слинкован,
репо `github.com/higgsfield-ai/cli`, v0.1.40. Алиасы: `higgsfield` / `higgs` / `hf`. NPM-shim (`higgsfield.cmd`)
пустой — вся логика в бинаре. **Per-model param-схемы НЕ в бинаре — приходят с сервера** (`hf model get`).

## Дерево команд (Cobra)
```
hf
├── account (acc)        — status | transactions [--size N]        (баланс/план/транзакции)
├── auth                 — login | logout | token                  (device-flow OAuth)
├── generate (gen)       — create <model> | cost <model> | get <id> | list | wait <id>
├── model                — list [--image|--video|--text] | get <jst>   (--json = схема params)
├── marketing-studio (ms)— avatars | products | hooks | brand-kits | ad-references | ad-formats
│                          | dtc-ads | webproducts | settings        (DTC Ads Engine, см. exclusive-models)
├── product-photoshoot   — create --mode <m> --prompt --image --count   (mode-specific enhance)
├── marketplace-cards    — create --scope product-images --prompt --image (→ возвращает nano_banana_2 промпты)
├── soul-id              — create --name --soul-2 --image×5 | list | get | wait   (обучение Soul-персонажа)
├── upload               — upload media inputs → upload_id (для --image)
├── workspace            — select billing workspace
└── version
Global: --json (raw JSON), --no-color
```

## Авторизация (auth/device.go, auth/refresh.go, auth/store.go)
**OAuth 2.0 Device Flow** через `fnf-device-auth.higgsfield.ai`:
1. `POST .../authorize` → `{device_code, user_code, verification_uri, expires_in, interval}` → открывает браузер (`auth.openBrowser`).
2. Polling по `interval` до `access_token`+`refresh_token`.
3. Хранит локально (`auth.Save`/`Load`/`Delete`, `WithLock`), у нас в `~/.claude/.credentials.master.env`: `HIGGSFIELD_ACCESS_TOKEN` (hf_…) + `HIGGSFIELD_REFRESH_TOKEN`.
4. `auth.Refresh` → `POST .../refresh` (postRefresh) при 401. Header `Authorization: Bearer hf_…`.
5. API-клиент детектит среду (`isClaudeCodeEnv`/`isCodexEnv`/`isCursorEnv`/`isHermesEnv`/`isOpenClawEnv`/`isPerplexityEnv`) → user-agent `hf-cli/1.0` + agent-client name.

## API (api/client.go, jobs.go) — generation backend
Host `fnf.higgsfield.ai` (dev: `dev-fnf.higgsfield.ai`).
- `POST /jobs` — create. payload: `{job_set_type, params:{prompt, aspect_ratio, resolution, width, height, batch_size, seed, duration/seconds, quality, style, medias:[{value,role}], reference_elements:[], soul_id, brand_kit_id, input_images, …}}`. Поля зависят от модели (см. `hf model get`).
- `POST /jobs/cost` (`/jobs/costmax`) — оценка кредитов (= `hf generate cost`).
- `GET /jobs/{id}` / `GET /jobs/{id}/status` / poll (`/jobs/poll`) — статус→результат.
- `GET /assets/{id}/detail` — финальная запись (urls+params).
- Результаты на CDN `d8j0ntlcm91z4.cloudfront.net` / `d2ol7oe51mr4n9.cloudfront.net`.
- Ошибки: `formatPydanticErrors`/`mapError`/`extractDetail` (бэкенд = FastAPI/Pydantic).

## Базовое использование (наш прямой доступ, 1200 кредитов)
```bash
export HIGGSFIELD_ACCESS_TOKEN=hf_…           # из creds
hf account status --json                       # баланс
hf model list --video --json                   # каталог
hf model get seedance_2_0 --json               # схема params модели
hf upload ./kf.png                             # → upload_id
hf generate cost seedance_2_0 --prompt "…" --image <upload_id>   # оценка кредитов ДО
hf generate create seedance_2_0 --prompt "…" --image <upload_id> --aspect 9:16 --resolution 720p
hf generate wait <job_id> --json               # → result url → curl скачать
```

## Что это даёт
- `hf.exe` = тонкий Go-клиент к их jobs-API. **Запчасти:** device-auth + jobs CRUD + model-schema (server-side) + спец-обвязки (marketing-studio/product-photoshoot/marketplace-cards = backend prompt-enhance).
- Для моделей, что есть у нас напрямую (Veo/Seedance-Runway/Nano/GPT-Image/flux/recraft/topaz/kling/seedream/wan/minimax) → бить в их родные API (дешевле, см. `model-provider-map.md`).
- `hf.exe` оставить для Higgsfield-эксклюзивов: **Soul Cast/Location, Marketing Studio/DTC Ads, Virality Predictor, marketplace-cards, product-photoshoot** (backend prompt-enhance + их fine-tunes) — см. `exclusive-models-soul-ms-virality.md`.
