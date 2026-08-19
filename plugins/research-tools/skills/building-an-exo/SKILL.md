---
name: building-an-exo
version: 1.3.0
description: "Справочник ExO 3.0 (OpenExO) для AI-перестройки компании: Intelligence Stack, REWRITE, Edge Twin, DRIVE/SHAPE, MTP. Триггеры: «экспоненциальная организация». НЕ маркетинг/CRO."
metadata:
  license: MIT
  source: "Salim Ismail — The Organizational Singularity, OS Outline v20 (OpenExO Pro, May 2026); operationalized by Kent Langley"
---

# Building an ExO Skill

## Attribution

This skill encodes the operating model published as *The Organizational Singularity* (OS Outline v20, May 2026), authored by **Salim Ismail with contributions from Dea Csuba, Charles Klasson, Kent Langley, Tony Manley, Vivek Matthews, Marconi Pereira, Ann Ralston, Gary Ralston, Miguel Angel Rojas, Patrik Sandin, Yuri van Geest, and Giovanni Pupo**. The frameworks (ExO 3.0, MTP-as-protocol, DRIVE, SHAPE, the Intelligence Stack, REWRITE, Edge Deployment, the Fiduciary Wedge, the Continuous Kill Switch, the PocketOS sidebar, the Amazon Q sidebar, the Middle 60% problem, the Four Pillars of GOVERN/ASSURE, the HIDO Six-Question Diagnostic, Silent Drift, the Peter Principle for AI Agents, Cross-Organizational Accountability, the Intelligence Stack ↔ 5-Layer Agent Stack Crosswalk, the Edge Twin Data-Governance sidebar, the Workflow Data Manifest, the Cold-Start Learning Protocol, the CIO Edge Twin Diagnostic) are the authors' intellectual property. The Miura-Ko L0–L5 ladder is attributed to Ann Miura-Ko (Floodgate, April 2026).

ExO 1.0 (the SCALE/IDEAS canvas) and the original MTP construct were introduced in *Exponential Organizations* (Salim Ismail, Michael S. Malone, Yuri van Geest, 2014). ExO 3.0 supersedes SCALE/IDEAS while preserving MTP, now upgraded to a three-layer machine-readable protocol. v13 was the **Accountability & Auditability pass** over v10 (Four Pillars, HIDO, Silent Drift, Peter Principle, Miura-Ko ladder, Cross-Organizational Accountability). **v15 was the Social Capital Primer Integration pass** over v14 (industry-vocabulary crosswalk, Amazon Q enterprise-scale failure sidebar, Direct-Mode existence proof via Steinberger / OpenClaw, tokens-as-COGS, per-outcome pricing). **v20 is the Edge Twin Data-Governance Pass** over v15-v18: framework architecture is unchanged, but the book now answers the CIO's first objection (does the Edge Twin fork the enterprise data estate? No), pins data access at the workflow level (Workflow Data Manifest), names the cold-start learning protocol (parallel run as shadow mode + four learning feeds), maps the Four Pillars onto the major AI risk taxonomies (NIST AI RMF, OWASP LLM Top 10, CSA AICM), and hands the CIO a ten-question diagnostic with a red/amber/green readiness gate (Appendix F).

Additional v20 sources cited in this skill: NIST, *AI Risk Management Framework* (2023), `https://www.nist.gov/itl/ai-risk-management-framework`; OWASP Foundation, *Top 10 for LLM Applications*, `https://owasp.org/www-project-top-10-for-large-language-model-applications/`; Cloud Security Alliance, *AI Controls Matrix* (243 control objectives across 18 domains, July 2025), `https://cloudsecurityalliance.org/artifacts/ai-controls-matrix`. v15 sources retained: Social Capital, *A Primer on AI Agents: The 5 Layers of AI Agents* (with Lederle Capital LLC, May 2026); Andrej Karpathy's *"maximally forkable repo"* X post (February 20, 2026); Dylan Patel / SemiAnalysis (newsletter and *Invest Like the Best* appearance, 2026); Salesforce, *Headless 360 and Agentforce Consumption Pricing* (April 15, 2026 launch); Amazon Q outage primary coverage in Fortune, MSN, TechRadar, and Engadget; IDC, *Worldwide AI Agents Forecast, 2025–2030*.

This skill is an operational adaptation for AI created by Kent Langley for ExO Builders. It is not a substitute for the source. Anyone applying the material in client engagements, teaching, publishing, or commercial settings should credit the authors and cite the source at `https://openexo.com/organizational-singularity`.

## Related Skills

## Triggers

- Founder or CEO is asking "what would we build today, with AI, from scratch?"
- The firm has launched isolated AI pilots that produced 20–40% gains and stalled. (Phase 2 trap.)
- Leadership has cut headcount without redesigning the underlying workflows. (Anti-case study from Chapter 10.)
- A board or investor has asked the CEO to publish an AI strategy and the CEO doesn't have a destination architecture.
- The firm is preparing for or executing a workforce transition affecting more than 10% of staff.
- An AI agent already operates somewhere in the business without a documented Permission Envelope or Fiduciary Wedge.
- The firm is single-vendor on foundation models or orchestration. (Cognitive captivity risk.)
- A high-coordination, low-judgment workflow has been identified as a candidate for an MVIS pilot.
- The firm is over 50 employees and any AI initiative is stalling inside an existing business unit. (Immune system signal.)
- The firm is under 50 employees and the founder is debating whether to grow headcount or grow agency.
- Intelligence density (revenue per employee, throughput per person, ARR growth per dollar of net burn) is on the diagnostic table.
- A near-miss has occurred, production data damaged by an agent, an autonomous decision outside the envelope, an unsafe handover. (PocketOS pattern.)
- The CEO needs to decide between Direct Mode and Edge Mode and is reaching for the wrong one.
- Mission-driven entity (government, non-profit) needs an Edge Mode adaptation that respects the immune-system-is-law constraint.

## Core Directives

### The Three Things to Remember

- MUST anchor every conversation in the three-part frame: **Destination (ExO 3.0)**, **Operating System (Intelligence Stack)**, **Playbook (REWRITE)**. Skip the rest of the framework if needed; never skip these three.
- MUST treat the Intelligence Stack as the operating core. The other nine ExO 3.0 characteristics define the context in which the Stack operates. Build the Stack first.
- MUST refuse the temptation to teach DRIVE without SHAPE or SHAPE without DRIVE. *DRIVE without SHAPE crashes. SHAPE without DRIVE stalls. You need both.*

