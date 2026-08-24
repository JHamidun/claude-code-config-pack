# Локальная voice-студия vs ElevenLabs — оценка (Voicebox)

> Источник: `jamiepine/voicebox` (MIT) — open-source локальная voice-студия «clone, dictate, create», позиционируется как локальная замена ElevenLabs + WisprFlow. Оценка внесена 2026-07-20. **ElevenLabs остаётся каноном для флагманской озвучки.** Это — путь экономии кредитов на массовой/черновой RU-озвучке.

## Вердикт: ДОПОЛНИТЬ (augment), не мигрировать

- **Флагман (клонированный голос, буктрейлеры, продающие шортсы)** → остаётся **ElevenLabs** (свой клон из `$ELEVENLABS_VOICE_ID_RU`, точные settings в SKILL.md). Когда клон обучен, тембр отлажен, а задержка и надёжность API известны — менять движок незачем.
- **Массовая/черновая RU-озвучка, драфты, длинные аудиокниги, dictation, локальный STT** → кандидат на **локальный движок на своей видеокарте** — без расхода кредитов ElevenLabs.
- НЕ ставить вслепую: это **heavy-job** (тяжёлая установка: multi-GB веса + Bun/Rust/Tauri toolchain) — ведите учёт таких задач в своём реестре тяжёлых работ. Ставить осознанно, когда реально упрётесь в кредиты ElevenLabs или понадобится офлайн/приватная озвучка.

## Что это и главный вопрос — RU-качество (закрыт положительно)

7 TTS-движков, zero-shot клонирование (10 сек рефа), эффекты (Pedalboard/Spotify), STT (Whisper), встроенный MCP-сервер. Бэкенд FastAPI (Python), десктоп — Tauri (Rust). Лицензия MIT (коммерческое использование ок).

**Russian:** родного упоминания RU в 23-язычном списке Chatterbox в README нет, но по факту:
- **Chatterbox Multilingual (0.5B, Resemble AI)** — 23 языка, **Russian включён** out-of-the-box, клон из 10 сек рефа.
- **Qwen3-TTS (0.6B/1.7B, Alibaba)** — 10 языков, **Russian явно поддержан**; по их техотчёту lowest WER в 6 языках включая RU и speaker-similarity выше ElevenLabs (вендорский бенч — проверять ушами, но многообещающе).
- Kokoro (82M), LuxTTS (EN-only), TADA (HumeAI 1B/3B) — RU слабо/нет; для RU целимся в **Qwen3-TTS 1.7B** и **Chatterbox Multilingual**.

Оба ключевых для RU движка влезают в GPU с 16 GB VRAM с запасом (0.5–3B).

## Сравнение

| Критерий | ElevenLabs (текущее) | Voicebox (локальный) |
|---|---|---|
| Стоимость | $/кредиты (Pro $99 / 500K симв.) | **0** после установки (свой GPU) |
| RU-качество флагман | эталон, production-клон отлажен | хорошо (Qwen3/Chatterbox), но клон надо переобучать/тюнить |
| Задержка | 75 ms (Flash) — API | локально, зависит от GPU; batch без сети |
| Приватность/офлайн | облако | **полностью локально** (чувствительные тексты, офлайн) |
| Клонирование | 1 мин аудио, стабильно | zero-shot 10 сек, но качество/консистентность ниже эталона |
| Sound effects / music | есть (`text_to_sound_effects`, `music.compose`) | **нет** (только TTS/STT) — за SFX/музыкой всё равно ElevenLabs |
| Speech-to-speech voice-changer | есть | нет |
| Интеграция | Python SDK (готовые сниппеты) | MCP `http://127.0.0.1:17493/mcp` (нужен запущенный app) ИЛИ движки напрямую |
| Надёжность в пайплайнах | проверено в проде | новое, GUI-first, headless-путь требует настройки |

## Рекомендация по интеграции (когда решим ставить)

1. **Для headless/batch-озвучки** чище не тащить весь Tauri-app Voicebox, а поднять **standalone Chatterbox-TTS-Server** (`devnen/Chatterbox-TTS-Server`) — OpenAI-совместимый TTS-эндпоинт + voice cloning + audiobook-обработка, CUDA. Дёргается из Python как обычный OpenAI TTS. Это ближе к паттерну локального гейтвея (0 токенов).
2. **Voicebox целиком** — если нужен GUI-студия + dictation (global hotkey) + встроенный MCP (`voicebox.speak/transcribe/list_captures/list_profiles`) в Claude Code/Cursor. Требует запущенного приложения.
3. RU-озвучку валидировать A/B: 5-10 фраз идентичного текста через Qwen3-TTS 1.7B vs Chatterbox Multilingual vs текущий ElevenLabs-клон — выбрать по тембру/просодии ушами, как обычно делается voice-selection в ElevenLabs.

## Установка — HEAVY (тяжёлая, НЕ запускать вслепую)

Prereqs: Bun, Rust, Python 3.11+, Tauri prereqs. Веса моделей качаются с HuggingFace (несколько GB на движок; без прокси, из вашего региона ок, платный ключ не нужен).

```bash
# Клон в temp-clones (не в конфиг)
git clone --depth 1 https://github.com/jamiepine/voicebox.git ./work/voicebox
cd ./work/voicebox
just setup   # создаёт Python venv, тянет зависимости
just dev     # backend (FastAPI) + Tauri app; первый прогон движка докачивает веса
# MCP-эндпоинт после старта: http://127.0.0.1:17493/mcp  (http/stdio)
```
Windows: NVIDIA → PyTorch CUDA бинарь скачивается автоматически (при наличии NVIDIA GPU). Есть готовый MSI-инсталлятор — но веса движков всё равно тянутся при первом использовании.

Альтернатива headless (рекомендуемая для пайплайнов): поднять `devnen/Chatterbox-TTS-Server` в Docker с CUDA, дёргать OpenAI-совместимый `/v1/audio/speech`.

## Что НЕ покрывает (за этим — только ElevenLabs)

- Sound effects (`client.text_to_sound_effects.convert`)
- Music generation (`client.music.compose`)
- Speech-to-speech voice changer
- Отлаженный production-клон голоса с известными settings

## Ссылки

- Voicebox: https://github.com/jamiepine/voicebox
- Chatterbox (Resemble AI): https://github.com/resemble-ai/chatterbox · headless-сервер: https://github.com/devnen/Chatterbox-TTS-Server
- Qwen3-TTS (Alibaba): https://github.com/QwenLM/Qwen3-TTS
