# tech-lead — document templates

Read this file only when actually producing one of these documents. Copy the skeleton, fill it,
keep the section names — downstream readers scan by heading.

## DACI Decision Record

Use for any architectural or technical decision. One page.

```text
Decision: [one-line summary]
Date: [YYYY-MM-DD]
Status: [PROPOSED | DECIDED | SUPERSEDED]

Driver:       [who drives it to completion]
Approver:     [final say — exactly one person]
Contributors: [who provides input and analysis]
Informed:     [who needs to know the outcome]

Context:
  [Why is this decision needed? What triggered it?]

Options considered:
  1. [Option A] — [one-line summary]
  2. [Option B] — [one-line summary]
  3. [Do nothing] — [consequence]

Decision:
  [What we decided and WHY]

Consequences:
  [What changes? What do we give up?]

Review date: [YYYY-MM-DD]
```

Exactly one Approver. Two approvers means the decision stalls; zero means it gets re-litigated.
"Do nothing" is always listed as an option — its consequence is the baseline everything else is
measured against.

## RFC

Use for any change affecting 3+ services or taking 2+ weeks. 2-5 pages.

```text
RFC-[NNN]: [Title]
Author: [name]   Date: [YYYY-MM-DD]
Status: [DRAFT | REVIEW | ACCEPTED | REJECTED | IMPLEMENTED]

## Summary
[2-3 sentences: what and why]

## Motivation
[What problem does this solve? What happens if we do nothing?]

## Proposal
[Detailed technical design. Diagrams welcome.]

## Alternatives Considered
[What else was evaluated? Why rejected?]

## Migration Plan
[How do we get from here to there? Rollback plan?]

## Risks
[What could go wrong? How is it mitigated?]

## Open Questions
[What do we still not know?]

## Timeline
[Milestones with dates]
```

"Alternatives Considered" and "Open Questions" are the sections reviewers actually use — an RFC
with both empty reads as a decision already made, and gets rubber-stamped instead of reviewed.

## Postmortem

Use after any incident with user-facing impact. 1-2 pages.

```text
Postmortem: [Incident Title]
Date: [YYYY-MM-DD]   Severity: [SEV1 | SEV2 | SEV3]
Duration: [start] - [end] ([total])   Author: [name]

## Summary
[1-2 sentences: what happened and user impact]

## Timeline
- [HH:MM] First alert / user report
- [HH:MM] Investigation started
- [HH:MM] Root cause identified
- [HH:MM] Fix deployed
- [HH:MM] Confirmed resolved

## Root Cause
[Technical explanation. No blame — systems failed, not people.]

## What Went Well
- [Detection was fast because…]
- [Rollback worked because…]

## What Went Wrong
- [Monitoring gap: …]
- [Communication gap: …]

## Action Items
| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|

## Lessons Learned
[What do we now know that we did not know before?]
```

Blameless wording is not politeness — a postmortem that names a person gets defended instead of
read, and the systemic cause stays unfixed. Every action item needs an owner and a date; without
them the list is a wish, and the same incident returns.

## Tech Debt Quadrant (classification aid)

|              | Deliberate                                      | Inadvertent                                            |
|--------------|-------------------------------------------------|--------------------------------------------------------|
| **Reckless** | "wrong but we ship anyway" → track + schedule fix, needs explicit stakeholder sign-off | "what are design patterns?" → skills gap: training, review, pairing |
| **Prudent**  | "we fix it next sprint" → ticket with a deadline | "now we know how it should have been" → refactor when next touching that code |

Prudent+Deliberate is normal and healthy. The other three quadrants each need a different response,
which is the whole point of classifying before reacting.

## Sprint hygiene checklist

Before: backlog groomed with acceptance criteria · capacity known (PTO, on-call, meetings) ·
dependencies mapped · **15-20% capacity allocated to tech debt** · on-call set · previous retro
actions included.

During: standups blockers-first · blocked items escalated within 4 hours · scope changes go through
the Driver, never silently · PRs reviewed within 24 hours.

Close: PRs merged or explicitly deferred · demo prepared · metrics captured (velocity, cycle time,
bug rate) · retro scheduled.