### ExO 3.0: The Destination Architecture

- MUST replace ExO 1.0's SCALE/IDEAS split with the ten-characteristic ExO 3.0 frame: MTP plus DRIVE (5) plus SHAPE (5). The internal/external distinction is obsolete; the firm boundary has collapsed.
- MUST encode MTP as a **three-layer machine-readable protocol**, not a poster:
  - **Constraint Layer**, what agents are categorically forbidden from doing. Hard constraints, not aspirational values.
  - **Decision Layer**, weighted priorities agents use when facing tradeoffs.
  - **Identity Layer**, the cultural cohesion mechanism that replaces "the office."
- MUST apply both MTP litmus tests before signing off:
  1. *Could an AI agent, given only your MTP protocol, make a decision your leadership team would endorse?* If no, your MTP is a poster.
  2. *Could that agent, given only your MTP, decide what NOT to build?* When execution is nearly free, the feature factory is the dominant failure mode.
- MUST enforce the Five Design Conditions as principled anchors, not KPIs: AI-Centric Workflow Architecture, Recursive Improvement Infrastructure, Model Sovereignty and Governed Autonomy, Intelligence Density at Every Layer, Human Flourishing as a Binding Constraint. If any condition is violated, the architecture fails.
- MUST locate every advantage on the Three Compounding Loops (Intelligence, Trust, Governance) and verify that no loop is being optimized at another's expense. The Intelligence Loop creates advantage. The Trust Loop scales it. The Governance Loop keeps it from collapsing under its own velocity. **Optimizing one loop at another's expense is the dominant ExO 3.0 failure mode.**
- MUST locate the firm on the **Miura-Ko L0–L5 AI-pilled ladder** alongside the binary Dabbling Test: L0 Theater, L1 Personal Productivity, L2 Team Workflow, L3 Organizational Infrastructure (where the architecture starts to compound), L4 Compounding Operating System (where Value Moats form), L5 Virtually Self-Driving (does not yet exist). **Trust-the-ladder rule:** if the Readiness Score and the Miura-Ko level diverge sharply, trust the ladder. A high Readiness Score with a low Miura-Ko level signals a firm that has bought the architecture but hasn't deployed it, *the most expensive failure mode in the framework.*

### DRIVE: The Intelligence Engine (score 1–5 each, total 25)

- MUST score and stage all five components in any assessment:
  - **D, Decision Architecture.** Two-way doors get speed; one-way doors get human gating. Map every decision type to who decides, under what conditions, with what guardrails. (Bezos, Taleb, Hart.)
  - **R, Recursive Learning.** Workflows versioned, performance measured, improvements codified and propagated. The LEARN layer of the Stack runs this at machine speed.
  - **I, Intelligence Stack.** The operating core (six layers + GOVERN/ASSURE). Treat as separate Stack section below; in DRIVE scoring, score whether the Stack exists and is operational.
  - **V, Value Moat.** Five sources: proprietary data, network effects, intelligence density, reconfiguration speed, curatorial judgment. Any moat that depends on customer inertia is a wasting asset, price it and plan its replacement.
  - **E, Elastic Agency.** Capability Registry, Graduated Authority, Decision Boundary in practice. Apply sliding talent ratios by sector; expect ~10 points/year shift toward AI as agent capability compounds.
- MUST apply the **GOVERN-cap rule**: a high DRIVE score in the absence of GOVERN/ASSURE is overstated. Cap the DRIVE total at 13/25 until GOVERN exists in alert-only mode at minimum. This is the PocketOS lesson institutionalized.
- MUST score the **Four Pillars of GOVERN/ASSURE** as a sub-rubric inside I = Intelligence Stack: Trusted Evals, Searchable Logs with Correlation IDs, Granular Rollback, Human Review Queue. **Cap the I score at the lowest pillar.** Most companies score 1s on at least three pillars, that is the size of the gap. **Do not deploy a new agent class until each pillar scores ≥ 3.**
- MUST flag **Silent Drift** (the dominant production failure mode): agents do not crash, they degrade slowly. Detection requires the Trusted Evals pillar with quantified thresholds (e.g., accuracy floor + override-rate ceiling). Absent eval suites, drift is discovered in customer escalations rather than dashboards.
- MUST flag **cognitive captivity**: if the Stack runs on a single provider's foundation models and infrastructure, the moat is around someone else's castle. Maintain inference capability across at least two model families. Own orchestration logic and fine-tuning data.
- MUST flag **customer-side agent inversion**: design for the agent buyer, not just the human buyer. Pricing, APIs, contract terms, SLAs, increasingly read by agents on behalf of customers. The slow side of an agent-to-agent negotiation loses by definition.
- MUST surface the **Block warning** when peer firms cite Dorsey's three-role structure as a template: Block is the canonical **DRIVE-without-SHAPE** case at corporate scale. Ask three questions in order. *Where is your Fiduciary Wedge? Where are the Four Pillars? What is your Continuous Kill Switch?* Silence is the warning.

### SHAPE: The Organizational Form (score 1–5 each, total 25)

- MUST score and stage all five components:
  - **S, Safe Autonomy.** The Fiduciary Wedge (every agent decision chains to a named human owner), compliance-as-code, kill switches at every Stack layer, audit trails, agent-to-agent oversight.
  - **H, Human Architecture.** Where human cognition creates irreplaceable value. Honest absorption modeling for the Middle 60% (the cohort that was excellent at coordination and process). Engineer the missing junior loop; without it the senior-talent pipeline runs out in a decade. Engineer the bridge against bifurcation/caste formation.
  - **A, Adaptive Architecture.** Modularity + antifragility. Every layer of the Stack swappable, retargetable, upgradable without rebuilding the whole. Pod-based intelligence networks replace fixed hierarchies.
  - **P, Purpose Control.** MTP as three-layer protocol (see Destination above). Compensation alone is insufficient binding; shared purpose, visible impact, judgment that shapes outcomes is what holds top talent.
  - **E, Ecosystem Trust.** Trust as protocol: cryptographic identity, verifiable credentials, smart contracts, audit trails, mechanism design (prediction markets, quadratic voting, combinatorial auctions, retroactive funding). Design for cognitive blocs (US/China/EU divergence); treat unified ecosystem as the optimistic scenario.
