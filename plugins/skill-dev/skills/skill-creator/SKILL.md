---
name: skill-creator
description: Guide for creating effective skills following Anthropic's official best practices and Manus methodology. Use when users want to create a new skill, update an existing skill, or review skill quality. Covers YAML frontmatter, progressive disclosure, degrees of freedom, context window economy, 5 design patterns, trigger optimization, and troubleshooting.
license: Complete terms in LICENSE.txt
metadata:
  version: 3.0.0
  updated: (see git history)
type: actionable
---

# Skill Creator

This skill provides guidance for creating effective skills following Anthropic's official skill-building guide, enriched with Manus's skill-creator methodology.

For detailed patterns, troubleshooting, and YAML reference, consult `references/official-skill-guide.md`.

## Design Principles

### Context Window as Public Good

The context window is a shared resource. Skills share it with the system prompt, conversation history, other skills' metadata, and the actual user request. Every token a skill consumes is a token unavailable for reasoning, user data, or other skills.

Default assumption: **Claude is already very smart.** Only add context Claude does not already have.

When writing or reviewing skill content, challenge each piece of information:

- "Does Claude really need this explanation?"
- "Does this paragraph justify its token cost?"
- "Would Claude figure this out on its own?"

Prefer concise examples over verbose explanations. A 5-line code sample often conveys more than 3 paragraphs of prose.

### Degrees of Freedom

Match the level of specificity in skill instructions to the task's fragility and variability. Think of Claude as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many valid routes (high freedom).

| Level | Format | When to Use | Example |
|-------|--------|-------------|---------|
| **High freedom** | Text-based instructions, heuristics | Multiple approaches are valid, decisions depend on context | "Write tests covering edge cases" |
| **Medium freedom** | Pseudocode or scripts with parameters | A preferred pattern exists, some variation is acceptable | "Use pytest with fixtures; parametrize over input types" |
| **Low freedom** | Specific scripts, few or no parameters | Operations are fragile, consistency is critical, a specific sequence must be followed | `scripts/rotate_pdf.py --angle 90 --input file.pdf` |

When designing a skill, consciously decide the freedom level for each workflow step. Fragile operations (database migrations, file format conversions, deployment sequences) warrant low freedom. Creative tasks (writing, code architecture, naming) warrant high freedom.

### Feature-to-Value Mapping

When planning skill contents, think in terms of Feature-to-User Value pairs. Each skill feature should map to a specific user value it provides:

| Feature | User Value |
|---------|------------|
| `scripts/rotate_pdf.py` | Instant PDF rotation without rewriting code |
| `references/schema.md` | No need to rediscover DB schemas each session |
| `assets/hello-world/` | Skip boilerplate, start building immediately |

If a feature does not map to a clear user value, question whether it belongs in the skill.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks---they transform Claude from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```text
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   ├── description: (required)
│   │   ├── license: (optional)
│   │   ├── compatibility: (optional, 1-500 chars)
│   │   ├── allowed-tools: (optional, e.g. "Bash(python:*) WebFetch")
│   │   └── metadata: (optional, custom key-value pairs)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

**Important:** Do NOT include README.md, CHANGELOG.md, or other auxiliary documentation files. Skills are consumed by AI agents, not human users. All documentation belongs in SKILL.md or `references/`.

#### SKILL.md (required)

**Metadata Quality:** The `name` and `description` in YAML frontmatter determine when Claude will use the skill. Be specific about what the skill does and when to use it. Use the third-person (e.g. "This skill should be used when..." instead of "Use this skill when...").

**Description formula:** `[What it does] + [When to use it] + [Key capabilities]`

- Max 1024 characters, no XML tags
- Include specific trigger phrases users would say
- Add negative triggers to prevent over-triggering (e.g. "Do NOT use for...")

**Security restrictions:**

- NO XML angle brackets (< >) in frontmatter
- NO "claude" or "anthropic" in skill name (reserved by Anthropic)

**Size guidelines:** Keep SKILL.md under 500 lines / 5,000 words. When a skill grows beyond this, split content into `references/` files with clear descriptions in SKILL.md of when each reference should be read. Keep the core workflow in SKILL.md; move variant-specific details and domain-specific data to reference files.

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

- **When to include**: For documentation that Claude should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when Claude determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill---this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.

For multi-domain skills, organize references by domain:

```text
bigquery-skill/
├── SKILL.md (overview + navigation: "Read references/finance.md when query involves revenue tables")
└── references/
    ├── finance.md
    ├── sales.md
    └── product.md
