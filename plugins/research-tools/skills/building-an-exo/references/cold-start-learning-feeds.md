# Cold-Start Learning for the Edge Twin: The Four-Feed Protocol

> Source: *The Organizational Singularity*, OS Outline v20, Chapter 9, REWRITE Step 5 (BUILD & PROVE). Salim Ismail with contributors, May 2026. v20 names the parallel run as **shadow mode** and specifies the four learning feeds that close the cold-start gap without forking corporate data.

## The Question

A new Edge Twin starts with no operating history on this workflow. How does it learn fast enough to outperform the legacy workflow without the legacy workflow's full data estate?

## The Position

The parallel run from REWRITE Step 5 *is* the shadow mode. The twin proposes, the human acts, and the gap between the two is the richest training signal the company will ever produce. Four feeds close the cold-start gap. None of them require forking the data estate.

The test of a real twin: **the human-override rate falls over time.** If it does not fall, you do not have a twin. You have workflow automation with a chat box.

## Feed 1: Historical Replay

A curated set of past cases for *this one workflow*. Not all data. The workflow record.

**What goes in.**

- Inputs (the data the workflow saw on the day it ran)
- The human decision (what the operator did)
- The action taken (what the system executed)
- The outcome (what happened next)
- The exception notes (why the case was hard, if it was hard)

**What goes out.** The twin practices on the curated set before going live in shadow. Performance on replay establishes a baseline. Drift between replay performance and live shadow performance is the first warning signal.

**Boundary.** Replay data is scoped to the Workflow Data Manifest. No fields outside the manifest are pulled into the replay set, even retrospectively.

## Feed 2: Shadow Comparison

During the parallel run, log every divergence:

- Twin recommendation vs. human action
- Twin recommendation vs. final outcome
- Human action vs. final outcome

**The signal lives in the gap.** When the twin agrees with the human and the outcome is good, you learn the workflow is well-instrumented. When the twin disagrees and the outcome favors the twin, you have evidence the twin is ahead of the human on that pattern. When the twin disagrees and the outcome favors the human, you have evidence the human is using context the twin lacks, and the next feed is what captures it.

**Instrumentation.** Every divergence logged on a correlation ID. Reviewed weekly by the workflow owner, the CAIO, and the human supervisor named in the Fiduciary Wedge.

## Feed 3: Human-Correction Capture

Every time a validator overrides the twin, capture the reason. Categorize using a controlled taxonomy. The taxonomy is workflow-specific; common categories include:

- **Strategic customer** (override to preserve a high-value relationship)
- **Policy exception** (override required by internal policy not yet codified)
- **Inventory constraint** (override required by physical reality the twin did not see)
- **Legal risk** (override required by regulatory or contractual exposure)
- **Data quality** (override because the twin's input was wrong)
- **Edge case** (override because the workflow hit a pattern the twin had not seen)

**Why this feed is the highest-value.** A workflow generates thousands of decisions and dozens of overrides. The overrides are the rare, expensive, judgment-heavy events. They carry more learning signal per case than every routine decision combined.

**Operational rule.** No override is captured without a reason from the taxonomy. *No reason, no override.* This is enforced in the validator UI.

## Feed 4: Synthetic Edge Cases

For rare or dangerous scenarios, generate synthetic cases so the twin practices on realistic patterns without touching sensitive records.

**Common synthetic scopes.**

- **Fraud** (synthetic transaction patterns that mimic known fraud signatures)
- **Supply disruption** (synthetic order, inventory, and shipment patterns for major-disruption scenarios)
- **Executive escalation** (synthetic patterns of high-visibility, high-pressure cases)
- **Regulatory edge** (synthetic patterns for cases sitting on a policy line)
- **Adversarial input** (synthetic prompt-injection and OWASP failure patterns)

**Generation.** Use the workflow's own data schema. Generate with parameters set by the workflow owner. Validate against the HIDO Six Questions for every synthetic object. Synthetic cases carry their own metadata flag so they never contaminate the production analytics.

**Boundary.** Synthetic data is generated, not copied. No real sensitive records are duplicated into the synthetic set. This is how rare-event practice happens without leakage.

## The Success Metric: Falling Human-Override Rate

A twin that does not improve is not a twin. The metric that proves the twin is real is the **falling human-override rate** over time.

**Baseline.** Measured on Day 1 of the parallel run. Typically high (50-80% override rate is common when the twin is new and the workflow is complex).

**Target.** Workflow-specific. Set by the workflow owner. A reasonable target for Wave 1 workflows is *the override rate falls by half within 60 days of parallel-run start*. The number matters less than the *trend*.

**The trend check.** Reviewed weekly. If the trend is not falling after the first month, treat it as a workflow signal, not a model signal. Common root causes include:

- The workflow is judgment-heavy and Wave 1 was the wrong placement (move to Wave 2 or Wave 3)
- The override taxonomy is wrong (too coarse, too fine, missing categories)
- The historical replay set was too narrow (rare events not represented)
- The human validators are overriding for inertia, not for cause (escalate to leadership)

## Mapping to GOVERN/ASSURE

The four feeds are not separate from the Four Pillars. They are *how* the Pillars hold during cold-start.

| Feed | Pillar that enforces it |
|---|---|
| Historical replay | Trusted Evals (the replay set is the eval set) |
| Shadow comparison | Searchable Logs (correlation-ID logging is the comparison instrumentation) |
| Human-correction capture | Human Review Queue (the queue is where corrections happen) |
| Synthetic edge cases | Trusted Evals (rare-event eval suite) |

If a pillar is below 3/5, the feed it supports is unreliable, and the cold-start protocol has a hole in it.

## The Failure Mode

Treating the parallel run as a *demo* instead of a *learning protocol*. The twin runs in parallel for 30 days, the team declares it ready, the legacy workflow is deprecated, and the override rate is never tracked again. Six months later the twin has drifted (Silent Drift, see `references/intelligence-stack.md`) and nobody noticed.

The defense. The four feeds run continuously, not just during the parallel run. Historical replay is the eval set. Shadow comparison is the divergence log. Human-correction capture is the override taxonomy. Synthetic edge cases are the rare-event eval suite. All four feed the LEARN layer of the Stack, which is the structural reason intelligence-dense firms compound (see `references/intelligence-stack.md`).

## The Cold-Start Sign-Off Checklist

Before the first parallel run begins:

- [ ] Workflow Data Manifest signed (see `templates/workflow-data-manifest-template.md`)
- [ ] Historical replay set curated and the eval baseline run
- [ ] Shadow comparison logging instrumented with correlation IDs
- [ ] Human-correction taxonomy defined and enforced in the validator UI
- [ ] Synthetic edge-case generators configured for the workflow's rare-event scopes
- [ ] Human-override rate baseline measured, target named, weekly review on the calendar
- [ ] Workflow owner, CAIO, and Fiduciary-Wedge supervisor confirmed for weekly review

If any line is unsigned, the parallel run is a pilot, not a Step 5 BUILD & PROVE.