- MUST refuse to dress headcount reduction as architecture. If absorption math has not been honestly modeled, score H ≤ 2/5. The federal-workforce anti-case study is the warning.
- MUST insist that Permission Envelopes have **scope isolation**, **approval thresholds for destructive actions**, and **soft-delete windows for irreversible operations**. The PocketOS / Cursor / Railway sequence (April 24, 2026, nine seconds from misconfigured token to gone production database and three months of backups) is the canonical SHAPE failure.
- MUST require the **HIDO Six Questions** answered for every data object an agent reads or writes: what is it / who says so / how can it be used / legal terms / what if wrong / dispute resolution. Carry the answers as immutable, hashed, signed metadata bound to the data object. The agent spec without the data spec is a half-architecture.
- MUST apply the **Cross-Organizational Accountability** stack before any cross-firm agent transaction: (1) policy-controlled API surface for external agents, (2) HIDO metadata travelling with the data, (3) liability framework codesigned with counterparty in advance, not in court. *If legal is not in the room when the integration is designed, the integration is a future lawsuit.* In the agent economy, **the moat is the trusted accountability stack, not the smartest agent.**
- MUST cite **Haier (RenDanHeYi / ZeroDX)** as the strongest pre-AI existence proof that the post-hierarchy firm scales at 80K-person scale, pair with Block to show the destination is viable, not aspirational.

### The Intelligence Stack: The Operating Core

- MUST treat the Stack as **Boyd's OODA loop scaled to enterprise architecture and run continuously at machine speed**. Six cognitive layers plus a cross-cutting control plane:
  - **PURPOSE**, sets objectives and constraints derived from the MTP. The constitutional layer Boyd assumed but never named.
  - **SENSE**, collects signals (Observe).
  - **INTERPRET**, builds context, retrieves history, frames scenarios (Orient, the most important loop).
  - **DECIDE**, generates options and commits within the Permission Envelope (Decide).
  - **ORCHESTRATE / ACT**, executes through tools, workflows, APIs, humans, robots, and other agents (Act).
  - **LEARN**, evaluates outcomes, updates models, propagates improvements (the feedback loop OODA implied; we make it a layer).
  - **GOVERN/ASSURE**, cross-cutting control plane. Logs every decision, enforces guardrails, owns kill switches. **Never off.**
- MUST require an **Agent Specification** for every deployed agent with eight properties: Purpose, Autonomy Tier, Permission Envelope, Memory Boundary, Escalation Rules, Eval Suite, Telemetry/Audit Trail, Reusability Scope. *No spec, no agent.*
- MUST require **Reusability Scope** in every agent spec. Agents built without it become single-purpose artifacts; agents with it become compounding capital. (McKinsey diagnostic, April 2026.)
- MUST require the **HIDO Six Questions** for every data object the agent reads or writes. The agent spec governs *who is allowed to act and how*; HIDO governs *what may be done with each piece of evidence*. The two are symmetric, `templates/agent-specification.md` and `templates/hido-six-questions.md`.
- MUST operationalize the **Four Pillars** as the production check on GOVERN/ASSURE: Trusted Evals, Searchable Logs with Correlation IDs, Granular Rollback, Human Review Queue. Score each 1–5. **No new agent class deploys until every pillar scores ≥ 3.**
- MUST cite the **Four Pillars Standards Mapping (v20)** whenever a CISO, auditor, or board member asks how the Pillars relate to industry frameworks. The Pillars *operationalize* the major AI risk taxonomies; they do not restate them. NIST AI Risk Management Framework (2023) governs risk across design, development, use, and evaluation. OWASP Top 10 for LLM Applications names the failure modes the Pillars catch (prompt injection, sensitive-information disclosure, insecure output handling, excessive agency). CSA AI Controls Matrix (243 controls across 18 domains, July 2025) is the controls superset. The Pillars are the production implementation of what those frameworks specify in the abstract. See `references/four-pillars-standards-mapping.md`.
- MUST stand up the **Minimal Viable Intelligence Stack (MVIS)** in week one regardless of which on-ramp the firm chooses: one event bus, basic agent registry, central logging, one agent per class. Every firm that skipped the MVIS regretted it within 60 days.
- MUST apply the **Intelligence Stack ↔ Social Capital 5-Layer Agent Stack Crosswalk** when the team, vendors, or board are speaking the industry-canonical vocabulary (Intelligence / Action / Governance / Orchestration / Economics). The book's Stack is the same architecture told as an *operating model*, not as an engineering stack: PURPOSE + SENSE + INTERPRET ↔ Intelligence; DECIDE + ORCHESTRATE/ACT ↔ Action; GOVERN/ASSURE + Four Pillars ↔ Governance; ORCHESTRATE layer + Agent Specs + Architecture Blueprint ↔ Orchestration; REWRITE Steps 4–6 + Appendix D ↔ Economics. **LEARN has no industry-layer equivalent**, that is the structural bet of this book, and the asymmetric opportunity for any firm that builds it. See `references/social-capital-crosswalk.md`.
- MUST deliver the **Amazon Q sidebar** lesson whenever an enterprise (Tier 4–5, regulated, or operating an autonomous coding agent at scale) is greenlighting deployment without a working control plane. The pattern is identical to PocketOS, the cost difference is the only thing that scales: Dec 2025 13-hour AWS China outage, Mar 2026 120,000 lost orders + 1.6M website errors, follow-on 99% North American marketplace order drop in six hours. **If Amazon can ship this, so can you.** Defense: GOVERN/ASSURE on Day 1, scoped credentials, mandatory approval thresholds on destructive endpoints, soft-delete windows, an Eval Suite that catches drift before the customer does.

### REWRITE: The Migration Playbook (six steps, sequence non-negotiable)

