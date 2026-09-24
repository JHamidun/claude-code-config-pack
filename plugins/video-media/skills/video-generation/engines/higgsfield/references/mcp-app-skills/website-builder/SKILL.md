---
name: website-builder
description: >
  Build and publish a complete website, web app or browser game on
  Higgsfield, or edit/redeploy an existing Higgsfield-hosted site. Use when the
  requested deliverable is that hosted product or a change to it. Components,
  snippets and fixes for a user's existing local codebase remain repository
  work; mentioning React, a website or a UI element does not request a hosted
  build. Exclude copywriting, external-site review, standalone media and
  read-only site administration. After a valid activation, collect missing
  product type and scope.
---

# Higgsfield website builder

## Project ownership

A local repository request does not authorize creating a Higgsfield website or
moving the project into a cloud sandbox. Use this workflow for a requested
hosted product or a known Higgsfield site's edit; keep component-only work in
the user's existing codebase and toolchain.

You build ONE per-product Cloudflare Worker: a **React 19 + TanStack Start** app,
**server-rendered**, deployed as a single Worker at the product's own subdomain.
The project lives in **`app/`** — every `bun`/build command runs from there.

The code is edited in the Higgsfield cloud sandbox with `sandbox_exec`, never on
a local machine. Read `references/repo-and-sandbox.md` before your first edit —
website_repo_access reserves a 15-minute editing lease. Commit and push progress
before the lease expires; checkout again if the sandbox was discarded.

## THREE product types — the user picks, not you

`create_website` requires `type`, and it is the **user's** choice. When the
request does not make it obvious, ask once, up front, in the same message as the
publish question below.

- **`type: "website"`** — a standalone product with NO Higgsfield integration and
  **no AI generation of any kind** inside the product (not via Higgsfield, not
  via another provider): no Sign in with Higgsfield, no fnf SDK. It gets a fully
  independent brand — own palette, type, and chrome, custom Tailwind/CSS. Never
  import `@higgsfield/quanta/*`, and never put a "Powered by Higgsfield" badge on
  the page. The user's brand is the only brand there.
  → **`references/website-flow.md`**
- **`type: "app"`** — a product tightly integrated with Higgsfield: its users Sign
  in with Higgsfield and generate images/videos through the fnf SDK, on their own
  Higgsfield credits. An app must look like a Higgsfield product: UI built with
  **Quanta**, starting from the starter layout picked at create.
  → **`references/app-flow.md`**
- **`type: "game"`** — a browser game on the game template, where the game itself
  is six pure functions in `app/src/logic.js` and the platform already owns
  sockets, rooms, and persistence. Requires a game genre as `category` and takes
  **no** template. Single-player counts — set `minPlayers: 1`.
  → **`references/game-flow.md`**

Each flow is complete for its type and pulls in the shared references below, so
you never have to read another flow.

