# Agents

> Specialized AI agents for delegation via orchestrator pattern.

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

## Meta (`meta/workers/`)

| Agent | Description |
|-------|-------------|
| `meta-agent-v3` | Creates new Claude Code agents |
