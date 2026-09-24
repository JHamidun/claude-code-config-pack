# scroll-scrub — the animated website (`type: "website"` only)

This is the **animated website** — the DEFAULT Tier-1 experience for every
`type: "website"` build. The visitor's scroll plays a generated film while the
page's semantic chapters read over it. Follow this reference for every website
unless the user EXPLICITLY asked for a different treatment (in which case pick a
technique from `references/wow-catalog.md` instead). It is also the reference for
any brief that asks for a scrollable world, continuous camera journey, diorama
fly-through, or browse-through-the-industry site. In catalog terms this is
**A4 — Seam-locked scroll scrub**.

This is a specialized website build, not a Higgsfield app. Generate the film
with Higgsfield during the build, download it into the site, and ship a
standalone branded website that performs no runtime generation, uses no fnf SDK,
and mentions no Higgsfield branding.

---

## The engine SHIPS — never rebuild it

`create_website` scaffolds the site from the **`scroll-scrub` template**, which
already contains the runtime:

```
create_website(type="website", template="scroll-scrub", category=..., subdomain=...)
```

**Always pass `template: "scroll-scrub"` for an animated website.** Omit
`template` only for a `non-animated` build, which gets the plain scaffold.

The repo then arrives with:

| Path | What it is |
|---|---|
| `app/src/components/scroll-scrub/scroll-scrub.tsx` + `.css` | The full engine. Do NOT rewrite it. |
| `app/src/scroll-scrub-scenes.ts` | Brand tokens + the scene array — the file you fill in. |
| `app/src/routes/index.tsx` | The page, composed around `<ScrollScrub />`. |
| `app/AGENTS.md` | The in-repo contract. Read it after cloning. |

The engine already handles Blob-backed seeking, seek coalescing, lazy nearby
segment loading, desktop/mobile sources, exact-frame posters held until a real
painted frame, iOS gesture priming, `prefers-reduced-motion`, reverse scroll,
and full teardown. You do not write, paste, or re-derive any of it.

`references/scroll-scrub-asset-react.md` and `-css.md` remain as the ENGINE
SOURCE OF RECORD for maintainers. During a build you do not need them: the
template already carries that code. Read them only when a task is specifically
about changing the engine itself.

---

## Fit it into the existing website pipeline

Keep the single intake call and every normal website phase. Do not add a second
interview. Resolve missing details in the existing intake or choose defaults in
the design brief.

### Phase 0 — lock the journey

This is the journey block that `Animation mode: animated-website` obligates (see
`references/website-flow.md` Phase 0). The brief is INCOMPLETE — a hard stop —
until these decisions are written into `app/design-brief.md`; the Phase 5 gate
(item 9f) checks that the Journey and Journey shape are present.

#### Journey shape — pick ONE (this is the big cost lever)

- **`single-shot` — the DEFAULT.** ONE continuous ~15s film, generated in ONE
  call, scrubbed end to end. No seams, because there is only one clip. The
  chapters are HTML that read over it. Choose this for a brand, a product, a
  service, a portfolio, a launch — anything whose story is one subject seen
  ever more closely. **When in doubt, single-shot.**
