# Skill: Quanta Design

**Higgsfield-SDK apps only.** Use Quanta ONLY for app surfaces that integrate the
Higgsfield fnf SDK — generation consoles and fnf-backed tools (image/video
generation, media upload, profile, workspace, credits, generation feed/history) —
for layout, styling, fonts, buttons, components, responsive composition,
empty/loading/error states, and premium polish.

**Do not use for anything that does not call the Higgsfield SDK** — marketing/
landing pages, portfolios, brochure/creative sites, and general SaaS/dashboards/
tools build from their template recipe with custom Tailwind/CSS, not
`@higgsfield/quanta/*` components or q-prefixed semantic utilities.

This skill has two layers. **Layer 1 (UX Craft)** decides what to build and how it
must behave — surface choice, interaction, keyboard, forms, motion, states.
**Layer 2 (Quanta Implementation)** decides what everything is made of — tokens,
components, typography, spacing. Never invent colors, fonts, or component styles:
those decisions are already made by Quanta. UX rules below are expressed in Quanta
vocabulary on purpose.

Before coding, read `app/packages/quanta/ai/AGENTS.md`. That package guide is the
canonical Quanta API/token reference — RELY ON IT for component props, variants,
and tokens; do NOT open or grep the component `.tsx` source to re-derive prop
names (it's already documented there, and re-deriving it wastes time). This
skill explains how this template must compose Quanta into generated fnf-SDK app
UIs.

**One exception to "don't read the source": compound-component parts.** For a
prop on a compound part (`Modal.Header`, `Modal.Footer`, `Card.*`, `Vault.*`,
`Grid`) whose mistake is a HARD compile error — or worse, a SILENT one — a
10-second look at that one component file is worth it. Known traps:

- **`Modal.Header` has NO `title` prop; `Modal.Footer` has NO `actions` prop.**
  Compose them: `<Modal.Header><Modal.Title>…</Modal.Title><Modal.CloseButton/></Modal.Header>`
  and `<Modal.Footer><Modal.FooterActions>…buttons…</Modal.FooterActions></Modal.Footer>`.
  `Modal.Footer actions={…}` is a hard error; `Modal.Header title="…"` is the
  dangerous one — `title` type-checks as a native HTML attribute (it renders as
  a hover tooltip) so the build passes but no heading shows. (`Vault.Footer` and
  `Card.Footer` DO take `actions` — the parts are not uniform, which is exactly
  why you check.)
- **`Grid`/`VirtualGrid` `minColWidth` is a CSS length STRING** (`"13rem"`), not
  a number — `minColWidth={200}` fails to type-check.

---

# LAYER 1 — UX CRAFT

These rules fix the "almost right but feels off" class of bugs: dead hover states,
unlabeled icons, forms that yell on every keystroke, spinners that never end,
modals you can't escape. They are ranked: CRITICAL rules are never skipped;
HIGH/MEDIUM rules are skipped only with a concrete reason.

## Surface Selection (what to build first)

Match the first screen to the product type. The product surface itself is screen
one — never a splash, never a marketing hero.

| Product type                              | Surface shape                                                                                                       | Base recipe                                                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Generator / console (image, video, audio) | Prompt box on center in main page + settings pane in prompt box, results screen after first generation with gallery | Studio layout — `app/src/layouts/studio.tsx` (`references/app-layouts.md`) |
| Feed / gallery / history                  | Filterable grid or list, item overlay/inspector                                                                     | App shell + grid section                                            |
| Editor / notes / project tool             | List sidebar, work canvas, optional inspector                                                                       | Split editor/tool                                                   |
| Board / pipeline                          | Horizontal scroll columns inside fixed shell                                                                        | App shell, `overflow-x-auto` region                                 |
| Settings / profile / billing              | Single constrained column of grouped sections                                                                       | Form panel                                                          |
| Dashboard / stats                         | Bands of metric groups, one chart per question                                                                      | App shell + sections                                                |

Density: consoles and tables run tight (`gap-3`, `p-4`); content-first surfaces
(feed, gallery, forms) run spacious (`gap-4 md:gap-6`, `p-4 md:p-6 xl:p-8`). Pick one density per region, not per element.

## Interaction (CRITICAL)

- Touch targets ≥ 44×44px, ≥ 8px apart. Small visual icons get padding or
`iconOnly` Button sizing, not a bigger glyph.
- Every clickable element: `cursor-pointer`, visible hover AND pressed feedback
within ~100ms. Hover is an enhancement, never the only signal — mobile has no
hover.
- Async actions: disable the trigger + show progress (`Progress`, or a
`Loader size="xs" color="neutral"` child inside the busy Button — there is NO
Button `loading` prop). Never leave a button clickable while its request is in
flight; never swap UI with no feedback for >300ms — show skeleton surfaces, not
a lone spinner, for longer loads.
- Disabled = semantic `disabled` attribute + Quanta disabled styling +
`text-q-text-disabled`, not just faded opacity that still accepts clicks.
- Destructive actions: `danger`/`dangerSoft` Button, spatially separated from the
primary action, confirmed via `Modal` — and prefer an "Undo" `toast` over a
confirm dialog for reversible bulk actions.
- Drag interactions need a movement threshold (~6px) so clicks don't become
accidental drags, and real-time visual tracking while dragging.

## Keyboard & Focus (CRITICAL)

- `:focus-visible` ring on every interactive element; never remove outlines.
Tab order must match visual order.
- `Esc` closes the topmost overlay (Modal, Vault, Dropdown, Command) — one layer
at a time. Every overlay also has a visible close affordance.
- Modals trap focus while open and restore focus to the trigger on close.
- Icon-only controls carry an accessible label (`aria-label` / Quanta `iconOnly`
labeling). Meaningful images get alt text; decorative ones get `alt=""`.
- Toasts must not steal focus — `Toaster` announces politely; keep toasts
3–5s with an action button when there is something to act on.
- Don't convey state by color alone: pair color with an icon, label, or `Badge`.

## Overlay Layering (CRITICAL)

- Use Quanta `Select`, `Dropdown`, `Popover`, `Modal`, and `Vault` with the
  portal/layer behavior documented in `app/packages/quanta/ai/AGENTS.md`.
  Popup content must escape a scrolling or `overflow-*` clipping ancestor; do
  not render a selector menu as an inline absolutely-positioned child of a
  creation rail, sticky footer, Modal, or Vault.
- Preserve the semantic layer stack. Use only documented Quanta z-layer
  utilities for app-local surfaces; never patch one collision with arbitrary
  `z-[9999]`, and never assign every popup `z-q-modal`. Avoid accidental local
  stacking contexts (`transform`, `filter`, `opacity`, `isolation`, or a
  positioned element with `z-index`) on wrappers around selector triggers.
- In nested overlays, `Esc` closes the selector/popover first, then the parent
  Modal/Vault. Test pointer, keyboard, focus trap/restore, and click-outside
  behavior with the selector open near every viewport edge.

## Forms & Feedback (HIGH)

- Every input has a visible label (Quanta `Input`/`Textarea` `label` prop), not a
placeholder-only label. Helper text under complex fields, persistent.
- Validate on blur or submit — not on every keystroke. Error appears under the
offending field, states cause + fix ("Prompt is empty — describe what to
generate"), and the first invalid field gets focus after a failed submit.
- Use semantic input types (`email`, `number`, `url`) and autocomplete attributes.
- Submit flows end in a visible outcome: success `toast`/state change, or error
with a retry path. A timeout is an error with retry, not silence.
- Multi-step flows show progress and allow going back; confirm before dismissing
a Modal/Vault with unsaved input.

## Layout & Responsive (HIGH)

- Mobile-first; `min-h-dvh` (never `100vh`); no page-level horizontal scroll —
wide content (boards, tables) scrolls inside its own `overflow-x-auto` region.
- Constrain everything: `min-w-0` + `truncate` on flexible text (with `title` for
the full value), `minmax(0,1fr)` grid columns, `max-w-*` on long-form text.
- Fixed bars (sticky submit rows, floating composers) reserve space for
content (`pb-*` on scroll regions);
respect safe areas on mobile.
- One primary CTA per screen; secondary actions are visually subordinate
(`tertiary`/`ghost`). When actions overflow a toolbar, collapse into
`Dropdown`, don't shrink buttons.
- Current location is always visible: active nav item highlighted independent of
hover; back navigation preserves scroll and filter state.
- Breakpoint behavior: sidebars collapse behind `Tabs`/`Vault` below desktop;
verify at 375px, tablet, and desktop before delivery.
- Generated-media grids use responsive `auto-fit` columns and each card's real
  result/submitted aspect ratio. Keep the full image/video visible; one shared
  16:9 or square cover crop is only for curated marketing/preset thumbnails,
  never Results, History, or a Simple app's generated output.

## Motion (MEDIUM)

- Micro-interactions 150–300ms; complex transitions ≤ 400ms; exits ~60–70% of
enter duration. Ease-out on enter, ease-in on exit.
- Animate `transform`/`opacity` only — never `width`/`height`/`top`/`left`, and
animations must not cause layout shift.
- Animate 1–2 key elements per view; stagger list entrances 30–50ms per item.
Motion expresses cause and effect (panel slides from its trigger side, modal
scales from center) — no decorative-only movement.
- Respect `prefers-reduced-motion` globally; never block input while something
animates.

## Data & Charts (LOW — dashboards only)

- Trend → line, comparison → bar, proportion → donut (≤5 slices, else bar).
- Legends visible, tooltips on hover/tap, gridlines low-contrast
(`border-q-border-subtle` weight), numbers `tabular-nums` and locale-formatted.
- Loading chart = skeleton, empty chart = designed empty state, failed chart =
error with retry. Never render a bare axis frame.

---

# LAYER 2 — QUANTA IMPLEMENTATION

## Higgsfield Integration Rules

Apps render INSIDE Higgsfield — they must be indistinguishable from Higgsfield's
own products.

1. **NEVER customize Quanta styles, and NEVER modify Quanta itself.** No
   className overrides that change a component's look, no color/size/font
   overrides on quanta components, no re-theming, and never edit the vendored
   `@higgsfield/quanta` package. Compose, don't restyle. If a Quanta component
   doesn't fit without customization (a variant/behavior it doesn't offer), do
   NOT bend it — build a small custom component from Quanta primitives instead
   (rule 5).
2. **NO app header.** Apps render inside Higgsfield, whose chrome already
   provides the global header, credits/balance, and account controls — never
   add a top header/app bar, brand/logo row, or nav bar inside the app, and
   never render credits/balance or sign-out controls. In-app navigation lives
   in a Quanta `Sidebar` (see the Studio layout, `app/src/layouts/studio.tsx`) or inline controls
   (tabs, steppers); a page title is just a heading inside the work area.
3. **When a piece of UI you want doesn't exist in Quanta, build it inside the
   app from Quanta primitives with zero customization** — never import a
   third-party UI library or hand-roll a different visual language (see rule 5).
4. **Always dark.** The template pins `data-theme="default-dark"` (+
   `color-scheme: dark`) on `<html>` — apps are permanently dark like every
   Higgsfield product. Never add a theme toggle or a light mode, never use
   `dark:`-conditional styling (there is no light state), and never wire
   quanta's bootstrapScript/ThemeController theme switching.
5. **Fill gaps with your OWN components, built from Quanta primitives + `q-`
   tokens, in the app's own `app/src/components/`** (date picker, calendar,
   sortable data table, multiselect autocomplete, color picker, …). Compose
   Quanta primitives (`Button`, `Input`, `Dropdown`, `Popover`, `Modal`, …) and
   `q-` utility classes into the piece you need, matching Quanta's tokens and
   spacing so it's indistinguishable from a built-in. There is NO fallback
   design system: never add a third-party UI dependency (no shadcn, no MUI, no
   Radix, etc.), and never restyle a Quanta component to force a fit.