- MUST run the steps in order. **Skipping Step 1 is the fastest way to fail.**
  1. **BACKCAST & DEFINE**, produce a Destination Architecture document from a 2–3 day facilitated executive workshop. Output: signed Destination Architecture, **Five Design Conditions instantiated as a binding exit gate** (if any one of the five is violated, the destination is incomplete and Step 1 is not done, do not advance), Edge Twin pipeline ranked, Architecture Blueprint for first Edge Twin, leadership mandate in writing.
  2. **ASSESS & PREPARE**, run the Readiness Score across eight dimensions (Organizational Drag, AI Elevation, Work Architecture, Firm Boundary Design, Decision Autonomy, Network Structure, Reinvention Cadence, Tacit Knowledge Accessibility). Bands: 56–80 ready; 33–55 foundational work; <33 survival risk. **Add Four Pillars Maturity sub-rubric (minimum across the four pillars, ≥ 3 to deploy new agents) and Miura-Ko L0–L5 cross-reference (if score and ladder diverge, trust the ladder).** Retake every six months. Choose on-ramp (MVIS / 90-Day Sprint / Full REWRITE).
  3. **EXTRACT**, Knowledge Archaeology + Extraction Sprint + Elicitation-First Principle + **Workflow Data Manifest (v20)**. The first agent deployed for any human shouldn't be a task executor; it should be an elicitation agent. Treat extraction with transparency and offer transition support as part of the process, not after. **Produce a one-page Workflow Data Manifest for each workflow you intend to migrate**: every data source the workflow touches, why it needs it, read or write, sensitivity tier, retention in the twin's memory, and the named data owner who approves access. The manifest is the workflow-level companion to the HIDO Six Questions per object. **The rule is binary: if you cannot state why a workflow needs a field, the Edge Twin does not get it.** The Manifest is a Step 3 exit-criterion.
  4. **DIAGNOSE & STRIP**, Zero-Based Organization Audit and **Task Decomposition Matrix** (the single most important diagnostic). Score every task 1–5 for Agent Readiness. Appoint a CAIO with both technical fluency and P&L literacy, reporting directly to the CEO.
  5. **BUILD & PROVE**, Decision Handover Waves (low-risk → medium → higher-judgment). Parallel-run-then-deprecate with success criteria defined before the run starts. Never more than 2–3 parallel workflows simultaneously. Budget 10–15% of savings for People Side of Parallel Runs (transition leader, retraining, severance, dual-staffing). **Cold-start learning protocol (v20):** the parallel run *is* shadow mode. Close the cold-start gap without forking corporate data using four learning feeds: (1) historical replay (curated workflow records, not the whole estate), (2) shadow comparison (every divergence between twin recommendation, human action, and outcome, logged), (3) human-correction capture (override reasons, strategic customer / policy exception / inventory constraint / legal risk; overrides are the highest-value training data the company produces), (4) synthetic edge cases (for rare/dangerous scenarios such as fraud, supply disruption, executive escalation). **The test of a real twin: the human-override rate falls over time.** If it doesn't, you don't have a twin; you have workflow automation with a chat box.
  6. **REWIRE & EVOLVE**, replace the org chart (a latency map) with pod-based intelligence networks. Re-architect the firm boundary using sector-appropriate Elastic Agency ratios. Make the **Continuous Kill Switch** the permanent operating rhythm. Measure Organizational Half-Life at the board level.
- MUST keep GOVERN/ASSURE alive across every step: alert-only at first, then with escalation authority, then with kill-switch capability. Not a gate between steps; a continuous layer.
- MUST recognize that the timeline is not the point. The sequencing is. A 30-person SaaS company may move through all six steps in under a year; a 10,000-person manufacturer with legacy ERP and union contracts may take two to three years.

### Edge Deployment: Where REWRITE Happens

- MUST choose the deployment mode by headcount and immune-system mass:
  - **≤50 employees: Direct Mode.** The company IS the edge. No immune system strong enough to kill transformation. Apply REWRITE to the whole company in place.
  - **>50 employees: Edge Mode mandatory.** Spawn a 3–5 person Edge Twin plus an agent cluster, board-mandated and CEO-sponsored, reporting directly to the CEO.
- MUST refuse to apply REWRITE inside the mothership at >50 employees. The framework can be right and still fail because the host organism rejects it. *You are not rebuilding the airplane while flying it. You are climbing into the jet engine turbine to fix it while the plane is in the air.*
- MUST anchor the Edge Twin rationale on the **Peter Principle for AI Agents** (Varsavsky, 2026): every AI system will be pushed to the limits of its competence; the only way to discover the autonomy ceiling is by going too far and recovering. **That recovery loop IS the learning mechanism.** It cannot run on customers of record. The Edge Twin is the only safe place to discover the ceiling. **Granular Rollback** (Pillar 3) must be in place before the Edge Twin begins this work.
- MUST fund the Edge Twin from the CEO's budget or board allocation, **never from a division budget** (immune system attack vector). Shared upside with the edge team; salaried teams optimize for survival, teams with skin optimize for results.
- MUST answer **"Does the Edge Twin fork your data?" (v20)** before the project is funded. **No.** The Edge Twin does not copy the enterprise data estate and does not get super-user access to production databases. It gets workflow-scoped, governed API access to the specific systems one migrated workflow needs. Read and write are separated. Every call is logged on a correlation ID. Credentials are short-lived and revocable. **Operational systems remain the source of truth: if the Edge Twin and the ERP disagree, the ERP wins.** The twin is the reasoning and orchestration layer, not a second system of record. This is the first question every CIO asks; the wrong answer kills the project before it starts. See `references/edge-twin-data-governance.md`.
- MUST hand the CIO **Appendix F: The CIO Edge Twin Diagnostic (v20)** before the first Edge Twin is funded. Ten governance questions answered in the book's framework language: (1) what is the twin allowed to do (Autonomy Tier + Decision Handover Waves), (2) what is the source of truth (operational systems; ERP wins), (3) what data does the twin need and why (Workflow Data Manifest + HIDO Six Questions), (4) does the twin train on the data (access ≠ training; pin retention, training rights, deletion rights, audit rights, model isolation in vendor contracts), (5) how do we prevent leakage (Permission Envelope + GOVERN/ASSURE catching OWASP failure modes), (6) how is identity handled (scoped workload identity, short-lived credentials, per-action logging, Searchable Logs with correlation IDs), (7) what happens when the twin is wrong (confidence score, source citation, decision rationale, human-approval rule, rollback path, audit log, exception queue: Granular Rollback + Human Review Queue), (8) who is accountable (named human, always: the Fiduciary Wedge), (9) what is the smallest safe first workflow (high coordination-to-judgment ratio, high-volume, rule-clear, measurable, reversible, low regulatory exposure; good: support triage, invoice-exception routing, order-status exceptions, renewal-risk detection; bad: hiring/firing, credit approval, strategic-account pricing, financial reporting, anything safety-critical), (10) how will we measure success (benchmarks set before parallel run; cycle time, error rate, cost per transaction, policy exceptions, experience scores; **the human-override rate must fall over time**). **Readiness gate: score each red/amber/green. Any red on 5, 6, 7, or 8 blocks the build. These four are the SHAPE controls.** Skipping them produces the PocketOS pattern. See `templates/cio-edge-twin-diagnostic.md`.
- **Discipline note: no third autonomy ladder.** The book retains the **Autonomy Tier** (per agent spec) and the **Decision Handover Waves** (per REWRITE Step 5). Reject the source paper's "Level 0–5 autonomy maturity ladder." Do not invent a competing ladder.
- MUST build the **Cross-Organizational Accountability stack** (policy-controlled API surface + HIDO metadata travel + codesigned liability framework) before the first cross-firm agent-to-agent transaction. The Edge Twin will eventually transact with other firms' agents; the architecture for that lives in Chapter 3.
- MUST sequence migration **easiest first**, low-risk customer routing, pricing, inventory before procurement, scheduling, QC before resource allocation, market entry/exit. One workflow at a time. Prove. Move to the next.
- MUST recognize that for any government, non-profit, or mission-driven entity, Direct Mode does not exist, the immune system is law. Edge deployment is the only path. Adapt for procurement timelines and political theatre, both solvable with executive-layer mandate.

