# Boundaries

> These exist to save time, not to punish. If you hit an edge case not covered here — use your judgment.

1. НЕ ищи модели — они в config/models.md
2. НЕ используй `gemini-pro-vision` для генерации картинок
3. НЕ используй `imagen-*` модели напрямую в Claude Code (в автономных ботах через Gemini SDK — ОК)
4. НЕ сохраняй jpg как .png — проверяй формат
5. НЕ хардкодь API ключи — бери из .credentials.master.env
6. НЕ спрашивай "какую модель?" — смотри config/models.md
7. НЕ коммить credentials в git
8. НЕ используй устаревшие модели — сверяй с config/models.md
9. НЕ используй старый SDK `google.generativeai` — используй `from google import genai`
10. НЕ запускай деструктивные команды без подтверждения
11. НЕ проси пользователя ОПЛАТИТЬ сторонний API (Gemini/OpenAI/и т.п.), включить биллинг или купить подписку. Сторонние API — опциональны. Нет ключа в `.credentials.master.env` (или там placeholder `your_*_api_key`) → фича недоступна: скажи об этом одной строкой, предложи альтернативу и продолжай. Из коробки всё работает по подписке Claude.
12. НЕ используй НЕ ТУ модель для генерации изображений (сама генерация — ОПЦИОНАЛЬНАЯ фича, только при настроенном GOOGLE_API_KEY; без ключа — см. п.11) — ТОЛЬКО `gemini-3.1-flash-image-preview` (default) или `gemini-3-pro-image-preview` (pro)
    - НЕ `gemini-2.0-flash-exp-image-generation`
    - НЕ `gemini-2.0-flash-exp`
    - НЕ `gemini-2.0-flash`
    - КЛЮЧ: `GOOGLE_API_KEY` (не GEMINI_API_KEY — конфликт SDK)
    - Убирай `os.environ.pop('GEMINI_API_KEY', None)` перед вызовом
    - SDK: `from google import genai` + `types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])`