```

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output Claude produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables Claude to use files without loading them into context
- **Naming note**: Some methodologies use `templates/` instead of `assets/` for template files. Both conventions are valid; this guide uses `assets/` consistently.

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by Claude (Unlimited*)

*Unlimited because scripts can be executed without reading into context window.

**Splitting guidelines:** When SKILL.md exceeds 500 lines, extract content to reference files. In SKILL.md, clearly describe when each reference file should be read, for example:

```markdown
## References

- `references/api-v2.md` - Read when working with API v2 endpoints
- `references/migration.md` - Read when migrating from v1 to v2
- `references/error-codes.md` - Read when debugging API errors
```

This allows Claude to load only the relevant reference at the right time, preserving context window for the actual task.

## Skill Creation Process

To create a skill, follow the "Skill Creation Process" in order, skipping steps only if there is a clear reason why they are not applicable.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

When gathering examples, map each to a Feature-to-User Value pair (see Design Principles above). This ensures every planned feature has a clear purpose.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly
3. For each identified resource, determining the appropriate degree of freedom (see Design Principles)

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill
3. PDF rotation is fragile and must follow a specific sequence --- low freedom (concrete script)

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill
3. The architecture on top of boilerplate varies per project --- high freedom (text guidelines)

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill
3. Query construction depends on the question --- medium freedom (pseudocode patterns with parameters)

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 3: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

Create the skill directory structure manually:

```bash
mkdir -p ~/.claude/skills/<skill-name>/{scripts,references,assets}
```

Then create `SKILL.md` with the required YAML frontmatter:

```markdown
---
name: <skill-name>
description: <What it does. When to use it. Key capabilities.>
metadata:
  version: 1.0.0
  updated: <YYYY-MM-DD>
---

# <Skill Name>

<!-- TODO: Overview -->

## When to Use

<!-- TODO: Trigger phrases -->

## Workflow