### The Vertical Rewrite: What Happens to Each Human Layer

- MUST map the rewrite to all three human layers, not just one:
  - **C-Suite, From Strategy Owner to Purpose Holder.** AI absorbs information synthesis, scenario modeling, strategic sensing. Leaders are left with purpose, judgment, capital allocation, accountability. The Continuous Kill Switch lives at this layer.
  - **Middle Layer, From Coordinator to Exception Architect.** AI absorbs coordination, reporting, workflow routing, status visibility. Managers become exception architects and talent developers. This is where the Middle 60% problem and the missing junior loop live.
  - **Coalface, From Task Executor to Agentic Operator.** AI absorbs routine execution. Frontline work becomes supervision, escalation, relationship handling, continuous improvement. Pod-based, agent-augmented, with real promotion paths into the inner ring.
- MUST avoid the consolation-prize framing. "You are now an exception handler" is a category error dressed as opportunity unless the firm has actually engineered the new role with budget, training, and authority.

### Tier-Appropriate Application

- MUST adjust depth and ambition to the OpenExO ICP tier (see `/org-config/icp.md`).
- **Tier 2 (≤50 employees, ≤$2M revenue), Direct Mode.** Apply REWRITE to the whole company. Stand up MVIS in week one. Use a 90-Day Sprint on the highest-coordination workflow. The founder can run BACKCAST themselves with a one-day workshop. SHAPE Human Architecture is small-team work; absorption math is simpler but no less honest. **v15 existence proof**, Peter Steinberger built the first version of OpenClaw on a single Friday evening in November 2025, ran 4–10 agents in parallel, pushed 6,600+ commits in January 2026 alone, surpassed 145,000 GitHub stars within weeks with no team and no revenue, and received acquisition bids from Meta and OpenAI in the same window. Solo-founded startups are now 36.3% of new ventures (Social Capital primer, May 2026). Direct Mode is not a thought experiment; it is the modal new company.
- **Tier 3 ($2M–$10M, 20–80 employees), Direct or borderline Edge.** If headcount is climbing past 50 with managerial layers forming, spawn the Edge Twin proactively before the immune system hardens. Run DRIVE and SHAPE assessments quarterly. CAIO appointment becomes a real role at this stage, not a hat.
- **Tier 4–5 ($10M+, 80+ employees), Edge Mode mandatory.** Spawn 3–5 person Edge Twin reporting to CEO. Board-level Continuous Kill Switch with quarterly review of Organizational Half-Life. Treat Sliding Talent Ratios as portfolio-level capital allocation. Sovereign AI capability becomes a strategic discussion, not a vendor-selection exercise.

### Output Discipline

- MUST produce concrete, named recommendations: a specific Destination Architecture, a scored Readiness Score with bands, a ranked Task Decomposition Matrix, named candidate workflows for Wave 1.
- MUST cite ExO 3.0 vocabulary precisely (DRIVE, SHAPE, MVIS, Edge Twin, Fiduciary Wedge, Continuous Kill Switch, Permission Envelope, Autonomy Tier, Capability Registry). Do not invent neighboring terms or use ExO 1.0 SCALE/IDEAS vocabulary by accident.
- MUST flag every assumption that needs human verification: "We've assumed the Stack runs on at least two model families, confirm with the CAIO before this Readiness Score is final."
- MUST acknowledge survivorship bias when citing case examples (Cognition Labs, Pieter Levels, Klarna, Nespresso, FifthRow, Board of Innovation). The pattern is real; the outcome is not guaranteed.

## Validation Checkpoints

