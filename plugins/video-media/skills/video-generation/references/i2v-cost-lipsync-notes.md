# i2v cost & lipsync — battle-notes (2026-06-08, музыкальное видео)

Hard-won findings from building a 60s music video. Read before choosing an i2v / lipsync route.

## i2v MOTION — choose by cost, not habit

| Route | Cost | Verdict |
|---|---|---|
| **Veo 3.1 Fast via Google API** (`veo-3.1-fast-generate-preview`, `GOOGLE_API_KEY`) | Google budget, ~44-54s/6s-clip | **DEFAULT for i2v motion.** Not Runway credits. Script pattern: `_tribute_project_2/scripts/veo_animate.py` (JPG keyframe → mime `image/jpeg`, aspect 9:16, `duration_seconds`∈{4,6,8}, workers≤3, soften-retry on safety filter). Veo emits native audio → strip with `-an` at assembly. |
| Runway **Seedance 2.0** (internal API) | **~180 credits / 5s 720p clip** — EXPENSIVE (1000 cr = only 5 clips) | Use sparingly. Quality good but burns credits fast. |
| Runway **Gen-4** | ~62 cr / 5s (3× cheaper than Seedance) | Cheaper Runway option if you must stay on Runway credits. |
| Runway **explore mode** (`exploreMode:True`, free on Unlimited) | Free | **THROTTLED to 0% for free users** — sits in queue, unreliable for batches. Don't depend on it. |
| **Ken Burns still** (ffmpeg zoompan) | Free | Last resort; reads as a slideshow in a music video — NOT a substitute for real i2v. |

`gpuCredits` empties silently → fast-mode create returns `400 {"error":"You do not have enough credits"}`. Check `/runway/v1/profile` `gpuCredits` before a batch.

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
