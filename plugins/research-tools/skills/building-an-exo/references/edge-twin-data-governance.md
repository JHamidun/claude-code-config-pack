# Edge Twin Data Governance: The CIO's First Objection, Answered

> Source: *The Organizational Singularity*, OS Outline v20, Chapter 8, Edge Deployment, and Appendix F, The CIO Edge Twin Diagnostic. Salim Ismail with contributors, May 2026. v20 is the *Edge Twin Data-Governance Pass*: the first question every CIO asks, the answer the book commits to, and the operational primitives that make the answer hold.

## Why This Reference Exists

When you propose an Edge Twin, the CIO and CISO do not ask *"can it work?"* They ask *"can I govern it, audit it, secure it, reverse it, and explain it?"* Every objection is legitimate. The first one, every time, is: **does the Edge Twin fork our data?**

This reference is the load-bearing answer. It pairs with:

- The Workflow Data Manifest (REWRITE Step 3 EXTRACT exit criterion). See `references/rewrite-playbook.md` and `templates/workflow-data-manifest-template.md`.
- The HIDO Six Questions (per data object). See `references/intelligence-stack.md` and `templates/hido-six-questions.md`.
- The CIO Edge Twin Diagnostic (Appendix F readiness gate). See `templates/cio-edge-twin-diagnostic.md`.

## The One-Sentence Answer

**No.** The Edge Twin does not copy the enterprise data estate. It gets workflow-scoped, governed API access to the specific systems one migrated workflow needs, with read and write separated, every call logged on a correlation ID, and credentials short-lived and revocable. Operational systems remain the source of truth. If the Edge Twin and the ERP disagree, the ERP wins. The twin is the reasoning and orchestration layer, not a second system of record.

## The Six Governance Primitives

### 1. Workflow-Scoped Access, Not Estate-Wide

Scope is set by the **Workflow Data Manifest** (REWRITE Step 3), not by IT defaults. The manifest enumerates every source the workflow touches, the reason it needs each one, read or write, the sensitivity tier, retention in the twin's memory, and the named data owner who approves access.

The binary rule. *If you cannot state why a workflow needs a field, the Edge Twin does not get it.*

A worked example. An Edge Twin running order-exception handling sees order status, inventory, shipping, contract terms, and resolution history. It does not see the HR system. It does not see the general ledger. It does not see anything that is not on the manifest.

### 2. Read and Write Separated

Different credentials. Different scopes. Writes pass through approval thresholds and soft-delete windows. The Permission Envelope enforces both. The PocketOS lesson institutionalized: destructive endpoints are a separate Autonomy Tier with mandatory approval, soft-delete windows on every destructive operation, backups in a different blast radius than the data they protect.

### 3. Correlation-ID Logging End to End

Every call is logged. Every decision traceable. SENSE -> INTERPRET -> DECIDE -> ORCHESTRATE -> outcome chained on a single correlation ID. This is Pillar 2 of GOVERN/ASSURE (Searchable Logs with Correlation IDs). Logs are immutable, hashed, and cryptographically signed.

The CISO's test: *"can I see exactly what the twin accessed, why, and what it did next?"* If the answer requires reconstructing the run, the architecture is not deployed yet.

### 4. Short-Lived, Revocable Credentials

The twin gets its own **scoped workload identity**. Not an employee's credentials. Not an admin token. Not a shared API key. Credentials are short-lived, rotated automatically, and immediately revocable. Per-action logging, per-action authorization. Approval thresholds on destructive endpoints. The Searchable Logs pillar makes every credential use auditable.

### 5. Operational Systems Are the Source of Truth

**If the Edge Twin and the ERP disagree, the ERP wins.** Every time. Without exception. The twin is the reasoning, simulation, and orchestration layer. It is not a second system of record, and it is never allowed to become one early.

This rule lives in the Edge Twin charter, signed by the CEO and the CIO before funding. Without it, the twin drifts into shadow-IT territory the moment the first reconciliation disagreement appears.

### 6. Per-Object HIDO Governance

Each object the twin touches still answers the **HIDO Six Questions**: what is it, who says so, how can it be used, what are the legal terms, what happens if it is wrong, how is a dispute resolved. Carried as immutable, hashed, signed metadata bound to the object.

The Manifest governs the workflow's data surface. HIDO governs each object inside the surface. Both are required.

