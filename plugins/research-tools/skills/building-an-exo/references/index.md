# Что лежит в каждом файле справочника и шаблона

Развёрнутые описания всех `references/*` и `templates/*` с пометками, что добавилось в v13/v15/v20. Читай, когда выбираешь, какой файл открыть, и короткой таблицы в `SKILL.md` не хватило.

---

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

