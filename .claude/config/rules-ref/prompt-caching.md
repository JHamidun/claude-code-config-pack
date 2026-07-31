> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Prompt Caching Optimization

## How Caching Works
Claude's API caches the **prefix** of prompts. If the same system prompt + initial messages are sent, cached tokens cost significantly less.

## What Gets Cached (automatically by Claude Code)
1. **System prompt** — CLAUDE.md, rules/, skills loaded at session start
2. **Tool definitions** — all available tools (Read, Write, Bash, MCP, etc.)
3. **Conversation prefix** — earlier messages in the conversation

## Cache Economics
| Token Type | Cost | Savings |
|-----------|------|---------|
| Cached input | ~90% cheaper | Huge for long system prompts |
| Uncached input | Full price | First message in session |
| Output | Full price | Not cached |

## Optimization Strategies

### For Individual Users (Max Subscription)
- **Keep sessions alive** — don't /clear unnecessarily (cache resets)
- **Use /compact instead of /clear** — preserves cache-friendly prefix
- **Batch related questions** — same session = same cached prefix

### For B2B / API Users (cost-critical)
1. **Stabilize system prompt** — avoid dynamic content in CLAUDE.md
   - Move changing data to user messages, not system prompt
   - Keep rules/ files stable between sessions
2. **Front-load static content** — put stable instructions before dynamic context
3. **Minimize tool changes** — each MCP server adds tool definitions to prompt
   - Only enable MCP servers you actually need
   - Fewer active MCP servers = smaller prompt = cheaper
4. **Reuse conversations** — `-c` flag to continue existing session

### System Prompt Size Impact
Current config loads ~50K tokens of system prompt (rules, skills, tools).
- With caching: ~$0.15 per session (cached after first message)
- Without caching: ~$1.50 per session
- **10x savings from caching**

## Anti-Patterns
- Frequently changing CLAUDE.md (breaks cache)
- Enabling all 19 MCP servers (inflates prompt with tool definitions)
- Starting new sessions for every question (cache cold start each time)
- Putting timestamps or dynamic data in rules/ files

## Cache Invalidation
Cache breaks when **any byte** in the prefix changes. This means:
- Editing a rules/ file invalidates cache for next message
- Adding/removing an MCP server invalidates cache
- Changing CLAUDE.md invalidates cache
- But editing project source files does NOT break cache (they are not in the prefix)

## Cache Lifetime
- Caches expire after ~5 minutes of inactivity
- Active conversations keep the cache warm automatically
- Long pauses between messages may cause cache miss on resume

## Best Practices Summary
1. Start session, let it cache, then ask many questions
2. Keep rules/ and CLAUDE.md stable during a session
3. Use /compact to reduce context without losing cache prefix
4. Enable only the MCP servers needed for current task
5. Continue sessions with `-c` instead of starting fresh
6. Put volatile data in conversation messages, not system prompt

## Monitoring
- `/cost` — see current session token usage
- `/usage` — see overall usage statistics
