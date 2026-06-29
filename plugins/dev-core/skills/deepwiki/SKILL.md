---
name: deepwiki
description: Fetch documentation for any GitHub repository via DeepWiki/gitmcp.io. Use when user needs docs for a specific GitHub repo (not npm packages - use Context7 for those).
---

# DeepWiki: GitHub Repository Documentation

Fetch and analyze documentation for any GitHub repository.

## When to Use

- **DeepWiki**: Any GitHub repository documentation
- **Context7** (separate skill): npm/pypi packages with published docs

## Methods

### Method 1: gitmcp.io (preferred)
Convert any GitHub URL to gitmcp.io format:
```
https://github.com/{owner}/{repo} -> https://gitmcp.io/{owner}/{repo}
```

Fetch via WebFetch:
```
WebFetch: https://gitmcp.io/{owner}/{repo}
Prompt: "Get the main documentation, API reference, and getting started guide"
```

### Method 2: Raw GitHub README
```
WebFetch: https://raw.githubusercontent.com/{owner}/{repo}/main/README.md
```

### Method 3: GitHub API
```bash
gh api repos/{owner}/{repo}/readme --jq '.content' | base64 -d
```

## Process

1. User provides GitHub repo URL or name
2. Fetch documentation using Method 1 (gitmcp.io)
3. If fails, fallback to Method 2 or 3
4. Summarize key sections: setup, API, examples
5. Answer user's specific questions about the repo

## Examples

```
User: "документация для langchain"
-> WebFetch https://gitmcp.io/langchain-ai/langchain

User: "как использовать playwright python"
-> WebFetch https://gitmcp.io/microsoft/playwright-python
```

## Notes
- For npm packages, use Context7 MCP instead
- For private repos, use `gh` CLI with authenticated access
- Cache results in memory for repeated queries
