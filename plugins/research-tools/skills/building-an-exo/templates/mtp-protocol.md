# MTP Protocol Authoring Template

> The MTP is not a poster. It is a protocol.
> Output: a three-layer machine-readable MTP that passes both litmus tests.

**Firm:** _______________________________________
**Authored by:** _______________________________________
**Date:** _______________________________________
**Version:** _______________________________________

## 0. The MTP Statement (the inspirational layer)

> One sentence. Massive. Transformative. Purpose. Memorable enough that an agent and a human both reach for it under stress.

___________________________________________________________

> *Examples (for calibration, not adoption):*
> - Tesla: "Accelerate the world's transition to sustainable energy."
> - Singularity University: "Positively impact a billion people."
> - SpaceX: "Make humanity multi-planetary."

## 1. Constraint Layer: Hard Constraints

> What agents are categorically forbidden from doing. Hard constraints, not aspirational values.
> Each must be machine-readable: an agent reading only this layer must know whether a proposed action is allowed.

| # | Forbidden action | Trigger / detection | Agent response on detection |
|---|---|---|---|
| 1 |  |  | Refuse + log + escalate |
| 2 |  |  | Refuse + log + escalate |
| 3 |  |  | Refuse + log + escalate |
| 4 |  |  | Refuse + log + escalate |
| 5 |  |  | Refuse + log + escalate |

**Categories to consider:**
- ☐ Unauthorized data exfiltration
- ☐ Customer harms (specify)
- ☐ Decisions outside the Permission Envelope
- ☐ Regulatory violations
- ☐ Decisions that would foreseeably conflict with the firm's MTP statement

## 2. Decision Layer: Weighted Priorities

> Weighted priorities agents use when facing tradeoffs. The Decision Layer resolves the tension without human intervention.

| Tradeoff | Priority | Weighting / rule |
|---|---|---|
| Speed vs. quality |  |  |
| Cost vs. impact |  |  |
| Customer retention vs. acquisition |  |  |
| Margin vs. growth |  |  |
| Short-term vs. long-term |  |  |
| Privacy vs. personalization |  |  |
| Internal vs. external trust |  |  |

> Add tradeoffs unique to this firm. The Decision Layer should be specific enough that two agents reading it independently arrive at the same call.

## 3. Identity Layer: Cultural Cohesion

> The cultural cohesion mechanism that replaces "the office." When agents handle coordination, humans lose the incidental bonds traditional work provided. Shared purpose, visible impact, and the knowledge that your judgment shapes outcomes is what binds top talent. Compensation alone is insufficient.

**Why a high-judgment human stays here:**
___________________________________________________________
___________________________________________________________

**What is visible (impact, judgment, contribution):**
___________________________________________________________
___________________________________________________________

**Rituals that replace office bonds:**
___________________________________________________________
___________________________________________________________

**Identity disqualifiers (we are not for):**
___________________________________________________________

## Litmus Tests

### Test 1: Endorsement Test

> *Could an AI agent, given only this MTP protocol, make a decision your leadership team would endorse?*

Test scenarios:

1. ___________________________________________________________
   Predicted agent decision: _______________________________________
   Leadership endorses? ☐ Yes ☐ No

2. ___________________________________________________________
   Predicted agent decision: _______________________________________
   Leadership endorses? ☐ Yes ☐ No

3. ___________________________________________________________
   Predicted agent decision: _______________________________________
   Leadership endorses? ☐ Yes ☐ No

**Test 1 result:** ☐ PASS ☐ FAIL

### Test 2: Refusal Test

> *Could that agent, given only this MTP, decide what NOT to build?*

Test scenarios (proposed features the agent should refuse):

1. ___________________________________________________________
   Predicted refusal? ☐ Yes ☐ No

2. ___________________________________________________________
   Predicted refusal? ☐ Yes ☐ No

3. ___________________________________________________________
   Predicted refusal? ☐ Yes ☐ No

**Test 2 result:** ☐ PASS ☐ FAIL

> If either test fails, return to authoring. The MTP is not yet a protocol.

## Distribution

- [ ] MTP protocol versioned and stored where every agent can retrieve it (PURPOSE layer of the Stack)
- [ ] All deployed agents updated to reference the new version
- [ ] Eval suites updated to test against the new layers
- [ ] CAIO has signed off
- [ ] CEO has signed off

## Source Attribution

The three-layer MTP-as-protocol construct is from ExO 3.0, published in *The Organizational Singularity* (OS Outline v13, May 2026, Chapter 3 and SHAPE Component P), authored by Salim Ismail with contributors. The original MTP construct is from *Exponential Organizations* (Ismail, Malone, van Geest, 2014).
