---
name: internal-comms
description: "Internal comms in company formats: status reports, leadership/3P updates, newsletters, FAQs, incident reports. Triggers: «team update», «status report»."
license: Complete terms in LICENSE.txt
---

## When to use this skill
To write internal communications, use this skill for:
- 3P updates (Progress, Plans, Problems)
- Company newsletters
- FAQ responses
- Status reports
- Leadership updates
- Project updates
- Incident reports

## How to use this skill

To write any internal communication:

1. **Identify the communication type** from the request
2. **Load the appropriate guideline file** from the `examples/` directory:
    - `examples/3p-updates.md` - For Progress/Plans/Problems team updates
    - `examples/company-newsletter.md` - For company-wide newsletters
    - `examples/faq-answers.md` - For answering frequently asked questions
    - `examples/general-comms.md` - For anything else that doesn't explicitly match one of the above
3. **Follow the specific instructions** in that file for formatting, tone, and content gathering

If the communication type doesn't match any existing guideline, use the templates below as a starting point.

## Status Report Template

```markdown
# Weekly Status Report
**Period:** [Week of MMM DD, YYYY]
**Author:** [Name]
**Team:** [Team Name]

## TL;DR
[1-2 sentences summary]

## Accomplishments This Week
- ✅ [Achievement 1 with metrics if possible]
- ✅ [Achievement 2]
- ✅ [Achievement 3]

## In Progress
- 🔄 [Task 1] - [X]% complete, ETA [date]
- 🔄 [Task 2] - blocked by [blocker]

## Planned for Next Week
- [ ] [Priority 1]
- [ ] [Priority 2]
- [ ] [Priority 3]

## Blockers / Risks
- 🚧 [Blocker 1] - need [action] from [person/team]
- ⚠️ [Risk 1] - mitigation: [plan]

## Metrics
| Metric | Last Week | This Week | Change |
|--------|-----------|-----------|--------|
| [Metric 1] | [X] | [Y] | [+/-Z%] |
| [Metric 2] | [X] | [Y] | [+/-Z%] |

## Team Updates
- [Team member] on PTO [dates]
- New hire: [Name] joining as [Role]
```

## Executive Update Template

```markdown
# Executive Update: [Topic]
**Date:** [Date]
**From:** [Name, Title]
**To:** Leadership Team

## Executive Summary
[2-3 sentences - the most important points]

## Key Highlights
1. **[Topic 1]:** [One sentence with key metric]
2. **[Topic 2]:** [One sentence with key metric]
3. **[Topic 3]:** [One sentence with key metric]

## Business Impact
- Revenue impact: $[X]
- Customer impact: [Y] customers affected
- Timeline impact: [Z] days saved/delayed

## Decisions Needed
1. [Decision 1] - Deadline: [Date]
   - Option A: [Pros/Cons]
   - Option B: [Pros/Cons]
   - **Recommendation:** Option [X]

## Next Steps
1. [Action] - Owner: [Name] - Due: [Date]
2. [Action] - Owner: [Name] - Due: [Date]

## Appendix
[Detailed data for those who want more]
```

## Newsletter Template

```markdown
# [Company] Newsletter
**Edition:** [Month Year] | **Issue #[X]**

---

## 📢 Headline Story
### [Title]
[Engaging 2-3 paragraphs about the main story]

---

## 🎉 Wins & Celebrations

### Team Accomplishments
- **[Team A]:** [Achievement]
- **[Team B]:** [Achievement]

### Employee Spotlights
**[Name]** - [Title]
[2-3 sentences about their recent contribution]

---

## 📅 Upcoming Events
| Date | Event | Location |
|------|-------|----------|
| [Date] | [Event] | [Location/Virtual] |

---

## 💡 Did You Know?
[Fun fact or useful tip about the company/industry]

---

## 📊 Numbers That Matter
- **[Metric]:** [Value] ([change] from last month)
- **[Metric]:** [Value]

---

## 🔗 Quick Links
- [Resource 1](link)
- [Resource 2](link)

---

*Have something to share? Email [newsletter@company.com]*
```

## Incident Report Template