- **`multi-leg` — opt in only when the brief genuinely needs several WORLDS.**
  4–7 distinct places the visitor travels between, where each destination is a
  different environment rather than a closer look at the same one. Costs one
  generation per leg, strictly sequential (each leg starts from the previous
  leg's real last frame), plus a per-leg encode and inspection. Budget several
  extra minutes PER LEG and say so before choosing it.

"It would look cooler with more scenes" is NOT a reason for `multi-leg`. A
tighter single-shot film beats a loosely-seamed chain, and it reaches the user
far sooner.

Write into the brief:

- **Journey shape:** `single-shot` or `multi-leg` (+ one line of justification
  if `multi-leg`).
- **Journey:** the chapters — for `single-shot`, 3–6 chapters mapped to moments
  of the one film; for `multi-leg`, 4–7 scenes as a real narrative or value
  chain. Give each a focal point, one short headline, one sentence, and at most
  0–3 proof tags. Keep the existing eyebrow ration.
- **World grammar:** one byte-identical style preamble, perspective, palette,
  light direction, surface finish, and background behavior. For `multi-leg`,
  change only the scene subject and focal action between legs.
- **Camera architecture** (`multi-leg` only): A or B below.
- **Mobile framing:** include mobile by default, without another question. Keep
  every focal point inside the center-safe area and plan lighter mobile
  encodes.
- **Delivery budget:** ≤32 MiB for all desktop clips, ≤16 MiB for all mobile
  clips. Shorten or re-encode before relaxing it.

---

## The footage contract — what makes a scrub look expensive

The page plays the film forward AND backward at the speed of the user's scroll,
and holds any single frame as a still whenever they pause. That dictates the
footage. Direct it like a high-end product film, and obey these or the scrub
looks broken regardless of how good the render is:

- **One continuous move — no hard cuts.** A cut becomes a jarring jump
  mid-scrub. Stage it as a single unbroken camera move (slow orbit, push-in,
  rise, fly-through) or one continuous transformation of the subject. Connect
  beats with continuous motion, never a cut.
- **One hero subject, kept centered, with clean negative space** around it —
  that space is where the chapter copy sits. The video fills the viewport and
  crops the edges (`cover`), so keep the subject center-safe and let the edges
  be expendable.
- **A background the copy can survive.** Dark, seamless, low-detail (studio
  black/charcoal, a soft gradient, the subject emerging from darkness) is the
  reliable choice. A bright, busy, full-frame environment behind body copy is
  the single most common reason a beautiful film reads as unusable.
- **Slow, steady motion** — constant speed, gentle ease only at the very start
  and end. It should feel cinematic-slow; the scroll supplies the pacing.
- **Locked exposure and white balance, no flicker; minimal motion blur.** Every
  frame is shown as a still, so exposure pumping shimmers and heavy blur smears.
- **Resolves at both ends:** the first frame reads as the establishing shot, the
  last as the closing beauty state. START state ≠ END state, or the scrub has no
  payoff.
- **No on-screen text, logos, or watermarks** — all type is HTML over the video,
  so it stays crisp, selectable, and translatable.

Subjects that scrub beautifully: a product slowly orbiting on black; an
exploded-view assembly; a macro detail traveling along a surface; a
transformation or morph; a hero object emerging from darkness. Avoid: cuts,
fast pans, handheld shake, busy bright backgrounds, and colour/exposure flicker.

---

### Phase 1 — the storyboard (ONE image), then the boards you actually need

**`single-shot`:** generate ONE 16:9 storyboard image laying the film out as
**6 keyframes of a single continuous move, in a 6-panel grid**. This pins
palette, look, lens, and camera progression for the price of one image, before
you spend on video. Prompt it explicitly as one continuous move — "NOT six
different scenes" — and with no text anywhere in the image.

Show the storyboard to the user as you continue (post its result URL, keep
working — do NOT block the build waiting for a reply). Do NOT download it or run
a vision pass over it — you just generated it from your own prompt, and
re-inspecting your own render tells you nothing the prompt didn't. The user is
the reviewer; re-roll only on their feedback (budget 2 re-rolls). The
storyboard's job id is all the film step needs.

**`multi-leg`:** generate one board per scene as usual, and make the boards
prove the chapters belong to one world — camera height, vanishing logic,
material language, palette, and light stay coherent while the subject varies.

Either way, compose boards and generation-source stills center-safe.

### Phase 2 — generate the film

Call `models_list` first for the current image/video model
schemas. Require the exact media roles the shape needs; never rely on a
remembered roster or invent `start_image`/`end_image` roles.

#### `single-shot` (default)

ONE `generate_video` call. Drive the video model at its highest
quality with the approved storyboard as a **style/look reference**, and put the
continuous move in the PROMPT:

- Pass the storyboard with the model's GENERIC image/reference role — **not
  `start_image`**. As a start frame it becomes the literal first frame, so the
  page opens on a static storyboard for a second or two before motion begins.
- Ask for the longest single take the model supports (~15s), 16:9, highest
  resolution, and audio off — the page scrubs frames, not sound, and off is
  cheaper.
- Name the grade and the hexes; restate "no cuts, no camera shake, slow steady
  motion only, locked exposure, no on-screen text".

**In the SAME beat as submitting the film, start the launch cover/OG — exactly
ONCE** (`references/app-cover.md`) — it renders concurrently with the film
instead of serializing a second wait at the end. This is its single start point:
kicking it off any earlier, before Phase 1 locked the look, is what makes a build
render the cover twice and abandon the first one. Then build the page (scenes
file, chapters, copy, styles) WHILE both render: clip filenames and poster paths
are yours to choose, so nothing about the page depends on the render finishing.
Poll each job ONCE, at the moment its output is the next input — not between
every step.

Download the finished film, encode (below), and wire the real files in. Do NOT
vision-inspect the film, its frames, or its posters — single-shot has no seams
to verify, and the footage contract was enforced by the prompt. That is the
whole media chain.

#### `multi-leg` — Architecture A, continuous forward flight

Generate the legs sequentially:

1. Start leg 1 from the approved scene-1 still using the model's documented
   start-frame role.
2. Extract the completed leg's ACTUAL last rendered frame, upload it, and use
   that exact frame as the next leg's start. Never use a board or an
   independently imagined destination still as the seam handoff or poster.
3. Do not constrain the next leg with a wide end frame. Prompt it to continue
   the same gentle forward velocity. An orbit, lateral track, crane, or detail
   push inside a leg is fine, but the final second settles into the same slow
   forward drift the next leg begins with.
4. Inspect the last frame before spending on the next leg. Re-roll a leg that
   ends mid-orbit, with sideways blur, or facing the wrong exit direction.

Position continuity comes from the exact-frame handoff; velocity continuity from
matching direction and speed on both sides. Both are required.

#### `multi-leg` — Architecture B, diorama dives plus aerial connectors

Use this only when pulling back to a world map is part of the concept.

1. Generate all scene dives independently from their approved stills.
2. Extract the ACTUAL last frame of dive `i` and ACTUAL first frame of dive
   `i+1`.
3. Generate connector `i` from those two uploaded boundary frames using the
   exact start/end roles the current model schema reports. Batch all connectors
   once their boundaries exist.
4. The connector pulls out of scene `i`, crosses the world, and descends into
   scene `i+1`.

Require both equalities at every join:

```text
dive[i].last pixels == connector[i].start pixels
connector[i].end pixels == dive[i+1].first pixels
```

A very short crossfade is insurance against encoder drift only. It cannot repair
a wrong endpoint or the rewind created by a forward dive followed by a backward
pull-out — switch that concept to A.

### Encode direct MP4s for scrubbing

Scrub the optimized MP4 directly. Do not export thousands of frame images.

Read `references/scroll-scrub-asset-video.md`, copy its fenced
Bash into `/tmp/scroll-scrub-video.sh`, and use that deterministic helper:

```bash
bash /tmp/scroll-scrub-video.sh desktop source.mp4 app/public/assets/world/scene-01.mp4
bash /tmp/scroll-scrub-video.sh mobile  source.mp4 app/public/assets/world/scene-01-mobile.mp4
bash /tmp/scroll-scrub-video.sh poster  app/public/assets/world/scene-01.mp4        app/public/assets/world/scene-01-poster.png
bash /tmp/scroll-scrub-video.sh poster  app/public/assets/world/scene-01-mobile.mp4 app/public/assets/world/scene-01-mobile-poster.png
```

`bounds` (writing `<prefix>-first.png` / `<prefix>-last.png`) is needed only for
`multi-leg` seam handoffs. Upload each boundary frame with `media_upload`, PUT
the bytes to its presigned URL, and call `media_confirm` before using its media
id in `generate_video`.

- Desktop: native resolution, H.264/yuv420p, CRF ~20, GOP 8, scene-cut keyframes
  disabled, audio removed, `faststart`.
- Mobile: cap height at 720px, CRF ~23, GOP 4, audio removed, `faststart`.
- The poster commands run AFTER encoding, so every poster is the first frame of
  the exact clip the browser decodes. Never substitute a still or a black box.
- Store only selected, encoded assets in `app/public/`; keep raw clips, boundary
  frames, and rejects out of public assets.
- Measure both chains against the brief's byte budget. Visited clips are
  retained for smooth reverse scroll, so oversized clips cost memory too.

The film's posters cover hero/content imagery for their chapters. Continue
generating the normal logo, icons, section UI assets, head kit, and OG assets,
but never a redundant second hero film.

### Phase 3 — fill in the scenes (the engine is already there)

Edit `app/src/scroll-scrub-scenes.ts`: set the brand tokens and replace every
`<...>` placeholder with real copy. For `single-shot` that is ONE entry whose
`clip` is the film; for `multi-leg`, one entry per leg in journey order.

Then compose `app/src/routes/index.tsx` around `<ScrollScrub />`: the site's own
nav, the chapter CTAs from the brief's CTA inventory, and the content sections
that follow the journey. Keep all chapter copy server-rendered in ordinary
semantic `<article>` flow; the client controller owns media time only.

Hard invariants (the template's `app/AGENTS.md` restates them):

- Every `poster` is the exact first frame of the clip beside it.
- Provide `mobilePoster` whenever `mobileClip` is set.
- Keep the scenes array a module constant — changing its identity rebuilds the
  controller.
- Never drive per-frame values through React state.
- Add `blob:` to the CSP `media-src`; keep clip fetches same-origin.

The engine intentionally builds no header, no generic button system, no scroll
hint, and no per-scene eyebrow. Compose those yourself.

### Phase 4 — motion and interaction

Let the controller own scroll-to-video time. Keep the normal Lenis-to-GSAP
ticker bridge for other cinema motion, but never attach a second scrub timeline
to the same video elements. Use transform-only entrance motion for surrounding
chrome, keep chapter copy fully rendered, and preserve the initial poster before
client initialization.

Support reverse scroll as a first-class path. A seam that works only forward is
still broken.

## A4 pre-delivery QA

Complete all normal Phase 5 checks, then verify by READING the code and the
encoded assets — the mechanical gate is the verification, and there is no
browsing step (the sandbox browser cannot reach a local preview, and the flow
does not do post-deploy visual review):

- `scroll-scrub-scenes.ts` has no `<...>` placeholder left, and every `clip` /
  `poster` / `mobileClip` / `mobilePoster` path exists in
  `app/public/assets/world/`.
- Every poster was generated from its ENCODED clip, after encoding.
- `multi-leg` only: every seam uses an actual rendered boundary frame, and
  camera velocity does not reverse unintentionally across a seam.
- Desktop and mobile encodes both exist; measured totals are inside the brief's
  byte budgets.
- The CSP includes `blob:` in `media-src`.
- Chapter headings are in DOM/reading order and route buttons are keyboard
  accessible; active state is not hover-only.
- Reduced motion keeps the full story usable with zero video fetches.
