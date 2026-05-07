---
name: self-reflect
description: Self-improvement analysis - review recent errors, find patterns, generate improvements for rules/skills. Use with "проанализируй себя", "self-reflect".
---

# Self-Reflect: Continuous Improvement

Analyze past sessions and errors to generate actionable improvements.

## Process

### Phase 1: Gather Data

1. **Recent errors from memory**:
```bash
python ${WORKSPACE}/tools/vector_memory.py search "ошибка error fix bug" --limit 10
```

2. **Recent decisions**:
```bash
python ${WORKSPACE}/tools/vector_memory.py search "решение выбрали decided" --limit 10
```

3. **Recent learnings**:
```bash
python ${WORKSPACE}/tools/vector_memory.py search "learned паттерн pattern" --limit 10
```

4. **Subagent usage patterns**:
```bash
powershell -c "Get-Content $env:USERPROFILE\.claude\logs\subagents.log -Tail 50"
```

### Phase 2: Analyze Patterns

For each error/issue found:
1. Has this type of error occurred before?
2. What was the root cause?
3. Could a rule/skill/hook have prevented it?
4. What's the fix pattern?

### Phase 3: Generate Improvements

Categories:
- **New rule** -> add to `~/.claude/rules/`
- **Updated routing** -> modify `routing.md`
- **New skill** -> add to `~/.claude/skills/`
- **Hook adjustment** -> modify `settings.json`
- **Memory entry** -> save via vector_memory

### Phase 4: Apply & Save

For each improvement:
```bash
python ${WORKSPACE}/tools/vector_memory.py learn "[improvement description]" "self-improvement"
```

## Report Format

```markdown
# Self-Reflection Report

## Errors Analyzed
1. [Error] -> [Root cause] -> [Fix applied]

## Recurring Patterns
- Pattern: [description]
  - Frequency: N times
  - Improvement: [what to change]

## Improvements Generated
- [ ] [Rule/skill/hook change description]

## Metrics
- Errors analyzed: N
- Patterns found: N
- Improvements proposed: N
```

## Rules
- Be honest about mistakes
- Focus on systemic fixes, not one-off patches
- Prioritize by frequency x impact
- Always save findings to vector memory
