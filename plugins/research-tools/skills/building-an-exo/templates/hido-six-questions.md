# HIDO: The Six-Question Data Object Diagnostic

> **The data spec is the contract. No spec, no agent action.**
> Symmetric to the eight-property Agent Specification: the agent spec governs *who is allowed to act and how*; the HIDO spec governs *what may be done with each piece of evidence*.
> Carry the six answers as **immutable, hashed, signed metadata** bound to the data object. Log every access.

**Data object name:** _______________________________________
**Object class / schema:** _______________________________________
**Owner (named human):** _______________________________________
**Created:** _______________________________________
**Version:** _______________________________________
**Bound to agents:** _______________________________________

## 1. What is it?

> Schema, type, canonical form, version.

**Schema / type:**
___________________________________________________________

**Canonical form (link or inline):**
___________________________________________________________

**Schema version:**
___________________________________________________________

**Versioning policy when schema changes:**
___________________________________________________________

## 2. Who says so?

> Provenance, issuer, signature, chain of custody.

**Issuer:**
___________________________________________________________

**Signature method:** ☐ Cryptographic signature ☐ Hash-chained log ☐ Other: __________

**Chain of custody (origin → current state):**
___________________________________________________________

**Verification procedure:**
___________________________________________________________

## 3. How can it be used?

> Permitted operations: read, decide-on, share, train-on.

| Operation | Permitted? | Conditions |
|---|---|---|
| Read | ☐ Yes ☐ No | |
| Decide on (use as input to agent decisions) | ☐ Yes ☐ No | |
| Share (with internal humans / agents) | ☐ Yes ☐ No | |
| Share across firm boundary | ☐ Yes ☐ No | |
| Train on (use to fine-tune or update models) | ☐ Yes ☐ No | |
| Aggregate (combine with other objects) | ☐ Yes ☐ No | |

**Permitted agent classes:**
___________________________________________________________

**Forbidden agent classes:**
___________________________________________________________

## 4. What are the legal terms?

> Licensing, contractual constraints, regulatory class.

**License / contract reference:**
___________________________________________________________

**Regulatory class:** ☐ PII ☐ PHI ☐ PCI ☐ Trade secret ☐ Privileged ☐ Public ☐ Other: __________

**Jurisdiction / data residency:**
___________________________________________________________

**Retention policy:**
___________________________________________________________

**Counterparty rights (if cross-firm):**
___________________________________________________________

## 5. What happens if it's wrong?

> Error semantics, who notices, who fixes, who pays.

**Failure modes:**
___________________________________________________________

**Detection mechanism (eval / monitor / customer escalation / Silent Drift threshold):**
___________________________________________________________

**Owner of remediation:**
___________________________________________________________

**Financial liability (who pays):**
___________________________________________________________

**Compensating control (if undetected for > N days):**
___________________________________________________________

## 6. How is a dispute resolved?

> Resolution path before lawyers: arbitration, escrow, rollback.

**Pre-litigation resolution path:**
___________________________________________________________

**Rollback procedure (if any):**
___________________________________________________________

**Escrow / hold mechanism (if any):**
___________________________________________________________

**Arbitration body (if cross-firm):**
___________________________________________________________

**Escalation to legal, trigger conditions:**
___________________________________________________________

## Metadata Binding

The six answers above MUST be:

- ☐ Bound to the data object as inline or referenced metadata
- ☐ Immutable (write-once after sign-off, or versioned with prior-version retained)
- ☐ Hashed (each answer hash committed to the data object's identity hash)
- ☐ Signed (cryptographic signature from the named owner)
- ☐ Travelling with the data, if this object crosses a firm boundary, the metadata crosses with it

## Sign-Off

- [ ] All six questions answered
- [ ] Owner named
- [ ] Permitted / forbidden operations match the agent specifications of every agent currently bound to this object
- [ ] Failure-mode detection mechanism is operational
- [ ] Dispute resolution path agreed with counterparty (if cross-firm)
- [ ] Metadata binding verified

**Approved by:** ____________________________________________
**Date:** ____________
**Cross-firm scope:** ☐ Internal only ☐ Crosses firm boundary

## Source Attribution

The HIDO Six-Question Diagnostic is published in *The Organizational Singularity* (OS Outline v13, May 2026, Chapter 4 "Governing the Data"), authored by Salim Ismail with contributors. The Six Questions also serve as the **machine-readable cross-firm contract** in the Cross-Organizational Accountability stack (Chapter 3, E, Ecosystem Trust).