## Template Wiring

Quanta is already wired through `app/src/styles.css`.

Keep these pieces:

- `@import "@higgsfield/quanta/tailwind.css";`
  - This single Tailwind entry imports Quanta primitives, theme variables,
  typography, z-index, border-width, and q-* component utilities.
- `@source "../packages/quanta/src";`
  - Required because Quanta is vendored in `app/packages/`; Tailwind must scan
  component source so literal class strings are generated.
- `@theme { --spacing: 0.25rem; }`
  - Restores native Tailwind spacing for generated app layout.
- `@theme inline { ... }`
  - Maps shadcn-style semantic aliases to Quanta variables so legacy scaffold
  pieces still render while new UI uses Quanta.
- `bootstrapScript()` in `app/src/routes/__root.tsx`
  - Keeps persisted theme/brand from flashing on first paint.

Do not remove or duplicate these imports. Do not import Quanta CSS again inside
individual components.

Responsive variants: Tailwind defaults (`sm: md: lg: xl:`) plus quanta's
`q-tablet:` (768px), `q-desktop:` (1280px), `q-wide:` (1920px). `tablet:`/`desktop:`
do NOT exist — they compile to nothing.

## Current Spacing And Token Rules

This is the rule agents must remember:

- **App layout spacing is native Tailwind:** `p-4`, `px-6`, `gap-3`, `mt-6`,
`h-10`, `w-80`, `min-h-dvh`.
- **Quanta semantic styling is q-prefixed:** `bg-q-background-primary`,
`text-q-body-md-regular`, `border-q-border-subtle`, `z-q-modal`.
- **Old numeric spacing classes are wrong for app layout:** do not write
`p-400`, `px-400`, `gap-200`, `mt-300`.
- **Do not use raw q-spacing vars in app code:** avoid `p-q-400` unless you are
intentionally maintaining Quanta internals. Generated app screens should use
native spacing.

