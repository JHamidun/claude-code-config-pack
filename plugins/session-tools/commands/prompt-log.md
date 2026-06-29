---
name: prompt-log
description: Analyze Claude Code session statistics - tokens, tool calls, prompt patterns. Use with /prompt-log or "статистика сессий".
---

# Prompt Log Analyzer

Parse Claude Code session JSONL files and extract usage statistics.

## Data Source

Session files: `~/.claude/projects/*/*.jsonl`

## Analysis Steps

### 1. Find Recent Sessions
```bash
powershell -c "Get-ChildItem -Path $env:USERPROFILE\.claude\projects -Recurse -Filter '*.jsonl' | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | Format-Table Name, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime"
```

### 2. Parse Session Data
For each JSONL file, extract:
- **Message count** — total messages in session
- **Tool calls** — which tools were used and how often
- **Session duration** — first to last timestamp
- **File size** — proxy for token usage

### 3. Aggregate Statistics
```bash
powershell -c @"
$files = Get-ChildItem -Path $env:USERPROFILE\.claude\projects -Recurse -Filter '*.jsonl'
$totalSize = ($files | Measure-Object -Property Length -Sum).Sum
$count = $files.Count
Write-Output "Total sessions: $count"
Write-Output "Total size: $([math]::Round($totalSize/1MB, 2)) MB"
Write-Output "Avg session: $([math]::Round($totalSize/$count/1KB, 1)) KB"
"@
```

## Report Format

```markdown
# Session Statistics

## Overview
- Total sessions: N
- Total data: X MB
- Average session size: Y KB
- Date range: [first] - [last]

## Recent Sessions (last 10)
| Date | Size | Duration |
|------|------|----------|

## Tool Usage (top 10)
| Tool | Count | % of total |
|------|-------|------------|

## Patterns
- Most active day of week: [day]
- Average session size trend: [growing/stable/shrinking]
- Most used agents: [list]

## Recommendations
- [Based on patterns]
```

## Process

1. Scan all JSONL files in projects directory
2. Parse recent files for detailed analysis
3. Calculate aggregated statistics
4. Identify patterns and trends
5. Generate report
6. Optionally save insights to vector memory
