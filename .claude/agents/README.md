# Agents

> Specialized AI agents for delegation via orchestrator pattern. Точные счётчики — `scripts/config_lint.py`. Text-агенты — model: fable (канон rules/models.md).

## Core

| Agent | Description |
|-------|-------------|
| `orchestrator` | Multi-agent workflow coordinator |
| `senior-developer` | Clean, production-ready code |
| `code-reviewer` | Security, quality, performance review |
| `tech-lead` | Architecture decisions, team coordination |
| `software-architect` | System architecture and task decomposition |
| `system-analyst` | Feasibility, dependencies, integration |
| `business-analyst` | Requirements, stakeholders, ROI |
| `error-handler` | Root cause analysis from stack traces |
| `memory-agent` | Long-term memory and context recall |

## Development

| Agent | Description |
|-------|-------------|
| `backend-dev` | Python, Node.js, APIs, databases |
| `frontend-dev` | React, TypeScript, modern frontend |
| `integration-dev` | Third-party APIs, webhooks |
| `devops-engineer` | Deployment, CI/CD, infrastructure |
| `qa-specialist` | Test strategy, automation, CI/CD |
| `legacy-modernizer` | Refactoring, migration, tech debt |

## Health (`health/workers/`)

| Agent | Description |
|-------|-------------|
| `bug-hunter` | Comprehensive bug detection |
| `bug-fixer` | Systematic bug fixing by priority |
| `security-scanner` | SQL injection, XSS, secrets detection |
| `vulnerability-fixer` | Security fix implementation |
| `dead-code-hunter` | Unused code detection via Knip |
| `dead-code-remover` | Safe dead code cleanup |
| `dependency-auditor` | Outdated/vulnerable package analysis |
| `dependency-updater` | Safe dependency updates with rollback |
| `reuse-hunter` | Code duplication detection |
| `reuse-fixer` | Consolidation to Single Source of Truth |

## Testing (`testing/workers/`)

| Agent | Description |
|-------|-------------|
| `test-writer` | Unit and contract tests (Vitest) |
| `integration-tester` | E2E and acceptance tests |
| `performance-optimizer` | Core Web Vitals optimization |
| `accessibility-tester` | WCAG 2.1 AA/AAA compliance |
| `mobile-responsiveness-tester` | Multi-viewport mobile testing |
| `mobile-fixes-implementer` | Mobile CSS/JS fix automation |

## Security

| Agent | Description |
|-------|-------------|
| `security-engineer` | Vulnerability assessment, secure coding |
| `pentest-engineer` | Penetration testing, exploit analysis |

## Specialized

| Agent | Description |
|-------|-------------|
| `slide-designer` | Production-ready HTML slides |
| `presentation-master` | Engaging presentations, storytelling |
| `product-designer` | UX/UI, wireframes, prototypes |
| `prompt-engineer` | LLM prompt optimization |
| `ml-specialist` | ML models, data pipelines, MLOps |
| `kimi-algorithm-specialist` | Algorithms, data structures, math |

## Proofreading (3-stage pipeline)

| Agent | Description |
|-------|-------------|
| `proofreader-ortho` | Stage 1: Russian spelling |
| `proofreader-punctuation` | Stage 2: Russian punctuation |
| `proofreader-typography` | Stage 3: Typographic corrections |

## Long-form Content (1 agent)

| Agent | Description |
|-------|-------------|
| `book-fact-checker` | Book chapters fact-check («a non-fiction book», UNKNOWN vs VERIFIED) |

## External Models

| Agent | Description |
|-------|-------------|
| `gpt-agent` | GPT-5.4/o4 via AI Gateway — alternative perspective |
| `gemini-agent` | Gemini 3.1/3.0 via AI Gateway — long context, multimodal |

## Pipelines

| Agent | Description |
|-------|-------------|
| `video-factory` | Trends → script → avatar → b-roll → audio → subtitles → YouTube |

## GSD (`gsd-*`, spawned by /gsd:* commands)

18 workers: planner, executor, verifier, debugger, roadmapper, phase/project/advisor researchers, research-synthesizer, plan/integration/ui checkers, ui-researcher/auditor, codebase-mapper, assumptions-analyzer, nyquist-auditor, user-profiler. Спавнятся оркестраторами `/gsd:*` — напрямую не вызывать.

## Meta (`meta/workers/`)

| Agent | Description |
|-------|-------------|
| `meta-agent-v3` | Creates new Claude Code agents |

## Writing your own

Start from `~/.claude/templates/agent-persona.yaml` — it carries the frontmatter
shape and the model rule. Keep `model:` an **alias** (`fable` for text workers,
`opus` for an orchestrator, `haiku` for bulk runs), never a dated ID: a stale ID
does not fail, it silently serves an older model. `python
~/.claude/scripts/config_lint.py` prints every file that pins one (section 3.6).
