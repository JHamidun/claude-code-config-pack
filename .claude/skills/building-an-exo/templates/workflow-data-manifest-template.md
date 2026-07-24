# Workflow Data Manifest

> Template, REWRITE Step 3 EXTRACT exit criterion (v20). One page per migration-candidate workflow. Workflow-level companion to the HIDO Six Questions per object. See `references/edge-twin-data-governance.md` and `references/rewrite-playbook.md`.

**Binary rule.** *If you cannot state why a workflow needs a field, the Edge Twin does not get it.*

---

## Workflow Identification

| Field | Value |
|---|---|
| Workflow name | _____________________________________ |
| Workflow owner (named human) | _____________________________________ |
| CAIO sign-off | _____________________________________ |
| Data steward sign-off | _____________________________________ |
| CISO sign-off | _____________________________________ |
| Manifest version | _____________________________________ |
| Date drafted | _____________________________________ |
| Date approved | _____________________________________ |

---

## Workflow Scope (one paragraph)

*State, in operational language, what this workflow does, who triggers it, and what outcome it produces. The scope here bounds the data set below: any field outside this scope must be removed from the manifest.*

```
[Scope description here]
```

---

## Data Sources Table

| # | Source (system / dataset) | Purpose (why this workflow needs it) | Access (read / write / read_write) | Sensitivity tier (public / internal / confidential / restricted / regulated) | Retention in twin's memory | Named data owner |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |

*Add rows as needed. If the table grows past one page, the workflow is probably too broad for Wave 1. Consider splitting.*

---

## Binary-Rule Check

For each source listed above, confirm:

- [ ] The purpose statement is workflow-specific, not generic ("for analytics" is not a purpose; "to read order status at the time of exception" is a purpose).
- [ ] The access level is the minimum the workflow needs (default to read; require justification for write).
- [ ] The sensitivity tier is set by the data owner, not the workflow owner.
- [ ] The retention in the twin's memory is bounded (default: zero retention beyond the run; longer retention requires justification).
- [ ] The data owner has been notified and has approved access in writing.

**If any row fails any check, that row is removed from the manifest. The workflow does not get that field.**

---

## Permission Envelope Mapping

For each agent in this workflow, name the Permission Envelope scope:

| Agent | Permission Envelope (scope, dollar limits, system access) | Autonomy Tier (recommend_only / execute_within_bounds / fully_autonomous) | Escalation rule |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

Cross-reference: each agent has a full Agent Specification at `templates/agent-specification.md`.

---

## Credential and Identity Plan

- [ ] Workload identity provisioned for this workflow (scoped, not shared)
- [ ] Credentials short-lived (rotation interval: __________)
- [ ] Credentials revocable on demand (revocation procedure documented)
- [ ] Per-action logging operational (correlation-ID format: __________)
- [ ] Read credentials separated from write credentials
- [ ] Write credentials subject to approval thresholds and soft-delete windows where destructive

---

## Source-of-Truth Statement

- [ ] Operational systems remain the source of truth for every source in the table above.
- [ ] If the Edge Twin and the operational system disagree, the operational system wins.
- [ ] No source on this manifest is the twin's own state.

Signed by CIO: _____________________________________

---

## HIDO Cross-Reference

For each source on the table above, confirm the HIDO Six Questions are answered on every object the workflow touches:

- [ ] What is it? (schema, type, canonical form, version)
- [ ] Who says so? (provenance, signature, chain of custody)
- [ ] How can it be used? (read / decide-on / share / train-on)
- [ ] What are the legal terms?
- [ ] What happens if it is wrong?
- [ ] How is a dispute resolved?

Use `templates/hido-six-questions.md` for each object's full answer. The manifest is the workflow surface; HIDO is the per-object detail.

---

## Access-vs-Training Statement

- [ ] The twin retrieves the data on this manifest at runtime.
- [ ] The twin does NOT train on any data on this manifest by default.
- [ ] Any future training or fine-tuning will use approved, curated, de-identified datasets under a separate contract.
- [ ] Vendor contract pins: retention, training rights, deletion rights, audit rights, model isolation.

Signed by CAIO and CISO: _____________________________________

---

## Manifest Review Cadence

- First review: 30 days after parallel-run start
- Subsequent reviews: every 90 days, or on any of: new data source proposed, new agent proposed for this workflow, sensitivity change in any source, regulatory change affecting any source
- Manifest version increments on every change
- Prior versions retained in the audit trail (Pillar 2, Searchable Logs)

---

## Failure-Mode Footer

The most common failure of the Workflow Data Manifest is that it is drafted late, on the way to Step 5. By then the twin is already operating, broad credentials are already provisioned, and the manifest is a backfill exercise instead of a gate. **The manifest is a Step 3 EXTRACT exit criterion. Step 4 does not begin without it.**