Before concluding any building-an-exo application:
- [ ] The Destination Architecture has been named, not just gestured at.
- [ ] **Five Design Conditions instantiated as binding Step-1 exit gate**, all five hold for this context; none violated.
- [ ] MTP is staged as three-layer protocol (Constraint, Decision, Identity), not as poster language.
- [ ] DRIVE has been scored across all five components with the GOVERN-cap rule applied.
- [ ] **Four Pillars of GOVERN/ASSURE scored 1–5 each** (Trusted Evals, Searchable Logs with Correlation IDs, Granular Rollback, Human Review Queue), I capped at the lowest pillar; no new agent class deploys until each pillar ≥ 3.
- [ ] SHAPE has been scored across all five components with honest Middle 60% absorption math.
- [ ] **HIDO Six Questions answered** for every data object an agent reads or writes; metadata immutable, hashed, signed.
- [ ] **Silent Drift detection**, every production agent class has named eval thresholds (accuracy floor + override-rate ceiling); drift triggers retraining or rollback.
- [ ] **Cross-Organizational Accountability stack** in place before any cross-firm agent transaction, policy-controlled API surface, HIDO metadata travel, codesigned liability framework with counterparty.
- [ ] The Intelligence Stack is identified at MVIS, intermediate, or full level, and the gap to MVIS is named.
- [ ] **Miura-Ko L0–L5 level identified** alongside the Readiness Score; if they diverge, the ladder wins.
- [ ] Every deployed or proposed agent has an Agent Specification (or a placeholder with the missing fields named).
- [ ] Direct Mode vs. Edge Mode has been chosen on headcount and immune-system mass, not preference.
- [ ] **Edge Twin rationale anchored on the Peter Principle for AI Agents**, Granular Rollback in place before push-to-limits-then-recover begins.
- [ ] At least one Wave 1 workflow has been named, with success criteria for the parallel run.
- [ ] The People Side of Parallel Runs has a budget figure (10–15% of savings) and a named transition leader.
- [ ] Sequencing of REWRITE Steps 1–6 is intact; no step is being skipped.
- [ ] GOVERN/ASSURE is operational at least in alert-only mode; if not, the recommendation calls this out as the first build.
- [ ] Cognitive captivity risk has been checked (single-vendor on foundation models or orchestration).
- [ ] If the firm cites Block as a template, the **DRIVE-without-SHAPE warning** has been delivered.
- [ ] If the team or board is using the **Social Capital 5-Layer Agent Stack vocabulary** (Intelligence / Action / Governance / Orchestration / Economics), the **Crosswalk** has been applied and the **LEARN-layer gap** has been named as an asymmetric opportunity.
- [ ] For any enterprise-scale agent deployment, the **Amazon Q sidebar** lessons have been applied (scoped credentials, mandatory approval thresholds on destructive endpoints, soft-delete windows, an Eval Suite that catches drift before the customer does). *If Amazon can ship this, so can you.*
- [ ] For Direct Mode firms, the **Steinberger / OpenClaw existence proof** has been delivered: Direct Mode is not a thought experiment, it is the modal new company. Solo-founded startups are **36.3% of new ventures** as of early 2026.
- [ ] For Tier 4–5 intelligence-dense designs, **tokens-as-COGS** has been put on the CFO's table (SemiAnalysis pattern) and **per-outcome pricing** (Salesforce Headless 360, April 15 2026) has been evaluated where the firm is the buyer of agent-native software.
- [ ] **Edge Twin data-fork question (v20) answered:** No fork. Workflow-scoped, governed API access. Read/write separated, correlation-ID logged, credentials short-lived and revocable. Source-of-truth statement signed: if the Edge Twin and the ERP disagree, the ERP wins.
- [ ] **Workflow Data Manifest (v20) produced** for every workflow targeted for migration: sources, why, read/write, sensitivity tier, retention in the twin, named data owner. The binary rule applied: any field that cannot be justified by the workflow does not travel to the twin. Step 3 exit criterion.
- [ ] **Cold-start learning protocol (v20) named** for every Wave 1 workflow: parallel run as shadow mode + the four learning feeds (historical replay, shadow comparison, human-correction capture, synthetic edge cases). The falling human-override rate is the success metric of a real twin, called out explicitly.
- [ ] **Four Pillars standards mapping (v20) cited** when CISO, auditor, or board asks: NIST AI RMF (2023), OWASP LLM Top 10, CSA AI Controls Matrix (243 controls, 18 domains, July 2025). The Pillars operationalize, do not restate.
- [ ] **CIO Edge Twin Diagnostic (v20, Appendix F) completed** before Edge Twin funding: ten questions scored red/amber/green. Any red on 5 (leakage), 6 (identity), 7 (recovery), or 8 (accountability) blocks the build.
- [ ] **Access vs. training distinction (v20)** pinned in writing with the vendor: retention, training rights, deletion rights, audit rights, model isolation.
- [ ] **No third autonomy ladder (v20):** the architecture uses Autonomy Tier per agent spec plus Decision Handover Waves per REWRITE Step 5. The source's Level 0–5 maturity ladder has been rejected.
- [ ] Source attribution to Salim Ismail and contributors is preserved on any output that will be republished or shared externally.

## References