**Generation is ALWAYS an app.** Any product that generates images, video, or
audio for its own users runs on Higgsfield — build it as `type: "app"`. Never
offer the user a "bring your own image/video API key" path for a website; it does
not exist. (An ordinary non-generation third-party API — payments, maps, email —
with the user's own key is unrelated to this rule and fine in a website.)

Quick tells: "landing page / portfolio / marketing site / SaaS with its own
users, no AI generation" → website. "generates images, video, or audio, or ties
into Higgsfield models, credits, or history" → app. "playable, rounds, score,
players" → game.

## The create call

Resolve all of this BEFORE calling `create_website` — `type`, `category`, and
`template` are fixed at create and are not editable afterwards.

- **`category`** — required. Call `list_website_categories` for the valid slugs
  and pass the closest one (`other` when nothing fits). A game takes a game genre
  (`arcade`, `puzzle`, `shooter`, …).
- **`subdomain`** — always set it. It becomes the slug, so the live URL is
  `<subdomain>.<host>`. Derive it from the product's name or purpose
  (`lumen-notes`, `pixelforge`), more than 4 characters, lowercase letters, digits
  and single hyphens only. Omit it only when the user explicitly asks for a random
  one. Reserved labels (`api`, `www`, `app`) and taken subdomains are rejected —
  try a close variant.
- **`template`** — REQUIRED for `type: "app"`, optional for `type: "website"`,
  never for `type: "game"`. App and website template names are not
  interchangeable; a cross-kind name is rejected.
  - App: `studio` (full creative workspace), `preset` (pick-a-style-then-generate,
    also the base for wizards), `app-detail` (a single tool's landing page). A
    `custom` bare shell exists but is used ONLY when the user says "use custom
    template" — never pick it yourself.
  - Website: `scroll-scrub` for an animated site (the scrub engine arrives
    pre-built), omitted for a non-animated one.

The chosen app layout ships as REAL CODE already wired as the home page. You
**adapt it in place** — thread the product's real data through the shipped
layout. Never rebuild the screen or swap layouts. After cloning, read
`app/src/layouts/AGENTS.md` and `app/src/components/AGENTS.md`: the layout is the
UI shell with demo placeholders, and the deliverable is the user's actual product
with complete business logic. A template that merely renders is NOT done.

## Order of work

1. Resolve `type` (ask if unclear). In that SAME first message, ask one more
   yes/no: publish it to the Higgsfield community feed when it is ready? Remember
   the answer — if yes, you publish at the end without asking again. Don't block
   the build on it.
2. Read the matching flow reference and follow it end to end. Each flow carries
   its own intake, references, hard rules, and gates, so you never need to read
   another one.
3. Ship it: cover + metadata, deploy, then publish if they said yes.

## The reference set

The flow you picked tells you when to open each of these. Do not read them all
up front.

**Every build**

| Reference | What it owns |
|---|---|
| `repo-and-sandbox.md` | The `sandbox_exec` edit loop, repo access, deploy/status/publish, db and secrets. **Read before the first edit.** |
| `asset-system.md` | The generated asset kit — what to generate per tier, and the post-processing this surface does not have |
| `app-cover.md` | The branded 3:2 launch cover and OG images |
| `security.md` | Input validation, authz, secrets, safe queries |
| `seo.md` | Metadata, sitemaps, structured data, crawlability |
| `runtime-and-infra.md` | The Worker runtime, routing, D1/R2/KV wiring |
| `containers.md` | Heavy or long-running work off the Worker |
| `contest.md` | The app contest entry rules |

**`type: "website"`**

| Reference | What it owns |
|---|---|
| `design-recipe.md`, `reference-boards.md` | Concept spine, palette, boards |
| `design-taste-frontend.md` | The craft bar — what separates a real design from a templated one |
| `wow-catalog.md`, `wow-maker.md` | The signature interaction, and how to build it |
| `image-to-code.md` | Turning an approved board into matching code |
| `scroll-scrub.md` | The animated-website scrub journey |
| `scroll-scrub-asset-video.md`, `-asset-react.md`, `-asset-css.md` | Its encode, React, and CSS halves |
| `review-rubric.md` | The gate before deploy |

**`type: "app"`**

| Reference | What it owns |
|---|---|
| `app-quickstart.md` | The critical path: auth → SDK client → submit/poll → render |
| `app-layouts.md` | Picking and adapting the starter layout |
| `quanta-design.md` | The design system and its UX rules |
| `fnf-sdk.md`, `fnf-react.md` | Generation, media, profile, credits |
| `auth.md` | Sign in with Higgsfield, server-side re-checks |
| `cover-animator.md` | The optional animated cover |

**`type: "game"`**

| Reference | What it owns |
|---|---|
| `game-design-system.md` | Game profile, core loop, asset manifest |
| `game-stylization.md` | The style formula every visual prompt reuses |
| `game-2d-animation.md`, `game-textures.md` | Spritesheets and tiles |
| `game-audio.md` | Music, SFX, voice |

## Cover + metadata — part of building, never publish-only

Every build — website, app, or game, however small — ships with a branded launch
cover and filled feed-card metadata written into `app/src/app-meta.json`
(`og_title`, `og_description`, `favicon_url`, `og_image_url`,
`marketplace_cover_url`). See `references/app-cover.md`. This is a BUILD
step, done before you present the work as finished and before the deploy that
ships it — not something deferred to `publish_website`.

- **No "simple app" exception.** A utility, a timer, a one-page toy — all get the
  generated cover. A hand-authored inline-SVG favicon is fine *as a favicon*; it
  never substitutes for the cover.
- **No permission needed** for the cover image — generate it the same way you
  write real copy. Only an optional cover VIDEO is permission-gated, because
  video costs credits: offer it, never generate it unprompted.
- A build presented as done with an empty cover or empty `og_title` is
  INCOMPLETE, and publishing it is a broken publish — an empty `og_title` is
  invisible on the feed and an empty cover is a blank card.

## Deploy is the only thing that ships

`deploy_website` builds from the **pushed** branch and ships the live site. There
is no separate preview stage. Commit and push everything first, then deploy — and
deploy again after ANY later change. `publish_website` does not deploy; it only
lists the already-live build on the community feed.

Everything you need is under this skill. Do not go looking for other website or
design guidance, and no other skill overrides these rules.

## What this client cannot do

Say so plainly when it comes up; never promise one of these and improvise.

- **No image-to-3D.** No mesh generation, rigging, or animation clips. Games
  built here are 2D, and a "3D" hero is the layered-depth rig in
  `references/wow-catalog.md`, not a model the user can spin.
- **No background remover, AI upscaler, or uncrop.** Generate at the size and
  aspect you need, and get a transparent subject by prompting it on a flat
  chroma ground and keying it out in `sandbox_exec`. `references/asset-system.md`
  has the commands.

## Turn economy

Every tool round-trip costs a turn and clients cap them, so a long build can die
mid-flight and leave the user an unfinished site. Turns are the scarcest resource
after credits:

- **Write every file ONCE, complete.** Compose the whole file, then one write. No
  write-then-patch loops, and never re-read a file you just wrote.
- **Never guess paths.** The tree is documented in the repo's `app/AGENTS.md` and
  in this skill's flows; searching a guessed directory is a wasted turn that ends
  in "not found".
- **Never download or vision-inspect your own generations.** You wrote the prompt;
  re-viewing the result tells you nothing new.
- **Submit everything that can render concurrently** (page assets and the cover)
  with one `generate_image_batch`, build the page while it renders, then collect
  with one `jobs_wait` and one `show_generation_by_ids`.
- **Tool errors cost double** — the failed turn plus the retry. Array params take
  real JSON arrays, never stringified ones.

## Talking to the user

Most users are not technical. Never expose the plumbing in what you SAY. Do not
mention the git repository, cloning, branches, commits, pushing, or the deploy
pipeline in user-facing messages — perform them silently and speak in product
terms:

- "Setting up your site…" — not "cloning the repo".
- "Saving your changes…" — not "committing and pushing".
- "Your site is live: <url>" — not "the build passed".

This is about the words in chat only; keep doing the real steps. The one
exception is a clearly technical user who explicitly asks about the repo or the
deploy mechanics — then answer plainly.

Repository credentials are handled by the service and never returned. Do not ask
for Git tokens or application secret values in chat.
