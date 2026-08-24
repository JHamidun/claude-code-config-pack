> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Plugins Catalog

> **Источник истины — `settings.json` → `enabledPlugins`.** На момент правки там
> 33 записи: 29 включены (`true`), 4 выключены (`false`: linear, notion,
> pdf-viewer, telegram). Каталог ниже сгенерирован из этого списка; при
> расхождении верь settings.json, не документу.

---

## Core Development (6)

| Plugin | What It Does | Key Commands/Skills |
|--------|-------------|---------------------|
| code-review | Automated code review with checklists | /code-review |
| pr-review-toolkit | Multi-agent PR review (reviewer, simplifier, type analyzer) | /review-pr |
| feature-dev | Guided feature development with architecture focus | /feature-dev |
| code-simplifier | Refines code for clarity after implementation | Auto-triggers after coding |
| commit-commands | Git commit, push, PR workflow | /commit, /commit-push-pr |
| claude-security | Security scan pipeline: inventory → research → verify → patch | /claude-security |

## Language Servers (2)

| Plugin | What It Does | When Active |
|--------|-------------|-------------|
| pyright-lsp | Python type checking, autocomplete, diagnostics | Python files open |
| typescript-lsp | TypeScript/JS intelligence, type checking | TS/JS files open |

## Frontend & Design (2)

| Plugin | What It Does |
|--------|-------------|
| frontend-design | Production-grade UI with high design quality |
| playground | Interactive HTML playgrounds for prototyping |

## Infrastructure, Agents & Plugin Dev (6)

| Plugin | What It Does |
|--------|-------------|
| agent-sdk-dev | Build Claude Agent SDK applications |
| claude-code-setup | Analyze codebase, recommend automations |
| claude-md-management | Audit and improve CLAUDE.md files |
| plugin-dev | Create and validate plugins (skills, agents, hooks, commands) |
| mcp-server-dev | Build MCP servers and MCP apps |
| hookify | Create hooks from natural-language rules |

## Integrations (7)

| Plugin | Service | Key Use Case |
|--------|---------|-------------|
| github | GitHub | PRs, issues, repos, actions |
| linear *(disabled)* | Linear | Tasks, issues, sprints |
| notion *(disabled)* | Notion | Knowledge base, databases |
| firecrawl | Firecrawl | URL extraction, site crawling |
| coderabbit | CodeRabbit | AI code review on PRs |
| greptile | Greptile | AI review for GitHub/GitLab repos |
| context7 | Library docs | Up-to-date API documentation for any library |

## Search & Docs (2)

| Plugin | What It Does |
|--------|-------------|
| sourcegraph | Code search across repositories |
| pdf-viewer *(disabled)* | View and read PDF files |

## Browser & Testing (2)

| Plugin | What It Does |
|--------|-------------|
| playwright | Browser automation, E2E testing, screenshots |
| dev-browser | Browser with persistent state, cookies, login sessions |

## Workflow & Reporting (5)

| Plugin | What It Does |
|--------|-------------|
| superpowers | Core workflow enhancements (brainstorming, TDD, debugging) |
| ralph-loop | Recurring task execution loop |
| skill-creator | Create and benchmark skills |
| receipts | Usage & impact report from local session transcripts |
| project-artifact | Project status artifact pages |

## Channels & Communication (1)

| Plugin | What It Does |
|--------|-------------|
| telegram *(disabled)* | Channels — управление Claude Code через Telegram-бота |

---

## Not in this pack (ставятся из official marketplace при желании)

`slack`, `sentry`, `semgrep`, `security-guidance`, `figma`, `huggingface-skills`,
`mintlify`, `zapier`, `adspirer-ads-agent`, `laravel-boost`, `legalzoom` — в
старых версиях этого каталога значились как установленные; в паке их НЕТ.
Нужен такой — `/plugin` → marketplace, а потом впиши строку в `enabledPlugins`.

## Summary by Source

| Source | Count |
|--------|-------|
| claude-plugins-official | 31 |
| dev-browser-marketplace | 1 |
| knowledge-work-plugins | 1 |
| **Total** | **33** (29 enabled, 4 disabled: linear, notion, pdf-viewer, telegram) |

## Plugin Management

- Plugins live in `settings.json` under `enabledPlugins`
- Each plugin provides a combination of: skills, commands, agents, hooks
- Create new plugins: `plugin-dev:create-plugin`
- Validate plugin structure: `plugin-dev:plugin-validator`
- Set `true`/`false` to enable/disable without removing

## When to Disable

- Language servers (pyright-lsp, typescript-lsp) only useful when working with that language
- Marketplace plugins (dev-browser) if not actively used
- Removing unused plugins reduces prompt size and saves tokens
