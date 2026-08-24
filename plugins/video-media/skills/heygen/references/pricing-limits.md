# HeyGen — цены и лимиты (self-serve, 2026)

Открывай, когда считаешь бюджет партии видео или упёрся в отказ по размеру
файла, длине скрипта, числу параллельных задач.

## Pricing (USD per second)

### Avatar IV & V (same rates since 2026-05-12)
| Avatar Type | 720p/1080p | 4K |
|---|---|---|
| Photo Avatar | $0.05/s | $0.0667/s |
| **Digital Twin** | **$0.0667/s** | $0.0833/s |
| Studio Avatar | $0.0667/s | $0.0833/s |

**Digital twin → $2.00 за 30-секундный short (1080p), $200 за 100 шортсов.**
Avatar V больше не дороже IV.

### Other
| Feature | Rate |
|---|---|
| Video Agent (prompt-to-video) | $0.0333/s (~половина прямого Digital Twin) |
| **Cinematic Avatar** | **$7.00 flat per video** (4–15 s) |
| HyperFrames 4K | resolution 4k billed **1.5×** vs 1080p |
| Lipsync — speed / precision | $0.0333 / $0.0667 per s |
| Translation — audio-only / lipsync speed / precision | $0.0167 / $0.0333 / $0.0667 per s |
| TTS Starfish | $0.000667/s — самый дешёвый вызов в API, удобен для коротких хуков и интро |
| Avatar creation (digital twin / photo) | $1.00 per call |
| Avatar III legacy (existing v1/v2 only) | $0.0167/s (720p/1080p), $0.02/s (4K) |

## Usage limits

| Resource | Limit |
|---|---|
| Concurrent video jobs | 10 (Pay-As-You-Go) → 429 + `Retry-After` |
| Script text | 5000 chars |
| Cinematic prompt / Video Agent prompt | 10,000 chars |
| Cinematic refs | ≤3 videos + ≤9 images (avatars+refs combined); 1–3 avatar looks |
| Cinematic duration | 4–15 s |
| Audio input | 600 s (10 min) |
| Multipart asset upload | 32 MB (use direct-uploads for larger) |
| Video input (lipsync/translate) | 100 MB, <2K, MP4/WebM |
| Image input | 50 MB, <2K, JPG/PNG |
| Audio input file | 50 MB, WAV/MP3 |
| Video Agent attachments | ≤20 (image/video/audio/PDF) |
| Output (avatar videos) | 25 fps, 128–4096 px/axis, ≤50 scenes, ≤30 min |
| Aspect ratio (avatar/image) | 16:9, 9:16, 4:5, 5:4, 1:1, auto (default 16:9) |
| Aspect ratio (cinematic/hyperframes) | 16:9, 9:16, 1:1 |
| TTS | 1–5000 chars, speed 0.5–2.0× |
