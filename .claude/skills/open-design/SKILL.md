---
name: open-design
description: Open-source альтернатива Claude Design — локальный design-tool с 35 скиллами, 72 дизайн-системами и поддержкой 10 AI-агентов. Запуск, workflow, сравнение с Claude Design / Manus Slides / Your Slide Service, интеграция с Claude Code.
---

# open-design

**GitHub:** https://github.com/nexu-io/open-design  
**Лицензия:** Apache-2.0 | **Звёзды:** 7.6k | **Статус:** активно, коммиты ежедневно  
**Локальный путь:** `~/.claude/tools/open-design/`

## Когда использовать

- "open design", "открой опен дизайн", "запусти open-design"
- "сделай дизайн через open-design"
- "лендинг / dashboard / pitch deck / mobile app" — более мощная альтернатива claude-design
- Импорт Claude Design ZIP: `POST /api/import/claude-design`
- Нужен конкретный бренд из 72 дизайн-систем (Stripe, Linear, Vercel, Tesla, Anthropic...)

## Что это

Локальное веб-приложение (Next.js frontend + Node.js daemon) с:
- **31 скилл**: web-prototype, saas-landing, dashboard, pricing-page, mobile-app, magazine-poster, saas-deck, email-marketing, finance-report, kanban-board, eng-runbook...
- **72 дизайн-системы**: Linear, Stripe, Vercel, Airbnb, Tesla, Notion, Apple, Anthropic, Cursor, Spotify...
- **10 AI-агентов**: Claude Code (основной), Cursor, Gemini CLI, Codex, OpenCode, Qwen, GitHub Copilot...
- **Экспорт**: HTML, PDF, PPTX, ZIP, Markdown
- **Импорт**: Claude Design ZIP

## Установка (первый раз)

**Требования:** Node 22+ (24 рекомендован), pnpm 10.33.x

```bash
# 1. Клонировать
git clone https://github.com/nexu-io/open-design.git ~/.claude/tools/open-design

# 2. Установить зависимости (ignore-scripts чтобы не падал Electron на Windows)
cd ~/.claude/tools/open-design
pnpm install --ignore-scripts

# 3. Собрать зависимости
pnpm --filter @open-design/tools-dev... build

# 4. Скомпилировать better-sqlite3 (нативный аддон, нужен Visual Studio Build Tools)
cd node_modules/.pnpm/better-sqlite3@*/node_modules/better-sqlite3
npx node-gyp rebuild
cd ~/.claude/tools/open-design

# 5. Запуск (2 терминала)
# Терминал 1 — daemon:
node apps/daemon/dist/cli.js --no-open
# → Daemon: http://127.0.0.1:7456 (порт рандомный, смотри вывод)

# Терминал 2 — web frontend:
cd apps/web && pnpm dev
# → Web UI: http://localhost:3000
```

## Быстрый старт (после установки)

```bash
# Запуск (из двух терминалов параллельно)
cd ~/.claude/tools/open-design && node apps/daemon/dist/cli.js --no-open
cd ~/.claude/tools/open-design/apps/web && pnpm dev

# Остановка
Ctrl+C в обоих терминалах
```

Открыть в браузере: **http://localhost:3000**

## API (для интеграции с Claude Code)

Daemon запущен на `http://127.0.0.1:7456` (порт динамический, смотри вывод `[od] listening on`):

```bash
# Список доступных агентов
curl http://127.0.0.1:7456/api/agents

# Список скиллов
curl http://127.0.0.1:7456/api/skills

# Список дизайн-систем
curl http://127.0.0.1:7456/api/design-systems

# Импорт Claude Design ZIP
curl -X POST http://127.0.0.1:7456/api/import/claude-design -F "file=@handoff.zip"

# Стриминг чата
curl -N -X POST http://127.0.0.1:7456/api/chat \
  -H "Content-Type: application/json" \
  -d '{"agentId":"claude","skillId":"saas-landing","designSystemId":"linear","message":"Landing page for AI platform"}'
```

## Сравнение с существующими инструментами

| Инструмент | Что делает | Когда лучше |
|-----------|-----------|-------------|
| **open-design** | Full local app, 31 скилл, 72 бренда, BYOK | Серьёзный дизайн, лендинги, dashboards |
| **claude-design** (skill) | Инструкции для claude.ai/design | Быстрый мокап в браузере, нет локал. установки |
| **manus-slides** | HTML слайды через Claude в chat | Быстрые слайды прямо в сессии |
| **design-orchestrator** | Оркестрирует design-skills пакет (55 скиллов) | Внутри Claude Code сессии, без внешнего UI |
| **Your Slide Service** (мёртв) | Был deck-генератор | Заменён open-design deck-режимом |

**Иерархия выбора:**
1. Быстро в чате → `manus-slides` или `design-orchestrator`
2. Нужен живой UI + итерации + экспорт → `open-design`
3. Только объяснить как пользоваться claude.ai/design → `claude-design` skill
4. Your Slide Service — больше не нужен, `open-design` deck mode лучше

## Интеграция с claude-code-skills (design-orchestrator)

open-design и design-orchestrator **дополняют** друг друга:

- **design-orchestrator** → генерирует HTML артефакты прямо в сессии Claude Code
- **open-design** → полноценный локальный design tool с UI, итерациями, импортом/экспортом

Workflow совместного использования:
1. Быстрый драфт в design-orchestrator (в сессии)
2. Экспортировать как standalone HTML
3. Импортировать в open-design для доработки и полировки
4. Финальный экспорт: PDF/PPTX/ZIP из open-design

## 31 скилл — полный список

**Prototype (27):**
web-prototype, saas-landing, dashboard, pricing-page, docs-page, blog-post, mobile-app, mobile-onboarding, gamified-app, email-marketing, social-carousel, magazine-poster, motion-frames, sprite-animation, dating-web, digital-eguide, wireframe-sketch, critique, tweaks, pm-spec, team-okrs, meeting-notes, kanban-board, eng-runbook, finance-report, invoice, hr-onboarding

**Deck (4):**
guizang-ppt (мощный, default), simple-deck, replit-deck, weekly-update

## 72 дизайн-системы — категории

AI/LLM: Claude, Cohere, Mistral, Replicate, RunwayML, ElevenLabs, Ollama  
Dev Tools: Cursor, Vercel, Linear, Framer, Expo, Supabase, PostHog, Sentry, Warp  
Productivity: Notion, Figma, Miro, Airtable, Raycast, Superhuman  
Finance: Stripe, Coinbase, Binance, Revolut, Wise  
Consumer: Airbnb, Uber, Nike, Starbucks, Spotify, Tesla, Apple, BMW

## Примеры использования

```
"open-design: saas-landing для ExampleProduct с дизайн-системой Linear"
"open-design: pitch deck для инвесторов, стиль Vercel"
"open-design: finance report dashboard, бренд Stripe"
"импортируй этот claude-design zip в open-design"
```

## Безопасность

- ✅ Daemon только localhost (127.0.0.1) — не открыт в сеть
- ✅ Нет hardcoded secrets, нет eval()
- ✅ SSRF защита в BYOK proxy
- ⚠️ Нет auth — любой local process может вызвать daemon
- Данные хранятся в `.od/` внутри папки проекта
