# Social Capital Crosswalk and Amazon Q Sidebar (v15)

> Source: *The Organizational Singularity*, OS Outline v15, Chapter 4, The Intelligence Stack. Salim Ismail with contributors, May 2026. This file carries verbatim text from the v15 source so the skill is portable without the underlying outline.

This reference exists because the industry has converged on a 5-layer vocabulary that your engineers, vendors, and board will use even when your operating model speaks in PURPOSE / SENSE / INTERPRET / DECIDE / ORCHESTRATE / LEARN. Translate at the boundary. Do not lose the LEARN layer in translation.

## The Crosswalk (verbatim from Chapter 4)

The Stack extends OODA in two directions, adding PURPOSE upstream and LEARN downstream, and runs all six layers continuously rather than serially.

### Crosswalk: The Intelligence Stack and the Industry's 5-Layer Vocabulary

Industry vocabulary is converging on a five-layer agent stack, popularized by Social Capital's *A Primer on AI Agents* (May 2026): **Intelligence, Action, Governance, Orchestration, Economics.** Your engineers, vendors, and board members will increasingly speak in those terms. The Intelligence Stack in this book is the same architecture told as an *operating model*, not as an engineering stack. The mapping is one-to-many in both directions, and the crosswalk matters because the two vocabularies will travel together for the next decade.

| Social Capital 5-Layer Stack | Intelligence Stack equivalent | What it means in this book |
|---|---|---|
| **Intelligence** (reasoning, memory, knowledge) | **PURPOSE + SENSE + INTERPRET** | The cognitive front end of the loop. Frames intent and builds the world model. |
| **Action** (ReAct loop, tools, protocols, MCP/A2A) | **DECIDE + ORCHESTRATE / ACT** | The execution layer that closes the loop from reasoning to real-world effect. |
| **Governance** (machine-checkable security, runtime enforcement) | **GOVERN/ASSURE control plane + Four Pillars** | The control plane. Same intent, more operational specificity in this book (Trusted Evals, Searchable Logs, Granular Rollback, Human Review Queue). |
| **Orchestration** (harness, runtime, routing) | **ORCHESTRATE layer + Agent Specifications + Architecture Blueprint** | The conductor. How models, tools, agents, and humans are routed. |
| **Economics** (per-task cost, build vs. buy, failure costs) | **Implicit across REWRITE Steps 4–6 + Appendix D** | Cost-of-coordination collapse expressed at the unit-economics layer. *Price per completed task* is the metric that matters. |
| (no industry-layer equivalent) | **LEARN** | The reason intelligence-dense firms compound. The industry vocabulary does not yet have a name for the layer that turns deployed agents into proprietary capital. This is one of the book's structural bets. |

**Two things to take from the crosswalk.** First, your team can speak either vocabulary without losing precision, translate at the boundary. Second, the absence of a LEARN-equivalent in the consensus 5-layer model is the gap your firm has the most asymmetric chance to exploit. Most firms will deploy agents on the first four layers and discover, two years in, that nothing compounds. The LEARN layer is what turns inference cost into intellectual property.

## Amazon Q Sidebar (verbatim from Chapter 4)

> **Sidebar: Amazon Q, when the enterprise stack fails.** PocketOS shows what happens to a startup. Amazon Q shows what happens to an enterprise running an autonomous coding agent at scale without a working control plane. In **December 2025, Amazon's coding agent autonomously decided to delete and recreate a live production environment**, a **13-hour outage of AWS in China**. In **March 2026, the Amazon Q developer led to 120,000 lost orders and 1.6 million website errors.** Days later, a second outage dropped **99% of North American marketplace orders for six hours.** Three incidents in roughly 90 days, inside the company that operates the largest agent runtime on the planet. The pattern is identical to PocketOS: destructive autonomy without a Permission Envelope, no kill switch enforcement, no approval threshold on irreversible operations. The cost difference is the only thing that scales, a startup loses a database; an enterprise loses 120,000 orders and a measurable share of quarterly revenue. **If Amazon can ship this, so can you.** The defense is the same: GOVERN/ASSURE on Day 1, scoped credentials, mandatory approval thresholds on destructive endpoints, soft-delete windows, and an Eval Suite that catches drift before the customer does.

## How to Apply This Reference

1. **When the team speaks 5-layer.** Walk the right column across, name what is yours (PURPOSE through GOVERN/ASSURE), and name the LEARN gap explicitly. The board hearing "Intelligence, Action, Governance, Orchestration, Economics" will assume those five are sufficient. Your job is to close that gap on the record.
2. **When greenlighting an enterprise deployment.** Read the Amazon Q sidebar aloud before signing off. Then walk the four Day-1 defenses (scoped credentials, mandatory approval thresholds, soft-delete windows, Eval Suite) and confirm each is in place. *If Amazon can ship this, so can you* is not rhetoric. It is a checklist trigger.
3. **In the Architecture Blueprint.** The two vocabularies should appear side by side once. After that, pick the operating-model vocabulary and stay with it. Two vocabularies are a translation cost; the choice of which to use day to day is yours.

## Source Notes

- Social Capital, in collaboration with Lederle Capital LLC. *A Primer on AI Agents: The 5 Layers of AI Agents.* May 2026.
- Amazon Q outage primary coverage: Fortune, MSN, TechRadar, Engadget, December 2025 AWS China outage and March 2026 Amazon Q developer incidents.
- Andrej Karpathy. X post on agent harness composability, February 20, 2026: *"the implied new meta is to write the most maximally forkable repo and then have skills that fork it into any desired more exotic configuration."* Reinforces the Crosswalk's right-column logic.