### Core (Always Available)
- `references/exo30-architecture.md`, The destination: MTP-as-protocol, DRIVE + SHAPE characteristics, Five Design Conditions (binding Step-1 exit gate in v13), Three Compounding Loops, **Miura-Ko L0–L5 ladder + Readiness Score cross-reference**, the canvas lineage (Porter → Osterwalder → Maurya → Wardley → ExO 1.0 → ExO 3.0), proof points (Block, Haier, Cognition Labs)
- `references/intelligence-stack.md`, Six layers + GOVERN/ASSURE control plane, **Four Pillars (Trusted Evals / Searchable Logs / Granular Rollback / Human Review Queue)**, **Silent Drift sidebar**, OODA mapping, Retailer Case Study end-to-end, Agent Specification (eight properties), **HIDO Six-Question Diagnostic**, MVIS standup recipe, the PocketOS / nine-seconds-to-zero sidebar, **Amazon Q enterprise sidebar (v15)**, **Intelligence Stack ↔ Social Capital 5-Layer Stack crosswalk (v15)**
- `references/drive-engine.md`, The five DRIVE components scored 1–5, GOVERN-cap rule, **Four Pillars sub-rubric under I**, Sliding Talent Ratios by sector, Value Moat sources (with Cognition Labs / Klarna / Pieter Levels receipts), customer-side agent inversion, cognitive captivity, **Block as DRIVE-without-SHAPE warning at corporate scale**
- `references/shape-form.md`, The five SHAPE components scored 1–5, Fiduciary Wedge, Middle 60% absorption math, missing junior loop, bifurcation/caste risk, Permission Envelope mechanics, **Four Pillars under S**, **HIDO data-side governance**, **Cross-Organizational Accountability stack under E**, Haier RenDanHeYi existence proof
- `references/rewrite-playbook.md`, Six-step migration with exit criteria per step, **Five Design Conditions as binding Step-1 gate**, Eight-Dimension Readiness Score banding, **Four Pillars Maturity sub-rubric**, **Miura-Ko cross-reference table**, on-ramp choices (MVIS / 90-Day Sprint / Full), Decision Handover Waves, Parallel-Run-Then-Deprecate, the People Side of Parallel Runs
- `references/edge-deployment.md`, Direct Mode vs. Edge Mode by headcount, the five Edge Twin build steps, **Peter Principle for AI Agents as anchor rationale**, **cross-firm operation note**, failure modes and defenses, Three-Phase Studio Evolution, Path A (FifthRow / Radical Transformation) vs. Path B (Board of Innovation / Evolutionary Repositioning), mission-driven adaptation, refreshed proof points (Block, Haier, Cognition Labs)
- `references/social-capital-crosswalk.md`, **(NEW in v15)** Verbatim Chapter 4 crosswalk text mapping the Intelligence Stack's six cognitive layers plus GOVERN/ASSURE control plane to Social Capital's industry-canonical 5-layer model (Intelligence / Action / Governance / Orchestration / Economics). Includes the Amazon Q enterprise-scale sidebar carried verbatim from the v15 source.
- `references/v15-deltas.md`, **(NEW in v15)** Verbatim CEO Quick Start and Chapter 11 paragraphs covering the Steinberger / OpenClaw existence proof, 36.3% solo-founded-startup datum, OpenClaw / NemoClaw / Anthropic ARR signals, IDC enterprise-agent forecast (28.6M → 2.2B by 2030), SemiAnalysis tokens-as-COGS evidence, and the Salesforce Headless 360 per-outcome pricing pattern.
- `references/edge-twin-data-governance.md`, **(NEW in v20)** The CIO's first objection answered: does the Edge Twin fork your data? No-fork architecture, workflow-scoped governed API access, read/write separation, correlation-ID logging, short-lived revocable credentials, ERP-wins source-of-truth rule, access-vs-training distinction.
- `references/four-pillars-standards-mapping.md`, **(NEW in v20)** Mapping the Four Pillars of GOVERN/ASSURE to NIST AI Risk Management Framework (2023), OWASP Top 10 for LLM Applications, and Cloud Security Alliance AI Controls Matrix (243 controls across 18 domains, July 2025). The Pillars operationalize, they do not restate.
- `references/cold-start-learning-feeds.md`, **(NEW in v20)** The four-feed cold-start learning protocol for the Edge Twin's parallel run as shadow mode: historical replay, shadow comparison, human-correction capture, synthetic edge cases. The falling human-override rate is the success metric of a real twin.

### Templates
- `templates/drive-scorecard.md`, DRIVE assessment template (5 components × 1–5, total 25, with GOVERN-cap rule prompt and **Four Pillars sub-rubric** under I)
- `templates/shape-scorecard.md`, SHAPE assessment template (5 components × 1–5, total 25, with Middle 60% absorption-math prompt, **Four Pillars under S**, **HIDO check**, **Cross-Organizational Accountability check** under E)
- `templates/rewrite-readiness-scorecard.md`, Eight-dimension Readiness Score (total 80) with banding, on-ramp recommendation, **Four Pillars Maturity sub-rubric**, and **Miura-Ko L0–L5 cross-reference**
- `templates/backcasting-canvas.md`, Step 1 facilitated workshop canvas: Destination Architecture, Five Design Conditions instantiated, Edge Twin pipeline, mandate
- `templates/task-decomposition-matrix.md`, Step 4 task-level audit: Role → Task → Category (judgment / pattern / coordination / creation) → Agent Readiness 1–5 → Disposition
- `templates/agent-specification.md`, Eight-property agent contract (Purpose, Autonomy Tier, Permission Envelope, Memory Boundary, Escalation Rules, Eval Suite, Telemetry/Audit Trail, Reusability Scope)
- `templates/hido-six-questions.md`, **(NEW in v13)** Six-question data-object diagnostic, symmetric to the Agent Specification: what is it / who says so / how can it be used / legal terms / what if wrong / dispute resolution. Required for every data object an agent reads or writes.
- `templates/mtp-protocol.md`, Three-layer MTP authoring template (Constraint, Decision, Identity) with both litmus tests built in
- `templates/workflow-data-manifest-template.md`, **(NEW in v20)** One-page per-workflow data manifest: sources, why this workflow needs each source, read/write, sensitivity tier, retention in the twin's memory, named data owner. Step 3 EXTRACT exit criterion. Workflow-level companion to HIDO Six Questions per object.
- `templates/cio-edge-twin-diagnostic.md`, **(NEW in v20)** Ten governance questions for the CIO with red/amber/green scoring boxes. Any red on questions 5, 6, 7, or 8 blocks the build (these are the SHAPE controls). Mirrors Appendix F of the v20 outline.

## Cross-Skill Workflows

### First-Pass Building-an-ExO Intake
When a founder or CEO asks "what would we build today, with AI, from scratch?":
1. Start here, confirm the three-things frame (Destination, Operating System, Playbook).
2. Score the firm with `templates/drive-scorecard.md` and `templates/shape-scorecard.md`.
3. Score readiness with `templates/rewrite-readiness-scorecard.md`. Choose Direct vs. Edge Mode by headcount.
4. Return here, produce a one-page Destination Architecture sketch and a named candidate workflow for Wave 1.

### Stand-Up-MVIS Workflow
When the firm needs the Minimal Viable Intelligence Stack in week one:
1. Start here, confirm the four MVIS components (event bus, agent registry, central logging, one agent per class) plus the **Four Pillars at MVP level** (eval suite scaffold, correlation-ID logging on by default, one rollback path defined, human-review queue with named owner).
2. Author the first Agent Specification using `templates/agent-specification.md` **and the matching HIDO Six Questions for each data object the agent will touch using `templates/hido-six-questions.md`.**
3. Return here, confirm GOVERN/ASSURE is alert-only and the kill switch is testable; confirm Silent Drift detection thresholds are defined for the first production agent class.

