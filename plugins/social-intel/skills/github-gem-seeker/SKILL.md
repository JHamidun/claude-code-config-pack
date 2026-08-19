---
name: github-gem-seeker
description: "Find battle-tested open source on GitHub instead of coding from scratch. Triggers: «find a library», «ready-made solution», «find a repo»."
---

# GitHub Gem Seeker

Find and use battle-tested open source projects to solve problems immediately.

## Core Philosophy

Classic open source projects tested by thousands of users are far more reliable than code written from scratch. **Solve first, skill-ify later.**

## Workflow

### Step 1: Understand the Need

Clarify what the user wants. Ask only if truly ambiguous.

### Step 2: Find the Right Tool

Search GitHub using `gh` CLI and web search:

```bash
# Search repos
gh search repos "video download tool" --sort stars --limit 10
gh search repos "pdf manipulation python" --sort stars --limit 10

# Get repo info
gh repo view yt-dlp/yt-dlp --json stargazersCount,description,updatedAt
```

| Need Type | Query Pattern | Example |
|-----------|---------------|---------|
| Tool/utility | `github [task] tool` | `github video download tool` |
| Library | `github [language] [function] library` | `github python pdf library` |
| Alternative | `github [known-tool] alternative` | `github ffmpeg alternative` |

### Step 3: Evaluate Quality

| Indicator | Gem Signal | Warning Signal |
|-----------|------------|----------------|
| Stars | 1k+ solid, 10k+ excellent, 50k+ legendary | <100 for mature projects |
| Last commit | Within 6 months | >2 years ago |
| Documentation | Clear README, examples | Sparse or outdated |
| Issues | Active responses | Hundreds of unanswered issues |

### Step 4: Solve the Problem

1. Install the chosen tool (`pip install`, `npm install`, `apt install`)
2. Run it with user's input
3. Deliver the result
4. Troubleshoot if needed

### Step 5: Credit & Offer Next Steps

After success:

> "Powered by **[Project Name]** — https://github.com/org/repo
> Consider giving it a star to support the maintainers."

## Quality Tiers

| Tier | Stars | Examples |
|------|-------|---------|
| **Legendary** | 50k+ | FFmpeg, ImageMagick, yt-dlp, Puppeteer |
| **Excellent** | 10k+ | Pake, ArchiveBox, sharp, Scrapy |
| **Solid** | 1k+ | Most well-maintained tools |
| **Promising** | <1k | Active newer projects |

## Common Gems Reference

| Category | Go-to Gems |
|----------|------------|
| Video/Audio | FFmpeg, yt-dlp, Whisper |
| Image processing | ImageMagick, sharp, Pillow |
| PDF | pdf-lib, PyMuPDF (fitz), WeasyPrint |
| Web scraping | Playwright, Puppeteer, Scrapy, Beautiful Soup |
| Format conversion | Pandoc, FFmpeg, LibreOffice CLI |
| Archiving | ArchiveBox, wget |
| Desktop app | Electron, Tauri, Pake |
| Data processing | pandas, DuckDB, jq |
| Security | nmap, Burp Suite, sqlmap |
| DevOps | Terraform, Ansible, k9s |
