# Что внутри пака

Собрано генератором `_gen_catalog.py` по фактическому содержимому дерева, а не написано руками: цифра в тексте устаревает молча.

## Ядро

Всё, что лежит в `.claude/` и работает без включения плагинов.

| | |
|---|---:|
| Навыков | 315 |
| Команд (`/имя`) | 99 |
| Агентов | 78 |
| Правил (грузятся каждую сессию) | 19 |
| Скриптов и инструментов | 45 |
| Хуков | 11 |

**Навык** — инструкция, которую модель подхватывает сама, когда задача подходит под её описание. **Команда** вызывается вручную через `/имя`. **Агент** — отдельный исполнитель со своим контекстом, ему поручают кусок работы целиком. **Правило** читается в начале каждой сессии и задаёт поведение. **Хук** срабатывает на событие, например перед выполнением команды в оболочке.

---

## Плагины — 33

Плагин это набор навыков, команд и агентов вокруг одной темы. Ставится и снимается целиком через `/plugin`, по умолчанию выключен. Содержимое плагинов — машинная копия соответствующих навыков ядра, поэтому включать их имеет смысл, когда ядро не подключено целиком.

### Работа с кодом

**`dev-core`** — Dev Core. 15 навыков, 15 команд, 10 агентов.
  Python/JS/TS dev, database design, API docs, build fix, git workflow, architecture agents.
  Внутри: `api-documentation`, `apple-developer`, `autocad-com`, `beads`, `build-fix`, `changelog-generator` и ещё 9

**`skill-dev`** — Skill & Agent Dev. 10 навыков, 5 агентов.
  Author skills/agents/plugins/MCP, prompt engineering, Claude API & CLI.
  Внутри: `claude-api`, `claude-cli-runner`, `content-policy`, `context-engineering`, `llm-evals`, `mcp-builder` и ещё 4

**`code-health`** — Code Health. 6 навыков, 6 команд, 12 агентов.
  Bug/cleanup/deps/reuse/security health audits, security audit, threat hunting.
  Внутри: `health-inline`, `leak-scan`, `osint-recon`, `privacy-filter`, `security-audit`, `threat-hunting`

**`dev-process`** — Dev Process. 5 навыков, 8 команд, 1 агент.
  TDD, systematic debugging, planning, code review, worktrees, parallel agents.
  Внутри: `parse-git-status`, `rollback-changes`, `run-quality-gate`, `scaling-stage`, `validate-plan-file`

**`browser-testing`** — Browser & Testing. 4 навыка, 2 команды, 4 агента. 1.3 МБ.
  Browser automation (dev-browser, gstack, Playwright), webapp testing, test/perf agents.
  Внутри: `dev-browser`, `gstack`, `playwright-automation`, `webapp-testing`

**`gsd`** — Get Shit Done (GSD). 18 агентов.
  Phase-based dev framework: roadmaps, plans, execution, verification, debugging.


### Дизайн и интерфейс

**`design-io`** — Design I/O & QA. 17 навыков, 1 команда, 3 агента.
  Figma import/export, PDF/PNG/PPTX export, dev handoff, verify, perf & a11y audits.
  Внутри: `a11y-audit`, `claude-design`, `design-guardrails`, `dev-handoff`, `document-import`, `export-pdf` и ещё 11

**`ui-motion`** — UI Motion & States. 13 навыков.
  Microinteractions, animations, mobile overlays, live tweaks, device frames, accessible forms.
  Внутри: `animations`, `comment-injector`, `device-frames`, `emil-design-eng`, `forms-a11y`, `live-preview` и ещё 7

**`design-system`** — Design System. 12 навыков.
  Design tokens, color scales, type scale, dark mode, themes, brand kit.
  Внутри: `brand-extractor`, `brand-guidelines`, `color-system-builder`, `dark-mode-add`, `deck-themes`, `design-md-brands` и ещё 6

**`prototyping`** — Prototyping. 12 навыков. 7.8 МБ.
  Wireframes, interactive prototypes, component playground, sketch/Claude-design to HTML.
  Внутри: `canvas-design`, `claude-in-html`, `component-playground`, `design-canvas`, `interactive-prototype`, `placeholders` и ещё 6

**`web-publish`** — Web Publishing. 12 навыков, 1 агент.
  Websites, HTML email, standalone/canonical HTML, PWA shell, web assets, slides, dataviz, diagrams.
  Внутри: `canonical-html`, `cards-creator`, `d3-visualization`, `excalidraw-flowchart`, `generate-report-header`, `html-email` и ещё 6

