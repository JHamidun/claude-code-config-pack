# Manifest v1

Start from `templates/deck.json`. All paths are relative to the manifest and stay inside its
project directory. Stable IDs use lowercase ASCII letters/digits/hyphens/underscores, max64.
Slide order is the array order; notes belong to the same object/ID, never a second positional list.

Required deck fields: `version:1`, `canvas:{width:1920,height:1080}`, `slides:[...]`.
Optional: `title`, `language`, `themes` (custom palette definitions), `branding:[]`, `art_inset`.
Each theme defines background/ink/accent/secondary six-digit colors and typography hints.
Built-in keys: `exec-sketch-light`, `exec-sketch-dark`, `exec-sketch-classic`,
`exec-sketch-light-calm`, `exec-sketch-dark-calm` (the calm pair is the default for new decks).

Required slide fields: `id`, `title`, `theme`, `text` (exact additional strings), `visual`
(semantic visual argument), `notes:{spoken:[paragraphs...]}`.
Optional: `notes.stage`, `sources`, `overlays`, `draw_order` (semantic objects in reveal order),
`art_inset` (overrides the deck value).

`art_inset` (0.8–1.0, default 1.0) scales the bound artwork around the slide centre at build time;
the margin is filled with the artwork's own paper colour (median of its corners), in the PNG, PDF
and the PPTX slide background, so no seam shows. It is layout only: not part of the art signature,
changing it never makes a binding stale, and `build-manifest.json` records it per slide. Values
outside the range, booleans and strings are rejected; so is `art_inset < 1` together with
`branding`/`overlays`, whose rectangles would no longer match the reserved quiet areas.

`art_prompt` overrides prompt synthesis. It is used in the verified historical examples to
retain their actual prompt; remove it before authoring a new slide. Binding also hashes title,
text, visual argument, palette, canvas and reservations, so changes cannot silently reuse art.

The `bind` command writes `binding:{image,image_sha256,prompt_sha256,art_signature,provider}`.
It strips image metadata by re-encoding to a true PNG. Bind explicitly only after verifying
the supplied image really corresponds to the slide; a hash is not semantic verification.

## Authentic assets

Deck `branding` and per-slide `overlays` both use:

```json
{"role":"logo","image":"media/brand.png","sha256":"actual-file-sha256","rect":[0.88,0.025,0.06,0.07]}
```

Rectangles are normalized x/y/width/height. They are contain-fit boxes, not stretch operations.
Any overlap with generated labels must be caught visually. Reserve quiet space in the prompt.
Use role `screenshot`, `portrait` or `qr` for other real assets. PNG/JPEG/WebP are accepted with
matching magic/extension; rasterize SVG safely in your own asset-preparation step. Supply only
licensed/authorized assets. Native text/chart overlays are outside this simple raster engine.

## Outputs

`presentation.pptx`, `presentation.pdf`, `preview.html` (offline, embeds images), `slides/*.png`,
`contact-sheet.png`, `speaker-notes.txt`, `teleprompter.txt`, `build-manifest.json`, `qa.json`,
`motion-handoff.json`. Technical QA is strict on IDs/hashes and exports but not OCR or fact-checking.
