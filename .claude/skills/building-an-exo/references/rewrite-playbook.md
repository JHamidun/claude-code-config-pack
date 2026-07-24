# REWRITE: The Migration Playbook

> Source: *The Organizational Singularity*, OS Outline v20, Chapter 9, The REWRITE Playbook. Salim Ismail with contributors, May 2026. v13 added a **Four Pillars Maturity sub-rubric** to the Readiness Score, a **Miura-Ko L0–L5 cross-reference table**, and hardened the **Five Design Conditions** from aspirational principles into a binding Step-1 exit gate. **v15** added the Direct Mode existence proof. **v20** adds the **Workflow Data Manifest** as a Step 3 exit criterion (workflow-level companion to HIDO Six Questions per object) and the **cold-start learning protocol** for Step 5 (parallel run as shadow mode + four learning feeds; falling human-override rate as the success metric of a real twin). See `references/edge-twin-data-governance.md` and `references/cold-start-learning-feeds.md`.

REWRITE answers the method question: *what happens once the Edge Twin (or in Direct Mode, the company itself) is committed to the rebuild?*

The AI-native organization is not the old company made faster. It is the company redesigned from first principles, as if it were being built today with the full capability of agentic AI.

## Two Deployment Modes

- **Direct Mode (≤50 employees).** Apply REWRITE to the entire company. The CEO has line of sight to every workflow. No immune system to route around. Each step transforms in place.
- **Edge Mode (>50 employees).** REWRITE is the design specification for the Edge Twin (see `edge-deployment.md`). You do not apply it to the mothership. You build new at the edge, run REWRITE inside it from day one, then migrate workflows from mothership to edge using parallel-run-then-deprecate.

**Every step in REWRITE is identical across both modes. Only the migration mechanism changes.**

## One Governance Principle Across Every Step

The GOVERN/ASSURE control plane operates from Day 1, not as a gate between steps, but as a continuous layer.

- Governance agents monitor in **alert-only mode** first.
- Then with **escalation authority**.
- Then with **kill-switch capability**.

Every agent action logged with correlation IDs. Every autonomous decision has a defined escalation threshold. Every parallel run has pre-defined success criteria and rollback protocols. **Never turned off.**

## Six Steps. The Sequence Is Non-Negotiable.

### Step 1: BACKCAST & DEFINE

Before committing capital, before deploying agents, before running any assessment, define the destination.

Backcasting is the discipline of defining a principled vision of success in the future and working backward to identify the steps that connect present to destination. When the problems you face are complex and current trends are themselves part of those problems, forecasting forward is the wrong tool. *"Today Forward"* planning means the existing org chart, job families, and approval processes act as gravitational constraints on every AI initiative. Backcasting breaks this by replacing *"How does this fit into what we do?"* with *"What would we build from scratch, and what connects our current state to that destination?"*

**The output:** a specific, operational **Destination Architecture** document, the detailed picture of what ExO 3.0 looks like for *this* company in *this* sector. This becomes the navigation anchor for every subsequent REWRITE decision.

**The mechanism:** Run the **Backcasting Canvas** (`templates/backcasting-canvas.md`) as a 2–3 day facilitated executive workshop with the full C-suite. Outputs: Destination Architecture document, the Five Design Conditions instantiated for this context, leadership mandate in writing.

**Why this is Step 1.** Every REWRITE failure where the technology worked but the initiative still stalled traces to a missing or incomplete destination definition. Step 1 is the insurance policy against that failure mode.

**Exit criteria:**
- Destination Architecture signed by CEO.
- **Five Design Conditions instantiated as binding gate**, all five must hold for this context: (1) AI-Centric Workflow Architecture, (2) Recursive Improvement Infrastructure, (3) Model Sovereignty and Governed Autonomy, (4) Intelligence Density at Every Layer, (5) Human Flourishing as a Binding Constraint. **If any one is violated, the destination is incomplete and Step 1 is not done. Do not advance to Step 2.**
- Edge Twin pipeline ranked with value-at-stake.
- Architecture Blueprint for first Edge Twin.
- Steps 2–6 sequenced.
- Leadership mandate in writing.

### Step 2: ASSESS & PREPARE

Before committing to a full rewrite, you need to know where you stand and how fast you can move.

#### The REWRITE Readiness Score (eight dimensions, total 80)

Leadership scores the organization 1–10 across:

1. **Organizational Drag**, how much friction routine work generates today.
2. **AI Elevation**, how high in the org AI is treated as a strategic concern.
3. **Work Architecture**, whether the unit of analysis is the role or the task.
4. **Firm Boundary Design**, whether internal vs. external is treated as a capability question or a HR question.
5. **Decision Autonomy**, how much real authority sits with the people closest to the work.
6. **Network Structure**, whether information moves through hierarchy or through a network.
7. **Reinvention Cadence**, how often the organization redesigns itself.
8. **Tacit Knowledge Accessibility**, whether institutional knowledge is extractable. The dominant failure mode (Jones, OpenClaw 2026) is humans who cannot articulate their own operating logic.

**Bands:**

- **56–80**, Ready for full REWRITE.
- **33–55**, Foundational work needed first.
- **Below 33**, Survival risk. Urgent action required.

Retake every six months.

#### Four Pillars Maturity sub-rubric (v13)

Inside the Readiness Score, score each Four Pillars primitive 1–5 separately. Most companies score 1s. The **Four Pillars Maturity** number is the **minimum** across the four (not the average), that is what gates new agent deployment.

| Pillar | Score |
|---|---|
| Trusted Evals | __ / 5 |
| Searchable Logs with Correlation IDs | __ / 5 |
| Granular Rollback | __ / 5 |
| Human Review Queue | __ / 5 |
| **Four Pillars Maturity (minimum)** | **__ / 5** |

**Rule:** Do not deploy a new agent class until Four Pillars Maturity ≥ 3.

#### Miura-Ko L0–L5 cross-reference (v13)

The Readiness Score is the input. The Miura-Ko level is the lived reality. **If they diverge sharply, trust the ladder.**

| Readiness Score | Miura-Ko Level | What it means |
|---|---|---|
| Below 33 | L0–L1 | Theater or personal productivity. Fails Dabbling Test. |
| 33–55 | L2 | Team workflow. AI-enhanced silos. |
| 56–80 | L3 emerging, L4 forming | Compounding begins. |
| Not measurable yet | L5 | Generative noticing. Post-2031. |

*"A high Readiness Score with a low Miura-Ko level is the signature of a firm that has bought the architecture but hasn't deployed it, the most expensive failure mode in the framework."*

#### Choose Your On-Ramp

1. **Minimal Viable Intelligence Stack (MVIS).** One event bus, agent registry, central logging, one agent per class. Stand up in a week. Do this regardless of which path you take.
2. **90-Day Sprint.** Pick one high-coordination, low-judgment workflow and run it end-to-end on the MVIS. Run it as a controlled proof of the full loop, not as a decorative pilot.
   - Days 1–30, stand up MVIS and deploy sensing agents.
   - Days 31–60, build Capability Registry and pilot one cross-boundary workflow.
   - Days 61–90, deploy autonomous coordination, create Agency Maps for top 20 decisions, present to leadership.
3. **Full REWRITE.** The complete framework. Pace depends on starting position: a 30-person SaaS company may move through all six steps in under a year; a 10,000-person manufacturer with legacy ERP and union contracts may take two to three years. **The timeline is not the point. The sequencing is.**

Each on-ramp feeds the next. No one starts at Step 3 without first building the MVIS.

**Exit criteria:** Readiness Score complete. On-ramp selected. MVIS operational. If Sprint chosen: completed and presented.

### Step 3: EXTRACT

The Intelligence Stack needs something to work with. Most mid-to-large firms have **Data Rot**, institutional knowledge locked in PDFs, Slack threads, email chains, SharePoint graveyards, and the heads of people about to retire. SENSE and INTERPRET can't function on data that doesn't exist in accessible form.

#### Knowledge Archaeology

Identify where institutional knowledge actually lives. Never "the knowledge base." Scattered across long-tenured employees' personal processes, undocumented workarounds in spreadsheets, tribal knowledge in Slack, email threads that hold the actual decision rationale, retiring employees who carry irreplaceable context.

#### The Extraction Sprint

1. Identify top 20 workflows for REWRITE.
2. Map knowledge sources per workflow.
3. Conduct structured knowledge capture sessions with SMEs. Record, transcribe, structure. **The most time-sensitive task in the entire process, these people are leaving.**
4. Score each workflow 1–5 on data readiness.
5. Build initial data pipeline feeding SENSE.

#### The Codifier's Curse