**`design-process`** — Design Process. 11 навыков, 1 агент.
  Design taste, orchestration, critique, comparison, frontend presets, cookbook.
  Внутри: `comparison-mode`, `content-rules`, `cookbook`, `critique-mode`, `design-guide`, `design-orchestrator` и ещё 5


### Тексты и публикации

**`content-writing`** — Content Writing. 9 навыков, 1 команда, 4 агента.
  Content engine, de-AI text, document interlinking, Telegram posts, RU proofreading.
  Внутри: `author-voice`, `brand-voice`, `content-creation`, `content-engine`, `content-research`, `de-ai-ify` и ещё 3

**`office-docs`** — Office Documents. 7 навыков.
  XLSX, PDF, EPUB, CSV analysis, file conversion & organization.
  Внутри: `csv-analysis`, `epub-tools`, `file-converter`, `file-organizer`, `invoice-organizer`, `pdf` и ещё 1

**`linkedin-suite`** — LinkedIn Suite. 6 навыков.
  Write, humanize, audit, plan LinkedIn posts; profile optimization; comment & reply drafting.
  Внутри: `linkedin`, `linkedin-comment-drafter`, `linkedin-employee-advocacy`, `linkedin-humanizer`, `linkedin-post-writer`, `linkedin-profile-optimizer`

**`presentations`** — Presentations. 6 навыков, 1 команда, 1 агент. 22.2 МБ.
  Gamma, Manus slides, Marp, native PPTX create/edit/import.
  Внутри: `gamma`, `manus-slides`, `marp-presentations`, `pptx`, `pptx-editable-extractor`, `pptx-import`

**`social-posting`** — Messaging & Posting. 3 навыка.
  Publish to Telegram channels via bot, send SMS (Twilio), work with any IMAP/SMTP mailbox.
  Внутри: `email-imap`, `sms-twilio`, `tg-bot-publish`


### Маркетинг и продажи

**`marketing-ru`** — Marketing Strategy. 18 навыков. 1.2 МБ.
  Offers, pricing, positioning, launches, retention, referrals, growth loops, JTBD, PR outreach, marketing team building.
  Внутри: `ai-marketing-stack-ru`, `b2b-marketing-ru`, `churn-prevention-ru`, `content-machine-ru`, `free-tools-lead-magnets-ru`, `jtbd` и ещё 12

**`sales-tools`** — Sales Tools. 11 навыков, 4 команды.
  Account research, call prep, outreach, lead research, battlecards, daily briefing.
  Внутри: `account-research`, `call-prep`, `competitive-intelligence`, `create-an-asset`, `daily-briefing`, `draft-outreach` и ещё 5

**`cro-funnels`** — CRO & Funnels. 10 навыков.
  Conversion optimization for landing pages, signup, onboarding, paywalls, popups and forms; funnel design, A/B testing, full-funnel analytics.
  Внутри: `ab-testing-ru`, `capi-no-code-setup`, `form-cro-ru`, `full-funnel-analytics-ru`, `funnel-design-ru`, `manychat-funnel-ru` и ещё 4

**`paid-ads`** — Paid Advertising. 7 навыков.
  Meta, Google, VK, Yandex Direct and Telegram Ads playbooks, performance creative production, benchmark diagnostics.
  Внутри: `ad-benchmarks-ru`, `ai-creative-factory-ru`, `google-ads-pro-ru`, `meta-ads-launch-ru`, `telegram-ads-pro-ru`, `vk-ads-pro-ru` и ещё 1

**`product-mgmt`** — Product Management. 5 навыков, 10 команд, 1 агент.
  Specs, roadmaps, metrics/OKR, user research synthesis, stakeholder comms.
  Внутри: `feature-spec`, `metrics-tracking`, `roadmap-management`, `stakeholder-comms`, `user-research-synthesis`

**`marketing-tools`** — Marketing Tools. 4 навыка, 7 команд.
  Campaign planning, competitive analysis, performance analytics (ROAS/CPL).
  Внутри: `campaign-planning`, `competitive-analysis`, `competitive-analysis-mktg`, `performance-analytics`

**`seo-geo`** — SEO & AI Answer Optimization. 4 навыка, 1 команда.
  SEO content pipeline, programmatic AI-SEO page generation, schema.org markup, GEO/AEO visibility in ChatGPT, Perplexity and AI Overviews.
  Внутри: `ai-seo-agent-pipeline`, `geo-aeo-ru`, `schema-markup-ru`, `seo-machine-ru`


### Медиа

