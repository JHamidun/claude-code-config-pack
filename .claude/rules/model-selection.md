# Model Selection Guide

## Quick Decision Table

| Task Type | Model | Why |
|-----------|-------|-----|
| Architecture decisions | Opus | Deep reasoning, tradeoff analysis |
| Complex debugging | Opus | Root cause analysis, multi-file context |
| Code implementation | Opus/Sonnet | Opus for complex, Sonnet for routine |
| Code review | Sonnet | Fast, good at pattern matching |
| Quick search/exploration | Haiku | Fast, cheap, good for simple queries |
| File operations | Haiku | Rename, move, simple edits |
| Subagent tasks | Sonnet/Haiku | Balance speed vs quality per task |
| Writing documentation | Sonnet | Good prose, fast enough |
| Security audit | Opus | Thoroughness matters most |
| Refactoring | Sonnet | Pattern recognition, speed |
| Test writing | Sonnet | Coverage patterns, mocking |
| Bug hunting | Opus | Systematic root cause analysis |
| Translation/i18n | Haiku | Simple string operations |
| Data migration scripts | Sonnet | Structured, predictable logic |
| API design | Opus | Consistency, edge cases, naming |

## Model Capabilities

### Opus 4.6 (default, most capable)

- **Best for:** Complex reasoning, architecture, deep analysis, extended thinking
- **Context:** 1M tokens
- **Speed:** Slowest
- **Cost:** Highest (covered by Max subscription)
- **Use when:** Quality > speed, complex multi-step tasks
- **Strengths:** Nuanced tradeoffs, long-range coherence, planning, security analysis
- **Avoid when:** Simple repetitive tasks (wastes time)

### Sonnet 4.5 (balanced)

- **Best for:** Code generation, reviews, routine tasks, good speed/quality balance
- **Context:** 200K tokens
- **Speed:** Medium
- **Use when:** Need good results fast, routine development
- **Strengths:** Code quality, pattern matching, refactoring, prose
- **Avoid when:** Tasks requiring deep multi-step reasoning

### Haiku 4.5 (fastest)

- **Best for:** Simple queries, file search, classification, quick operations
- **Context:** 200K tokens
- **Speed:** Fastest
- **Use when:** Speed > quality, simple tasks, subagent work
- **Strengths:** Low latency, classification, extraction, simple transforms
- **Avoid when:** Complex logic, architecture, anything requiring nuance

## External Models (via AI Gateway)

| Model | When to Use |
|-------|------------|
| GPT-5.4 | Cross-model validation, function calling patterns |
| Gemini 3.1 Pro | 2M context, multimodal, Google ecosystem |
| Gemini Flash Image | Image generation (default model) |
| o4-mini | Math, logic, structured reasoning tasks |
| Kimi K2 | Algorithm problems, deep reasoning |
| deep-research-pro | Multi-step research with citations |

## Subagent Model Selection

```
model: "haiku"   -- exploration, simple search, file operations
model: "sonnet"  -- code generation, reviews, moderate complexity
model: "opus"    -- architecture, security, complex analysis
```

### Decision Flow for Subagents

1. Is it a search/lookup/classification task? -> Haiku
2. Does it generate or modify code? -> Sonnet
3. Does it require reasoning about tradeoffs or security? -> Opus
4. Is it a worker in a multi-agent pipeline? -> Sonnet (default)
5. Is it the orchestrator of a multi-agent pipeline? -> Opus

## When to Override Default (Opus)

Switch DOWN to Sonnet when:
- Implementing a well-defined feature (clear spec, no ambiguity)
- Running code reviews on small PRs
- Writing tests for existing code
- Generating boilerplate or CRUD operations

Switch DOWN to Haiku when:
- Exploring codebase structure
- Renaming variables or files
- Running simple search-and-replace
- Classifying or categorizing items
- Generating commit messages

Stay on Opus when:
- Debugging production issues
- Designing new systems or APIs
- Performing security audits
- Making decisions with incomplete information
- Working with 500K+ token context

## Switching Models

- `/model opus` or `/use-opus` -- switch to Opus 4.6
- `/model sonnet` or `/use-sonnet` -- switch to Sonnet 4.5
- `/model haiku` or `/use-haiku` -- switch to Haiku 4.5
- In agent definition: `model: opus|sonnet|haiku` in YAML frontmatter
- In Task(): `Task(subagent_type="general-purpose", model="sonnet", ...)`

## Cost-Efficiency Rules

1. Never use Opus for tasks Haiku can handle -- saves time, not money (Max sub)
2. Prefer Sonnet as the default subagent model -- best speed/quality ratio
3. Reserve Opus for orchestrators and complex decisions
4. Use Haiku for high-volume parallel subagents (10+ concurrent)
5. External models cost real money -- use only when Claude models lack capability