Knowledge extraction simultaneously enables the Stack *and* accelerates the obsolescence of the humans who provided the knowledge. The people helping you build the system are building their own replacement. This is not a reason to skip extraction, the knowledge walks out the door regardless. But it is a reason to handle the process with transparency. **Tell people what the knowledge will be used for. Offer transition support as part of the extraction, not after.**

#### The Elicitation-First Principle

The first agent deployed for any human in the system shouldn't be a task executor. It should be an **elicitation agent**, an interviewer extracting the human's operating knowledge through structured conversation across five layers: operating rhythms, recurring decisions, dependencies, friction, judgment patterns. Output feeds directly into the Stack.

#### The Workflow Data Manifest (v20)

For each workflow you intend to migrate, produce a one-page **Workflow Data Manifest**: every data source the workflow touches, why it needs it, read or write, sensitivity tier, retention in the twin's memory, and the named data owner who approves access.

The manifest is the workflow-level companion to the HIDO Six Questions per object (`templates/hido-six-questions.md`). The six questions govern each object; the manifest governs the workflow's whole data surface.

**The rule is binary.** *If you cannot state why a workflow needs a field, the Edge Twin does not get it.*

This is the answer to the CIO's first question (see `references/edge-twin-data-governance.md`). Workflow-scoped access, not data-estate fork. Use `templates/workflow-data-manifest-template.md`.

**Exit criteria:** Data readiness scored. Knowledge capture complete for SMEs. Initial pipeline operational. **Workflow Data Manifest drafted for each migration-candidate workflow** (v20).

### Step 4: DIAGNOSE & STRIP

Subtraction before addition. AI amplifies whatever system it enters, including bureaucracy. **Give agents to a bureaucracy and you get faster bureaucracy.**

#### Zero-Based Organization Audit

- Which decisions require more than three humans?
- Where does information wait?
- Where does approval exist purely for risk theater?
- Which reports are never used?

**Target:** Identify the 50% of decision latency that is organizational habit, not regulatory requirement. Map every process against: *"If we built this today, would we build it this way?"*

#### The Task Decomposition Matrix

Run across top 3 functions (highest-coordination, highest-headcount, or highest-cost):

1. List every role.
2. Break each role into component tasks.
3. Categorize: judgment, pattern, coordination, creation.
4. Score each task 1–5 for Agent Readiness (5 = agent handles today; 1 = fully human).
5. Deploy: 4–5 → agents immediately. 3 → pilot in Step 5. 1–2 → stay human.

**This is the single most important diagnostic in the framework.** Use `templates/task-decomposition-matrix.md`.

#### Elevate AI to the Executive Layer: Appoint a CAIO

Reporting directly to the CEO. Strategic role with technical fluency. Responsible for decision automation, agent deployment, organizational redesign.

A CAIO who can't read a technical architecture diagram will be captured by vendors. A CAIO who can't read a P&L will be captured by engineers.

Comparable to the arrival of the CFO in the early 20th century. At first optional, soon unimaginable to operate without.

**Exit criteria:** Audit complete for top 3 functions. Task Decomposition scored for every role. CAIO appointed with board-level authority. 50% of identified drag flagged for removal.

### Step 5: BUILD & PROVE

Step 4 told you where the work is. Step 5 deploys agents against that work, proves they perform, and begins the structural shift from hierarchy to intelligence network.

#### Decision Handover Waves

- **Wave 1, Low-risk, high-frequency.** Pricing adjustments, inventory flows, customer routing, fraud detection. The 4s and 5s.
- **Wave 2, Medium-complexity.** Supplier selection, scheduling, product recommendations, quality control, cash flow management. The 3s and 4s.
- **Wave 3, Higher-judgment.** Strategic resource allocation, market entry/exit, risk modeling, capital deployment recommendations. The 2s and 3s.

**Rule:** *Humans set direction. Machines set velocity. Each wave proves before the next begins.*

#### Parallel-Run-Then-Deprecate (Edge Mode)

1. **Build** the agentic workflow.
2. **Run parallel**, both systems on the same inputs.
3. **Benchmark**, speed, cost, error rate, quality, throughput. Define success criteria *before* the run starts.
4. **Prove**, minimum 30 days for low-risk, 60–90 for medium and higher-judgment. Cover edge cases, seasonal variation.
5. **Deprecate**, once proven, shut down the legacy workflow. **Cleanly. Not gradually.**
6. **Next** workflow.

Never run more than 2–3 parallel workflows simultaneously.

#### How the Edge Twin Learns Cold-Start (v20)

