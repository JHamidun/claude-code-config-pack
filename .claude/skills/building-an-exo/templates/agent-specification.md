# Agent Specification

> **The spec is the contract. No spec, no agent.**
> Every agent operating in the Intelligence Stack must have all eight properties filled.

**Agent name:** _______________________________________
**Stack layer(s):** ☐ PURPOSE ☐ SENSE ☐ INTERPRET ☐ DECIDE ☐ ORCHESTRATE/ACT ☐ LEARN ☐ GOVERN/ASSURE
**Owner (named human):** _______________________________________
**Created:** _______________________________________
**Version:** _______________________________________

## 1. Purpose

> What is this agent for? Derived from the PURPOSE-layer intent (the MTP).

___________________________________________________________
___________________________________________________________

## 2. Autonomy Tier

☐ **recommend_only**, produces options for a human; does not execute.
☐ **execute_within_bounds**, executes inside Permission Envelope without human approval per action.
☐ **fully_autonomous**, operates without per-action human oversight; escalates by exception.

> **PocketOS rule:** destructive or irreversible operations may *never* be `execute_within_bounds`. They require explicit human approval at the action level.

## 3. Permission Envelope

> The exact scope of authority. Must include scope isolation.

**Data access:**
___________________________________________________________

**System access (APIs, services):**
___________________________________________________________

**Dollar / resource limits:**
___________________________________________________________

**Allowed actions:**
___________________________________________________________

**Forbidden actions:**
___________________________________________________________

**Scope isolation check:**
- ☐ Token / credential is scoped to the smallest viable surface
- ☐ Cannot access tokens or credentials outside its declared scope
- ☐ Approval threshold required for destructive actions
- ☐ Soft-delete window on irreversible operations
- ☐ Tested kill switch with documented recovery procedure

## 4. Memory Boundary

> What the agent can remember, retrieve, and persist; what it cannot.

**Can remember:**
___________________________________________________________

**Can retrieve from:**
___________________________________________________________

**Cannot persist:**
___________________________________________________________

**Memory window:**
___________________________________________________________

## 5. Escalation Rules

> When human intervention is required and to whom.

| Trigger | Action | Recipient |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |

**Default escalation owner:** ____________________________________________
**Backup escalation owner:** ____________________________________________

## 6. Eval Suite

> The test battery the agent passes before deployment and re-passes after every model or workflow change.

**Eval scenarios:**

1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________
4. ___________________________________________________________
5. ___________________________________________________________

**Pass / fail criteria:**
___________________________________________________________

**Re-eval triggers (check all that apply):**
- ☐ Model upgrade or replacement
- ☐ Workflow change
- ☐ Permission Envelope change
- ☐ Quarterly cadence
- ☐ Drift detection signal from GOVERN/ASSURE

## 7. Telemetry / Audit Trail

> Every autonomous decision logged with correlation IDs, traceable, explainable.

**Log destination:**
___________________________________________________________

**Log retention period:**
___________________________________________________________

**Required log fields:**
- ☐ Correlation ID
- ☐ Decision input snapshot
- ☐ Reasoning trace
- ☐ Decision output
- ☐ Permission Envelope check result
- ☐ Escalation decisions
- ☐ Outcome (when known)
- ☐ Model version
- ☐ Prompt version

**Audit access (named):** ____________________________________________

## 8. Reusability Scope

> *"How do I make them reusable, so once trained I can deploy them in multiple places?"* (McKinsey, April 2026)
>
> Agents built without reusability scope become single-purpose artifacts. Agents with it become compounding capital.

**Designed-for contexts:**
___________________________________________________________

**Out-of-scope contexts:**
___________________________________________________________

**Required adaptations to redeploy:**
___________________________________________________________

**Composability with other agents (Capability Registry tags):**
___________________________________________________________

## Sign-Off

- [ ] All eight properties filled
- [ ] Owner named
- [ ] Permission Envelope passes scope isolation check
- [ ] Eval suite passed
- [ ] Telemetry destination configured and tested
- [ ] Reusability scope filled (or marked single-purpose with justification)

**Approved for deployment by:** ____________________________________________
**Date:** ____________
**Tier:** ☐ Pilot ☐ Production ☐ Critical-path

## Source Attribution

The Agent Specification (eight properties) is the contract layer of the Intelligence Stack, published in *The Organizational Singularity* (OS Outline v13, May 2026, Chapter 4), authored by Salim Ismail with contributors. The Reusability Scope property is highlighted from McKinsey's April 2026 enterprise diagnostic.
