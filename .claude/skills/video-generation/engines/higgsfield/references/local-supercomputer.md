# Local Supercomputer — собрать аналог Higgsfield-агента на нашем стеке

Реверс Higgsfield Supercomputer показал: это **pluggable-LLM оркестратор → загружает «сотрудника»
(sub-agent + flow-skill) → prompt-enhance → создаёт job в generation-бэкенде → folder/memory → approval/cron**.
У нас уже есть 90% кирпичей. Ниже — маппинг 1:1 и что достроить.

## Маппинг их механики → наш стек

| Higgsfield компонент | Наш эквивалент | Статус |
|---|---|---|
| Orchestrator (выбор LLM: Claude/Gemini/GPT/Grok) | главный цикл Claude Code + agent `orchestrator` + Task subagents (model: opus/sonnet/haiku) | ✅ есть |
| Employees (21 sub-agent) | `~/.claude/agents/` (51 агент) + skills | ✅ есть |
| Flow-skills (cinematic-flow, ugc-*-flow, montage…) | `~/.claude/skills/*` (198 скиллов) | ✅ есть (montage→video-editor, audio→elevenlabs/suno, maps→maps-places, pdf/pptx/youtube…) |
| Внутренние sub-skills (cinematic-dramaturg) | под-шаги внутри наших скиллов / under-the-hood reference | ⚠ воспроизвести как шаг скилла |
| Generation backend (jobs API) | `higgsfield` skill (hf.exe, 1200cr) + Veo/Seedance/Runway/Nano/Suno | ✅ есть (теперь +Higgsfield) |
| prompt-enhancement step | под-шаг «enhance prompt» (short→rich EN) перед генерацией | ⚠ сделать reusable |
| Approval gate («Ask before generation») | permission modes + AskUserQuestion | ✅ есть |
| Files / Memory (folders per chat) | `~/.claude/projects/<proj>/memory/` + scratchpad | ✅ есть |
| Scheduled tasks (higgsclaw cron) | `/schedule` + CronCreate + ScheduleWakeup | ✅ есть |
| Connectors (Slack/Drive/Notion/Gmail/Figma+30) | MCP-серверы + cloud-MCP подписки + skills | ✅ есть |
| Virality Predictor (brain_activity) | `hf generate create brain_activity --video` | ✅ есть (через higgsfield skill) |
| Marketplace (skills/employees, install) | наш skills/ каталог + `skill-creator` + `autonomous-agent-creator` | ✅ есть |
| Multi-model routing (Orchestrator picks best) | model-selection.md decision tree + per-agent model | ✅ есть |

## Что достроить (gaps → задачи)

1. **«Employee» = именованный профиль агента** = тонкая обёртка: agent + набор skills + дефолт-модель.
   Уже выражается через `agents/*.md` (frontmatter `model`, описание) + ссылки на skills. Можно завести
   `agents/` под их 21 роль (Cinematic Director, Podcast Producer, Motion Designer…) — большинство уже есть
   (video-factory, slide-designer, presentation-master…).
2. **Prompt-enhancement шаг**: переиспользуемый под-шаг «короткий бриф → насыщенный EN-промпт + film vocab»
   (у нас уже в video-generation Phase 3/director-rules). Вынести в общий helper.
3. **cinematic-dramaturg аналог**: шаг «раскадровка/драматургия» перед генерацией — у нас это
   `video-generation` storyboard + `SCENARIO.md` паттерн (уже применяли в ролике [Client] и viral-ролике).
4. **Единый «runner»**: один скилл-оркестратор (или agent `orchestrator`), который по брифу выбирает employee→flow,
   гонит enhance→dramaturg→keyframes→video→montage, кладёт в `memory/` проекта, спрашивает approval на дорогих шагах,
   умеет `/schedule`. Это ровно наш `video-factory` + `orchestrator` — расширить под их флоу.

## Вывод

Нам НЕ нужен их Supercomputer как продукт — у нас уже есть оркестратор + 198 skills + 51 agent + memory +
/schedule + MCP. Не хватало только **generation-бэкенда их моделей** — теперь закрыто скиллом `higgsfield`
(hf.exe, прямой jobs API, 51 модель, 1200cr, Virality Predictor). Плюс мы взяли их **паттерны**:
employee-роли, prompt-enhance шаг, dramaturg-шаг, Soul-anchoring для консистентности, approval-gate.

Полная механика и эндпоинты → `supercomputer-architecture.md`.