**`video-media`** — Video Production. 12 навыков, 3 команды, 9 агентов. 15.0 МБ.
  8-role production pipeline (brief to QC), generation (Runway), avatars (HeyGen/D-ID), edit, download, export, subtitles, transcripts.
  Внутри: `did`, `heygen`, `submagic`, `video-downloader`, `video-editor`, `video-export` и ещё 6

**`image-gen`** — AI Image Generation. 10 навыков, 1 агент.
  Nano Banana, DALL-E, Replicate, enhancement, OCR, stickers, generative art.
  Внутри: `algorithmic-art`, `edit-banana`, `image-enhancer`, `image-generation`, `nano-banana-pro`, `ocr-restore` и ещё 4

**`audio-voice`** — Audio & Voice. 3 навыка.
  Music generation (ACE-Step), TTS & voice cloning (ElevenLabs), transcription (Deepgram).
  Внутри: `ace-step`, `deepgram`, `elevenlabs`


### Данные и разведка

**`research-tools`** — Research & Analysis. 11 навыков, 4 команды.
  Document Q&A, stock analysis, CEO council, thinking frameworks, meeting analysis.
  Внутри: `building-an-exo`, `ceo-council`, `check-skill-solo`, `developer-growth`, `domain-brainstormer`, `internal-comms` и ещё 5

**`social-intel`** — Social Intelligence. 10 навыков. 12.0 МБ.
  Trends, ad spy, TikTok intel, SimilarWeb, Reddit/HN, scraping, GitHub gem hunting.
  Внутри: `ad-spy`, `apify-scraping`, `github-gem-seeker`, `last30days`, `meta-ads-analyzer`, `reddit-hn` и ещё 4


### Инфраструктура

**`integrations`** — Integrations & DevOps. 11 навыков, 6 команд, 2 агента. 42.8 МБ.
  n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, Home Assistant, webhooks.
  Внутри: `agent-api-server`, `aws-skills`, `claude-server-auth`, `deepl-pro`, `home-assistant`, `maps-places` и ещё 5

**`session-tools`** — Session & Memory. 8 навыков, 14 команд, 1 агент.
  Memory search/learn, chat history, daily planning, reviews, model switching, session save/restore.
  Внутри: `away-summary`, `btw`, `dream`, `memory-agent`, `save-knowledge-base`, `self-reflect` и ещё 2

**`ai-gateways`** — Multi-Model Gateways. 5 навыков, 1 команда, 3 агента.
  Route to GPT, Gemini, Kimi, DeepSeek, Perplexity for cross-model work.
  Внутри: `deepseek`, `gemini-3-pro`, `kimi`, `multi-model-gateway`, `perplexity`

**`google-workspace`** — Google Workspace. 1 навык, 14 команд.
  Gmail, Docs, Sheets, Drive, Calendar, Contacts, Tasks, Meet, Chat, Ads, Analytics.
  Внутри: `google-workspace`


---

## С чего начать

Навыки вызываются сами, но эти стоит знать по именам:

- **`design-orchestrator`** — Главный дизайн-скилл: «сделай дизайн/прототип/слайды/лендинг/макет» — любой HTML-артефакт с дизайном; ведёт процесс, подключает design-скиллы
- **`leak-scan`** — PII/деанон перед публикацией (leak_scan.py) + prompt-injection в чужом скилле (skill_injection_scan.py)
- **`n8n`** — n8n workflow automation: API, ноды, MCP + локальный каталог 2061 готового воркфлоу
- **`playwright-automation`** — Playwright: e2e-тесты, скрапинг + демон-браузер bdo.py (параллельные сессии)
- **`video-editor`** — Видеомонтаж FFmpeg+Python: тишина, субтитры, рефрейм 9:16
- **`llm-evals`** — Эвалы LLM/агентов: golden-set, LLM-судья + метрики, вердикт keep/rollback, свип моделей и effort
- **`skill-creator`** — Создание, правка и эвалы навыков, оптимизация description
- **`health-inline`** — Codebase health инлайн (сам оркестратор): детекция→фикс→верификация

---

## Установка

```bash
# macOS / Linux
chmod +x install.sh uninstall.sh
./install.sh --dry-run     # посмотреть, что будет сделано
./install.sh
```

```powershell
# Windows
.\install.ps1 -DryRun
.\install.ps1
```

`uninstall.sh` / `uninstall.ps1` убирает ровно то, что положил установщик, и ничего сверх.

Ключи к внешним сервисам нужны не всем навыкам; шаблон — `.claude/templates/.credentials.master.env.example`, в нём только имена переменных, без значений.
