# General skill and workflow routing

Adapted from Matt Pocock's ask-matt at commit
c55ee46073ed923f86ce59a5eb3b6d895095d1b7, MIT; see LICENSE-MATT.
The adaptation retains situation-based flows and decision branches, replacing the
handwritten map of one author's skills with evidence from the common skill base.

## Resolve capabilities instead of assuming a fixed map

1. Identify the outcome, what exists already, whether a working project exists,
   current stage, uncertainty, and whether the task fits one session.
2. Search active inventory, local hot router (`rules/routing.md`) and focused cold
   catalog (`config/routing-ext.md`); see discovery.md. A skill omitted from the
   active list is not necessarily absent. Verify selected skill files read-only
   before calling them installed or asserting their behavior.
3. Reuse suitable installed capabilities first. When a gap remains, use discovery.md
   for skills.sh, SkillsMP and original repositories, including mattpocock/skills.
4. Represent each candidate with name, source/path, installed/available/unverified
   status, purpose, inputs, outputs, prerequisites, permissions and audit state.
   Read the actual entrypoint for every load-bearing recommendation. Do not equate
   the same name from different authors or replace a requested author silently.
5. Construct the shortest sequence whose outputs satisfy the next step's inputs.
   Mark missing tools, account setup, runtime, or approval at the step that needs it.
   Recommend and stop unless the user also asked to execute the underlying work.

## Situation branches, not mandatory pipelines

- **Idea to build:** clarify unresolved decisions first. With a project, use a
  project-aware planning skill; without one, a standalone interview/planning skill.
  If a question needs runnable evidence, recommend a bounded prototype and bring
  its findings back. Do not create a prototype merely because a template lists it.
- **Build spans sessions:** recommend a specification and independently testable,
  dependency-aware tasks before implementation. For a small clear task, prefer
  direct implementation plus suitable tests/review; avoid redundant planning.
- **Incoming reports:** triage raw external reports. Do not triage already prepared
  implementation tasks again.
- **Broken behavior:** reproduce and establish a failing feedback loop before
  diagnosis, minimal fix and regression verification.
- **Large unclear effort:** resolve decision questions first; hand resolved decisions
  to planning before implementation. Investigation is not completion of the product.
- **Codebase upkeep:** survey problems first, then select a bounded improvement.
- **Vocabulary/understanding problem:** choose domain modeling, explanation or
  reference material rather than starting an implementation workflow.
- **Standalone task:** choose the directly suitable skill for writing, design,
  documents, research, merges, learning or other domains, irrespective of author.

Matt's names such as ask-matt, grill-me, to-spec, tdd and wayfinder are examples,
not preinstalled dependencies. Native/local alternatives are valid when their
actual behavior and outputs fit. Do not require setup-matt-pocock-skills globally.

## Phase boundaries

Prefer staying in the current session when the next step needs its reasoning.
If context transfer is actually needed, identify what must survive and recommend
an appropriate native handoff/summary mechanism. Claude Code has the Skill tool and
slash commands, but the boundary stays "recommend and stop": do not hardcode a token
threshold, invoke the recommended skill, clear context, spawn agents, or create
new tasks from a recommendation. Those are separate actions with their own scope
and authorization. Never claim all relevant context survives a lossy summary.

## Output

Give the recommended skill or ordered flow, why it fits, alternatives if relevant,
what is installed versus only found, exact sources and the next human decision.
Call out unavailable prerequisites. A one-step answer is preferable when sufficient.
Do not turn recommending a skill into permission to install, execute or publish.
