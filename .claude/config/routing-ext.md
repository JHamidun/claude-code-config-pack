# Routing — полная справочная карта (читается ПО ТРЕБОВАНИЮ, не в авто-load)

Короткий рабочий роутер — rules/routing.md. Здесь — ПОЛНЫЙ список всех триггеров→инструментов. Когда в rules/routing.md указатель на семью — детали ищи здесь.

| Категория | Триггеры | Инструмент |
|-----------|----------|------------|
| Сохранить в память (база знаний) | "запомни эту инструкцию", "сохрани в память", "чтобы не забыл", "добавь в постоянную память", "запомни мои X", "сохрани знание о", "save knowledge base", "сделай чтобы при запросе X выдавал" | Skill `save-knowledge-base` — 4 уровня (memory topic + MEMORY.md + routing.md + vector_memory) |
| Семантическая память (Second Brain) | "brain search", "семантический поиск по памяти", "поиск по мозгу" | MCP-сервера `second-brain` в паке НЕТ. Ближайшее из коробки: Skill `graph-memory` (MCP `graph-memory` + `scripts/memory_graph.py`) и `tools/vector_memory.py`. Свой семантический слой — разворачивай отдельно и подключай как MCP |
| Консолидация памяти | "dream brain", "консолидация памяти", "сон мозга" | Skill `dream` |
|-----------|----------|------------|
| Дизайн-системы известных продуктов | "в стиле Stripe/Linear/Vercel", "72 дизайн-системы", "эстетика Notion" | Skill `design-md-brands` (банк DESIGN.md брендов) + Skill `design-orchestrator`. Отдельный локальный дизайн-тул (`open-design`) в пак НЕ входит: это была шпаргалка к одной установке на диске, без неё оставался пересказ README |
| Музыка/аудио | "сгенерируй музыку", "сделай трек", "music generation", "ace-step", "напиши песню", "soundtrack", "jingle", "background music", "сгенерируй аудио" | Skill `ace-step`, CLI: `cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py` |
| Тендеры/закупки | "тендеры", "госзакупки", "закупки", "найди контракты", "подходящие контракты", "zakupki", "rostender", "тендерные закупки", "ОКПД2" | Skill `tender-search-ru` (Playwright + rostender; обход гео-блока zakupki) |
| Реставрация фото | "реставрируй фото", "улучши старую фотку", "восстанови фото", "photo restoration", "шакальная фотка", "улучши качество фото" | Skill `nano-banana-pro` (раздел Photo Restoration) |
| Видео аватар | "видео с аватаром", "аватар" | Skill `heygen` |
| Видеомонтаж | "склей видео", "монтаж", "concat videos", "склейка", "видеоредактор", "наложи музыку на видео" | Skill `video-editor`, CLI: `python ~/.claude/skills/video-editor/video_editor.py` |
| Pro монтаж (toolkit) | "профессиональный монтаж", "смонтируй ролик", "докрути монтаж", "как у блогеров", "крутой монтаж" | Skill `video-editor` → `skills/video-editor/references/montage-toolkit.md` (индекс скриптов + правила ремесла) |
| Вырезать паузы/тишину | "вырежи паузы", "убери тишину", "jump cut", "auto-editor", "убери эээ", "плотный монтаж" | `python ~/.claude/skills/video-editor/scripts/silence_cut.py in.mp4 out.mp4` |
| Beat-sync нарезка | "под биты", "beat sync", "нарежь под музыку", "клип под трек", "ритмичный монтаж" | `python ~/.claude/skills/video-editor/scripts/beat_sync_edit.py music.mp3 c1.mp4 c2.mp4 -o out.mp4` |
| Виральные субтитры | "виральные субтитры", "субтитры на видео", "капкат субтитры", "word highlight", "хормози субтитры", "караоке субтитры" | `python ~/.claude/skills/video-editor/scripts/karaoke_captions.py in.mp4 out.mp4 --lang ru --style hormozi` |
| Переходы видео | "переходы", "transition", "flash переход", "glitch", "whip pan", "красивый переход между" | `python ~/.claude/skills/video-editor/scripts/transitions.py a.mp4 b.mp4 -o out.mp4 --effect flash` |
| Цветокор/LUT | "цветокор", "LUT", "плёночный лук", "teal orange", "кинолук", "color grade", "Kodak 2383" | `python ~/.claude/skills/video-editor/scripts/color_grade.py in.mp4 out.mp4 --lut kodak2383` → `video-generation/references/color-grading.md` |
| Авто-рефрейм 9:16 | "сделай вертикалку", "16:9 в 9:16", "auto reframe", "перекадрируй под reels/shorts", "вертикальное из горизонтального" | `python ~/.claude/skills/video-editor/scripts/reframe_9x16.py in.mp4 out.mp4 --method yolo` |
| Speed ramps | "слоумо", "ускорь видео", "slow motion", "speed ramp", "замедли момент", "ускорь скучное" | `python ~/.claude/skills/video-editor/scripts/speed_ramp.py in.mp4 out.mp4 --ramp "0:3:0.25,3:12:1.0"` |
| Sound design | "звуковые эффекты", "whoosh", "sfx", "freesound", "подложи звук под переход", "приглуши музыку под голос" | `python ~/.claude/skills/video-editor/scripts/sfx.py search whoosh` / `place` / `duck` |
| Соц-UI оверлеи | "соц-UI оверлей", "instagram оверлей на видео", "telegram баблы", "фейк лента", "как в том рилсе", "kinetic UI", "motion graphics на видео" | Skill `video-generation` → `skills/video-generation/references/remotion-overlays.md` + `skills/video-generation/scripts/motion_graphics.py` |
| VOID (удаление объектов) | "удали объект из видео", "remove object from video", "VOID", "video inpainting", "убери из видео", "video object removal" | Skill `void-video`, CLI: `python ~/.claude/skills/void-video/void_remove.py` |
| Видео фабрика | "полный ролик", "video factory", "ролик под ключ", "сделай видео и выложи", "запиши и выложи" | Agent `video-factory` |
| Озвучка | "озвучь", "голос", "TTS" | Skill `elevenlabs` |
| Субтитры | "субтитры" | Skill `submagic` |
| Транскрипция | "транскрибируй", "распознай речь" | Command `transcribe` (обёртка), Skill `deepgram` (reference) |
| База знаний | "найди в встречах", "kb", "knowledge base", "в истории" | Command `kb` |
| Перевод | "переведи", "translate" | Command `translate` (обёртка), Skill `deepl-pro` (reference) |
| Figma design | "сверстай из фигмы", "implement design" | Plugin `figma:implement-design` |
| Figma connect | "code connect", "компоненты фигмы" | Plugin `figma:code-connect-components` |
| Баги | "найди баги", "ошибки" | Agent `bug-hunter` → `bug-fixer` |
| Безопасность | "security", "уязвимости" | Agent `security-scanner` |
| Тесты | "напиши тесты" | Agent `test-writer` |
| Деплой | "задеплой", "deploy" | Command `deploy` |
| Last 30 Days | "last30", "за последние 30 дней", "что обсуждают", "тренды соцсетей", "social media research", "what's trending" | Skill `last30days` |
| Social Intel | "досье на", "найди соцсети", "обогати контакт", "due diligence", "KYC check", "кто этот человек", "social profile" | Skill `social-intel` |
| Ad Spy | "реклама конкурентов", "ad spy", "ad library", "что рекламируют", "креативы конкурентов", "мониторинг рекламы" | Skill `ad-spy` |
| TikTok Intel | "тикток тренды", "инфлюенсеры", "TikTok Shop", "популярные рилсы", "тикток аналитика", "trending TikTok" | Skill `tiktok-intel` |
| Obsidian | "obsidian", "vault", "заметки obsidian" | Obsidian MCP (WebSocket :OBSIDIAN_PORT, NOT CONFIGURED — порт не активен) |
| GSD | "gsd", "get shit done", "новый проект GSD", "фазы разработки" | `/gsd:new-project`, `/gsd:next`, `/gsd:autonomous` |
| Исследование | "research", "найди информацию" | Command `deep-research` |
| Research Docs | "research docs", "Q&A по документам", "отчёт по PDF с цитатами", "проанализируй папку документов", "answer from documents", "visual citations", "deep research folder", "liteparse" | Skill `research-docs` (`/research-docs ./folder Question`) |
| Google Docs | "документ", "gdoc" | Command `gdocs` |
| Google Sheets | "таблица", "gsheet" | Command `gsheets` |
| Gmail | "письмо", "email" | Command `gmail` |
| Google Contacts | "контакты google", "gcontacts" | Command `gcontacts` |
| Google Tasks | "задачи google", "gtasks" | Command `gtasks` |
| Google Meet | "meet", "видеозвонок google" | Command `gmeet` |
| Zoom | "zoom", "зум", "zoom meeting", "создай встречу zoom", "запланируй зум", "zoom recording", "записи зум" | Skill `zoom` |
| Google Chat | "google chat", "gchat" | Command `gchat` |
| Google Analytics | "GA4", "google analytics", "ganalytics" | Command `ganalytics` |
| Google Ads | "google ads", "реклама google", "gads" | Command `gads` |
| Search Console | "search console", "GSC", "gsearch" | Command `gsearch-console` |
| Cloud Translation | "переведи через google", "gtranslate" | Command `gtranslate` |
| Cloud Storage | "GCS", "бакеты", "gcloud storage" | Command `gcloud-storage` |
| Telegram бот (разработка) | "бот", "telegram бот", "напиши бота", "handlers", "scenes", "deploy бота" | Skill `telegram-bot-toolkit` |
| Публикация через бота (Bot API) | "опубликуй через бота", "пост в канал от бота", "бот-админ канала", "кнопка к посту в канале", "rich-пост с таблицей", "таблица/заголовок в тг-посте", "рассылка подписчикам бота", "отправь подписчику в личку", "опрос от бота", "платный пост Stars", "инвайт-ссылка бот", "почему updates молчит", "вебхук бота", "tg_bot.py" | Skill `tg-bot-publish`, CLI: `python ~/.claude/tools/tg_bot.py` (+ TG_BOT_API_REFERENCE.md) |
| MAX мессенджер | "чат в максе", "max chat", "канал в максе", "напиши в макс", "поиск в максе", "экспортируй чат макс" | Неофициальный клиент MAX в пак НЕ входит (нужен свой `max_client.py` поверх их web-API). Ближайшие поставляемые аналоги: Skill `telegram-bot-toolkit`, Skill `tg-bot-publish`, Skill `sms-twilio` |
| N8N | "автоматизация", "workflow" | Skill `n8n` |
| CEO Council | "совет директоров", "ceo council", "стратегическое решение", "параллельные эксперты", "мнения экспертов" | Skill `ceo-council` |
| Investor Materials | "питч-дек", "investor", "one-pager", "финмодель", "инвестор", "фандрейзинг", "pitch deck" | Skill `investor-materials` |
| Content Engine | "контент-конвейер", "content engine", "контент для соцсетей", "контент-план" | Skill `content-engine` |
| CRO страниц | "CRO", "конверсия страницы", "лендинг не конвертит", "увеличить конверсию", "почему не покупают" | Skill `page-cro-ru` |
| CRO онбординга | "активация", "онбординг", "aha-момент", "time-to-value", "первый запуск" | Skill `onboarding-cro-ru` |
| CRO пейволла | "пейволл", "paywall", "free→платный", "апгрейд тарифа", "конверсия в подписку" | Skill `paywall-cro-ru` |
| CRO попапов | "попап", "popup", "exit-intent", "лид-магнит баннер", "модалка захвата" | Skill `popup-cro-ru` |
| CRO форм захвата | "форма заявки", "заявка на консультацию", "конверсия формы", "трение формы", "конверсия регистрации", "воронка регистрации", "trial signup", "захват email", "подписка на новости" | Skill `form-cro-ru` |
| Удержание/отток | "отток", "churn", "удержание", "cancel-флоу", "save-оффер", "dunning", "вернуть подписчиков" | Skill `churn-prevention-ru` |
| Ценообразование | "ценообразование", "тарифы", "pricing", "упаковка", "value metric", "повышение цен", "freemium" | Skill `pricing-strategy-ru` |
| Холодный аутрич | "холодное письмо", "cold email", "аутрич", "цепочка касаний", "написать ЛПР", "продать воркшоп/консалтинг" | Skill `draft-outreach` |
| Поиск лидов B2B | "поиск компаний", "prospecting", "список лидов", "ICP-компании", "квалификация лидов" | Skill `lead-research` |
| Дообогащение/квалификация лидов | "дообогати базу", "обогати список/лиды/контакты", "обогати для обзвона", "квалифицируй контакт", "кто оставил заявку", "пробей по цифровому следу", "кто этот человек по email/телефону", "номер оставил лид кто это", "matched against Bitrix", "checko", "ЕГРЮЛ обогащение", "DaData фирмографика", "enrich leads" | Готовый навык обогащения в пак НЕ входит (был завязан на конкретную CRM и платные RU-источники). Собирается из поставляемых: Skill `account-research` (компания/человек по открытым источникам), Skill `osint-recon` (цифровой след домена), Skill `social-intel` (соцсети), Skill `lead-research` (новый список по ICP). Клиента к ЕГРЮЛ/ФНС/DaData/Checko заводи свой — ключи и лимиты у каждого свои |
| Sales-материалы | "питч-дек продаж", "one-pager", "отработка возражений", "демо-скрипт", "sales enablement" | Skill `sales-enablement-ru` |
| RevOps | "revops", "жизненный цикл лида", "MQL/SQL", "хэндофф маркетинг-продажи", "nurture воронка" | Skill `revops-ru` |
| A/B тесты | "A/B тест", "сплит-тест", "эксперимент", "проверить гипотезу", "статзначимость", "размер выборки" | Skill `ab-testing-ru` |
| Schema-разметка | "schema", "structured data", "JSON-LD", "rich snippets", "FAQ schema", "Course schema", "разметка для Яндекса" | Skill `schema-markup-ru` |
| Маркетинг-петли | "маркетинг-петля", "marketing loop", "растущая петля", "рекуррентный маркетинг", "маркетинг на автопилоте", "weekly marketing review", "еженедельный маркетинг-обзор", "зациклить маркетинг", "цикл для бота", "loop для Bot-Aа/Bot-B", "контент-петля", "churn watch", "ad fatigue цикл", "постоянный мониторинг конкурентов", "сделай чтобы проверялось каждую неделю", "always-on marketing", "flywheel", "маховик" | Skill `marketing-loops-ru` (9-частная анатомия петли, ~20 циклов под воронку пользователя, agent-fleet + ресурс-гард; coreyhaines MIT, RU 2026-07-18) |
| Рефералка/партнёрка | "рефералка", "реферальная программа", "referral", "приведи друга", "партнёрская программа", "партнёрка", "affiliate", "амбассадоры", "сарафанное радио", "word of mouth", "viral loop", "вирусная петля", "промокод другу", "комиссия партнёру", "реферальная ссылка", "клиенты приводят клиентов", "выплаты партнёрам" | Skill `referrals-ru` (ЮKassa промокоды, t.me/bot?start=ref_, партнёрка ТГ-каналов, sizing от LTV, фрод-защита) |
| Лид-магниты/free tools | "лид-магнит", "lead magnet", "бесплатный инструмент", "free tool", "engineering as marketing", "калькулятор для лидов", "ROI-калькулятор", "грейдер", "аудит-тул", "квиз", "квиз-воронка", "чек-лист для скачивания", "шаблон за email", "гайд за подписку", "gated content", "закрытый контент", "что отдать за email", "opt-in", "захват email", "контент-апгрейд", "мини-курс по email", "что раздавать бесплатно" | Skill `free-tools-lead-magnets-ru` (скоркарта тула, гейтинг email/ТГ-бот, бенчмарки; виджет → interactive-prototype) |
| Психология маркетинга | "психология маркетинга", "когнитивные искажения", "persuasion", "ментальные модели", "почему покупают" | Skill `marketing-psychology-ru` |
| Запуск/Go-to-market | "запуск продукта", "launch", "go-to-market", "GTM", "запуск курса/воркшопа", "анонс потока" | Skill `launch-strategy-ru` |
| Build Fix | "build broken", "ошибки сборки", "fix build", "build-fix", "не собирается" | Skill `build-fix` |
| Инсталляторы (Win+Mac) | "сделай инсталлятор", "установщик в один клик", "офлайн-инсталлятор", "exe + dmg", "вшить ПО в один установщик", "накатить софт на чистую машину", "offline installer", "bundle apps installer", "electron installer" | Skill `installer-builder` (Electron portable exe + dmg, офлайн-vendor, паки, GitHub Actions mac-сборка; грабли BOM/stderr/100МБ) |
| Архитектура | "архитектура", "дизайн системы" | Agent `software-architect` |
| Фронтенд | "React", "UI", "компонент" | Agent `frontend-dev` |
| Бэкенд | "API", "endpoint" | Agent `backend-dev` |
| БД | "миграция", "schema", "SQL" | Command `setup-db` |
| CI/CD | "pipeline", "docker" | Agent `devops-engineer` |
| Презентация | "слайды", "презентация", "pitch deck", "whiteboard", "маркерная доска" | Agent `slide-designer`, Skill `manus-slides`, Command `slides` |
| Manus Slides | "manus slides", "html slides", "html презентация" | Skill `manus-slides`, Command `slides` |
| Marp слайды | "marp", "slides from markdown", "слайды из markdown" | Skill `marp-presentations` |
| Рефакторинг | "рефакторинг", "legacy" | Agent `legacy-modernizer` |
| Performance | "оптимизируй", "медленно" | Agent `performance-optimizer` |
| Мёртвый код | "dead code", "unused" | Agent `dead-code-hunter` |
| Дубли кода | "дублирование" | Agent `reuse-hunter` |
| Зависимости | "dependencies", "outdated" | Agent `dependency-auditor` → `dependency-updater` |
| Уязвимости фикс | "исправь уязвимости", "fix vulnerabilities" | Agent `vulnerability-fixer` (после `security-scanner`) |
| Дубли фикс | "консолидируй дубли", "fix duplicates" | Agent `reuse-fixer` (после `reuse-hunter`) |
| Мёртвый код фикс | "удали мёртвый код", "remove dead code" | Agent `dead-code-remover` (после `dead-code-hunter`) |
| Код-ревью | "проверь код", "ревью", "review" | Agent `code-reviewer`, Plugin `pr-review-toolkit` |
| Ошибки/баги | "ошибка", "error", "stack trace", "не работает" | Agent `error-handler` |
| Бизнес-анализ | "бизнес-анализ", "market sizing", "ROI", "stakeholder mapping" | Agent `business-analyst` |
| DevOps | "CI/CD", "docker", "pipeline", "infrastructure" | Agent `devops-engineer` |
| Интеграции | "интеграция", "webhook", "third-party API" | Agent `integration-dev` |
| Kimi алгоритмы | "алгоритм", "data structure", "computational", "kimi" | Agent `kimi-algorithm-specialist` |
| Memory agent | "запомни контекст", "memory agent", "long-term memory" | Agent `memory-agent` |
| ML/AI | "machine learning", "model training", "ML pipeline" | Agent `ml-specialist` |
| Оркестратор | "orchestrate", "координируй агентов", "multi-agent" | Agent `orchestrator` |
| Пентест | "pentest", "penetration test", "exploit" | Agent `pentest-engineer` |
| Презентация мастер | "мастер презентаций", "presentation master", "training program" | Agent `presentation-master` |
| Product дизайн | "UX", "UI дизайн", "wireframe", "user flow", "accessibility" | Agent `product-designer` |
| Промпт инженер | "промпт агент", "optimize prompt agent" | Agent `prompt-engineer` |
| Корректура | "проверь текст", "корректура" | Agent `proofreader-ortho` → `proofreader-punctuation` → `proofreader-typography`, Command `proofread` |
| QA | "QA", "test strategy", "test automation" | Agent `qa-specialist` |
| Security инженер | "security engineer", "secure coding", "compliance" | Agent `security-engineer` |
| Senior dev | "напиши код", "implement feature", "production code" | Agent `senior-developer` |
| Системный аналитик | "feasibility", "data flow", "migration plan" | Agent `system-analyst` |
| Tech lead | "tech lead", "architectural decision", "technical debt" | Agent `tech-lead` |
| GPT agent | "спроси GPT", "ask GPT" | Agent `gpt-agent` |
| Gemini agent | "спроси Gemini", "ask Gemini" | Agent `gemini-agent` |
| Meta agent | "создай агента", "generate agent" | Agent `meta-agent-v3` |
| Accessibility | "accessibility", "WCAG", "screen reader" | Agent `accessibility-tester` |
| Интеграционные тесты | "integration test", "acceptance test", "e2e test" | Agent `integration-tester` |
| Мобильная адаптация | "mobile responsiveness", "мобильная версия" | Agent `mobile-responsiveness-tester` → `mobile-fixes-implementer` |
| Де-аифай | "убери ИИ стиль", "де-аифай", "humanize" | Skill `de-ai-ify` |
| Фреймворки | "фреймворк", "think deeper", "first principles" | Skill `thinking-frameworks` |
| Итоги недели | "итоги недели", "weekly synthesis" | Command `weekly-synthesis` |
| Статистика | "статистика сессий", "prompt log" | Command `prompt-log` |
| Dream (память) | "dream", "консолидируй память", "почисти память" | Skill `dream` |
| Away Summary | "где остановился", "что делал", "recap", "while you were away" | Skill `away-summary` |
| BTW (side question) | "/btw", "кстати", "side question" | Skill `btw` |
| Year/Month Review | "итоги месяца", "итоги года", "work analytics", "year review" | Skill `year-review` |
| Саморефлексия | "проанализируй себя", "self-reflect" | Skill `self-reflect` |
| GitHub доки | "документация репо", "deepwiki" | Skill `deepwiki` |
| План дня | "спланируй день", "plan my day" | Command `plan-my-day` |
| Диаграммы | "диаграмма", "flowchart", "excalidraw" | Skill `excalidraw-flowchart` |
| Мониторинг | "мониторинг", "uptime", "статус-страница" | Навыка-обёртки над Uptime Kuma в паке нет (был написан под конкретный сервер). Поднять свой: Uptime Kuma в docker, дальше Skill `webhook-receiver` для алёртов и Skill `n8n` для сценариев |
| DNS/Домены | "DNS", "домен", "cloudflare" | Command `domain-dns-ops` |
| Reddit/HN | "reddit", "hacker news", "мнения" | Skill `reddit-hn` |
| LinkedIn | "linkedin", "outreach", "контакты" | Skill `linkedin` |
| LinkedIn хук-формулы | "viral hook", "hook formula", "linkedin formulas", "F1-F10", "anaphora hook", "RIP obituary hook", "year-over-year pivot" | Skill `linkedin-post-writer` (10 формул 2026 от Jake Ward, Lara Acosta, Cam Trew, Noam Nisand) |
| LinkedIn humanizer | "убери AI tells", "humanize linkedin", "scrub AI", "oaicite", "knowledge cutoff", "forensic strict aesthetic", "humanizer tier" | Skill `linkedin-humanizer` (3-tier scrubber; объяснение правил = режим rules-explainer, merged 2026-07-18) |
| LinkedIn audit | "audit my linkedin draft", "pre-publish check", "20-point linkedin", "проверь черновик linkedin", "post audit" | Skill `linkedin-humanizer` (режим post-audit, merged; тело в references/linkedin-post-audit) |
| LinkedIn emoji detector | "ai emoji", "lightbulb tell", "rocket sparkles tell", "проверь эмодзи в посте", "ChatGPT emoji" | Skill `linkedin-humanizer` (режим emoji-detector, merged) |
| LinkedIn AI detector тест | "GPTZero", "originality.ai", "zerogpt", "детекторы AI", "false positive linkedin", "разброс детекторов" | Skill `linkedin-humanizer` (режим detector-tester: 5 детекторов параллельно — Stanford 2023 receipts; merged) |
| LinkedIn comment drafter | "коммент на linkedin", "comment on linkedin post", "first commenter", "engage with this post", "linkedin url comment", "draft me a comment" | Skill `linkedin-comment-drafter` (7 паттернов 2026) |
| LinkedIn reply handler | "ответь на коммент в linkedin", "reply to linkedin comment", "thread continuation", "автор ответил", "follow up в треде" | Skill `linkedin-comment-drafter` (режим reply-handler, фикс 2-level flattening; merged) |
| LinkedIn hook extractor | "разбери viral пост", "reverse engineer hook", "какая формула у поста", "teardown linkedin", "blank template из поста" | Skill `linkedin-post-writer` (режим hook-extractor, merged) |
| LinkedIn content planner | "linkedin content plan", "план на неделю linkedin", "weekly linkedin calendar", "Authority Personal Community pillars" | Skill `linkedin-post-writer` (режим content-planner, 40-30-20-10 mix; merged) |
| LinkedIn thread engagement | "follow-up linkedin", "окно ответа автора", "автор реплайнул", "thread monitoring", "inbound from comments", "compounding engagement" | Skill `linkedin-comment-drafter` (режим thread-engagement, 6-24h window; merged) |
| LinkedIn profile audit | "review my profile", "rewrite my headline", "fix my About", "linkedin profile audit", "optimize bio", "Featured section linkedin" | Skill `linkedin-profile-optimizer` (9 секций) |
| LinkedIn employee advocacy | "team posting linkedin", "employee advocacy", "scale linkedin across team", "advocacy ROI", "брендовая адвокатура" | Skill `linkedin-employee-advocacy` (14-day launch + ROI) |
| Design orchestrator | "сделай дизайн", "сделай прототип", "сделай слайды", "лендинг", "макет", "дизайн-задача" | Skill `design-orchestrator` (главный — решает какие design-скиллы запустить) |
| Design guide | "design taste", "иерархия дизайн", "ритм визуала", "дизайн-памятка" | Skill `design-guide` (общий гайд о вкусе) |
| Design content rules | "анти-слоп", "не лей воду в дизайн", "design content rules" | Skill `content-rules` (что НЕ делать в дизайне) |
| Design cookbook | "готовый сценарий дизайна", "pitch deck workflow", "saas landing workflow", "social explainer" | Skill `cookbook` (5 готовых рецептов от запроса к результату) |
| Design critique | "покритикуй мой дизайн", "design critique", "design review" | Skill `critique-mode` (не делать, а критиковать) |
| Design system create | "создай дизайн-систему", "tokens", "design system from scratch" | Skill `design-system-create` |
| Color system | "палитра", "9-step scale", "color tokens", "построй цветовую систему" | Skill `color-system-builder` |
| Dark mode | "добавь dark mode", "тёмная тема к дизайну", "dark theme tokens" | Skill `dark-mode-add` |
| Deck themes | "тема презентации", "minimal/editorial/dark/data/brutalist", "5 готовых тем слайдов" | Skill `deck-themes` (5 готовых CSS тем) |
| Design canvas | "несколько вариантов бок-о-бок", "сравни 3 версии", "артборды в одном файле", "pan/zoom canvas" | Skill `design-canvas` |
| Animations skill | "анимация в HTML", "timeline scrubber", "motion design HTML", "video-стиль" | Skill `animations` (anim-engine.jsx) |
| Lottie анимации | "lottie", "лотти", "bodymovin", "векторная анимация", "анимированная иконка", "лоадер анимация", "json-анимация", "анимация для приложения/сайта", "after effects в json" | Skill `text-to-lottie` (Skia/Skottie плеер, degit-скаффолд, slots+properties panel) |
| Component playground | "storybook страница", "компонент со всеми вариантами", "all states UI" | Skill `component-playground` |
| Comment injector | "click-to-comment overlay", "Alt+click selector", "ревью прототипа в браузере" | Skill `comment-injector` |
| Claude in HTML | "LLM прямо в артефакте", "встрой Claude в HTML", "AI inside prototype" | Skill `claude-in-html` |
| A11y audit | "проверь accessibility", "axe-core", "WCAG нарушения", "контраст AA" | Skill `a11y-audit` |
| Device frames | "iOS frame", "Android рамка", "macOS window", "browser frame для скриншота" | Skill `device-frames` |
| Dev handoff | "пакет для разраба", "design handoff zip", "specs для разработчика" | Skill `dev-handoff` |
| Design questions | "уточни задачу", "вопросы перед дизайном", "что мне нужно знать", "questions protocol" | Skill `questions-protocol` |
| Frontend design preset | "5 пресетов", "editorial monochrome", "soft brutalism", "premium dark", "warm minimalism", "data dense" | Skill `frontend-design` |
| Wireframe | "вайрфрейм", "wireframe", "грубый каркас", "структура без стиля", "lo-fi" | Skill `wireframe` |
| Старт дизайн-проекта | "инициализация дизайн-проекта", "scaffold дизайн", "wizard старта" | Skill `design-orchestrator` (ведёт процесс с нуля) + Skill `questions-protocol` (вопросы до дизайна). Отдельный wizard `project-init` в пак НЕ входит: 7 из 7 функций scaffold были пустыми заглушками |
| Moodboard | "moodboard", "мудборд", "извлеки палитру из картинок", "vibe-tags" | Skill `moodboard` |
| Slides skill | "html слайды", "1920x1080 дек", "slides канва" | Skill `slides` |
| Interactive prototype | "кликабельный прототип", "react babel прототип", "interactive prototype" | Skill `interactive-prototype` |
| Mobile overlays | "iOS клавиатура", "bottom sheet", "action sheet", "toast", "mobile UI overlay" | Skill `mobile-overlays` |
| Tweaks panel | "крутилки в прототипе", "tweaks panel", "live tweaks", "слайдер для primary color" | Skill `tweaks-panel` |
| Microinteractions | "skeleton loader", "hover эффекты", "scroll-reveal", "click ripple", "оживи прототип" | Skill `microinteractions` |
| Type scale | "modular scale", "type ratio", "typography scale", "font pair" | Skill `type-scale` |
| Forms a11y | "доступная форма", "accessible form", "label aria error", "fieldset" | Skill `forms-a11y` |
| States checklist | "8 состояний UI", "empty loading error", "states checklist", "happy path только" | Skill `states-checklist` |
| Onboarding UX | "первый запуск", "tour", "setup wizard", "permissions request", "TTV" | Skill `onboarding-ux` |
| Document import | "из PDF в слайды", "DOCX в лендинг", "PPTX парсинг", "import документа" | Skill `document-import` |
| Github import | "из репо токены", "project context из github", "сохрани конвенции проекта" | Skill `github-import` |
| Verifier | "проверь артефакт", "headless console error", "screenshot verify", "перед export" | Skill `verifier` |
| Perf audit | "lighthouse", "Core Web Vitals", "LCP CLS TBT", "оптимизация перформанс" | Skill `perf-audit` |
| i18n stress | "длинные слова", "RTL тест", "CJK", "стресс-тест локализации", "emoji в строке" | Skill `i18n-stress-test` |
| License check | "лицензии шрифтов", "Helvetica можно", "Getty риск", "OFL Apache MIT" | Skill `license-check` |
| Proto smoketest | "playwright smoke", "E2E прототипа", "happy path тест", "playwright test" | Skill `proto-smoketest` |
| Export PDF | "html в pdf", "сохрани в pdf", "pdf через playwright" | Skill `export-pdf` |
| Export PNG | "html в png", "screenshot для twitter", "1080x1080 для instagram", "социалки cover" | Skill `export-png` |
| Export PPTX | "html в pptx", "powerpoint screenshots", "pptx из html" | Skill `export-pptx` |
| PPTX editable | "редактируемый pptx", "native text-боксы pptx", "pptx с editable text" | Skill `pptx-editable-extractor` |
| Video export | "html в mp4", "анимация в видео", "ffmpeg encode", "GIF из html" | Skill `video-export` |
| Standalone HTML | "один файл html", "embed all assets", "self-contained html", "inline base64" | Skill `standalone-html` |
| Print styles | "@media print", "стили для печати", "page-break", "print css" | Skill `print-styles` |
| Real data | "подключи к API", "real data в прототип", "static JSON для демо", "fake data faker" | Skill `real-data` |
| Live preview | "browser-sync", "live reload", "локальный сервер для дизайна", "auto-reload" | Skill `live-preview` |
| Visual edit | "drag handle в браузере", "visual edit overlay", "alt+click resize" | Skill `visual-edit` |
| Version snapshots | "история версий артефакта", "snapshot перед правкой", "откати к baseline" | Skill `version-snapshots` |
| Tweaks persist | "сохрани tweaks", "запиши обратно в tokens.css", "tweaks в localStorage" | Skill `tweaks-panel` (persist поглощён 2026-07-18, тело в references) |
| Sketch to HTML | "из скетча в html", "whiteboard photo в каркас", "excalidraw в html" | Skill `sketch-to-html` |
| HTML email | "newsletter html", "email html outlook gmail", "MJML", "transactional email" | Skill `html-email` |
| PWA shell | "PWA обёртка", "install prompt", "manifest.json", "service worker offline" | Skill `pwa-shell` |
| Outlook | "outlook", "exchange", "рабочая почта" | Command `outlook` |
| Multi-model | "спроси GPT", "ask GPT", "ask Gemini", "compare models", "cross-model", "consensus", "мульти-модель", "gateway models" | Skill `multi-model-gateway`, Agents: `gpt-agent`, `gemini-agent` |
| AI модели | "replicate", "FLUX", "stable diffusion" | Skill `replicate` |
| Аватар видео | "D-ID", "talking head" | Skill `did` |
| Сервер | "сервер", "server health", "docker ps", "почему упало на сервере" | Навыки эксплуатации флота (`server-health`, `runbook`) в пак НЕ входят — они были написаны под конкретный хост, его контейнеры и порты. Поставляется: Skill `claude-server-auth` (Claude CLI на своём VPS). Свой чек-лист заводи навыком под хост из `~/.ssh/config` — как, см. Skill `skill-creator` |
| Презентация AI | "gamma", "AI презентация" | Skill `gamma` |
| Slack | "slack", "напиши в slack" | Плагина `slack` в паке НЕТ — поставь из official marketplace |
| Linear | "linear", "задачи linear", "issues" | Plugin `linear` (official MCP), также: Command `sprint-planning` |
| AI ревью PR | "greptile", "AI review PR" | Plugin `greptile` |
| Tapestry (документы) | "tapestry", "weave", "свяжи документы", "interlink docs" | Skill `tapestry` (интерлинкинг внешних документов, YouTube, PDF) |
| EPUB | "epub", "ebook", "электронная книга", "kindle" | Skill `epub-tools` |
| Claude CLI | "claude CLI", "без API ключа", "without API key", "claude binary" | Skill `claude-cli-runner`, модуль `~/.claude/tools/claude_cli.py` |
| Claude серверная авторизация | "авторизуй на сервере", "setup-token", "токен подписки", "server auth" | Skill `claude-server-auth` |
| Акции/Финансы | "stock", "акции", "курс", "биржа", "yfinance" | Skill `stock-analysis`, CLI: `python ~/.claude/skills/stock-analysis/scripts/stock_analysis.py` |
| Трафик сайта | "similarweb", "трафик сайта", "посещаемость", "web analytics" | Skill `similarweb-analytics` |
| Meta Ads | "meta ads", "facebook ads", "рекламный кабинет", "breakdown effect" | Skill `meta-ads-analyzer` |
| GitHub поиск | "найди библиотеку", "open source tool", "github gem", "найди репо" | Skill `github-gem-seeker` |
| Создать плагин | "создай плагин", "plugin dev" | Plugin `plugin-dev` |
| PRD/Спецификация | "PRD", "спецификация", "write spec", "напиши спеку" | Command `write-spec`, Skill `feature-spec`, Command `/sprint-planning-pm` (спринт-планирование PM) |
| Роадмап | "роадмап", "roadmap", "приоритизация фич" | Skill `roadmap-management`, Command `roadmap-update` (обновление) / `roadmap` (генерация XLSX/PPTX) |
| Стейкхолдеры | "стейкхолдер", "апдейт для руководства", "stakeholder" | Skill `stakeholder-comms`, Command `stakeholder-update` |
| Продуктовые метрики | "OKR", "north star metric", "продуктовые метрики", "product metrics" | Skill `metrics-tracking`, Command `metrics-review` |
| UX исследования | "user research", "синтез интервью", "юзабилити" | Skill `user-research-synthesis`, Command `synthesize-research` |
| Конкурентный анализ | "конкуренты", "competitive analysis", "конкурентная разведка" | Skill `competitive-analysis` (PM), `competitive-analysis-mktg` (маркетинг), `competitive-intelligence` (sales battlecard); Commands `/competitive-brief` (PM), `/competitive-brief-mktg` (маркетинг) |
| Подготовка к звонку | "подготовься к звонку", "call prep", "предстоящий звонок" | Skill `call-prep` |
| Саммари звонка | "саммари звонка", "итоги встречи", "call summary" | Command `call-summary` |
| Sales прогноз | "прогноз продаж", "forecast", "pipeline" | Command `forecast`, Command `pipeline-review` |
| Sales outreach | "напиши письмо клиенту", "cold email", "outreach" | Skill `draft-outreach` (персонализированный), Skill `linkedin` (bulk LinkedIn) |
| Sales брифинг | "утренний брифинг", "daily briefing", "с чего начать день" | Skill `daily-briefing` (sales), Command `daily` (dev standup) |
| Исследование компании | "расскажи про компанию", "account research", "что за компания" | Skill `account-research` |
| Маркетинг контент | "напиши пост", "блог", "draft content", "копирайт" | Skill `content-creation`, Command `draft-content` |
| Маркетинг кампания | "кампания", "campaign plan", "маркетинговый план" | Skill `campaign-planning`, Command `campaign-plan` |
| Email рассылка | "email sequence", "цепочка писем", "nurture" | Command `email-sequence` |
| SEO | "SEO", "seo audit", "ключевые слова" | Command `seo-audit` |
| Бренд | "бренд", "brand voice", "tone of voice" | Skill `brand-voice`, Command `brand-review` |
| Маркетинг аналитика | "маркетинг отчёт", "performance report", "ROAS", "CPL" | Skill `performance-analytics`, Command `performance-report` |
| Браузер (dev) | "открой в браузере", "dev browser", "browse with cookies" | Skill `dev-browser` (лёгкий, с куками) / Plugin `playwright` (полный) |
| Браузер (gstack) | "gstack browse", "browse fast", "скриншот headless", "быстрый браузер" | `~/.claude/skills/gstack/browse/dist/browse` (~100ms/cmd, daemon auto-start). Бинаря в репозитории нет (`*.exe` в .gitignore) — собрать из исходников: `cd ~/.claude/skills/gstack && bun install && bun run build` |
| Алгоритм-арт | "generative art", "алгоритмическое искусство", "p5.js art" | Skill `algorithmic-art` |
| API документация | "API docs", "swagger", "openapi", "postman collection" | Skill `api-documentation` |
| Apify скрапинг | "apify", "scrape website", "actors" | Skill `apify-scraping` |
| Артефакты | "artifact", "интерактивный HTML", "shadcn artifact" | Skill `web-artifacts-builder` (канон; artifacts-builder merged 2026-07-18) |
| AWS | "aws", "lambda", "CDK", "serverless", "S3" | Skill `aws-skills` |
| Брейнсторм | "brainstorm", "мозговой штурм", "идеи" | Plugin `superpowers:brainstorming` (локальный dir убран 2026-07-18 — коллизия имён) |
| Бренд гайдлайн | "brand guidelines", "стиль Anthropic", "фирменный стиль" | Skill `brand-guidelines` |
| Canvas дизайн | "canvas", "poster", "визуальный дизайн", "постер" | Skill `canvas-design` |
| Changelog | "changelog", "что нового", "release notes" | Skill `changelog-generator` |
| CSV анализ | "CSV", "анализ данных", "Excel анализ", "статистика данных" | Skill `csv-analysis` |
| D3 визуализация | "D3", "chart", "график данных", "data visualization" | Skill `d3-visualization` |
| Дизайн БД | "schema design", "дизайн базы", "нормализация", "индексы" | Skill `database-design` |
| Домены | "придумай домен", "domain name", "доменное имя" | Skill `domain-brainstormer` |
| Конвертер файлов | "конвертируй файл", "convert file", "file format" | Skill `file-converter` |
| Организация файлов | "организуй файлы", "sort files", "разбери папку" | Skill `file-organizer` |
| Gemini Pro | "gemini 3 pro", "gemini API" | Skill `gemini-3-pro` |
| Git workflow | "git workflow", "merge conflict", "git branches" | Skill `git-workflow` |
| Счета/чеки | "invoice", "чеки", "счета", "expense tracking" | Skill `invoice-organizer` |
| Кайдзен | "kaizen", "continuous improvement", "улучшение процессов", "PDCA", "A3 report" | Skill `thinking-frameworks` (режим 7 kaizen, merged 2026-07-18) |
| Лиды | "lead research", "поиск лидов", "qualify leads" | Skill `lead-research` |
| Manus | "manus agent", "autonomous agent", "manus task" | Skill `manus` |
| MCP builder | "создай MCP", "build MCP server", "MCP сервер" | Skill `mcp-builder` |
| MCP usage | "как использовать MCP", "MCP tools", "какой MCP сервер" | Read `config/mcp-servers.md` (skill mcp-usage merged туда 2026-07-18, секция «Советы по выбору») |
| Анализ встреч | "анализ встречи", "meeting analysis", "action items" | Skill `meeting-analyzer` |
| OCR восстановление | "OCR", "распознай скан", "garbled text" | Skill `ocr-restore` |
| PDF обработка | "обработай PDF", "merge PDF", "split PDF", "fill PDF form" | Skill `pdf` |
| PDF генерация | "сгенерируй PDF", "create PDF" | Skill `pdf` (pdf-generation merged 2026-07-18; рецепты в references) |
| Perplexity | "perplexity", "AI search" | Skill `perplexity` |
| Pinecone | "pinecone", "vector database", "embeddings" | Skill `pinecone` |
| Playwright | "playwright test", "e2e test", "browser automation" | Skill `playwright-automation` |
| PPTX | "PowerPoint", "pptx", "слайды pptx" | Skill `pptx` |
| Prompt engineering | "промпт инжиниринг", "оптимизируй промпт", "system prompt" | Skill `prompt-engineering`, Agent `prompt-engineer` |
| Python dev | "python", "django", "fastapi", "flask" | Skill `python-fullstack-dev` |
| JS/TS dev | "javascript", "typescript", "react", "next.js", "node" | Skill `javascript-typescript-dev` |
| Архитектор | "архитектура системы", "system design", "tech stack" | Agent `software-architect` |
| SerpAPI | "serpapi", "google search API" | Skill `serpapi` |
| Slack GIF | "gif для slack", "slack emoji", "animated gif" | Skill `slack-gif-creator` |
| Тема/стиль | "theme", "тема оформления", "стилизация" | Skill `theme-factory` |
| Скачать видео | "скачай видео", "yt-dlp", "download video" | Skill `video-downloader` |
| Тестирование веб | "протестируй сайт", "webapp test", "test UI" | Skill `webapp-testing` |
| Создание сайта | "создай сайт", "лендинг", "landing page", "website" | Skill `website-creation` |
| Word/DOCX | "word", "docx", "документ Word", "tracked changes" | Навык `docx` в пак НЕ входит — его лицензия прямо запрещает передачу третьим лицам. Собрать .docx: `pip install python-docx`, рабочий пример на 300 строк — `skills/seo-machine-ru/scripts/build_report_docx.py` (обложка, нативные стили Word, таблицы). Прочитать/сконвертировать чужой .docx — Skill `file-converter` (markitdown, `pdf_to_docx`, `docx_to_pdf`) |
| XLSX | "xlsx", "spreadsheet", "таблица Excel" | Skill `xlsx` |
| YouTube транскрипт | "транскрипт ютуба", "youtube transcript", "субтитры видео" | Skill `youtube-transcript` |
| Mermaid диаграммы | "mermaid", "mermaid chart", "рендер mermaid" | Cloud MCP `claude_ai_Mermaid_Chart` (validate_and_render_mermaid_diagram) |
| Airtable | "airtable", "база airtable", "таблица airtable" | Cloud MCP `claude_ai_Airtable` (search_bases, list_records, create_records) |
| Canva | "canva", "дизайн canva", "постер canva", "презентация canva" | Cloud MCP `claude_ai_Canva` (generate-design, export-design, edit) |
| Gamma cloud | "gamma", "AI презентация gamma", "gamma slides" | Cloud MCP `claude_ai_Gamma` (generate, get_themes), Skill `gamma` |
| Gmail cloud | "gmail cloud", "письмо gmail", "черновик gmail" | Cloud MCP `claude_ai_Gmail` (search, read, create_draft), Command `gmail` |
| Google Calendar cloud | "google calendar", "календарь google", "встреча google" | Cloud MCP `claude_ai_Google_Calendar` (create/list/update events, find free time) |
| Granola | "granola", "заметки встречи granola", "meeting notes" | Cloud MCP `claude_ai_Granola` (list_meetings, get_transcript) |
| n8n cloud | "n8n cloud", "workflow n8n cloud" | Cloud MCP `claude_ai_n8n` (search/execute/get workflows) |
| Figma cloud | "figma cloud", "figma MCP", "дизайн figma" | Cloud MCP `claude_ai_Figma` (get_design_context, screenshot, generate_diagram) |
| Context7 cloud | "context7 cloud", "docs library" | Cloud MCP `claude_ai_Context7` (resolve-library-id, query-docs) |
| Sentry | "sentry", "ошибки production", "error monitoring" | Плагина `sentry` в паке НЕТ — поставь из official marketplace |
| Semgrep | "semgrep", "static analysis", "SAST" | Плагина `semgrep` в паке НЕТ — поставь из marketplace; из коробки — skill `security-audit` |
| Sourcegraph | "sourcegraph", "поиск по репо", "code search" | Plugin `sourcegraph` (sg-search, sg-file) |
| Firecrawl | "firecrawl", "scrape URL", "crawl site", "extract web" | Plugin `firecrawl` (firecrawl-cli, skill-gen) |
| CodeRabbit | "coderabbit", "AI review PR" | Plugin `coderabbit` (code-review) |
| Adspirer Ads | "google ads agent", "meta ads agent", "keyword research" | Плагина `adspirer-ads-agent` в паке НЕТ — поставь из marketplace; из коробки — skills `google-ads-pro-ru`, `meta-ads-launch-ru` |
| HuggingFace | "huggingface", "train model", "dataset HF", "gradio" | Плагина `huggingface-skills` в паке НЕТ — поставь из official marketplace |
| Notion | "notion", "notion page", "notion database", "notion task" | Plugin `notion` (search, create-page, database-query, tasks) |
| Slack расширенный | "slack digest", "slack announcement", "slack standup" | Плагина `slack` в паке НЕТ — поставь из official marketplace |
| Beads issues | "beads", "issue tracking", "баг-трекер" | Skill `beads`, Command `beads-init` |
| Context Engineering | "context engineering", "контекст инжиниринг" | Skill `context-engineering` |
| Threat Hunting | "threat hunting", "sigma rules", "detection engineering" | Skill `threat-hunting` |
| PPTX skill | "pptx", "PowerPoint", "слайды pptx" | Skill `pptx` |
| Internal Comms | "internal comms", "status report", "leadership update", "incident report" | Skill `internal-comms` |
| Content Research | "content research", "fact-checking", "source verification" | Skill `content-research` |
| Defense in Depth | "validation layers", "defense in depth" | Плагин `superpowers:systematic-debugging` (defense-in-depth = его reference) |
| Privacy Filter / Обезличивание | "обезличь текст", "деперсонализация", "убери персональные данные", "privacy filter", "opf", "redact PII", "найди ПД", "обезличить перед отправкой в GPT", "де-идентификация", "вырежи имена/телефоны/адреса" | Skill `privacy-filter` (локальная on-device модель openai/privacy-filter, обратимое обезличивание + fine-tune RU) |
| GTD | "GTD", "todoist", "getting things done" | Command `gtd` |
| Figma library | "figma library", "design system figma", "figma tokens" | Plugin `figma:figma-generate-library` |
| Figma write | "write to figma", "push to figma", "create in figma" | Plugin `figma:figma-generate-design` + `figma:figma-use` |
| Voice mode | "голосовой режим", "voice", "диктовка", "push to talk" | `/voice` (CLI + VSCode, push-to-talk пробелом) |
| Remote Control | "удалённый доступ", "remote", "с телефона", "веб сессия", "QR код" | `/remote` → URL claude.ai/code или QR-код (CLI + VSCode) |
| Channels | "channels", "telegram channel", "discord channel", "управление через тг" | `claude --channels plugin:telegram@claude-plugins-official` |
| Loop | "повторяй", "loop", "каждые N минут", "мониторь", "следи" | `/loop 5m <prompt>`, дефолт 10 мин |
| Schedule | "schedule", "cron", "запланируй агента", "по расписанию" | `/schedule` — cron-задачи для remote agents |
| Цвет сессии | "цвет сессии", "color" | `/color` |
| Переименовать сессию | "переименуй сессию", "rename session" | `/rename` |
| Effort | "effort", "глубина ответа", "ultrathink", "думай глубже" | `/effort low\|medium\|high\|max\|auto`, `/model ultrathink` |
| Fork/Branch | "форк", "ветка разговора", "branch", "эксперимент" | `/fork` или `/branch` — ответвление диалога |
| Rewind | "откати", "rewind", "верни назад", "отмени изменения" | `/rewind` — откат кода и диалога к checkpoint |
| Resume | "продолжи сессию", "resume", "восстанови" | `/resume` — восстановить предыдущую сессию |
| Diff | "покажи изменения", "diff", "что поменялось" | `/diff` — интерактивный просмотр uncommitted изменений |
| Fast mode | "быстрый режим", "fast mode" | `/fast` — toggle быстрого режима |
| Cost | "сколько потрачено", "cost", "токены" | `/cost` — usage текущей сессии |
| Usage | "лимиты", "usage", "квота", "rate limit" | `/usage` — статус подписки и лимитов |
| Init | "инициализация проекта claude", "init" | `/init` — генерация CLAUDE.md для проекта |
| Batch | "массовые правки", "batch", "bulk edit" | `/batch` — параллельные правки нескольких файлов |
| PR Comments | "комменты PR", "pr-comments", "отзывы на PR" | `/pr-comments` — подтянуть комменты GitHub PR |
| Security Review | "security review", "проверь безопасность" | `/security-review` — сканирование уязвимостей |
| Config | "настройки claude", "config", "settings" | `/config` — панель настроек |
| Permissions | "разрешения", "permissions" | `/permissions` — управление правами доступа |
| MCP | "mcp серверы", "подключи mcp" | `/mcp` — управление MCP серверами |
| Desktop | "открой в десктопе", "desktop app" | `/desktop` — передать сессию в Desktop приложение |
| Mobile | "открой на телефоне", "mobile" | `/mobile` — QR-код для мобильного |
| Context | "контекст", "сколько занято", "context window" | `/context` — визуализация использования контекста |
| Doctor | "диагностика", "doctor", "проверь установку" | `/doctor` — диагностика конфигурации |
| Debug | "дебаг сессии", "debug session" | `/debug` — troubleshoot текущей сессии |
| Copy | "скопируй ответ", "copy" | `/copy N` — копировать N-й ответ, `w` записать в файл |
| Reload plugins | "обнови плагины", "reload plugins" | `/reload-plugins` — применить изменения плагинов без рестарта |
| Keybindings | "горячие клавиши", "keybindings", "шорткаты" | `/keybindings` — настройка клавиатурных сокращений |
| Memory | "память claude", "memory", "что запомнил" | `/memory` — управление auto-memory |
| Model | "смени модель", "model", "переключи на opus" | `/model opus\|sonnet\|haiku`, `/model ultrathink` |
| Plan | "план", "plan mode", "спланируй" | `/plan` — режим планирования |
| Compact | "сожми контекст", "compact" | `/compact` — сжатие истории диалога |
| Clear | "очисти", "clear", "начни заново" | `/clear` — полный сброс сессии |
| Help | "помощь", "help", "команды" | `/help` — список всех команд |
