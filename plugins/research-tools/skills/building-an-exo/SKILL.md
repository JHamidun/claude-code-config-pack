---
name: building-an-exo
version: 1.3.0
description: "Справочник ExO 3.0 (OpenExO) для AI-перестройки компании: Intelligence Stack, REWRITE, Edge Twin, DRIVE/SHAPE, MTP. Триггеры: «экспоненциальная организация». НЕ маркетинг/CRO."
metadata:
  license: "не установлена — см. раздел Attribution и файл ATTRIBUTION.md рядом"
  source: "Salim Ismail — The Organizational Singularity, OS Outline v20 (OpenExO Pro, May 2026); operationalized by Kent Langley"
---

# Building an ExO Skill

## Attribution

Модель — *The Organizational Singularity* (OS Outline v20, май 2026), Salim Ismail с соавторами; операционная адаптация для ИИ — Kent Langley, ExO Builders. ExO 1.0 (SCALE/IDEAS) — *Exponential Organizations* (2014). Лестница L0–L5 — Ann Miura-Ko (Floodgate, 2026).

Применяешь в клиентской работе, преподавании, публикации или коммерчески — атрибуция обязательна, полный список авторов и источников в `references/attribution.md`, первоисточник: <https://openexo.com/organizational-singularity>.

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

- Anchor every conversation in the three-part frame: **Destination (ExO 3.0)**, **Operating System (Intelligence Stack)**, **Playbook (REWRITE)**. Skip the rest of the framework if needed; never skip these three.
- Treat the Intelligence Stack as the operating core. The other nine ExO 3.0 characteristics define the context in which the Stack operates. Build the Stack first.
- Refuse the temptation to teach DRIVE without SHAPE or SHAPE without DRIVE. *DRIVE without SHAPE crashes. SHAPE without DRIVE stalls. You need both.*

Полный свод директив по ExO 3.0, DRIVE, SHAPE, Intelligence Stack, REWRITE и Edge Deployment — `references/core-directives.md`. Открывай его до того, как что-то считать или писать клиенту.

### Tier-Appropriate Application

- Adjust depth and ambition to the OpenExO ICP tier (see `/org-config/icp.md`).
- **Tier 2 (≤50 employees, ≤$2M revenue), Direct Mode.** Apply REWRITE to the whole company. Stand up MVIS in week one. Use a 90-Day Sprint on the highest-coordination workflow. The founder can run BACKCAST themselves with a one-day workshop. SHAPE Human Architecture is small-team work; absorption math is simpler but no less honest. **v15 existence proof**, Peter Steinberger built the first version of OpenClaw on a single Friday evening in November 2025, ran 4–10 agents in parallel, pushed 6,600+ commits in January 2026 alone, surpassed 145,000 GitHub stars within weeks with no team and no revenue, and received acquisition bids from Meta and OpenAI in the same window. Solo-founded startups are now 36.3% of new ventures (Social Capital primer, May 2026). Direct Mode is not a thought experiment; it is the modal new company.
- **Tier 3 ($2M–$10M, 20–80 employees), Direct or borderline Edge.** If headcount is climbing past 50 with managerial layers forming, spawn the Edge Twin proactively before the immune system hardens. Run DRIVE and SHAPE assessments quarterly. CAIO appointment becomes a real role at this stage, not a hat.
- **Tier 4–5 ($10M+, 80+ employees), Edge Mode mandatory.** Spawn 3–5 person Edge Twin reporting to CEO. Board-level Continuous Kill Switch with quarterly review of Organizational Half-Life. Treat Sliding Talent Ratios as portfolio-level capital allocation. Sovereign AI capability becomes a strategic discussion, not a vendor-selection exercise.

### Output Discipline

- Produce concrete, named recommendations: a specific Destination Architecture, a scored Readiness Score with bands, a ranked Task Decomposition Matrix, named candidate workflows for Wave 1.
- Cite ExO 3.0 vocabulary precisely (DRIVE, SHAPE, MVIS, Edge Twin, Fiduciary Wedge, Continuous Kill Switch, Permission Envelope, Autonomy Tier, Capability Registry). Do not invent neighboring terms or use ExO 1.0 SCALE/IDEAS vocabulary by accident.
- Flag every assumption that needs human verification: "We've assumed the Stack runs on at least two model families, confirm with the CAIO before this Readiness Score is final."
- Acknowledge survivorship bias when citing case examples (Cognition Labs, Pieter Levels, Klarna, Nespresso, FifthRow, Board of Innovation). The pattern is real; the outcome is not guaranteed.

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

Читай ТОЛЬКО тот файл, который нужен текущему шагу. Развёрнутые описания всех файлов — `references/index.md`.

| Файл | Когда читать |
|---|---|
| `references/core-directives.md` | перед любой оценкой, скоркардой, стратсессией, слайдами: обязательные директивы по ExO 3.0, DRIVE, SHAPE, Intelligence Stack, REWRITE, Edge Deployment |
| `references/exo30-architecture.md` | проектируешь Destination Architecture, MTP-протокол, Five Design Conditions |
| `references/intelligence-stack.md` | шесть слоёв + GOVERN/ASSURE, Agent Specification, Four Pillars |
| `references/drive-engine.md` · `references/shape-form.md` | считаешь скоркарды DRIVE и SHAPE (по 1–5, всего 25 каждая) |
| `references/rewrite-playbook.md` | ведёшь миграцию по шести шагам REWRITE, Readiness Score |
| `references/edge-deployment.md` | Direct vs Edge Mode, сборка Edge Twin |
| `references/edge-twin-data-governance.md` · `references/four-pillars-standards-mapping.md` | вопросы CIO/CISO/аудитора: форкает ли Edge Twin данные, как это ложится на NIST AI RMF / OWASP LLM Top 10 / CSA AICM |
| `references/cold-start-learning-feeds.md` | параллельный прогон Edge Twin в shadow mode, четыре канала обучения |
| `references/social-capital-crosswalk.md` · `references/v15-deltas.md` | команда или вендор говорит на языке 5-Layer Agent Stack; нужны существование-пруфы и экономика токенов |
| `references/attribution.md` | материал идёт наружу — в публикацию, преподавание, клиентский документ |
| `references/changelog.md` | расхождение с прошлогодним материалом, надо понять версию |
| `templates/*.md` | заполняешь скоркарду, канвас, спецификацию агента, HIDO, MTP, манифест данных, диагностику CIO — список в `references/index.md` |

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