### Edge Twin Spawn Workflow (Tier 4–5)
When a >50-person firm needs to launch the Edge Twin:
1. Start here, confirm board mandate and CEO sponsorship; veto if either is missing.
2. Apply the five Edge Twin build steps from `references/edge-deployment.md` (Spawn / Fund / REWRITE-from-Day-1 / Migrate easiest first / Become center of gravity).
3. Run the **CIO Edge Twin Diagnostic (v20)** from `templates/cio-edge-twin-diagnostic.md` *before* funding. Any red on questions 5, 6, 7, or 8 blocks the build.
4. Produce the **Workflow Data Manifest** for each candidate Wave 1 workflow using `templates/workflow-data-manifest-template.md`. Confirm the binary rule: no field travels to the twin without a stated workflow reason.
5. Confirm the **no-data-fork architecture** from `references/edge-twin-data-governance.md` is signed: workflow-scoped API access, read/write separated, correlation-ID logging, short-lived revocable credentials, ERP-wins.
6. Define the **cold-start learning protocol** for the first parallel run using `references/cold-start-learning-feeds.md`. Name the human-override-rate baseline and the falling-rate target.
7. Return here, name the first three workflows to migrate, easiest first.

### Workforce-Transition Workflow
When a workforce reduction or restructuring is on the table:
1. Start here, refuse to dress headcount cuts as architecture. If the Destination Architecture isn't signed and the Task Decomposition Matrix isn't scored, stop and route back to Steps 1–4.
2. Return here, confirm the People Side of Parallel Runs has 10–15% of savings allocated and a named transition leader.

### PocketOS / Silent Drift Postmortem Workflow
When a failure has occurred, loud (autonomous agent crossed an envelope, destructive action without approval, data loss) **or quiet (Silent Drift surfaced in customer escalations)**:
1. Start here, name the failure pattern: DRIVE-without-SHAPE, missing GOVERN, blanket-privilege token, missing approval threshold, missing soft-delete window, missing kill switch, **missing Trusted Evals (Silent Drift)**, **missing Granular Rollback**, or **missing HIDO metadata on the data object the agent acted on**.
2. Return here, verify the eight Agent Specification properties **and the HIDO Six Questions on every data object** for every agent in the same class as the one that failed; score the **Four Pillars** for the affected agent class and bring each pillar to ≥ 3 before redeployment.

### Mission-Driven Adaptation Workflow
When the entity is government, non-profit, or other mission-driven (immune-system-is-law):
1. Start here, confirm Edge Mode is the only path; Direct Mode does not exist.
2. Adjust REWRITE Steps 1–6 for procurement timelines, civil service protections, and codified compliance.
3. Frame the citizen demand forcing function (Singapore Ask Jamie, UK Bobbi, US municipal permit acceleration).
4. Return here, name the sovereign-AI requirement (own the inference, the orchestration logic, and the fine-tuning data).

#### Attribuion
This AI skill was specially created by Kent Langley for OpenExO and its community using Founder OS (https://fos.kentlangley.com) and is based on ExO 3.0: The Organizational Singularity by Salim Ismail and Contributors. The book is available at https://openexo.com/organizational-singularity 

## Changelog

- **v1.3.0 (2026-05-19)**, v20 sync: *Edge Twin Data-Governance Pass*. Added the "Does the Edge Twin fork your data?" answer (no fork; workflow-scoped governed API access; read/write separated; correlation-ID logging; short-lived revocable credentials; ERP wins ties as source of truth). Added the Workflow Data Manifest as a REWRITE Step 3 exit criterion (one-page per-workflow: sources, why, read/write, sensitivity tier, retention, named data owner; binary rule). Added the cold-start learning protocol for REWRITE Step 5 (parallel run as shadow mode + four feeds: historical replay, shadow comparison, human-correction capture, synthetic edge cases; falling human-override rate is the test of a real twin). Added the Four Pillars standards mapping (NIST AI RMF 2023, OWASP LLM Top 10, CSA AI Controls Matrix 243 controls / 18 domains, July 2025; the Pillars operationalize, do not restate). Added Appendix F: The CIO Edge Twin Diagnostic, a ten-question pre-funding checklist with red/amber/green readiness gate; any red on 5/6/7/8 blocks the build. Discipline note: rejected the source's "Level 0-5 autonomy maturity ladder" to protect the existing Autonomy Tier + Decision Handover Waves. Three new references (`edge-twin-data-governance.md`, `four-pillars-standards-mapping.md`, `cold-start-learning-feeds.md`) and two new templates (`workflow-data-manifest-template.md`, `cio-edge-twin-diagnostic.md`). Source bumped from OS Outline v15 to OS Outline v20. Validation checkpoints extended for data fork, Workflow Data Manifest, cold-start learning, standards mapping, CIO Diagnostic readiness gate, access-vs-training, and no-third-ladder discipline.
- **v1.2.0 (2026-05-12)**, v15 sync: *Social Capital Primer Integration*. Added the Intelligence Stack ↔ Social Capital 5-Layer Agent Stack Crosswalk (Intelligence / Action / Governance / Orchestration / Economics), the Amazon Q enterprise-scale sidebar (Dec 2025 13-hour AWS China outage, Mar 2026 120K lost orders / 1.6M website errors / 99% North American marketplace order drop), the Steinberger / OpenClaw solo-founder case plus the 36.3% solo-founded-startup datum as Direct Mode existence proof, SemiAnalysis tokens-as-COGS evidence, Salesforce Headless 360 per-outcome pricing (April 15 2026), and the IDC enterprise-agent forecast (28.6M agents in 2025 → 2.2B by 2030, 524% task CAGR). Two new reference docs: `references/social-capital-crosswalk.md` and `references/v15-deltas.md`. Source bumped from OS Outline v13 to OS Outline v15. Validation checkpoints extended for Crosswalk awareness, Amazon Q-style enterprise defenses, Direct Mode existence proof, and tokens-as-COGS / per-outcome pricing.
- **v1.1.0 (2026-05-11)**, v13 sync: *Accountability & Auditability pass* over v10. Added the Four Pillars of GOVERN/ASSURE (Trusted Evals / Searchable Logs / Granular Rollback / Human Review Queue), the HIDO Six-Question Diagnostic for data objects, the Silent Drift sidebar, the Peter Principle for AI Agents (Edge Twin anchor rationale), the Miura-Ko L0–L5 ladder with Readiness Score cross-reference, and the Cross-Organizational Accountability stack as first-class concepts. New template: `templates/hido-six-questions.md`.
- **v1.0.0 (2026-05-01)**, Initial release encoding OS Outline v10: ExO 3.0 (MTP + DRIVE + SHAPE), the Intelligence Stack, the REWRITE Playbook, the Edge Deployment model, and tier-appropriate application.