A new Edge Twin starts with no operating history, and it does not need the full data estate to fix that. The parallel run above *is* shadow mode: the twin proposes, the human acts, and the gap between the two is the richest training signal in the building. Four feeds close the cold-start gap without forking corporate data:

1. **Historical replay.** A curated set of past cases for this one workflow: inputs, the human decision, the action taken, the outcome, and the exception notes. Not all data. The workflow record.
2. **Shadow comparison.** During the parallel run, log every place the twin's recommendation diverged from the human's action and from the final outcome. Divergence is the signal.
3. **Human-correction capture.** Every time a validator overrides the twin, capture the reason: strategic customer, policy exception, inventory constraint, legal risk. **Overrides are the highest-value training data the company produces.**
4. **Synthetic edge cases.** For rare or dangerous scenarios (fraud, supply disruption, executive escalation), generate synthetic cases so the twin practices on realistic patterns without touching sensitive records.

**The test of a real twin: the human-override rate falls over time.** If it doesn't, you don't have a twin. You have workflow automation with a chat box.

See `references/cold-start-learning-feeds.md` for the full protocol and instrumentation pattern.

#### Work Redesign: Tasks, Not Jobs

Wrong frame: jobs lost vs. jobs gained. Right frame: task-level analysis. The job is an Industrial Revolution artifact, a bundle of tasks assigned to a human because humans were the only available processing unit. Unbundle the job. Reassign tasks to whoever, or whatever, handles them best.

#### The People Side of Parallel Runs

Workflow migration can operate inside the edge venture. People migration cannot.

Every parallel run requires:
- A dedicated transition leader.
- Pre-deprecation conversations with every affected person.
- Explicit budget (10–15% of savings) for retraining, severance, and dual-staffing.

Three outcomes per affected person:
- **Concentrate**, expand judgment work in place.
- **Redeploy**, lateral move to the edge.
- **Exit with support.**

**Exit criteria:** All three Waves completed. Agent performance proven across benchmarks. At least 5 workflows migrated. People transition protocol executed. Stack expanded from MVIS to multi-agent deployment.

### Step 6: REWIRE & EVOLVE

Steps 4 and 5 diagnosed the work and proved workflows. Step 6 redesigns the organization itself, structure, boundaries, operating rhythm, around the Stack. **This is where REWRITE earns its name.**

#### Transition from Hierarchy to Intelligence Network

The org chart is a latency map. Replace it.

The Stack, six cognitive layers plus GOVERN/ASSURE, replaces departmental silos. Pod-based intelligence networks. Manager-to-IC ratios moving from 1:6 to 1:20+. Hybrid: fluid pods on top of a thin residual accountability hierarchy.

#### Re-architect the Firm Boundary

Coase revisited. By this point, you have extensive data on what agents can do, what humans must do, where the firm boundary actually needs to be. Apply the sector-appropriate ratios from Elastic Agency. Internal humans become the high-trust, high-judgment core. External elastic talent plugs in for defined sprints. Agents handle coordination that used to require permanent headcount.

**CEO diagnostic:** *"If we built this company today with AI, how many employees would we actually hire?"* The delta is your redesign roadmap.

#### Continuous Corporate Rebirth

The industrial firm optimized for stability. The AI-native firm optimizes for perpetual redesign. This is a structural requirement, not a philosophical preference.

- **Organizational Half-Life.** *"How long before half of what we do is obsolete?"* If the answer isn't shrinking every year, you're falling behind.
- **The Continuous Kill Switch** becomes permanent operating rhythm. Detection → Action → Migration. The loop is continuous.

**Exit criteria:** Hierarchy replaced by pod-based intelligence network. Firm boundary redesigned based on actual agent performance data. Continuous Kill Switch operational. Organizational Half-Life measured at board level. Reinvention cadence built into compensation.

#### The Human Shift

Continuous rebirth ≠ continuous layoffs. It means continuous evolution. **Humans who operate across multiple intelligence layers become the most valuable assets.**

## REWRITE Summary

Six steps, sequenced but not time-bound. Step 1 defines the destination. Step 2 assesses readiness and stands up the MVIS. Step 3 extracts the institutional knowledge the Stack needs. Step 4 diagnoses the work and strips drag. Step 5 deploys agents, proves performance, migrates workflows. Step 6 redesigns the organization around the Stack and institutionalizes continuous rebirth.

**Skipping Step 1 is the fastest way to fail.**
