> Справочник, читается по требованию (не в авто-load промпта). Перенесён из rules/ 2026-07-18.

# Headless & CI/CD Integration

## Headless Mode Basics
Claude Code can run without interactive input using `claude -p`:

```bash
# One-shot query (prints result and exits)
claude -p "Explain the main function in src/app.ts"

# Pipe input
cat error.log | claude -p "Analyze this error log and suggest fixes"

# With specific model
claude -p --model sonnet "Quick code review of src/utils.ts"
```

## Common CI/CD Patterns

### PR Description Generator
```bash
# In GitHub Actions:
git diff main...HEAD | claude -p "Write a PR description for these changes"
```

### Automated Code Review
```bash
claude -p "Review the changes in the last commit for security issues. Output JSON with {issues: [{file, line, severity, description}]}"
```

### Changelog Generation
```bash
claude -p "Generate a changelog entry from the last 5 commits" > CHANGELOG_ENTRY.md
```

### Test Generation
```bash
claude -p "Write unit tests for src/new-feature.ts using Vitest"
```

## GitHub Actions Example
```yaml
name: Claude Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Claude
        run: npm install -g @anthropic-ai/claude-code
      - name: Run Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          git diff origin/main...HEAD | claude -p "Review these changes" > review.md
          gh pr comment ${{ github.event.number }} --body-file review.md
```

## Output Parsing
- Use `--output-format json` for structured output
- Use `-p` flag to suppress interactive prompts
- Pipe output to files or other commands
- Exit code 0 = success, non-zero = error

## Environment Variables
- `ANTHROPIC_API_KEY` — required for API auth
- `CLAUDE_MODEL` — override default model
- `CLAUDE_MAX_TOKENS` — limit response length

## Limitations
- No interactive tools (no user prompts, no browser)
- No MCP servers that require user interaction
- Context limited to single invocation (no session)
- No hooks that require user approval

## Tips
- Keep prompts focused — one task per invocation
- Use JSON output format when parsing results programmatically
- Set timeouts in CI to avoid hanging on large codebases
- Cache Claude Code installation in CI for faster runs
- Use `--allowedTools` to restrict which tools Claude can use in CI
- Combine with `git diff` for targeted reviews instead of full repo scans
