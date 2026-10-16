# Происхождение материалов в assets/ и themes/

Коротко: то, что рисует сертификат (шрифты, значки инструментов), — чужое и открытое,
с лицензиями ниже. То, что называет вас (логотип, подпись, бренд-строка), — заглушки.

| Что | Откуда | Лицензия |
|---|---|---|
| `fonts/` — Inter, Manrope, Oswald, JetBrains Mono | Google Fonts, файлы woff2 (субсеты latin и cyrillic), без изменений | SIL Open Font License 1.1 — https://openfontlicense.org. Условие лицензии: при раздаче шрифтов вместе с навыком прикладывать её текст; ссылка выше ведёт на него |
| `ai_logos/*.svg` — 12 знаков инструментов (Claude, OpenAI, Cursor, Gemini, DeepSeek, Perplexity, GitHub, Docker, n8n, Hugging Face, Telegram, ElevenLabs) | Simple Icons, https://simpleicons.org | данные иконок — CC0 1.0; сами знаки — товарные знаки своих владельцев |
| значки OpenAI и Claude в `themes/company.py` (контуры 16×16) | набор иконок codicons (VS Code), Microsoft | иконки — CC BY 4.0, © Microsoft Corporation, https://github.com/microsoft/vscode-codicons |
| остальные медальоны `themes/company.py` (парусник, шестиугольник, искра) | нарисованы для этого навыка | как и весь навык |
| `brand/company_wordmark.svg`, `company_mark.svg`, `vibe_mark.svg` | заглушки, созданные для пакета | свободно использовать и заменять |
| `signature.png` | условный росчерк, сгенерированный кодом; не чья-то подпись | свободно использовать и заменять |

Знаки инструментов стоят в декоре как иллюстрация «чему учили на программе», а не как
утверждение о партнёрстве или одобрении. Если выдаёте сертификаты от лица организации,
убедитесь, что такое использование знаков допустимо в вашем случае, или уберите
лишние значки из `AI_SPOTS` (`themes/vibe.py`) и `MEDALS` (`themes/company.py`).

Заглушки перед выпуском заменить своими: логотип — SVG в `assets/brand/` и поле
`logos` в конфиге; подпись — PNG с прозрачным фоном и поле `signer.image`.
