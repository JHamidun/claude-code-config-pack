# Plugins Catalog

> 38 plugins total (see settings.json). All from settings.json `enabledPlugins`.
> Last updated: see git history

---

## Core Development (5)

| Plugin | What It Does | Key Commands/Skills |
|--------|-------------|---------------------|
| code-review | Automated code review with checklists | /code-review, review-pr |
| pr-review-toolkit | Multi-agent PR review (reviewer, simplifier, type analyzer) | /review-pr |
| feature-dev | Guided feature development with architecture focus | /feature-dev |
| code-simplifier | Refines code for clarity after implementation | Auto-triggers after coding |
| commit-commands | Git commit, push, PR workflow | /commit, /commit-push-pr |

## Language Servers (2)

| Plugin | What It Does | When Active |
|--------|-------------|-------------|
| pyright-lsp | Python type checking, autocomplete, diagnostics | Python files open |
| typescript-lsp | TypeScript/JS intelligence, type checking | TS/JS files open |

## Frontend & Design (2)

| Plugin | What It Does | Key Skills |
|--------|-------------|-----------|
| frontend-design | Production-grade UI with high design quality | /frontend-design |
| figma | Figma design to code, Code Connect components | /implement-design, /code-connect |

## Infrastructure & Agents (4)

| Plugin | What It Does |
|--------|-------------|
| agent-sdk-dev | Build Claude Agent SDK applications |
| claude-code-setup | Analyze codebase, recommend automations |
| claude-md-management | Audit and improve CLAUDE.md files |
| playground | Interactive HTML playgrounds for prototyping |

## Code Quality (3)

| Plugin | What It Does |
|--------|-------------|
| security-guidance | Security best practices, vulnerability detection |
| semgrep | Static analysis with Semgrep rules |
| plugin-dev | Create and validate plugins (skills, agents, hooks, commands) |

## Integrations (11)

| Plugin | Service | Key Use Case |
|--------|---------|-------------|
| github | GitHub | PRs, issues, repos, actions |
| slack | Slack | Messages, channels, search |
| linear | Linear | Tasks, issues, sprints |
| sentry | Sentry | Error monitoring, debugging |
| notion | Notion | Knowledge base, databases |
| firecrawl | Firecrawl | URL extraction, site crawling |
| coderabbit | CodeRabbit | AI code review on PRs |
| greptile | Greptile | AI review for GitHub/GitLab repos |
| context7 | Library docs | Up-to-date API documentation for any library |
| mintlify | Mintlify | Documentation sites generation |
| sourcegraph | Sourcegraph | Code search across repositories |

## Browser & Testing (2)

| Plugin | What It Does |
|--------|-------------|
| playwright | Browser automation, E2E testing, screenshots |
| dev-browser | Browser with persistent state, cookies, login sessions |

## AI & Specialized (4)

| Plugin | What It Does |
|--------|-------------|
| huggingface-skills | HuggingFace model training, datasets, inference |
| superpowers | Core workflow enhancements |
| ralph-loop | Recurring task execution loop |
| skill-creator | Create and benchmark skills |

## Automation & SaaS (2)

| Plugin | What It Does |
|--------|-------------|
| zapier | Zapier automation integration (5000+ apps) |
| adspirer-ads-agent | Google/Meta/LinkedIn ad campaign management |

## Domain-Specific (2)

| Plugin | What It Does |
|--------|-------------|
| laravel-boost | Laravel PHP development patterns *(disabled)* |
| legalzoom | Legal document analysis and guidance |

## Channels & Communication (1)

| Plugin | What It Does |
|--------|-------------|
| telegram | Channels — управление Claude Code через Telegram-бота |

---

## Summary by Source

| Source | Count |
|--------|-------|
| claude-plugins-official | 37 |
| dev-browser-marketplace | 1 |
| **Total** | **38** (35 enabled, 3 disabled: mintlify, zapier, laravel-boost) |

## Plugin Management

- Plugins live in `settings.json` under `enabledPlugins`
- Each plugin provides a combination of: skills, commands, agents, hooks
- Create new plugins: `plugin-dev:create-plugin`
- Validate plugin structure: `plugin-dev:plugin-validator`
- Set `true`/`false` to enable/disable without removing

## When to Disable

- Language servers (pyright-lsp, typescript-lsp) only useful when working with that language
- Domain-specific (laravel-boost, legalzoom) only if working in that domain
- Marketplace plugins (dev-browser, adspirer-ads-agent) if not actively used
- Removing unused plugins reduces prompt size and saves tokens
