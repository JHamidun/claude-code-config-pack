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
12. НЕ используй НЕ ТУ модель для генерации изображений (сама генерация — ОПЦИОНАЛЬНАЯ фича, нужен свой ключ `GOOGLE_API_KEY` или `OPENAI_API_KEY`; без ключа — см. п.11). Лестница из трёх ступеней, выбор — по цене ошибки, а не по вендору:
    - 🥉 **дёшево и дефолт** — `gemini-3.1-flash-image-preview` / `gemini-3.1-flash-image` (Nano Banana 2 Flash)
      - ещё дешевле: `gemini-3.1-flash-lite-image` (NB2 **Lite**, ×2; хорош для потоковых новостных обложек)
    - 🥈 **подороже** — `gemini-3-pro-image-preview` / `nano-banana-pro-preview` (Nano Banana Pro)
    - 🥇 **лучшее** — `gpt-image-2.5-sunburst` (быстрее и по той же цене: `gpt-image-2.5-flare`).
      Только здесь есть `input_fidelity` (одна личность на всей пачке), до 16 референсов и прозрачный фон
    - НЕ `gemini-2.0-flash-exp-image-generation`, НЕ `gemini-2.0-flash-exp`, НЕ `gemini-2.0-flash`
    - НЕ `gemini-2.5-flash-image` (Nano Banana 1 — устарела, есть NB2)
    - НЕ `dall-e-2` / `dall-e-3` — сняты OpenAI 12.05.2026, вызов вернёт ошибку
    - КЛЮЧИ: Gemini — `GOOGLE_API_KEY` (не GEMINI_API_KEY, конфликт SDK); OpenAI — `OPENAI_API_KEY`
    - Перед вызовом Gemini **вызывай** `os.environ.pop('GEMINI_API_KEY', None)` — снять конфликтующую переменную
    - SDK Gemini: `from google import genai` + `types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])`
