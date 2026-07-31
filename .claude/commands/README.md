# Commands

> Custom slash commands for Claude Code. Usage: `/command-name`. ~100 root commands + `/gsd:*` family (57, в `gsd/`). Точные счётчики — `scripts/config_lint.py`, не этот каталог.

## Development

| Command | Description |
|---------|-------------|
| `/init-project` | Initialize project with chosen stack |
| `/generate-api` | Generate full CRUD API for a resource |
| `/add-auth` | Add authentication to project |
| `/setup-db` | Setup database integration |
| `/code-review` | Comprehensive code review |
| `/docs` | Generate documentation from code |
| `/changelog` | Auto-generate changelog from git |
| `/scaffold` | Project scaffolding |
| `/start-feature` | Start feature from Linear issue |
| `/feature-cycle` | Full feature dev cycle with agents |
| `/worktree` | Manage git worktrees |
| `/push` | Automated release with version bump |
| `/proofread` | 3-stage Russian text proofreading |

## AI

| Command | Description |
|---------|-------------|
| `/kimi-reasoning` | Deep analysis with Kimi K2 |
| `/manus` | Manus AI complex task automation |
| `/deep-research` | Perplexity-powered research |
| `/ultra-think` | Multi-dimensional deep analysis |

## Telegram

| Command | Description |
|---------|-------------|
| `/bot-debug` | Telegram bot debugging |
| `/bot-deploy` | Deploy bot with Docker/webhooks |
| `/bot-test` | Comprehensive bot testing |

## Project Management

| Command | Description |
|---------|-------------|
| `/sprint-planning` | Sprint planning via Linear/Jira |
| `/daily` | Daily standup summary |
| `/standup-report` | Standup report for period |
| `/roadmap` | Product roadmap generation |
| `/write-spec` | Feature specification (PRD) |
| `/specs` | Technical specifications |
| `/userflow` | User flow and wireframes |
| `/estimate` | Complexity and time estimation |
| `/retro` | Retrospective facilitation |
| `/bug-triage` | Bug prioritization |
| `/meeting` | Structure meeting notes |
| `/gtd` | GTD task management from Todoist |

## Deploy

| Command | Description |
|---------|-------------|
| `/deploy` | Universal deployment |
| `/quick-deploy` | Quick deploy with lint/test |
| `/parallel-dev` | Parallel dev via git worktrees |

## Context, Memory, Search

| Command | Description |
|---------|-------------|
| `/context-optimize` | Optimize context window |
| `/search-chats` | Full-text search across Claude Code chats (canon) |
| `/kb` | Local knowledge base: tl;dv/Spark/Gmail/Outlook/TG/Calendar |
| `/memory-search` | Search chats + knowledge base |
| `/memory-learn` | Save knowledge to memory |
| `/memory-extract` | Extract knowledge by topics (legacy) |
| `/memory-ingest` | Index chat history into chats.db |
| `/memory-stats` | Memory statistics |
| `/self-learn` | Auto-learn from errors |
| `/rename-sessions` | Bulk informative session titles |
| `/weekly-synthesis` | Weekly synthesis report |
| `/plan-my-day` | Optimized daily plan |
| `/prompt-log` | Session statistics (tokens, tools) |

## Analysis

| Command | Description |
|---------|-------------|
| `/analyze` | Codebase health analysis |
| `/review` | Comprehensive code/doc review |
| `/orchestrate` | Auto-orchestrate feature development |
| `/monitor-agents` | Monitor parallel agents |
| `/performance` | Performance analysis and optimization |
| `/security-scan` | Comprehensive security audit |

## Health

| Command | Description |
|---------|-------------|
| `/health-bugs` | Bug detection and fixing |
| `/health-security` | Security vulnerability scan |
| `/health-deps` | Dependency audit and update |
| `/health-cleanup` | Dead code detection and cleanup |
| `/health-reuse` | Code duplication consolidation |

## Models

Переключение моделей — встроенная команда `/model opus|sonnet|haiku` (кастомные /use-* удалены).

## Google Workspace / Cloud

| Command | Description |
|---------|-------------|
| `/gdrive` | Google Drive operations |
| `/gdocs` | Google Docs operations |
| `/gsheets` | Google Sheets operations |
| `/gcalendar` | Google Calendar operations |
| `/gmail` | Gmail (личная почта) |
| `/gcontacts` | Google Contacts (People API) |
| `/gtasks` | Google Tasks |
| `/gmeet` | Google Meet meetings and recordings |
| `/gchat` | Google Chat spaces and messages |
| `/gads` | Google Ads (GAQL) |
| `/ganalytics` | Google Analytics 4 |
| `/gsearch-console` | Google Search Console |
| `/gtranslate` | Google Cloud Translation |
| `/gcloud-storage` | Google Cloud Storage buckets |

## Knowledge-Work (PM / Sales / Marketing, connector-based)

| Command | Description |
|---------|-------------|
| `/write-spec`, `/roadmap-update`, `/metrics-review`, `/stakeholder-update`, `/synthesize-research`, `/competitive-brief`, `/sprint-planning-pm` | PM family |
| `/call-summary`, `/forecast`, `/pipeline-review` | Sales family |
| `/campaign-plan`, `/draft-content`, `/email-sequence`, `/seo-audit`, `/brand-review`, `/performance-report`, `/competitive-brief-mktg` | Marketing family |

## Media / Comms

| Command | Description |
|---------|-------------|
| `/transcribe` | Deepgram audio/video transcription |
| `/translate` | DeepL Pro translation |
| `/slides` | Presentation via Manus Slides pipeline |
| `/video-factory` | Full video production pipeline |
| `/youtube-upload` | Upload video to YouTube |
| `/domain-dns-ops` | Cloudflare DNS management |

## Other

| Command | Description |
|---------|-------------|
| `/beads-init` | Initialize Beads issue tracking |
| `/test-frontend` | Frontend testing with Playwright |
| `/kimi-reasoning` | (см. AI) Kimi K2 reasoning |
| `/gsd:*` | Get Shit Done workflow family (57 commands, `gsd/`) |
