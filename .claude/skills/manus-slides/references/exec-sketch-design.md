# Visual system and the three treatments

## Identity of this engine

Our hybrid adapts an existing presentation's visual grammar rather than replacing it with a
generic AI template. It combines the supplied palette/type, executive-slide readability and
semantic marker diagrams. It is different from a literal notebook theme or photographed whiteboard.

| Mode | Canvas | Ink/accent | Use |
|---|---|---|---|
| Light | Warm paper #F8F5EC | Black / yellow #FFC000 | Explanation, comparisons, setup |
| Dark | Black #000000 | White / yellow #FFC000 | Strong claims, loops, summary |
| Classic | Light #F1F3F5 | Indigo #0B1021, blue #3B5BDB, copper #C77B30 | Executive/business decks |
| Light calm ⭐ | Warm paper #F7F3E8 | Warm black #1A1814 / marigold #FFC000 | Default light for new decks |
| Dark calm ⭐ | Black #000000 | Warm off-white #F2EFE6 / marigold #FFC000 | Default dark for new decks |

Light/dark are independent art directions, not a CSS inversion of one PNG. Change tokens and
regenerate with the intended contrast. Marker is a selective animation treatment, not a mandatory
fourth palette. In video, alternate light, dark and occasional moving marker according to meaning,
not mechanically on every cut. Keep typography and object vocabulary coherent across treatments.

## Semantic composition

Prefer one of: task → tool → result; before → after; three-step workflow; feedback loop;
contained comparison; cause → effect; checklist anchored to actual objects. Name the argument
before writing the prompt. Every arrow has an unambiguous start, direction and target.

Avoid a giant generic icon unrelated to the sentence; tiny sketches in leftover space;
decorative boxes around every bullet; dense fake dashboards; excessive stickers; 3D/glow;
four competing accent colors. Empty space is useful; empty placeholder boxes are not.

Main text remains crisp. Sketch imperfection belongs to line work, not spelling or baseline chaos.
Keep the strongest heading on the slide itself. In a video composition, avoid another equally
large header repeating it. Logos do not need to be repeated both inside and outside the slide.

## Respect an existing template

Inventory colors, fonts, repeated header/footer rules and authentic logos before generation.
Request a minimal two-slide light/dark proof. Match the palette, not just the black background.
Keep an intentional quiet safe area if assets will be overlaid. Do not draw the logos with AI.
Logos use contain-fit, original proportions and a restrained common optical size. The count
is configurable: zero, one or several; no brand initials are embedded in the reusable engine.

Real interface demonstrations use real captures with visible product/version context when needed.
If drawing a conceptual UI, call it a scheme; do not pass it off as a product screenshot.
Blur/redact private data before packaging. Do not put real secrets into a screenshot prompt.

## Accepted examples

`examples/media/light.png`: an untidy text list becomes three clear cards. The speech bubble
is an instruction; the yellow arrow explains the transformation.
`examples/media/dark.png`: reload extension → refresh page → save and verify, with a return
loop. The drawing encodes the retest cycle rather than showing three unrelated icons.

`examples/improved/` (light-v4, dark-v4): the same two arguments after the 23.09.2026 proof —
a wall of wavy text becomes three identical cards; on the dark slide yellow carries the check
(magnifier with «?»), the return loop and the question in the takeaway. Built with `art_inset: 0.92`.

Exact reference prompts are in `prompts/verified-examples.json`; prompts of the other course
slides are in `prompts/course-sketch-recipes.json`. The classic prefix is in
`prompts/classic-prefix.txt`; preserve its visual intent, not every literal card instruction.

## Enrichment without losing the style

Add carefully chosen paper/ink texture, coherent stroke width and purposeful hatching; do not
add noisy filter overlays. Introduce diagrams with a composition-specific drawing order. Keep
the final frame as strong as the static slide. Increase depth through hierarchy and spatial
relationships before reaching for drop shadows or cinematic camera effects.

## Proof 23.09.2026 — what changed the design and what did not

Same two slides (a before → after comparison and a retest loop), same model for everything
(gpt-image-2.5-sunburst, 1920×1088 → 1080), plus a control run of the original prompts, so
differences come from the prompt and not the model. Metrics: yellow share of area,
emphasis-ray bursts, margins at 1920 px; every slide was also read at full size and in
PowerPoint. The two V4 slides are bundled as `examples/improved/`; the other proof images and
the metrics script are not.

| Variant | Change | Result |
|---|---|---|
| Original prompts | — | yellow 11.4 % / 8.3 %, 9 ray bursts on light, side margins 3–4 %, instruction smaller than captions, disclaimer highlighted like a heading |
| V1 accent budget + type hierarchy | yellow on one phrase + one object, 3 sizes + footnote | clearest hierarchy; dark slide best of all: outlined puzzle, «?» inside the magnifier; light footnote too small at «a quarter» |
| V2 margins by prompt | grid percentages, mirrored margins | **rejected**: the model ignored the numbers (light 4.2 % / 3.7 %), and added a random yellow word |
| V3 drawing language + calm tokens | outline-first, identical repeats, no pictograms, warm ink | strongest meaning: «wall of text → identical cards»; yellow 2.8 % |
| **V4 = V1 + V3** (footnote at label size) | now the semantic prefix + `*-calm` palettes | kept: single entry point per slide, correct Cyrillic, calm tone; with `art_inset 0.92` margins L7.4/R7.1 (light) and L9.5/R9.3 (dark), 0 violations; PowerPoint render = engine render (mean pixel diff 0.4/255) |

Lessons: (1) always include a control with the new model — otherwise a model change passes for a
prompt improvement; (2) numbers in a prompt do not buy geometry — enforce margins at build time
(`art_inset`); (3) «a quarter of the heading» is unreadable on a projector — the footnote floor is
the object-label size; (4) the same prefix also worked with gemini-3.1-flash-image-preview on a
fresh slide (one yellow highlight, outline drawing, clean Cyrillic).
