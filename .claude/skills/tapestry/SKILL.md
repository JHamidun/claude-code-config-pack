---
name: tapestry
description: "Tapestry — knowledge weaving: связывает документы (YouTube-транскрипты, статьи, PDF, код) в интерлинкованный граф знаний + implementation plans. Триггеры: tapestry, weave, «свяжи документы», «граф знаний», «knowledge graph», «interlink docs»."
---

# Tapestry — Knowledge Weaving

> Use when: "tapestry", "weave", "свяжи документы", "граф знаний", "knowledge graph", "interlink docs"
> Interlinks documents into knowledge networks with implementation plans.

## Overview

Tapestry weaves learning content into actionable knowledge:
1. Extract content from any source (YouTube, articles, PDFs, code)
2. Identify connections and patterns between documents
3. Create interlinked knowledge graphs
4. Generate implementation plans from extracted knowledge

## Workflow

### Step 1: Extract Sources

```bash
# YouTube transcripts (existing skill: youtube-transcript.md)
# Articles (WebFetch tool)
# PDFs (existing skill: document-skills/pdf/)
# Code documentation (Glob + Read tools)
```

### Step 2: Weave Knowledge Graph

For each set of sources, create a knowledge map:

```markdown
## Knowledge Graph: [Topic]

### Core Concepts
1. **Concept A** — definition
   - Related to: Concept B, Concept D
   - Source: [video1], [article2]

2. **Concept B** — definition
   - Depends on: Concept A
   - Contradicts: Concept C (from [article3])
   - Source: [article1], [pdf1]

### Connections
- A → B: "A enables B because..."
- B ↔ D: "bidirectional relationship..."
- C conflicts with E: "different approaches to..."

### Gaps
- No source covers: [missing topic]
- Conflicting views on: [topic] between [source1] and [source2]

### Implementation Priority
1. [Most actionable insight] — from [source]
2. [Second priority] — from [source]
3. [Requires more research] — gap identified
```

### Step 3: Generate Action Plan

Transform knowledge graph into concrete steps:

```markdown
## Action Plan: [Topic]

### Phase 1: Foundation (from Concepts A, B)
- [ ] Task 1 — based on [source] insight
- [ ] Task 2 — addresses [gap]

### Phase 2: Implementation (from Concepts C, D)
- [ ] Task 3 — applies [pattern] from [source]
- [ ] Task 4 — resolves [conflict] between approaches

### Phase 3: Validation
- [ ] Verify against [source] recommendations
- [ ] Test [concept] in practice
```

## Usage Patterns

### Research Synthesis
```
"Weave these 5 articles about [topic] into a knowledge graph"
→ Extract key concepts → Find connections → Identify gaps → Action plan
```

### Documentation Audit
```
"Tapestry: analyze our docs/ folder for completeness"
→ Map all documented concepts → Find undocumented areas → Priority list
```

### Learning Path
```
"Create a learning path from these YouTube videos and articles"
→ Extract concepts → Order by dependency → Create study plan
```

### Competitive Analysis
```
"Weave competitor docs into comparison matrix"
→ Extract features → Map overlaps → Identify differentiators
```

## Integration with Existing Skills

| Source Type | Extraction Skill | Then |
|-------------|-----------------|------|
| YouTube | `youtube-transcript` | Tapestry weave |
| Articles | `content-research` | Tapestry weave |
| PDFs | `pdf` | Tapestry weave |
| Code | Agent `code-reviewer` | Tapestry weave |
| Meetings | `tldv` | Tapestry weave |

## Output Format

Knowledge graphs are saved as Markdown files in the project directory:
- `knowledge-graph-[topic].md` — the graph itself
- `action-plan-[topic].md` — generated action plan

## Notes

- Based on [tapestry-skills-for-claude-code](https://github.com/<author>/tapestry-skills-for-claude-code)
- Works best with 3-10 sources on a related topic
- Can be combined with vector_memory for persistent knowledge storage
- For visual graphs, use Mermaid diagrams or excalidraw-flowchart skill
