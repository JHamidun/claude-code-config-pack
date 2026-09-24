# app-layouts — picking the starter template (`type: "app"` builds ONLY)

The starter template is chosen AT CREATE TIME — `create_website(type: "app",
template: ...)` — and the repo arrives with that template's layout shipped as
REAL CODE, already wired as the home page. This file exists primarily to pick
the right template BEFORE the repo exists. Layout anatomy, component APIs,
design-system mechanics, and copy-paste wiring live IN THE REPO: after
`website_repo_access` + clone, read `app/src/layouts/AGENTS.md` and
`app/src/components/AGENTS.md`, then **adapt the shipped layout in place**.
Don't re-derive implementation details from this skill; read them from the
clone when you need them. The cross-template acceptance outcomes at the end
still apply even if a shipped demo is older.

## The three templates (pass one to `create_website`)

| Template | Pick when |
|---|---|
| `studio` | The app is MORE than a one-shot or preset generator: a prompt-centric professional tool with many settings, and/or multiple projects and a browsable generations feed. The DEFAULT, most-capable shell (full workspace: sidebar + prompt dock + feed). |
| `preset` | **Pick-a-style-then-generate**: the user browses a gallery of presets/styles and generates from one (creation rail + preset grid + History tab). Also the base for upload-configure-iterate workspaces (try-on, restyle, character). |
| `app-detail` | A single tool's **public landing page** (the "simple app"): generator hero + how-it-works explainer around ONE quick action — not a full workspace. |

Rules:

- An unusual request still maps to the NEAREST template (a before/after
  enhance tool → `app-detail`; a step-by-step wizard or
  upload-configure-iterate workspace → `preset`). Do not plan to swap
  layouts after create.
- A fully custom shell is fine only when the user asks for something none of
  the three covers — still create from the closest template and rework the
  route in place.
- There is also a hidden `custom` template (a bare shell, no shipped layout).
  Use it ONLY when the user explicitly says "use custom template" — never pick
  it yourself.

## Cross-template acceptance outcomes (after clone)

The cloned repo's layout and component guides remain the source of truth for
implementation mechanics. Regardless of the chosen template, enforce these
outcomes:

- **Accepted generation becomes visible immediately.** Once confirmation is
  accepted and submit returns queued/running generations, add those real
  generations to the visible result set and move focus to it. `preset` must
  activate History/Results instead of leaving the user on the preset gallery;
  inline-feed layouts scroll or focus the new card. Render the pending state
  immediately and poll it in place. Validation errors and confirmation cancel
  stay on the current form; a post-submit failure remains on Results as a
  failed card with retry. Preserve the chosen preset and composer state.
- **Generated-media galleries are responsive and uncropped.** Every generated
  output gallery — including Simple app output, History, and Results — adapts
  to its container and to mixed media geometry. Derive each pending/ready
  card's aspect ratio from result dimensions or the canonical submitted
  `aspectRatio`, and preserve the complete image/video with contain or natural
  sizing. Never force 1:1, 4:3, 16:9, and 9:16 outputs into one crop. Fixed
  crops are only for curated preset or marketing thumbnails.
- **Settings stay usable at every viewport.** Keep primary controls visible and
  put secondary settings behind progressive disclosure. A tall settings panel
  must be a real `min-h-0 overflow-y-auto overscroll-contain` region with a
  visible scrollbar or edge-fade/“more settings” cue; hidden, non-obvious
  scrolling is a bug. A pinned Generate action must not cover the final field
  and must respect mobile safe areas. Below desktop, stack settings above the
  result or move them into the repo-prescribed mobile sheet instead of
  squeezing the desktop rail. Verify expanded settings at 375px, tablet, and
  desktop with keyboard and touch access.
- **History stays inspectable in place.** Every ready History card opens the
  repo's detail view without leaving History. Detail provides Previous/Next
  plus Left/Right arrow keys over the current filtered/sorted results. Closing
  returns to the same History tab, filters, sort, and scroll position; never
  require the user to exit History and reopen generations one by one.
