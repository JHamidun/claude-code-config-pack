# Optional built-in motion styles

This library gives the user recognizable starting points. It is not a template
allow-list and does not replace episode-specific direction. The workflow has three
style routes:

- `auto` — the user picks Auto or delegates the choice, including an explicit
  no-questions request without a supplied style. Derive a bespoke direction from the script,
  audience, supplied references, and host footage. A built-in style may be used as
  inspiration, blended, or ignored; automatic mode is never required to resolve to a
  preset.
- `preset` — use one built-in style only when the user explicitly selects it. Adapt
  its visual grammar to the channel, script, assets, and actual host footage instead
  of reproducing a fixed palette or layout.
- `custom` — follow the user's own art direction, brand system, or visual references.
  Do not force custom input into the nearest built-in style.

## Initial style choice

For a direct episode with no resolved style, include one motion-style question in
the grouped intake. Present ten individually named choices: **Auto**, each of the
eight built-ins below, and **My own direction or references**. Show a numbered list
in normal chat, or use an actually available host question UI with its supported
schema. Do not invent a callable question tool. Translate the question and short
descriptions into the user's language; keep each built-in name recognizable.

Wait for the answer; an unanswered question is not permission to choose Auto. Apply
an already supplied style, style reference or saved choice directly, without asking
again. An explicit delegation or no-questions request uses Auto when no style was
supplied.

If the user directly asks to see styles or an older conversation has only resolved
the built-in category, present the same flat selectable list. Wait for an actual
preset selection; interest in the built-ins alone does not authorize selecting one.
For custom, ask only for the missing direction or references and reuse anything
already supplied. Never invent a replacement preset list or mix music settings into
these options.

Save the resolved route in `brief.json.motion_style` (`mode: "auto"`,
`mode: "preset"` plus `preset: "<built-in-id>"`, or `mode: "custom"` plus the supplied
direction and references), then proceed with the usual autonomous flow. This choice
does not add a later approval checkpoint. Auto still requires authored, implemented
motion; it does not mean omitting motion or using generic static-image fades.

## Built-in choices

| Id                    | Name                                                       | Direction                                                                                                                  |
| --------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `bold-editorial`      | [Bold Editorial](motion-style-bold-editorial.md)           | Magazine composition, expressive type scale and image crops, with decisive reveals and composed holds.                     |
| `funky-modular`       | [Funky Modular](motion-style-funky-modular.md)             | Playful modules, graphic shapes and color blocking, with sequential builds and controlled snap-and-settle.                 |
| `luminous-interface`  | [Luminous Interface](motion-style-luminous-interface.md)   | Layered product and data language, with clear state changes, connected elements and restrained luminous depth.             |
| `documentary-collage` | [Documentary Collage](motion-style-documentary-collage.md) | Layered evidence, paper and archival material, with placed entrances and continuity between related objects.               |
| `web-brutalism`       | [Web Brutalism](motion-style-web-brutalism.md)             | Raw condensed type and monospace metadata on a hard grid; mechanical cuts and wipes against dead-still holds.              |
| `minimal`             | [Minimal](motion-style-minimal.md)                         | Precise typography, generous space and one clear focal idea; controlled reveals, connected transformations and calm holds. |
| `press`               | [Press](motion-style-press.md)                             | Machined print structure on one hard margin; switch-like events, screened objects and completely still holds.              |
| `editorial-overlay`   | [Editorial Overlay](motion-style-editorial-overlay.md)     | Presenter-led overlays in composed emptiness; serif claims, soft plates and one accent, arriving and settling.             |

Bold Editorial uses magazine hierarchy and image/type composition; Web Brutalism uses
mechanical print-and-terminal structure, stark scale extremes and harder attacks.
Minimal keeps movement expressive through placement, timing and continuity, with a
quieter surface than Luminous Interface's layered modules and luminous depth. Press shares
Web Brutalism's mechanical attacks but organizes everything on one margin as printed matter,
with screened objects and figure captions rather than terminal metadata. Editorial Overlay
keeps the host in frame and docks quiet serif compositions into the empty side, where Bold
Editorial composes the full frame and Minimal drops the accent and the containers.

Every style can use standalone typography, text with imagery, or a graphic system,
depending on the beat. These are composition choices within the selected style, not
extra presets or intake questions. A word, phrase, quotation or numeral can carry the
whole composition. Add a card, panel or label background only when grouping or
readability needs it; a style's modules and surfaces are not required around every text.

The detailed profiles belong to this workflow and sit beside this file. After a preset is selected, load
the installed `references/motion-style-<preset-id>.md` file before
motion direction and again before final motion authoring. Read only that profile.
Supply its visual intent and the episode adaptation to `motion-craft`, which chooses
suitable craft techniques within that direction. Profile timings and proportions are
adjustable starting points, not a rendering contract or a mandatory treatment sequence.
In auto/custom, consult a relevant profile only as an influence and keep the chosen
route. Never turn this library into an automatic topic-to-preset lookup.

## Adaptation contract

For any selected preset:

1. Keep the preset's compositional logic, element family, and motion character
   recognizable.
2. Re-author palette, typography, copy, density, asset use, and exact treatments for
   the current episode.
3. Use only elements that clarify a real script beat. The style does not create an
   event quota.
4. Treat shared vocabulary as a grammar, not a reusable finished component. Related
   ranking, timeline, catalog, and evidence beats should develop an intentional state;
   do not reset the same panel, composition, or reveal with new copy for each item.
5. Protect the host, captions, evidence, and actual generated camera geometry. Omit or
   redesign an element when the footage cannot support it.
6. Do not import external branded marks, logos, or reference copy. References describe
   visual principles, not assets to reproduce.
7. Read the completed `visual-plan.json.coverage` before adapting
   the preset. Its selected stills, generated video, supplied media, and host-only
   passages are first-class inputs; never replace them with the preset's graphic
   vocabulary.
8. The selected profile informs `motion-direction.md` and governs craft choices over
   generic defaults. Keep its character recognizable in composition, information
   states and movement, while `video-editing` and `motion-craft` choose exact mechanisms
   and values from measured speech and actual footage. Renderer capabilities bound
   feasibility; adapt unsupported effects without replacing the style with generic
   fades. In auto/custom, the authored direction has the same authority.
9. Tie speech-dependent treatments to measured phrase anchors and preserve readable
   lifetimes, including a preset's hard attacks or quiet holds. Protect the host's face and
   evidence from obscuring texture, inversion or glitch effects. A style does not
   change picture/audio ownership or authorize another generation.
   For Web Brutalism, threshold, halftone or frame-wide inversion over the host's face
   requires an explicitly approved emphasis moment; otherwise keep that treatment
   on the graphic material. Reuse existing user authorization without adding a checkpoint.

In `auto`, describe why the resulting direction fits the episode. If it borrows from a
built-in, name the influence without changing the route to `preset`. In `custom`,
record the user's supplied direction and references directly and mention any necessary
readability adaptation rather than renaming the result as a built-in.