Good:

```tsx
<main className="min-h-dvh bg-q-background-primary p-4 text-q-text-primary md:p-6">
  <section className="grid gap-4 xl:grid-cols-[280px_1fr]">
    ...
  </section>
</main>
```

Bad:

```tsx
<main className="bg-background-primary px-400 py-300 text-sm font-medium">
  ...
</main>
```

## Component Priority

Use Quanta components before legacy `app/src/components/ui/*`, before direct Radix,
and before third-party equivalents.

| Need                           | Use                                                                                                                                                     |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actions and links              | `Button` from `@higgsfield/quanta/button`                                                                                                                 |
| Top navigation                 | `NavigationMenu` from `@higgsfield/quanta/navigation-menu`                                                                                                |
| App navigation rail            | `Sidebar` from `@higgsfield/quanta/sidebar`                                                                                                               |
| Text fields                    | `Input` from `@higgsfield/quanta/input`                                                                                                                   |
| Generation prompt surface      | The shipped template dock components (`StudioPromptBox` / `Composer` / `PromptBox`) — never hand-rolled; which one and how is in the repo's `app/src/components/AGENTS.md` catalog |
| Multi-line text (non-prompt)   | `Textarea` from `@higgsfield/quanta/textarea`                                                                                                             |
| Binary settings                | `Switch`, `Checkbox`, `Toggle`                                                                                                                            |
| Exclusive choices              | `RadioGroup`, `RadioLabel` from `@higgsfield/quanta/radio`                                                                                                |
| Option pickers (settings)      | `Select` from `@higgsfield/quanta/select`                                                                                                                 |
| Segmented modes/views          | `Tabs`                                                                                                                                                    |
| Menus/model pickers            | `Dropdown`                                                                                                                                                |
| Command palette/search actions | `Command` from `@higgsfield/quanta/cmdk`                                                                                                                  |
| Dialog/editor/confirm          | `Modal`                                                                                                                                                   |
| Edge sheet/mobile panel        | `Vault`                                                                                                                                                   |
| Toasts                         | `Toaster`, `toast` from `@higgsfield/quanta/sonner`                                                                                                       |
| Progress/loading               | `Progress`                                                                                                                                                |
| In-button/inline busy spinner  | `Loader` from `@higgsfield/quanta/loader`                                                                                                                 |
| Generation feeds / result grids | `Grid` from `@higgsfield/quanta/grid` (`cols="auto-fit"` + `minColWidth` for generation feeds — never breakpoint column ladders)                         |
| Metadata/status                | `Badge`, `Tag`, `Dot`, `Kbd`, `Avatar`, `Divider`                                                                                                         |

