# Four Pillars of GOVERN/ASSURE: Standards Mapping

> Source: *The Organizational Singularity*, OS Outline v20, Chapter 4 (footnote on standards mapping). Salim Ismail with contributors, May 2026. v20 adds the explicit mapping of the Four Pillars to NIST, OWASP, and CSA frameworks. The Pillars *operationalize* these frameworks. They do not restate them.

## The Position

CISOs, auditors, and boards already speak the language of NIST, OWASP, and the Cloud Security Alliance. The Four Pillars are the production implementation of what those frameworks specify in the abstract.

When the conversation starts at *"how does this map to NIST AI RMF?"* the answer is not *"it doesn't, because we use the Four Pillars."* The answer is *"each Pillar is the production primitive that operationalizes a specific set of NIST controls, OWASP failure modes, and CSA control objectives. Here is the mapping."*

## The Three Frameworks Anchored

### NIST AI Risk Management Framework (2023)

- Source: National Institute of Standards and Technology
- URL: `https://www.nist.gov/itl/ai-risk-management-framework`
- Scope: Voluntary framework governing risk across the AI lifecycle (design, development, use, evaluation).
- Why it matters: NIST AI RMF is the default reference framework for US federal agencies and the de facto vocabulary used by enterprise risk committees.

### OWASP Top 10 for LLM Applications

- Source: OWASP Foundation
- URL: `https://owasp.org/www-project-top-10-for-large-language-model-applications/`
- Scope: The ten most critical failure modes for LLM-backed applications, including prompt injection, sensitive-information disclosure, insecure output handling, and excessive agency.
- Why it matters: OWASP names the *failures the Pillars catch*. When the security team asks *"how do you handle prompt injection?"* the OWASP vocabulary is the bridge.

### Cloud Security Alliance AI Controls Matrix (AICM)

- Source: Cloud Security Alliance
- URL: `https://cloudsecurityalliance.org/artifacts/ai-controls-matrix`
- Scope: 243 control objectives across 18 domains (July 2025 release).
- Why it matters: AICM is the controls superset. Auditors map it directly to ISO 27001, SOC 2, and HIPAA controls inventories. The Pillars implement, rather than restate, the relevant AICM controls.

## Per-Pillar Mapping

### Pillar 1: Trusted Evals

**Operationalizes.**

- NIST AI RMF: *Measure* function (testing, evaluation, validation, monitoring across the lifecycle).
- OWASP LLM Top 10: catches drift that surfaces as model misbehavior, hallucination, and quality degradation.
- CSA AICM: control domains covering model validation, performance monitoring, and continuous testing.

**What it does in production.** Every agent runs continuously against a known test set. Drift below a quantified threshold (accuracy floor, override-rate ceiling) triggers retraining or rollback automatically. An agent without an eval suite is a demo, not a production agent.

### Pillar 2: Searchable Logs with Correlation IDs

**Operationalizes.**

- NIST AI RMF: *Manage* function (transparency, accountability, traceability of decisions and outcomes).
- OWASP LLM Top 10: insecure output handling (LLM07) and sensitive-information disclosure (LLM06) detection through log inspection.
- CSA AICM: logging, audit trail, and forensic recovery control objectives across multiple domains.

**What it does in production.** Every decision is recoverable from the audit trail alone. SENSE -> INTERPRET -> DECIDE -> ORCHESTRATE -> outcome chained on a single correlation ID. Logs are immutable, hashed, and cryptographically signed. Humans can reconstruct, debug, and explain any outcome without reproducing the run.

### Pillar 3: Granular Rollback

**Operationalizes.**

- NIST AI RMF: *Manage* function (incident response, recovery, model lifecycle versioning).
- OWASP LLM Top 10: response to insecure output (LLM07), excessive agency (LLM08), and overreliance (LLM09).
- CSA AICM: configuration management, version control, and recovery control objectives.

**What it does in production.** Any single agent revertible to last week's prompt, last month's model, or last quarter's policy version, without taking the rest of the Stack down. Treat agent versions the way disciplined engineering treats software versions: traceable, diffable, recoverable. An agent stack without rollback is an agent stack you cannot govern.

### Pillar 4: Human Review Queue

**Operationalizes.**

- NIST AI RMF: *Govern* function (accountability, human oversight, decision authority).
- OWASP LLM Top 10: excessive agency (LLM08), overreliance (LLM09), and insecure output handling (LLM07).
- CSA AICM: human oversight, escalation, segregation-of-duties control objectives.

**What it does in production.** Anything that touches money, legal text, or a customer-of-record routes to a named human in a queue with SLAs. The queue is staffed, measured, and visible to leadership. Humans-above-the-loop, not humans-in-the-loop, on decisions where the Fiduciary Wedge requires a name.

## OWASP Failure Modes the Pillars Catch (verbatim from the v20 source)

When the CISO asks *"how do we handle the OWASP LLM Top 10?"* these are the four failure modes the Pillars catch directly:

- **Prompt injection** caught by Pillar 1 (Trusted Evals testing for injection-pattern drift), Pillar 2 (logs reveal the injection path on review), and Pillar 4 (high-risk outputs route through human review).
- **Sensitive-information disclosure** caught by Pillar 2 (audit trail detects the disclosure), Pillar 3 (rollback contains the blast radius), and Pillar 4 (sensitive outputs route to a human).
- **Insecure output handling** caught by Pillar 1 (eval suite tests for unsafe output patterns), Pillar 2 (output logged with correlation ID for downstream review), and Pillar 3 (rollback recovers from bad output propagation).
- **Excessive agency** caught by Pillar 3 (rollback contains the agency overreach), Pillar 4 (high-agency decisions route to a human), and the Permission Envelope plus Autonomy Tier from the agent specification.

## Standards Mapping in the CIO Edge Twin Diagnostic

In Appendix F (`templates/cio-edge-twin-diagnostic.md`):

- Question 5 (leakage) maps directly to the OWASP failure modes above.
- Question 6 (identity) maps to NIST AI RMF *Govern* function and CSA AICM identity-and-access control domains.
- Question 7 (recovery) maps to Pillar 3 (Granular Rollback) and Pillar 4 (Human Review Queue).
- Question 8 (accountability) maps to NIST AI RMF *Govern* function and the Fiduciary Wedge.

Any red on Q5-Q8 blocks the build. These are the SHAPE controls. Skipping them produces the PocketOS pattern.

## What This Mapping Is Not

It is not a substitute for a NIST AI RMF self-assessment, an OWASP threat model, or a CSA AICM controls audit. The Pillars are operational primitives. The frameworks are the broader risk taxonomies the primitives live inside.

If the CISO asks for a NIST AI RMF self-assessment, do the self-assessment. If the auditor asks for AICM controls evidence, generate the evidence. The Pillars give you the production reality the frameworks describe in the abstract. Both layers exist for a reason.

## The Failure Mode

Telling the CISO *"we use the Four Pillars instead of NIST."* The CISO hears: *"we have made up our own framework and ignored the standard the rest of the industry uses."* The build stalls.

The right move. Lead with the standards the CISO already knows. Show the per-Pillar mapping above. End with the operational reality the Pillars deliver that the framework alone does not.
