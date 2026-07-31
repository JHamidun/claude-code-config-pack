---
description: Process call notes or a transcript — extract action items, draft follow-up email, generate internal summary
argument-hint: "<call notes or transcript>"
---

# /call-summary

> If you see unfamiliar placeholders or need to check which tools are connected, see the MCP registry: `~/.claude/config/mcp-servers.md`.

Process call notes or a transcript to extract action items, draft follow-up communications, and update records.

## Usage

```
/call-summary <notes or transcript>
```

Process these call notes: $ARGUMENTS

If a file is referenced: @$1

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      CALL SUMMARY                                │
├─────────────────────────────────────────────────────────────────┤
│  STANDALONE (always works)                                       │
│  ✓ Paste call notes or transcript                               │
│  ✓ Extract key discussion points and decisions                  │
│  ✓ Identify action items with owners and due dates              │
│  ✓ Surface objections, concerns, and open questions             │
│  ✓ Draft customer-facing follow-up email                        │
│  ✓ Generate internal summary for your team                      │
├─────────────────────────────────────────────────────────────────┤
│  SUPERCHARGED (when you connect your tools)                      │
│  + Transcripts: Pull recording automatically (e.g. Gong, Fireflies) │
│  + CRM: Update opportunity, log activity, create tasks          │
│  + Email: Send follow-up directly from draft                    │
│  + Calendar: Link to meeting, pull attendee context             │
└─────────────────────────────────────────────────────────────────┘
```

---

## What I Need From You

**Option 1: Paste your notes**
Just paste whatever you have — bullet points, rough notes, stream of consciousness. I'll structure it.

**Option 2: Paste a transcript**
If you have a full transcript from your video conferencing tool (e.g. Zoom, Teams) or conversation intelligence tool (e.g. Gong, Fireflies), paste it. I'll extract the key moments.

**Option 3: Describe the call**
Tell me what happened: "Had a discovery call with Acme Corp. Met with their VP Eng and CTO. They're evaluating us vs Competitor X. Main concern is integration timeline."

---

## Output

### Internal Summary
```markdown
## Call Summary: [Company] — [Date]

**Attendees:** [Names and titles]
**Call Type:** [Discovery / Demo / Negotiation / Check-in]
**Duration:** [If known]

### Key Discussion Points
1. [Topic] — [What was discussed, decisions made]
2. [Topic] — [Summary]

### Customer Priorities
- [Priority 1 they expressed]
- [Priority 2]

### Objections / Concerns Raised
- [Concern] — [How you addressed it / status]

### Competitive Intel
- [Any competitor mentions, what was said]

### Action Items
| Owner | Action | Due |
|-------|--------|-----|
| [You] | [Task] | [Date] |
| [Customer] | [Task] | [Date] |

### Next Steps
- [Agreed next step with timeline]

### Deal Impact
- [How this call affects the opportunity — stage change, risk, acceleration]
```

### Customer Follow-Up Email
```
Subject: [Meeting recap + next steps]

Hi [Name],

Thank you for taking the time to meet today...

[Key points discussed]

[Commitments you made]

[Clear next step with timeline]

Best,
[You]
```

---

## Email Style Guidelines

When drafting customer-facing emails:

1. **Be concise but informative** — Get to the point quickly. Customers are busy.
2. **No markdown formatting** — Don't use asterisks, bold, or other markdown syntax. Write in plain text that looks natural in any email client.
3. **Use simple structure** — Short paragraphs, line breaks between sections. No headers or bullet formatting unless the customer's email client will render it.
4. **Keep it scannable** — If listing items, use plain dashes or numbers, not fancy formatting.

**Good:**
```
Here's what we discussed:
- Quote for 20 seats at $480/seat/year
- W9 and supplier onboarding docs
- Point of contact for the contract
```

**Bad:**
```
**What You Need from Us:**
- Quote for 20 seats at $480/seat/year
```

---

## If Connectors Available

**Transcripts connected (e.g. Gong, Fireflies):**
- I'll search for the call automatically
- Pull the full transcript
- Extract key moments flagged by the platform

**CRM connected:**
- I'll offer to update the opportunity stage
- Log the call as an activity
- Create tasks for action items
- Update next steps field

**Email connected:**
- I'll offer to create a draft in email
- Or send directly if you approve

---

## Tips

1. **More detail = better output** — Even rough notes help. "They seemed concerned about X" is useful context.
2. **Name the attendees** — Helps me structure the summary and assign action items.
3. **Flag what matters** — If something was important, tell me: "The big thing was..."
4. **Tell me the deal stage** — Helps me tailor the follow-up tone and next steps.

---

## Transcript Auto-Fetch

Before asking for manual input, attempt to fetch the transcript automatically.

Sources (checked in order):

1. **tl;dv skill** — fetch transcript by meeting title, date, or attendee name. Use skill `tldv` to list recent meetings and pull the matching transcript.
2. **Paste raw transcript text** — if auto-fetch fails, accept pasted text from Zoom, Teams, Google Meet, or any conferencing tool.
3. **Upload audio file** — if only a recording exists, use the `transcribe` command (Deepgram skill) to convert audio to text first, then process the resulting transcript.

```
# Auto-fetch flow:
if tldv available:
    search meetings by title/date → pull transcript