<!-- TODO: Core instructions -->
```

Remove any subdirectories (`scripts/`, `references/`, `assets/`) that the skill does not need. Only keep what will be populated with actual content.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Focus on including information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

Apply the "Context Window as Public Good" principle: every line in SKILL.md must earn its place. If Claude already knows how to do something (e.g., write a for-loop, parse JSON), do not explain it. Focus on what Claude does not know: your specific schemas, your team's conventions, fragile sequences that must be followed exactly.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Also, delete any example files and directories not needed for the skill.

#### Update SKILL.md

**Writing Style:** Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X" or "If you need to do X"). This maintains consistency and clarity for AI consumption.

To complete SKILL.md, answer the following questions:

1. What is the purpose of the skill, in a few sentences?
2. When should the skill be used?
3. In practice, how should Claude use the skill? All reusable skill contents developed above should be referenced so that Claude knows how to use them.

### Step 5: Validate and Publish

Once the skill is ready, validate it by testing with a real prompt that should trigger the skill:

1. Save the skill to `~/.claude/skills/<skill-name>/`
2. Start a new Claude Code session (or reload skills)
3. Issue a prompt that matches the skill's trigger phrases
4. Verify Claude picks up the skill and follows its instructions correctly
5. Check that outputs match expectations

The skill becomes available immediately after saving to `~/.claude/skills/`.

**Validation checklist:**

- YAML frontmatter has `name` and `description`
- No XML angle brackets in frontmatter
- Skill name does not contain "claude" or "anthropic"
- Description is under 1024 characters
- SKILL.md is under 500 lines
- All referenced scripts/references/assets exist
- No README.md or CHANGELOG.md in the skill directory

### Step 5b: Register in System (MANDATORY)

After saving the skill, register it in the routing and navigation files:

1. **Add to `~/.claude/rules/routing.md`** — add a row to the routing table:
   ```
   | Category | "trigger1", "trigger2" | Skill `skill-name` |
   ```

2. **Update `~/CLAUDE.md`** — increment skill count in the tools table and add reference if the skill is a major integration (config section or docs section).

3. **Update `~/.claude/config/` if needed** — add relevant config file for new service credentials or connections.

Skipping this step means the skill won't be auto-routed on trigger phrases.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again

## Best Practices

### 0. Economy of Tokens

Before all other best practices, remember that the context window is shared. Apply these filters to every piece of content:

- **Delete what Claude already knows.** Do not explain standard library functions, common patterns, or well-known conventions.
- **Compress what remains.** Replace paragraphs with tables. Replace explanations with examples. Replace examples with one-liners when possible.
- **Measure the cost.** A 200-word section costs ~300 tokens. Does it save more than 300 tokens of confusion or error-correction downstream?

### 1. Clear Naming

Use descriptive, unique names that clearly indicate the skill's purpose.

```yaml
# Good
name: git-workflow
description: Git operations - commits, branches, PRs, merge conflicts

# Bad
name: git-stuff
description: Git things
```

### 2. Specific Triggers

Define specific, actionable triggers that clearly indicate when the skill should be used.

```yaml
# Good - specific triggers
## When to Use
- Creating commit messages following Conventional Commits
- Resolving merge conflicts
- Setting up branch protection rules
- Squashing commits before merge

# Bad - vague triggers
## When to Use
- Git stuff
- When working with code
```

### 3. Actionable Instructions

Provide step-by-step instructions that are clear and actionable.

```yaml
# Good - step by step
## Creating a Release

1. Update version in package.json
2. Run `npm run changelog` to generate CHANGELOG
3. Create release commit: `git commit -m "chore: release v1.2.0"`
4. Tag the release: `git tag v1.2.0`
5. Push with tags: `git push --follow-tags`

# Bad - no steps
## Creating a Release
Make a release when ready
```

### 4. Code Examples

Include real, working code examples that demonstrate the skill's usage.

```yaml
# Good - real examples
## API Usage

```python
import requests

response = requests.post(
    "https://api.example.com/users",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"name": "John", "email": "john@example.com"}
)
user = response.json()
print(f"Created user: {user['id']}")
```

# Bad - pseudo-code
## API Usage
Call the API with your data
```

### 5. Error Handling

Document common errors and their solutions.

```yaml
## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check API_KEY in .env |
| 429 Rate Limited | Too many requests | Add delay between calls |
| 500 Server Error | API issue | Retry with exponential backoff |
```

## Skill Template

Complete markdown template for creating new skills:

```markdown
---
name: [skill-name]
description: [One line description - when Claude should use this]
---

# [Skill Name]

## Overview

[2-3 sentences about what this skill does]

## When to Use

- [Specific trigger 1]
- [Specific trigger 2]
- [Specific trigger 3]

## Prerequisites

- [Requirement 1]
- [Requirement 2]

## Quick Start

```python
# Minimal working example
[code]
```

## Core Functions

### [Function 1]

[Description]

```python
[Code example]
```

### [Function 2]

[Description]

```python
[Code example]
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VAR_1` | [Description] | [Value] |
| `VAR_2` | [Description] | [Value] |

## Common Patterns

### [Pattern 1]

[Description and example]

### [Pattern 2]

[Description and example]

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| [Error] | [Cause] | [Solution] |

## Integration Examples

### With [Other Tool/Skill]

[Example of combining skills]

## Tips

1. [Tip 1]
2. [Tip 2]
3. [Tip 3]

