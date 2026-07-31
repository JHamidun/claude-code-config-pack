# The CIO Edge Twin Diagnostic

> Template, Appendix F readiness gate (v20). Ten governance questions a CEO hands the CIO *before* funding an Edge Twin. Score each red, amber, or green. Any red on questions 5, 6, 7, or 8 blocks the build. Those four are the SHAPE controls. Skipping them produces the PocketOS pattern.

**Source:** *The Organizational Singularity*, OS Outline v20, Appendix F. Salim Ismail with contributors, May 2026.

---

## Header

| Field | Value |
|---|---|
| Company | _____________________________________ |
| Proposed Edge Twin name | _____________________________________ |
| First workflow targeted | _____________________________________ |
| CIO completing this diagnostic | _____________________________________ |
| Date | _____________________________________ |
| Funding decision date | _____________________________________ |

---

## Scoring Legend

- **Green**, the answer is in place, in writing, and demonstrable today.
- **Amber**, the answer is partial; gaps named, owner assigned, deadline set.
- **Red**, the answer is missing or wrong.

**Gate rule.** Any **Red** on **questions 5, 6, 7, or 8** blocks the build until it turns Amber or Green. These four are the SHAPE controls (leakage, identity, recovery, accountability).

---

## The Ten Questions

### 1. What is the Edge Twin allowed to do?

Make autonomy explicit, never implied. Every agent carries an **Autonomy Tier** in its agent specification (recommend_only / execute_within_bounds / fully_autonomous). The twin graduates through the **Decision Handover Waves** of REWRITE Step 5: Wave 1 low-risk and high-frequency, Wave 2 medium-complexity, Wave 3 higher-judgment. Each wave proves before the next begins.

*Do not invent a new ladder. Use the Tier and the Waves the architecture already has.*

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

---

### 2. What is the source of truth?

**Operational systems, not the twin.** If the Edge Twin and the ERP disagree, the ERP wins. The twin is the reasoning, simulation, and orchestration layer. It is not a second system of record, and it is never allowed to become one early.

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

---

### 3. What data does the twin need, and why?

Answer with a **Workflow Data Manifest** (REWRITE Step 3): every source, the reason it is needed, read or write, sensitivity tier, retention, and the named owner who approves access. Each object the twin touches also answers the **HIDO Six Questions** from Chapter 4.

**The rule is binary.** If you cannot state why a workflow needs a field, the twin does not get it.

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

Manifest reference: `templates/workflow-data-manifest-template.md`

---

### 4. Does the twin train on our data?

**By default, no.** The twin retrieves governed data at runtime and learns from workflow traces, human corrections, outcomes, and simulation, not from possession of the data estate. Training or fine-tuning happens only on approved, curated, de-identified datasets.

Executives confuse **access** with **training**. They are different contracts. Pin both in writing with the vendor:

- Retention
- Training rights
- Deletion rights
- Audit rights
- Model isolation

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

---

### 5. How do we prevent leakage? *(SHAPE control)*

**Permissions are enforced outside the model, before retrieval and before action.** Telling the model "do not reveal confidential information" is not a control. The defense is the **Permission Envelope** plus the GOVERN/ASSURE control plane catching the OWASP failure modes:

- Prompt injection
- Sensitive-information disclosure
- Insecure output handling
- Excessive agency

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

*Any Red here blocks the build.*

---

### 6. How is identity handled? *(SHAPE control)*

The twin gets its own **scoped workload identity**. Not an employee's credentials, not an admin token, not a shared API key. Short-lived credentials, per-action logging, revocation, and approval thresholds.

**The CISO's test.** *"Can I see exactly what the twin accessed, why, and what it did next?"* The **Searchable Logs** pillar with correlation IDs is the answer.

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

*Any Red here blocks the build.*

---

### 7. What happens when the twin is wrong? *(SHAPE control)*

Every workflow ships with:

- Confidence score
- Source citation
- Decision rationale
- Human-approval rule (for the relevant Autonomy Tier and workflow class)
- Rollback path
- Audit log
- Exception queue

The **Granular Rollback** and **Human Review Queue** pillars make mistakes recoverable and accountable. For high-impact workflows, the twin does not act unless the action is explainable and reversible, and the legacy workflow stays available as fallback until deprecation.

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

*Any Red here blocks the build.*

---

### 8. Who is accountable? *(SHAPE control)*

**A named human, always.** This is the **Fiduciary Wedge**: anything that touches money, legal text, or a customer-of-record routes to a person. The human shifts from doing every transaction to governing the workflow (validator, not gatekeeper).

Name the roles before launch:

- Business-process owner: _____________________________________
- Data owner: _____________________________________
- Risk owner: _____________________________________
- Human supervisor: _____________________________________
- CAIO (model behavior): _____________________________________
- Security owner (threat model): _____________________________________

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

*Any Red here blocks the build.*

---

### 9. What is the smallest safe first workflow?

Pick the workflow with the **highest ratio of coordination work to judgment work**, and that is also:

- High-volume
- Rule-clear
- Measurable
- Reversible
- Low regulatory exposure
- Historical cases available

**Good first candidates.** Support triage. Invoice-exception routing. Order-status exceptions. Renewal-risk detection.

**Bad first candidates.** Hiring and firing. Credit approval. Strategic-account pricing. Financial reporting. Anything safety-critical.

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

---

### 10. How will we measure success?

Define benchmarks **before** the parallel run starts (REWRITE Step 5):

- Cycle time
- Error rate
- Cost per transaction
- Policy exceptions
- Experience scores (customer or operator)

**One metric sits above the rest.** The **human-override rate must fall over time**. A twin that does not improve is not a twin. It is workflow automation with a chat box.

Reference: `references/cold-start-learning-feeds.md`

| Score |  |
|---|---|
| [ ] Green |  |
| [ ] Amber |  |
| [ ] Red |  |

Notes / evidence / gap owner:

```
[Your notes here]
```

---

## Readiness Gate Summary

| Question | Score (R/A/G) | Blocks build? |
|---|---|---|
| 1, Allowed to do (Autonomy Tier + Waves) |  | No |
| 2, Source of truth (ERP wins) |  | No |
| 3, Data needed, why (Manifest + HIDO) |  | No |
| 4, Train on data (access vs. training) |  | No |
| **5, Prevent leakage (SHAPE control)** |  | **Yes if Red** |
| **6, Identity handling (SHAPE control)** |  | **Yes if Red** |
| **7, When the twin is wrong (SHAPE control)** |  | **Yes if Red** |
| **8, Accountability (SHAPE control)** |  | **Yes if Red** |
| 9, Smallest safe first workflow |  | No |
| 10, Measure success (override rate falls) |  | No |

**Gate decision.**

- [ ] All four SHAPE controls (Q5, Q6, Q7, Q8) are at Amber or Green. The build is funded.
- [ ] One or more SHAPE controls is Red. The build is **blocked** until those questions turn Amber. Owners and deadlines named above.

CEO signature: _____________________________________

CIO signature: _____________________________________

Board acknowledgement (Tier 4-5 only): _____________________________________
