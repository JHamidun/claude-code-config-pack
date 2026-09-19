# i2v cost & lipsync — battle-notes (2026-06-08, музыкальное видео)

Hard-won findings from building a 60s music video. Read before choosing an i2v / lipsync route.

## i2v MOTION — choose by cost, not habit

| Route | Cost | Verdict |
|---|---|---|
| **Veo 3.1 Fast via Google API** (`veo-3.1-fast-generate-preview`, `GOOGLE_API_KEY`) | Google budget, ~44-54s/6s-clip | **DEFAULT for i2v motion.** Not Runway credits. Script pattern: `scripts/direct_video.py gen … --engine veo-fast --first-frame kadr.jpg` (JPG keyframe → mime `image/jpeg`, aspect 9:16, `duration_seconds`∈{4,6,8}, workers≤3, soften-retry on safety filter). Veo emits native audio → strip with `-an` at assembly. |
| Runway **Seedance 2.5** (internal API; преемник 2.0) | Официальный прайс: **20 / 30 / 68 кредитов за секунду** (480p / 720p / 1080p) → 5 с 720p = **150 кредитов** (1000 cr ≈ 6 клипов). Входное видео добавляет половину ставки за каждую секунду входа | Use sparingly — жжёт кредиты быстро. Замер 06.2026 давал ~180 cr за тот же 5-секундный 720p клип и относился к **2.0**; расхождение с прайсом не разобрано, планировать бюджет по прайсу, сверять по факту. Снята ли 2.0 — Runway нигде не сказал, только что «2.5 — преемник». |
| Runway **Gen-4** | ~62 cr / 5s | Cheaper Runway option if you must stay on Runway credits (было «3× дешевле Seedance» — по новому прайсу 720p разрыв ≈2,4×). |
| Runway **explore mode** (`exploreMode:True`) | «Free on Unlimited» — но только пока Unlimited живой | **Сомнение из этой строки подтвердилось, и хуже, чем было записано.** Здесь стояло «THROTTLED to 0% for free users», то есть медленно, но работает. На деле 22.06.2026 подписка свалилась на free plan, и Runway отказывал **и в explore, и в stable** — не троттлинг, а отказ. На 09.09.2026 сверх этого `RUNWAY_JWT` просрочен с 31.07 (40 дней), любой вызов = 401. Не закладывать в пайплайн вообще. |
| **Ken Burns still** (ffmpeg zoompan) | Free | Last resort; reads as a slideshow in a music video — NOT a substitute for real i2v. |

`gpuCredits` empties silently → fast-mode create returns `400 {"error":"You do not have enough credits"}`. Check `/runway/v1/profile` `gpuCredits` before a batch.

**Порядок проверки Runway перед любым батчем (09.09.2026)** — три ступени, именно в этом порядке:
1. **План** в `/v1/profile`. Не кредиты, а план: на free Runway отказывает и в explore, и в stable, сколько бы кредитов ни лежало.
2. **Токен**: `runway_client.py token-status` — offline-проверка срока `RUNWAY_JWT`. Сейчас просрочен с 31.07.2026, всё отдаёт 401. Автообновления нет нигде — только руками, `localStorage` → `RW_USER_TOKEN` на app.runwayml.com.
3. **Кредиты** `gpuCredits` — уже после первых двух.

Обновить один токен может не помочь: если план не платный, свежий токен упрётся в тот же отказ. Версия Seedance определяется автоматически через `/v1/profile/features`.

## LIPSYNC (audio→lips) — every hosted route has a wall

| Route | Wall |
|---|---|
| **Replicate** (`bytedance/latentsync`) | `429 ... until you add a payment method` — free tier blocked entirely. Needs a card on the Replicate account. |
| **Runway** | Only **Act-Two** = *driving-VIDEO* performance capture, NOT clean audio→lips. Apps grid is flaky to automate. |
| **HF Space `fffiloni/LatentSync`** | **WORKS free** via `gradio_client`: `Client("fffiloni/LatentSync").predict(input_video_path=handle_file(v), input_audio_path=handle_file(a), api_name="/generate_lip_sync_video")`. Token via `HF_TOKEN` **env** (gradio_client 2.5.0 `Client()` does NOT take `hf_token=`). BUT **ZeroGPU free quota ≈5 min/day** → ~1 shot/day. |
| **HeyGen / D-ID** | wallet $0 (per memory). |
| Local Wav2Lip/LatentSync on your GPU | Free but needs GPU env + checkpoint download (this py-env is CPU torch). |

LatentSync accepts ANY face video — including a **Ken Burns of a still keyframe** (no i2v needed for the lipsync base). Output keeps input resolution.

## MUSIC-VIDEO ASSEMBLY (Higgsfield-style)
- **Beat-snap cuts:** librosa `beat_track` → snap each shot boundary to nearest beat. Hard cuts (NO xfade — references use hard cuts).
- **Kodak LUT:** `luts/_sanitized_Kodak2383_D55.cube`. Windows fix: run ffmpeg **from the LUT dir** with bare filename (`lut3d=name.cube`) — the drive colon `C:` breaks the filter parser.
- **White flash on the drop:** `eq=brightness=0.85:enable='between(t,DROP,DROP+0.10)'` (cheap, reliable).
- **Grain:** `noise=alls=4` (STATIC). NEVER `noise=...:allf=t` (temporal) — it defeats inter-frame compression and bloats the file **5-10×** (426 MB vs 74 MB for the same 60s).
- Title card via burned ASS; run subtitles filter from the .ass dir with bare filename (same colon fix).

## Keyframe gotcha
Nano Banana Pro occasionally **rotates a shot 90°** (subject on its side) despite a vertical container. QA every keyframe for orientation; swap to the other variant or regen.
