# SHAPE Scorecard

> Score the organizational form. Five components, 1–5 each. Total 25.
> Apply the Middle-60% absorption rule: if absorption math is not honestly modeled, cap H at ≤2/5.

**Firm:** _______________________________________
**Date:** _______________________________________
**Scored by:** _______________________________________

## Component Scores

### S: Safe Autonomy (1–5): ____

> Fiduciary Wedge, compliance-as-code, kill switches, audit trails, agent-to-agent oversight.

| Score | Anchor |
|---|---|
| 1 | Agents operate without spec; tokens have blanket privileges; no Fiduciary Wedge. |
| 2 | Fiduciary Wedge partial; envelopes informal. |
| 3 | Fiduciary Wedge in place; envelopes documented; kill switches exist but untested. |
| 4 | Compliance-as-code for major regulations; kill switches tested annually. |
| 5 | Compliance-as-code; agent-to-agent oversight; envelopes with scope isolation, approval thresholds, soft-delete windows; kill switches tested quarterly. |

Permission Envelope check (PocketOS prevention):
☐ Scope isolation on all tokens
☐ Approval threshold for destructive actions
☐ Soft-delete window on irreversible operations
☐ Tested kill switch with documented recovery procedure

#### Four Pillars Sub-Rubric (score each 1–5)

| Pillar | Score | Anchor |
|---|---|---|
| Trusted Evals | ____ | Every agent runs continuously against a known test set. Catches Silent Drift before customers do. |
| Searchable Logs with Correlation IDs | ____ | Every decision recoverable from the audit trail alone. |
| Granular Rollback | ____ | Any single agent revertible without taking the Stack down. |
| Human Review Queue | ____ | Money / legal / customer-of-record decisions routed to a named human with SLAs. |
| **Four Pillars Maturity (minimum)** | **____** | **Do not deploy new agent class until ≥ 3.** |

HIDO check (data-side governance, see `templates/hido-six-questions.md`):
☐ HIDO Six Questions answered for every data object an agent acts on
☐ HIDO metadata is immutable, hashed, signed
☐ HIDO metadata travels with the data, including across firm boundary

Reasoning: _______________________________________________________________

### H: Human Architecture (1–5): ____

> Where human cognition is irreplaceable. Middle 60%, missing junior loop, bifurcation risk.

| Score | Anchor |
|---|---|
| 1 | Headcount cuts without workflow redesign; no absorption math; no apprenticeship loop. |
| 2 | Some absorption modeling; transition leader unnamed. |
| 3 | Absorption math modeled; transition leader named; some Stack-mentored learning rotations. |
| 4 | Funded transition; engineered junior loop; bridges visible. |
| 5 | Honest absorption math; fully funded transition (10–15% of savings); engineered junior loop; measured caste-formation indicators; porous inner ring. |

Middle-60% absorption math:
☐ Current headcount in target functions: ___________
☐ AI-native headcount projection in target functions: ___________
☐ Math published and reviewed by leadership? ☐ Yes ☐ No
☐ Transition budget allocated (10–15% of projected savings)? ☐ Yes ☐ No
☐ Three outcomes mapped (concentrate / redeploy / exit)? ☐ Yes ☐ No

**If absorption math is not modeled, cap H at ≤2/5.**

Missing junior loop check:
☐ Stack-mentored learning rotations exist
☐ AI-augmented mentoring program in place
☐ Structured exposure to judgment patterns agents can't yet handle

Bifurcation / caste check:
☐ Promotion paths from outer ring to inner ring exist
☐ Caste-formation measured as a leading indicator
☐ Inner ring is porous

Reasoning: _______________________________________________________________

### A: Adaptive Architecture (1–5): ____

> Modularity + antifragility. Pod-based intelligence networks. The org chart itself is swappable.

| Score | Anchor |
|---|---|
| 1 | Monolithic systems; model swap requires rebuild; org chart sacred. |
| 2 | Some modularity; model swap painful. |
| 3 | Stack layers can be swapped with effort; some pods replacing departments. |
| 4 | Most layers swappable; pods replacing most departments. |
| 5 | Every layer swappable, retargetable; pods are the default; model deprecation is routine. |

Reasoning: _______________________________________________________________

### P: Purpose Control (1–5): ____

> MTP as three-layer protocol (Constraint, Decision, Identity).

| Score | Anchor |
|---|---|
| 1 | MTP is a poster; no Constraint Layer; no machine-readable form. |
| 2 | Some constraint statements documented; not machine-readable. |
| 3 | Constraint and Decision layers documented; Identity Layer relies on legacy office culture. |
| 4 | All three layers documented; first litmus test passes. |
| 5 | All three layers operational; both litmus tests pass; MTP routinely refuses feature requests. |

MTP litmus tests:
☐ Could an agent, given only the MTP, make a decision leadership would endorse?
☐ Could that agent, given only the MTP, decide what NOT to build?

Reasoning: _______________________________________________________________

### E: Ecosystem Trust (1–5): ____

> Trust as protocol. Cryptographic identity, verifiable credentials, mechanism design.

| Score | Anchor |
|---|---|
| 1 | Trust by lunch and reputation only. |
| 2 | Some audit trails; no cryptographic identity. |
| 3 | Audit trails and reputation systems for major partners; some agent-to-agent auth. |
| 4 | Verifiable credentials in production with key partners. |
| 5 | Mechanism-design protocols in production; verification networks operational; bloc-aware design. |

Balkanization design check:
☐ Designed for cognitive blocs (US / China / EU divergence)
☐ Sovereign AI capability evaluated
☐ Multi-bloc partner strategy

Cross-Organizational Accountability check (any cross-firm agent action):
☐ Policy-controlled API surface for external agents (scoped credentials, rate limits, action whitelists, kill-switch authority)
☐ HIDO metadata travels with every data object exchanged
☐ Liability framework codesigned with counterparty in advance, agreed error budgets, mitigation paths, arbitration mechanism
☐ Legal team in the room when the integration was designed

Reasoning: _______________________________________________________________

## Totals

| Field | Value |
|---|---|
| **Total (S + H + A + P + E)** | ____ / 25 |
| Middle-60% absorption modeled? | ☐ Yes ☐ No |
| H capped at 2 due to absorption gap? | ☐ Yes ☐ No |

## Recommendations

- **Lowest-scoring component:** ____________ → Highest-leverage area for the next 90 days.
- **First three actions:**
  1. ___________________________________________________________
  2. ___________________________________________________________
  3. ___________________________________________________________

## Source Attribution

SHAPE is a component of ExO 3.0, published in *The Organizational Singularity* (OS Outline v13, May 2026), authored by Salim Ismail with contributors. See `openexo-fOS/active-projects/OS_v13/shape-toolkit-v13/` for the full bound playbook and scoring template (the source for the Four Pillars sub-rubric, HIDO check, and Cross-Organizational Accountability check added in v13).