Legacy shadcn-style components may remain for scaffold compatibility, but new
client UI should not start there. Also do not import `cmdk`, `sonner`, or
`vaul` directly for new UI; Quanta already wraps those interaction patterns with
the correct visual system.

Components import from Quanta subpaths (`import { Button } from
'@higgsfield/quanta/button'`, `import { Toaster, toast } from
'@higgsfield/quanta/sonner'`, …). Mount one `<Toaster />` near the root shell
before calling `toast.*`.

## Premium App Layout Rules

Generated app UIs must look designed, not like raw low-level layouts.

1. **Start with the product surface** (Surface Selection table in Layer 1) —
   the actual tool is screen one.
2. **Stable shell, meaningful regions** — `min-h-dvh bg-q-background-primary
   text-q-text-primary`, scroll regions `min-h-0 overflow-auto`; most tools
   need a sidebar/list + main work area (+ optional inspector). No header/top
   bar — actions live in the work area's toolbar row or the sidebar.
3. **Space + constraints** — start `p-4 md:p-6 xl:p-8`, `gap-4 md:gap-6`
   (tighten only for dense tables/toolbars); `min-w-0` + `truncate` +
   `max-w-*` + `minmax(0,1fr)` so content never overlaps.
4. **Make state visible** — selected/hover/focus/empty/loading/error are
   designed surfaces, not bare text.
