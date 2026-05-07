# Workflow: Follow Up

> Проверка статуса, напоминания, follow-up после действий

## Keywords
`follow up`, `напомнить`, `проверить статус`, `check in`, `bump`, `ping`

## Inputs
- **task**: описание задачи из Todoist
- **target**: кому/что follow up
- **context**: о чём изначально шла речь
- **urgency**: low | medium | high

## Steps

### 1. Retrieve Context
```
Tool: Memory MCP + Todoist
Get:
- Original interaction (date, content)
- What was promised/expected
- Previous follow-ups (if any)
- Relationship context
```

### 2. Determine Appropriate Action
```
Decision tree:

IF first follow-up AND < 7 days:
  → Gentle check-in

IF first follow-up AND > 7 days:
  → Direct follow-up

IF second follow-up:
  → Add value + reminder

IF third+ follow-up:
  → Final follow-up or close loop
```

### 3. Craft Message

#### First Follow-Up (Gentle)
```
Subject: Quick check-in on [topic]

Hi [Name],

Hope you're doing well! Just circling back on [topic] from [date].

[Brief context reminder if needed]

Any updates on your end?

Best,
[Name]
```

#### Second Follow-Up (Add Value)
```
Subject: Re: [topic] + [new value]

Hi [Name],

Following up on our conversation about [topic].

[NEW VALUE: relevant article, insight, or update]

Thought this might be useful as you're thinking about [decision].

Let me know if you'd like to reconnect.

Best,
[Name]
```

#### Final Follow-Up (Close Loop)
```
Subject: Closing the loop on [topic]

Hi [Name],

I've reached out a few times about [topic] and haven't heard back.

I understand priorities shift - no worries at all.

I'll close this out for now, but feel free to reach out if [topic] becomes relevant again.

All the best,
[Name]
```

### 4. Send via Right Channel
```
Match original channel:
- Email → Email
- LinkedIn → LinkedIn
- Telegram → Telegram

Unless:
- No response after 2 tries → try different channel
```

### 5. Track & Update
```
Tool: Todoist
Actions:
- Mark current follow-up done
- Create next follow-up (if needed)
- Update notes with response/no response
- Save to Memory MCP
```

## Quality Checks
- [ ] Context retrieved (не generic message)
- [ ] Timing appropriate (не слишком рано/поздно)
- [ ] Tone matches relationship
- [ ] Value added (не просто "checking in")
- [ ] Clear next step (для тебя и них)

## Completion Criteria
- Follow-up sent
- Tracking updated
- Next action scheduled (or closed)

## Time Estimate
- **Typical**: 3-5 minutes
- **Max**: 10 minutes (если нужен research)

## Follow-Up Sequence Best Practices

### Timing
```
Initial outreach → Day 0
Follow-up #1 → Day 3-5
Follow-up #2 → Day 10-14
Follow-up #3 (final) → Day 21-30
```

### Frequency by Urgency
```
High urgency: 2-3 days between
Medium: 5-7 days between
Low: 7-14 days between
```

### When to Stop
```
Stop after:
- 3 follow-ups with no response
- Explicit "not interested"
- Clear signal of bad timing

Re-engage after:
- 3-6 months (if relationship worth maintaining)
- Trigger event (funding, new role, news)
```

## Message Templates

### Status Check (Internal)
```
Hi [Name],

Checking in on [task/project].

Quick questions:
- On track for [deadline]?
- Any blockers?
- Need anything from me?

Thanks!
```

### Vendor/Partner Follow-Up
```
Hi [Name],

Following up on [proposal/quote] from [date].

Just wanted to check:
- Any questions from your side?
- Timeline for decision?

Happy to jump on a call if helpful.

Best,
[Name]
```

### Post-Introduction Follow-Up
```
Hi [Name],

Did you get a chance to connect with [Person] after my intro?

Would love to hear how it went!

Best,
[Name]
```

### Post-Meeting Follow-Up
```
Hi [Name],

Great meeting yesterday!

As promised, here's [resource/doc discussed].

Next steps from my end:
- [Action 1]
- [Action 2]

Let me know if questions come up.

Best,
[Name]
```

## Anti-Patterns (НЕ ДЕЛАТЬ)
- "Just checking in" без value
- Следующий follow-up на следующий день
- Guilt trips ("You never responded...")
- Same message copy-pasted
- Too many follow-ups (max 3)

## Notes
- ALWAYS check Memory for past interactions first
- Add value in every follow-up (не просто "bump")
- Track response rates для learning
- Different contexts = different patience levels
- Close loops cleanly (даже если no response)