elif user pastes text:
    use as-is
elif user provides audio file:
    /transcribe <file> → get transcript → process
```

---

## CRM Integration

When CRM is available, automatically sync call results.

### Auto-detect deal

- Scan transcript for company names, project names, deal references
- Match against existing CRM deals (search by company name or deal title)
- If multiple matches found, ask user to confirm

### Fields to update

| CRM Field | Source |
|----------------|--------|
| `last_activity_date` | Meeting date (today if not specified) |
| `next_steps` | Extracted next steps from transcript |
| `notes` | Internal summary (appended, not overwritten) |

### Actions

1. **Create activity log** — log the call as a completed activity in the matched deal, including attendees, duration, and summary
2. **Update deal stage** — if the transcript indicates progression (e.g., "they agreed to a pilot", "contract sent", "deal closed"), suggest stage change and confirm with user before applying
3. **Create tasks** — for each action item assigned to our team, create a CRM task linked to the deal

```
# CRM update flow:
deal = detect_deal_from_transcript(transcript)
if deal:
    crm.add_activity(deal_id, type="call", summary=internal_summary)
    crm.update(deal_id, last_activity_date=today, next_steps=next_steps, notes+=summary)
    if stage_change_detected:
        confirm_with_user → crm.update_stage(deal_id, new_stage)
    for item in our_action_items:
        crm.create_task(deal_id, title=item.action, responsible=item.owner, deadline=item.due)
```

---

## Follow-up Email Draft

Generate a professional follow-up email immediately after processing the transcript.

### Template

```
Subject: Follow-up: [Meeting Topic] — [Date]

Hi [Name],

Thank you for taking the time to meet [today / on Date]. It was great connecting
with [you / you and the team].

Here is a quick recap of what we discussed:

[Key decisions — 2-4 bullet points, plain text]

Action items on our side:
- [Our commitment 1 — with timeline]
- [Our commitment 2 — with timeline]

We agreed on the following next steps:
- [Next step with owner and date]

[Optional: anything they committed to, phrased diplomatically]

Looking forward to [next interaction]. Please let me know if I missed anything
or if you have any questions.

Best regards,
[Your name]
```

### Guidelines

- **Tone**: professional, concise, warm but not overly casual
- **Always include**: meeting date, attendees referenced, key decisions, action items, next steps
- **Never include**: internal notes, competitive intel, deal stage assessments, pricing strategy
- **Length**: 150-250 words max — respect the recipient's time
- **No markdown** in the email body (per Email Style Guidelines above)

---

## Action Items Extraction

Systematically extract every commitment made during the call.

### Detection patterns

Look for these signals in the transcript:

- **Explicit**: "[Person] will [action] by [date]"
- **Commitment verbs**: "I'll send", "we'll prepare", "let me follow up", "I can share"
- **Requests**: "Could you send us...", "We'll need...", "Please provide..."
- **Deadlines**: "by Friday", "next week", "before the next call", "end of month"
- **Implicit**: "That's on my list", "I'll take care of that", "Let me check"

### Output format

```markdown
## Action Items

- [ ] **[Owner Name]** — [Action description] — Due: [Date or "TBD"]
- [ ] **[Owner Name]** — [Action description] — Due: [Date or "TBD"]
- [ ] **[Owner Name]** — [Action description] — Due: [Date or "TBD"]
```

### Task creation

When project management tools are connected:

| Tool | Action |
|------|--------|
| **Linear** | Create issue per action item, assign to team member, set due date, link to project |
| **Your CRM** | Create task linked to deal, set responsible, set deadline, add to sprint if applicable |

### Rules

1. Every action item MUST have an **owner** — if unclear from transcript, ask the user
2. Every action item SHOULD have a **deadline** — if not mentioned, mark as "TBD" and flag for user
3. Separate **our items** vs **their items** — different follow-up workflows
4. If more than 5 action items, group by owner or by topic
5. Flag any item that seems blocked or dependent on another item
