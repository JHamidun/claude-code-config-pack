# DRIVE Scorecard

> Score the intelligence engine. Five components, 1–5 each. Total 25.
> Apply the GOVERN-cap rule: if GOVERN/ASSURE is absent, cap the total at 13/25.

**Firm:** _______________________________________
**Date:** _______________________________________
**Scored by:** _______________________________________
**Sector:** ☐ Information-centric ☐ Hybrid ☐ Regulated ☐ Mission-driven

## Component Scores

### D: Decision Architecture (1–5): ____

> Two-way doors get speed. One-way doors get human gating. Every decision type maps to who decides, under what conditions, with what guardrails.

| Score | Anchor |
|---|---|
| 1 | All decisions human, all routed through approval chains. |
| 2 | Some decisions delegated; no documentation of reversibility. |
| 3 | Some decision categories mapped to agents under guardrails. |
| 4 | Most decision classes have an Agency Map; one-way doors gated. |
| 5 | Every decision class has a defined Agency Map; reversibility tested; fragile middle eliminated. |

Reasoning: _______________________________________________________________

### R: Recursive Learning (1–5): ____

> Workflows versioned. Performance measured. Improvements codified and propagated.

| Score | Anchor |
|---|---|
| 1 | Lessons trapped in postmortems and Slack threads. |
| 2 | Periodic retros; lessons stay in the team. |
| 3 | Some workflows versioned; learnings reach adjacent teams in weeks. |
| 4 | LEARN layer of the Stack functional; cross-team propagation. |
| 5 | Improvements codified and propagated at machine speed; recursive cadence in compensation. |

Reasoning: _______________________________________________________________

### I: Intelligence Stack (1–5): ____

> The operating core. Six layers + GOVERN/ASSURE. **Cap the I score at the lowest Four Pillars score.**

| Score | Anchor |
|---|---|
| 1 | Isolated AI tools, no Stack architecture. |
| 2 | Pilot agents in one or two areas. |
| 3 | MVIS operational (event bus, agent registry, central logging, one agent per class). |
| 4 | Multi-layer Stack with cross-layer dataflow; some learning loops live. |
| 5 | Full six-layer Stack with GOVERN/ASSURE in kill-switch-capable mode and cross-layer learning. |

#### Four Pillars Sub-Rubric (score each 1–5)

| Pillar | Score | Anchor |
|---|---|---|
| Trusted Evals | ____ | Every agent runs continuously against a known test set. Without one, agent is a demo, not production. |
| Searchable Logs with Correlation IDs | ____ | Every decision recoverable from the audit trail alone. Immutable, hashed, signed. |
| Granular Rollback | ____ | Any single agent revertible to last week's prompt, last month's model, last quarter's policy, without taking the Stack down. |
| Human Review Queue | ____ | Anything touching money, legal text, or customer-of-record routes to a named human with SLAs. |
| **Four Pillars Maturity (minimum across the four)** | **____** | **Do not deploy new agent class until ≥ 3.** |

HIDO check (data-side governance):
☐ HIDO Six Questions answered for every data object an agent reads or writes
☐ HIDO metadata immutable, hashed, signed
☐ HIDO metadata travels with the data across firm boundary (if applicable)

Reasoning: _______________________________________________________________

### V: Value Moat (1–5): ____

> Five sources: proprietary data, network effects, intelligence density, reconfiguration speed, curatorial judgment. Inertia moats are wasting assets.

| Score | Anchor |
|---|---|
| 1 | Pure inertia moat; single model vendor. |
| 2 | One durable source emerging; mostly inertia. |
| 3 | Mix of inertia and one durable source; multi-vendor inference. |
| 4 | Two durable sources demonstrably compounding. |
| 5 | Two+ durable sources compounding; multi-family inference; owned orchestration and fine-tuning data. |

Identify all sources present (check all that apply):
☐ Proprietary data
☐ Network effects
☐ Intelligence density
☐ Reconfiguration speed
☐ Curatorial judgment

Cognitive captivity check:
☐ Inference across ≥2 model families
☐ Owned orchestration logic
☐ Owned fine-tuning data

Customer-side agent inversion check:
☐ Pricing legible to agents
☐ APIs designed for agent buyers
☐ Counter-agent strategy in place

Reasoning: _______________________________________________________________

### E: Elastic Agency (1–5): ____

> Capability Registry, Graduated Authority, Decision Boundary in practice. Sliding talent ratios by sector.

| Score | Anchor |
|---|---|
| 1 | Fixed org chart; no Capability Registry. |
| 2 | Some agent / human composition logic ad hoc. |
| 3 | Capability Registry live; Graduated Authority used for new hires; ratios understood. |
| 4 | Composition replaces some hiring; ratios tracked. |
| 5 | Capability Registry is the org chart; composition replaces hiring; ratios tracked quarterly. |

Sector ratios applied:

| Sector | AI / Agents | Internal Humans | Elastic External |
|---|---|---|---|
| Information-centric | ~70% | ~20% | ~10% |
| Hybrid | ~50% | ~30% | ~20% |
| Regulated | ~40% | ~35% | ~25% |

Reasoning: _______________________________________________________________

## Totals

| Field | Value |
|---|---|
| Raw total (D + R + I + V + E) | ____ / 25 |
| GOVERN/ASSURE status | ☐ Absent ☐ Alert-only ☐ Escalation ☐ Kill-switch capable |
| GOVERN-cap rule applied? | ☐ Yes (cap at 13) ☐ No (no cap) |
| **Final DRIVE score** | ____ / 25 |

## Recommendations

Based on the score:

- **Lowest-scoring component:** ____________ → Highest-leverage area for the next 90 days.
- **First three actions:**
  1. ___________________________________________________________
  2. ___________________________________________________________
  3. ___________________________________________________________

## Source Attribution

DRIVE is a component of ExO 3.0, published in *The Organizational Singularity* (OS Outline v13, May 2026), authored by Salim Ismail with contributors. See `openexo-fOS/active-projects/OS_v13/drive-toolkit-v13/` for the full bound playbook and scoring template (which is the source for the Four Pillars sub-rubric and HIDO check added in v13).
