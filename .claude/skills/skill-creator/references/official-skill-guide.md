# Official Anthropic Skill Building Guide (recent)

Reference extracted from "The Complete Guide to Building Skills for Claude" PDF.

## YAML Frontmatter - All Fields

### Required
- `name` (string): kebab-case, no spaces/capitals, must match folder name
- `description` (string): WHAT + WHEN + trigger phrases, max 1024 chars, no XML tags

### Optional
- `license` (string): e.g. MIT, Apache-2.0
- `compatibility` (string, 1-500 chars): Environment requirements (product, system packages, network)
- `allowed-tools` (string): Restrict tool access, e.g. `"Bash(python:*) Bash(npm:*) WebFetch"`
- `metadata` (object): Custom key-value pairs (author, version, mcp-server, category, tags, etc.)

## Security Restrictions

- NO XML angle brackets (< >) in frontmatter
- NO "claude" or "anthropic" in skill name (reserved)
- Reason: Frontmatter appears in system prompt, malicious content could inject instructions

## Description Formula

```
[What it does] + [When to use it] + [Key capabilities]
```

### Good Examples
```yaml
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".
```

### Bad Examples
```yaml
description: Helps with projects.  # Too vague
description: Creates sophisticated multi-page documentation systems.  # Missing triggers
description: Implements the Project entity model with hierarchical relationships.  # Too technical
```

### Negative Triggers
Prevent over-triggering by adding what the skill should NOT be used for:
```yaml
description: Advanced data analysis for CSV files. Use for statistical modeling, regression, clustering. Do NOT use for simple data exploration (use data-viz skill instead).
```

## Three Skill Categories

### Category 1: Document & Asset Creation
- Creating consistent, high-quality output (documents, presentations, apps, designs, code)
- Techniques: embedded style guides, template structures, quality checklists
- No external tools required

### Category 2: Workflow Automation
- Multi-step processes with consistent methodology
- Techniques: step-by-step workflow with validation gates, templates, iterative refinement loops

### Category 3: MCP Enhancement
- Workflow guidance on top of MCP tool access
- Techniques: coordinate multiple MCP calls, embed domain expertise, error handling

## Five Design Patterns

### Pattern 1: Sequential Workflow Orchestration
Use when: Multi-step processes in specific order.
- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

### Pattern 2: Multi-MCP Coordination
Use when: Workflows span multiple services.
- Clear phase separation
- Data passing between MCPs
- Validation before moving to next phase
- Centralized error handling

### Pattern 3: Iterative Refinement
Use when: Output quality improves with iteration.
- Explicit quality criteria
- Iterative improvement loop
- Validation scripts
- Know when to stop

### Pattern 4: Context-Aware Tool Selection
Use when: Same outcome, different tools depending on context.
- Clear decision criteria
- Fallback options
- Transparency about choices

### Pattern 5: Domain-Specific Intelligence
Use when: Skill adds specialized knowledge beyond tool access.
- Domain expertise embedded in logic
- Compliance/validation before action
- Comprehensive documentation
- Clear governance

## Size Guidelines

- SKILL.md: keep under 5,000 words
- Description: max 1024 characters
- Compatibility: 1-500 characters
- 20-50 skills simultaneously is reasonable maximum
- Move detailed docs to references/ (progressive disclosure)

## Troubleshooting

| Problem | Symptom | Fix |
|---------|---------|-----|
| Won't upload | "Could not find SKILL.md" | Rename to exactly SKILL.md (case-sensitive) |
| Won't upload | "Invalid frontmatter" | Check YAML --- delimiters, unclosed quotes |
| Won't upload | "Invalid skill name" | Use kebab-case, no spaces/capitals |
| Doesn't trigger | Never loads automatically | Revise description: add trigger phrases, be specific |
| Triggers too often | Loads for unrelated queries | Add negative triggers, clarify scope |
| MCP fails | Skill loads but calls fail | Check MCP connection, auth, tool names |
| Not followed | Loads but ignores instructions | Keep instructions concise, use headers, be specific |
| Slow/degraded | Large context | Reduce SKILL.md size, use references/ |

## Testing Checklist

### Before Upload
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works

### After Upload
- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Iterate on description and instructions
