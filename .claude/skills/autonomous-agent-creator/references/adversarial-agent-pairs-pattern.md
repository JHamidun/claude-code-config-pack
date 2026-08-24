# Adversarial Agent Pairs + Quantified Veto Gate (shenhao-stu/openclaw-agents)

> Distilled from github.com/shenhao-stu/openclaw-agents (2026-07-20). NOT a new engine —
> a **coordination pattern** for multi-agent fleets and multi-agent reviews. Importantly,
> this template is built **on OpenClaw itself**: `agents.yaml` manifest +
> `.agents/<id>/soul.md` + `openclaw.json` channels — so the wiring below is directly
> usable on an OpenClaw fleet, and the rubric ports 1:1 to a Hermes `SOUL.md`.

## The core idea — productive antagonism, not consensus

A 9-agent research fleet (`main` orchestrator, `planner`, `ideator`, `critic`,
`surveyor`, `coder`, `writer`, `reviewer`, `scout`) deliberately pins two roles against
each other:

- **💡 Ideator** — generates novel concepts, frames the contribution, maximizes novelty.
- **🎯 Critic** — holds the **taste veto**: no idea passes the ideation phase without a
  quantified score ≥ threshold. The Critic's *job* is to kill weak ideas *before* the
  expensive agents (coder/writer) burn effort on them.

The insight most fleets miss: without an explicit adversary + a **numeric gate**, a
multi-agent chain becomes a mutual-admiration society — each agent politely accepts the
previous one's output and slop compounds downstream. The Critic + SHARP score converts
"looks fine" into a pass/fail number that a downstream agent can branch on.

## SHARP — the quantified taste rubric (verbatim from the repo)

Five dimensions, each scored **1–5**, total **/25**:

| Letter | Dimension | Gate question |
|--------|-----------|---------------|
| **S** | Sharpness | Is the core insight piercing / one-strike-to-the-point? |
| **H** | Horizon | Does it hold *lasting* value, not just a one-off? |
| **A** | Asymmetry | Do you have a unique angle / information others lack? |
| **R** | Resistance | Does the core claim survive the most hostile reviewer? |
| **P** | Parsimony | Is the method elegant and minimal (no bloat)? |

**Bands & veto:**

- **23–25 Exquisite** — rare, pursue fully
- **18–22 Refined** — reliable, worth investment ← **PASS threshold**
- **13–17 Raw** — potential but needs major rework → send back to Ideator
- **≤12 Bland** — lacks substance → abandon / restart

**Veto rule: nothing advances past ideation below SHARP 18/25.**

## Four checkpoints, not one gate

The Critic doesn't score once — it gates at four points along the pipeline, cheapest
test first (fail-fast):

1. **One-Sentence Insight Test** — can the idea be stated in one compelling sentence?
2. **Bar Test** — would a 30-second pitch intrigue a colleague?
3. **Reviewer Pressure Test** — name the 3 harshest critiques an adversary would raise.
4. **Resistance Rating** — can those counterarguments be credibly answered?

A second veto sits at the *end*: the **🔍 Reviewer** agent — "paper cannot submit without
Reviewer's Accept" — so there's a gate on both entry (Critic/SHARP) and exit (Reviewer).
Dual gating: filter cheap ideas early, filter finished output late.

## Why this matters for a fleet of single-lane bots

A typical fleet grows as *independent* personalities: one bot answers about copy, another
about analytics, a third about support — each in its own lane, each agreeing with whoever
asked. This pattern says: pair two of them antagonistically and add a numeric gate.

Concrete adaptations (substitute your own bots for the roles):

- **Copy bot ↔ Critic role**: before a post or an offer ships, a Critic pass scores it on
  a SHARP-style rubric adapted to marketing (Sharpness=hook, Horizon=evergreen vs
  news-bound, Asymmetry=angle competitors can't copy, Resistance=survives a skeptical
  buyer, Parsimony=no filler). Below 18/25 → back to the copy bot, don't publish. This is
  a cheaper, always-on version of a `de-ai-ify` / `linkedin-humanizer` audit, but with a
  branchable number instead of prose.
- **Analytics bot as the Critic's evidence source**: Resistance/Asymmetry scores get teeth
  when the Critic can pull real numbers (a bot with CRM or analytics read access) instead
  of vibing. Score claims against data, not taste alone.
- **Adversarial multi-agent review**: one agent proposes, a second is *instructed to
  attack* and must emit S/H/A/R/P integers + the 3 harshest critiques. The orchestrator
  branches on the total. This turns "get a second opinion" into a gate with a threshold —
  complements cross-**model** validation (`multi-model-gateway`, `check-skill-solo`),
  which varies the *model*; SHARP varies the *role/stance* and can run even on a single model.

## Wiring on both engines

**OpenClaw fleet (agents.yaml manifest — same shape the repo uses):**

```yaml
agents:
  - id: ideator          # 💡 proposes
    workspace: .agents/ideator
    protected: true
  - id: critic           # 🎯 vetoes — soul.md carries the SHARP rubric verbatim
    workspace: .agents/critic
    protected: true
```

Put the SHARP rubric + the "≥18 to pass, else return with the 3 harshest critiques"
instruction in `.agents/critic/soul.md` (OpenClaw loads `soul.md`/`SKILL.md` as
system-prompt context — this is the native mechanism, no code needed). Agents talk via the
`agentToAgent` tool in local-workflow mode, or `@critic` mention bindings on the channel.

**Hermes bot (SOUL.md snippet — same rubric, respect the ~2200-char memory cap):**

```
You are the Critic. Score every proposal on SHARP (S/H/A/R/P, each 1-5, /25):
Sharpness, Horizon, Asymmetry, Resistance, Parsimony. Reply with the 5 integers,
the total, and — if <18 — the 3 harshest critiques an adversary would raise. Never
approve <18; return it to the proposer instead.
```

Because the rubric is just a prompt + a threshold, it's engine-agnostic: no plugin, no
weights, no install. Cost = one extra LLM turn per gated artifact.

## Gotchas / when NOT to use

- **Don't gate cheap, reversible output** (a routine reply, a status ping) — the extra
  Critic turn costs more than the slop it prevents. Gate only expensive/irreversible
  artifacts: published posts, offers, KP, code that ships, research directions.
- **Grade-inflation drift**: an LLM Critic scored by *itself* creeps toward passing
  everything. Anchor with the band descriptions ("≤12 Bland = abandon") and occasionally
  spot-check that it actually vetoes. A Critic that rubber-stamps is worse than none
  (mirrors our own quality-gates rule: "a verifier that rubber-stamps undermines
  everything").
- **Two gates, not a committee**: the value is *one* dedicated adversary + a number, not
  five agents voting. Adding more reviewers ≠ better; it dilutes accountability. Keep the
  veto with a single named role.

## Verdict — pattern noted, not a new engine

Nothing to install. `openclaw-agents` is a template on top of OpenClaw (which we already
run) — the reusable value is the **antagonistic-pair + quantified-veto-gate** design and
the concrete **SHARP rubric**, filed here for the fleet and for multi-agent reviews. Not a
Decision-Tree engine option; a coordination pattern to layer onto existing Hermes/OpenClaw
bots and onto the adversarial-review workflow.