## Access Is Not Training

This is the single most common executive confusion. Access and training are different contracts.

**Default posture.** The twin retrieves governed data at runtime. It learns from workflow traces, human corrections, outcomes, and synthetic edge cases. It does not learn from possession of the data estate.

**Training and fine-tuning** happen only on approved, curated, de-identified datasets, under a separate vendor contract.

**Pin both in writing** with the vendor:

- Retention (how long the vendor holds data and logs)
- Training rights (whether the vendor may use customer data to train any model)
- Deletion rights (timeline, completeness, audit)
- Audit rights (the customer's ability to inspect what the vendor holds)
- Model isolation (separation between this customer's model state and any shared model)

If these five are not in the contract, the data answer is *yes, the twin trains on your data*, regardless of the marketing copy.

## The Earned-Data Principle

**The Edge Twin earns its data the way a new hire does, by doing the work, not by being handed the vault.**

A new hire on Day 1 gets a laptop, an email account, and access to the specific systems they need for their job. They do not get root on the file server. They do not get the customer database. They do not get HR records. As they take on more responsibility, their access expands. The same discipline applies to the twin.

Day 1: one workflow, one data manifest, one scoped credential set, one correlation-ID stream.
Day 60: the twin has earned access to the next workflow by proving it on the first.
Day 180: a second workflow is on parallel run. Manifests, credentials, and logs are all separate and additive.

This is the operational shape of the *easiest first* rule from Edge Deployment (`references/edge-deployment.md`).

## Mapping to GOVERN/ASSURE

The data-governance primitives are not separate from the Four Pillars. They are *how* the Pillars hold for data.

| Data primitive | Pillar that enforces it |
|---|---|
| Workflow-scoped access | Trusted Evals (workflow-specific eval suite) + Searchable Logs (audit trail) |
| Read/write separation | Granular Rollback (writes are recoverable per scope) + Human Review Queue (writes touching money/legal/CoR route to a named human) |
| Correlation-ID logging | Searchable Logs (the pillar by name) |
| Short-lived, revocable credentials | Searchable Logs (per-action logging) + Granular Rollback (credential revocation is the rollback path) |
| ERP-wins source of truth | Trusted Evals (twin output evaluated against operational system on every cycle) |
| HIDO metadata per object | Underpins all four pillars; metadata travels with the data |

If a pillar is below 3/5 for this workflow, the data primitive it backs cannot be relied on. That is the gate.

## Standards Cross-Reference

The data-governance primitives operationalize, rather than restate, the following:

- **NIST AI Risk Management Framework (2023)** for risk across design, development, use, and evaluation
- **OWASP Top 10 for LLM Applications** for the failure modes (prompt injection, sensitive-information disclosure, insecure output handling, excessive agency)
- **CSA AI Controls Matrix (July 2025)** for the 243 control objectives across 18 domains

See `references/four-pillars-standards-mapping.md` for the per-control crosswalk.

## The Failure Mode

Treating data governance as Phase-2 polish. The twin starts with broad access *"to get something working"* and the manifest is promised for *"the next sprint."* Within 60 days the twin is a second system of record, the ERP reconciliation is contested, the CISO is in the room, and the Edge Twin is killed or quarantined.

The defense. The Workflow Data Manifest is a Step 3 EXTRACT exit criterion, not a Step 5 nice-to-have. The CIO Edge Twin Diagnostic runs before funding, not after. The first workflow is a workflow the manifest can describe completely on one page.

## The CIO Sign-Off Checklist

Before the Edge Twin is funded, the CIO confirms in writing:

- [ ] No fork of the enterprise data estate
- [ ] Workflow Data Manifest signed for the first workflow
- [ ] Workflow-scoped API access only (no super-user, no admin tokens)
- [ ] Read and write credentials separated, with write approval thresholds
- [ ] Correlation-ID logging operational end to end
- [ ] Scoped workload identity provisioned, short-lived, revocable
- [ ] Operational systems remain source of truth (ERP wins ties)
- [ ] HIDO metadata in place on every data object the workflow touches
- [ ] Access-vs-training distinction pinned in vendor contract (retention, training rights, deletion rights, audit rights, model isolation)
- [ ] Appendix F (CIO Edge Twin Diagnostic) scored: no red on Q5, Q6, Q7, or Q8

If any line is unsigned, the Edge Twin is not funded.
