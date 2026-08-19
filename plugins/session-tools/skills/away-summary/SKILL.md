---
name: away-summary
description: "Recap the current session — what was done, where you stopped. Triggers: «recap», «while you were away», resuming after a break."
triggers:
  - "away summary"
  - "что я делал"
  - "где я остановился"
  - "recap"
  - "while you were away"
---

# Away Summary

Generate a short session recap for returning after a break.

## Rules

1. Write exactly 1-3 short sentences
2. Start by stating the **high-level task** — what was being built or debugged, not implementation details
3. Then: the **concrete next step**
4. Skip status reports and commit recaps
5. Use only the last ~30 messages for context

## Example Output

> Building the admin panel with AI chat integration. Next: test the briefing cron job and verify collector scheduling.

## How to Generate

1. Look at the recent conversation context
2. Identify the main task/goal
3. Identify where work left off
4. Write 1-3 sentences following the rules above