5. **Avoid card soup** — no cards inside cards inside cards; shells, bands,
   lists, and repeated item cards only where semantically useful.
6. **Icons** — icon-only buttons take `iconOnly` + an accessible label; never
   emojis as icons; ONE family: lucide via the Quanta `Icon` wrapper
   (`import { Sparkle } from "lucide-react"` → `<Icon as={Sparkle} />`).
7. **Balanced palette** — Quanta provides the surfaces and accents; no
   one-note gradients, blur blobs, or raw decorative shapes.

## Layout Recipes

### Code layouts (preferred starting points)

The app's starter template is chosen at `create_website` (`template` param —
`studio` / `preset` / `app-detail`; picking guide:
`references/app-layouts.md`); the repo then ships that layout as REAL CODE in
`app/src/layouts/`, already wired as the home page. Adapt it in place from the
code — the full anatomy and rules are the repo's `app/src/layouts/AGENTS.md` +
`app/src/components/AGENTS.md`, read after cloning.

| Product shape                                                                | Template (adapt in place)          |
| ---------------------------------------------------------------------------- | ---------------------------------- |
| Full workspace — projects sidebar + prompt composer + generations feed        | `studio`                           |
| Pick-a-style-then-generate — preset/template gallery + a creation rail        | `preset`                           |
| Step-by-step generate → select → refine wizard                                | `preset` + `Tabs`                  |
| Single tool's landing/detail page — two-column generator hero + how-it-works  | `app-detail`                       |
| Upload-configure-iterate workspace (try-on / restyle / character)             | `preset` + `upload-field`/`Tabs`   |
| Before/after enhance tool (retouch / restore / upscale)                       | `app-detail` + `before-after-compare` |

When none fits and the user asks for a custom shell, still create from the
closest template and compose the same primitives: a
`min-h-dvh bg-q-background-primary text-q-text-primary` shell, `grid`
regions (`xl:grid-cols-[280px_minmax(0,1fr)]` sidebar+main, add a
`_360px` inspector column for editor/tool splits), scroll regions with
`min-h-0 overflow-auto`, page title as a heading row inside the work area
(never an app header), sidebars collapsing behind `Tabs`/`Vault` on small
screens, and a `max-w-3xl` single column for form panels. Use cards for real
grouped content, not as a wrapper around every section.

## Typography Rules

Use Quanta composite typography utilities. Do not make the whole app
`text-sm font-medium`.

The composite utilities carry the brand fonts: title/headline/display utilities
render Space Grotesk (the brand headline face) and body renders Inter — use the
composite utility and the right font comes with it. Never import fonts.