## References

- [Link 1]
- [Link 2]
```

## Skill Categories

### API Integration Skills

Focus on:
- Authentication methods
- Endpoint documentation
- Request/response examples
- Rate limiting
- Error codes

### Workflow Skills

Focus on:
- Step-by-step processes
- Decision trees
- Checklists
- Templates

### Tool Skills

Focus on:
- Installation
- CLI commands
- Configuration
- Common use cases

### Methodology Skills

Focus on:
- Principles
- Techniques
- When to apply
- Examples

## File Organization

Recommended directory structure for organizing skills:

```text
.claude/skills/
├── ai-models/           # AI API integrations
│   ├── openai.md
│   ├── anthropic.md
│   └── gemini.md
├── development/         # Dev tools & practices
│   ├── git-workflow.md
│   ├── tdd.md
│   └── code-review.md
├── business/           # Business processes
│   ├── invoicing.md
│   └── leads.md
└── automation/         # Automation tools
    ├── n8n.md
    └── playwright.md
```

## Testing Your Skill

### Manual Test

1. Save skill to `~/.claude/skills/<skill-name>/`
2. Start a new session or reload
3. Ask Claude: "[trigger phrase]"
4. Verify Claude uses the skill correctly
5. Check outputs match expectations

### Checklist

- [ ] Name is descriptive and unique
- [ ] Description fits in one line (<1024 chars)
- [ ] Triggers are specific
- [ ] Has working code examples
- [ ] Error cases documented
- [ ] All referenced files exist
- [ ] No README.md or CHANGELOG.md included
- [ ] SKILL.md under 500 lines
- [ ] Every section earns its token cost
- [ ] Degrees of freedom match task fragility
- [ ] Tested with Claude

## Updating Skills

### When to Update

- API changes
- New features discovered
- Bug fixes
- Better examples found
- User feedback

### Version Notes

Track changes using comments in the skill file:

```markdown
<!-- Changelog -->
<!-- v1.1 - Added rate limiting section -->
<!-- v1.0 - Initial version -->
```

## Common Mistakes

### Too Vague

```markdown
## When to Use
Use this for API stuff
```

**Fix --- be specific:**

```markdown
## When to Use
- Generating API documentation from OpenAPI spec
- Creating Postman collections
- Mocking API endpoints for testing
```

### No Examples

```markdown
## Authentication
Use OAuth2 to authenticate
```

**Fix --- add working code:**

```markdown
## Authentication

```python
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

client = BackendApplicationClient(client_id=CLIENT_ID)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(
    token_url='https://api.example.com/oauth/token',
    client_secret=CLIENT_SECRET
)
```
```

### Explaining What Claude Already Knows

```markdown
## JSON Parsing
JSON (JavaScript Object Notation) is a lightweight data format.
To parse JSON in Python, use the json module. First import it
with `import json`, then call `json.loads()` on a string...
```

**Fix --- skip to what matters:**

```markdown
## Response Format
API returns JSON with nested `data.items[]` array. Each item has
`id` (int), `status` (enum: active|archived), `metadata` (object).
```

### Wrong Degree of Freedom

```markdown
## Database Migration
Run the migration however you think is best.
```

**Fix --- fragile operations need low freedom:**

```markdown
## Database Migration
1. Back up: `pg_dump -Fc mydb > backup_$(date +%Y%m%d).dump`
2. Run migration: `python scripts/migrate.py --target v2`
3. Verify: `python scripts/verify_schema.py`
4. If verification fails: `pg_restore -d mydb backup_*.dump`
```

## Tips

1. **Start simple** - Add details as needed
2. **Real examples** - Use working code
3. **Update regularly** - Skills should remain current
4. **Test with Claude** - Verify that Claude understands
5. **Cross-reference** - Link to related skills
6. **Token budget** - Treat every line as spending shared context
7. **Match specificity to fragility** - Tight scripts for fragile ops, loose guidance for creative tasks