```markdown
# Incident Report: [Title]

**Severity:** [P0/P1/P2/P3]
**Date:** [Date & Time]
**Duration:** [X hours/minutes]
**Author:** [Name]

## Summary
[2-3 sentences describing what happened]

## Timeline (All times in UTC)
| Time | Event |
|------|-------|
| HH:MM | [Initial trigger/alert] |
| HH:MM | [First response action] |
| HH:MM | [Escalation/notification] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Full resolution] |

## Impact
- **Users affected:** [Number/percentage]
- **Services affected:** [List]
- **Revenue impact:** $[Amount] (estimated)
- **SLA impact:** [Yes/No - details]

## Root Cause
[Technical explanation of what caused the incident]

## Resolution
[What was done to fix the immediate issue]

## Lessons Learned
### What went well
- [Positive 1]
- [Positive 2]

### What could be improved
- [Improvement 1]
- [Improvement 2]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action 1] | [Name] | [Date] | [Status] |
| [Action 2] | [Name] | [Date] | [Status] |

## Prevention
[How we'll prevent this from happening again]
```

## Project Update Template

```markdown
# Project Update: [Project Name]
**Date:** [Date]
**Project Lead:** [Name]
**Status:** 🟢 On Track / 🟡 At Risk / 🔴 Off Track

## Progress Overview
[2-3 sentences on overall status]

**Overall Progress:** [XX]% complete

## Milestone Status
| Milestone | Target Date | Status | Notes |
|-----------|-------------|--------|-------|
| [Milestone 1] | [Date] | ✅ Complete | |
| [Milestone 2] | [Date] | 🔄 In Progress | [X]% |
| [Milestone 3] | [Date] | ⏳ Upcoming | |

## This Period's Achievements
- [Achievement 1]
- [Achievement 2]

## Risks & Issues
| Risk/Issue | Severity | Mitigation | Owner |
|------------|----------|------------|-------|
| [Risk 1] | High | [Plan] | [Name] |

## Budget Status
- Allocated: $[X]
- Spent: $[Y] ([Z]%)
- Remaining: $[W]

## Resource Status
- Team capacity: [X]%
- Additional needs: [Description]

## Next Steps
1. [Next action 1]
2. [Next action 2]
```

## Announcement Template

```markdown
# 📢 [Announcement Title]

**Effective Date:** [Date]
**From:** [Name/Department]

---

## What's Happening
[Clear explanation of the change/news]

## Why This Matters
[Context and rationale]

## What You Need to Do
1. [Action 1]
2. [Action 2]

## Timeline
- **[Date]:** [Event/milestone]
- **[Date]:** [Event/milestone]

## FAQs

**Q: [Common question 1]?**
A: [Answer]

**Q: [Common question 2]?**
A: [Answer]

## Questions?
Contact [Name/Team] at [email/Slack]

---

*Thank you for your attention to this matter.*
```

## Writing Tips

### Tone Guidelines

```markdown
✅ Do:
- Be clear and concise
- Use active voice
- Lead with the most important info
- Include specific data/metrics
- Provide clear next steps

❌ Don't:
- Use jargon without explanation
- Bury the lead
- Be vague about timelines
- Skip the "so what"
- Assume everyone has context
```

### Structure

```markdown
1. **Lead with TL;DR** - busy readers first
2. **Use headers** - scannable structure
3. **Bullet points** - easier to read
4. **Tables for data** - clear comparisons
5. **Bold key info** - highlights important
6. **End with actions** - what's next
```

### Email Subject Lines

```markdown
✅ Good:
- "[Action Required] Q4 Budget Review - Due Oct 15"
- "Weekly Update: Engineering (Oct 7-13)"
- "[FYI] New PTO Policy Effective Nov 1"
- "🎉 We Hit $1M ARR!"

❌ Bad:
- "Update"
- "Please read"
- "Important"
- "FYI"
```

## Tips

1. **Know your audience** - executives vs team vs all-hands
2. **TL;DR first** - respect busy readers
3. **Be specific** - numbers > vague statements
4. **Action-oriented** - clear next steps
5. **Consistent format** - templates save time
6. **Proofread** - typos undermine credibility

## Keywords
3P updates, company newsletter, company comms, weekly update, faqs, common questions, updates, internal comms