| Use                                       | Utility                                                          |
| ----------------------------------------- | ---------------------------------------------------------------- |
| App page title / hero in a tool surface   | `text-q-headline-sm-semi-bold` or `text-q-headline-md-semi-bold` |
| Large in-app display (generator headline) | `text-q-display-lg-bold` or `text-q-display-md-bold`             |
| Section title                             | `text-q-title-md-semi-bold`                                      |
| Item title                                | `text-q-title-sm-semi-bold` or `text-q-label-lg-semi-bold`       |
| Body                                      | `text-q-body-md-regular`                                         |
| Meta/help                                 | `text-q-body-sm-regular` or `text-q-caption-sm-medium`           |
| Code/ids                                  | `text-q-mono-sm-regular`                                         |

Color text with semantic utilities:

- Primary: `text-q-text-primary`
- Supporting: `text-q-text-secondary`
- Low emphasis: `text-q-text-tertiary`
- Disabled: `text-q-text-disabled`
- On brand/inverse surfaces: `text-q-text-inverse`

Readability details: prefer wrapping over truncation; when truncating, add
`truncate` + `title`. Use `tabular-nums` for counters, prices, timers, and table
number columns so digits don't jitter.

## Button Rules

Use `@higgsfield/quanta/button`.

```tsx
import { Button } from '@higgsfield/quanta/button'
import { Loader } from '@higgsfield/quanta/loader'
```

- **Default size is `md`.** Set `size="md"` on Buttons by default — Quanta's own
default is `sm`, which reads too small on app surfaces, so pass `md` explicitly
(drop to `sm`/`xs` only in genuinely dense toolbars/pills, per below).
- Main/generate action: `variant="marketingPrimary" size="md"` — the accent CTA
every Higgsfield product uses for the generate/main action (like the composer's
GENERATE button).
- Generate buttons ALWAYS show the credit cost INSIDE the button, formatted
`{label} {sparkles icon} {credits}` — the sparkle is the branded asset
(`import Sparkles from "@/assets/icon-sparkles-soft.svg?react"`, 14px) and
the credits number inherits the label's font (no smaller/other typography) —
never a separate cost line outside the button, never a costless generate
button. See any template scaffold's submit.
- Variant colors do NOT follow the names: `primary` = flat LIME,
`secondary` = solid WHITE, `tertiary` = dark white/10 glass, `ghost` =
transparent. Ordinary actions and navigation use the dark `tertiary`/`ghost`;
`secondary` (white) only where the real product shows a white button; flat
lime `primary` is almost never right — the lime CTA is `marketingPrimary`
(3D bevel).
- Destructive action: `danger` or `dangerSoft`.
- Soft brand emphasis: `brandSoft`.
- Marketing accents: `marketingPrimary`, `marketingSecondary`,
`marketingTertiary`, `marketingGhost`.
- Busy: render a `Loader size="xs" color="neutral"` child while the request is
in flight — there is NO Button `loading` prop.
- Dense toolbars use `size="sm"` or `size="xs"`.
- Icon-only buttons must pass `iconOnly`, fixed dimensions from the component,
and an accessible label.

## State Rules

Every generated app UI should have credible states:

- Loading: `Progress`, skeleton-like surfaces, or disabled controls. Anything
over ~300ms shows a skeleton; anything async disables its trigger.
- Empty: a centered or region-local empty state with a title, supporting text,
and a relevant action.
- Error: a styled message with retry/action; do not dump raw stack traces.
- Disabled/unavailable: disabled controls plus short explanation when needed.
- Selected/current: visible selected state independent of hover.
- Mutations feel instant: update the UI optimistically, reconcile on response,
and offer `toast` + Undo for destructive/bulk operations.

## Debugging Missing Styles

When styles look missing or spacing collapses:

1. Check `app/src/styles.css` still imports `@higgsfield/quanta/tailwind.css`.
2. Check `@source "../packages/quanta/src";` is present.
3. Check `@theme { --spacing: 0.25rem; }` is still present after the Quanta
  import to restore normal Tailwind layout spacing in generated app UIs.
4. Check the app uses native spacing (`p-4`, `gap-2`) and q-prefixed semantic
  utilities (`bg-q-*`, `text-q-*`).
5. Check imports are from Quanta subpaths like `@higgsfield/quanta/button`.
6. Check `app/packages/quanta/package.json` still depends on `@base-ui/react`.

Run a quick stale-spacing scan when layouts look wrong:

```bash
rg 'px-400|p-400|py-300|mt-300|gap-200' app/src app/packages/quanta/ai
```

Fix any hits in app/source code to native spacing (`px-4`, `py-3`, `mt-3`,
`gap-2`). It is fine for docs to mention old classes only inside bad examples.

## Anti-Patterns

- Raw palette classes like `bg-red-500`, `text-zinc-400`, and raw hex values in
`className`/`style`.
- Invented `q-*` utilities like `bg-q-card-primary`.
- `tablet:`/`desktop:` responsive variants — they do not exist; use `md:`/`xl:`
(or quanta's `q-tablet:`/`q-desktop:`/`q-wide:`).
- Old spacing token classes: `p-400`, `px-400`, `gap-200`, `mt-300`.
- Raw q-spacing in app code: `p-q-400`, unless maintaining Quanta internals.
- Arbitrary text sizes such as `text-[13px]`.
- Splitting Quanta typography into `text-xl font-semibold`.
- Custom fonts / Google Fonts imports — Quanta typography is the type system.
- Restyling Quanta components: className/color/size/font overrides that change
how a component looks, or any re-theming.
- Credits/balance displays or sign-out/account controls inside the app — the
Higgsfield host chrome owns those.
- Floating loose text/actions on the canvas without a shell or region.
- Hover-only selected states; hover-only affordances of any kind.
- Empty/loading/error states as bare text.
- Emojis as icons; mixed icon families or stroke widths.
- Placeholder-only form labels; errors shown only in a toast or page top.
- Removing focus outlines; positive `tabindex`.
- Direct `cmdk`, `sonner`, `vaul`, Radix, or Base UI usage for new app UI when
Quanta already provides the pattern.

## Pre-Delivery Checklist

Mechanical scan first:

```bash
rg 'px-400|p-400|py-300|mt-300|gap-200|bg-(red|blue|zinc|gray|slate|neutral)-\d|text-(zinc|gray|slate|neutral)-\d|text-\[\d+px\]|#[0-9a-fA-F]{3,6}' app/src
```

Any hit in app source is a defect (docs/bad-examples excluded).

Then verify by hand:

- [ ] First screen is the product surface, inside a stable shell
- [ ] All styling via q-tokens and Quanta components; spacing via native Tailwind
- [ ] Quanta components unstyled (no restyling overrides); no app header/top
  bar, no credits/balance or sign-out controls anywhere (apps render inside
  Higgsfield — host chrome owns those)
- [ ] Dark only: no theme toggle, no light mode, no `dark:` styling; every
  generate button reads `{label} {sparkles} {credits}` (the branded
  `@/assets/icon-sparkles-soft.svg` icon, credits in the label's font);
  non-generation buttons use the dark `tertiary`/`ghost`
- [ ] One icon family: lucide (`import { X } from "lucide-react"`, rendered
  via the Quanta `Icon` wrapper) — never a second icon set
- [ ] Every interactive element: cursor-pointer, hover + pressed feedback,
  visible `:focus-visible` ring
- [ ] Touch targets ≥ 44px; icon-only controls have accessible labels
- [ ] `Esc` closes overlays; modals trap and restore focus
- [ ] Select/Dropdown/Popover content portals above its owning Modal/Vault and
  is neither clipped by a scroll rail nor hidden behind a sticky surface
- [ ] Forms: visible labels, validation on blur/submit, error under field with a
  fix, focus moves to first invalid field
- [ ] Async: triggers disable while pending; >300ms shows skeleton; success and
  failure both have designed outcomes (toast / retry)
- [ ] Empty, loading, error, and selected states exist for every list/region
- [ ] Destructive actions: danger variant, separated, confirmed or undoable
- [ ] No page-level horizontal scroll; text truncates with `min-w-0`/`truncate`;
  checked at 375px, tablet, desktop
- [ ] Mixed 1:1, 4:3, 16:9, and 9:16 generation cards reflow with `auto-fit`
  columns and preserve complete media instead of inheriting one preset crop
- [ ] Motion 150–300ms, transform/opacity only, `prefers-reduced-motion`
  respected
- [ ] State never conveyed by color alone
