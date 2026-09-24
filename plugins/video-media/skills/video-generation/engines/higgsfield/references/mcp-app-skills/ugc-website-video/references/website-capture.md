# Website capture — real mobile stills from the URL (sandbox headless Chromium)

Produce `output/site_full.png` (one mobile full-page capture → the section map) plus dedicated stills
of the USEFUL sections (product, reviews, specs, pricing, individual feature screens) that become the
overlay cards. Real pixels only — never generated, never upscaled or restyled. Do not size or crop
here; geometry is step D of `screen-broll-and-composite.md` and overrides anything in this file. One
product = one site; never capture a competitor or an unrelated page.

The sandbox is ephemeral (SKILL.md): pre-create `media_upload` slots for `site_full.png` and the
expected section stills first, then capture AND upload in ONE `sandbox_exec` call:

```bash
node ${HF_WORKFLOWS}/ugc-website-video/scripts/capture_site.mjs <url> --out output/site_full.png     # mobile full-page (overlays auto-dismissed)
node ${HF_WORKFLOWS}/ugc-website-video/scripts/capture_site.mjs <url> --sections "Reviews,Top review,Pricing,Free plan,Specifications,Dashboard,Search,Product gallery" --outdir output
# bot-wall / empty-page check without a vision tool — the page's own text and the file size
curl -sL -A 'Mozilla/5.0' "<url>" -o page.html
grep -Eic 'captcha|verify you are human|cf-browser-verification|access denied|enable javascript' page.html
python3 -c "import os;print('site_full bytes', os.path.getsize('output/site_full.png'))"
for f in output/*.png; do curl -X PUT --upload-file "$f" "<upload_url for $f>"; done
```

(`media_confirm` after the call; slots for sections that were not found simply go unused.)

**Read the capture result from the command output, not from the picture.** The script prints one JSON
line per capture — `{kind:"full"|"section", label, path, exists, rect}` — and unfound sections print an
`error` line and are skipped. What the script guarantees:

- **`exists` is true before the line prints** — a caller chaining `&&` off that line can rely on the
  PNG being on disk, not still flushing.
- **`rect`** is the section's document-absolute position (`{top, height, dpr}`, CSS px + device ratio) —
  crop bands with `rect.top * rect.dpr`, never with a y-fraction (page height swings ~14% between runs).
  A lazy section that never painted comes back `null`; skip that card rather than cropping blind.
- **Google One Tap is blocked at the network layer** (`accounts.google.com` / `gsi/client` aborted) plus
  a DOM sweep, because it renders in a cross-origin iframe the text-based dismissal cannot reach — and it
  lands exactly over the hero. Analytics is deliberately NOT blocked — blocking `googletagmanager` can
  break hydration and return a single blank viewport.
- **Lazy content gets a slower pass** (500px steps, ~260ms dwell, bottom hold) and the anchors are
  re-probed with up to two extra passes while any label is still missing.

Treat the capture as a **bot wall / dead page** when the grep above hits a CAPTCHA or access-denied
marker, or `site_full.png` comes back implausibly small (a few KB), or fewer than 3 section stills
succeeded — then take the failure path below and build no cards from that frame.

The `--sections` run clicks matching tabs and headings, centres each in the viewport (site chrome stays
in frame) and saves `output/section_<label>.png`. **Capture generously (~6-10 stills)** — card count
equals the number of distinct useful stills. Be GRANULAR: break broad sections into individual feature
screens (dashboard, search, editor…), a couple of review shots, pricing plus a specific plan, specs,
distinct product views. Skip filler (nav, footer, logo strips) — it never becomes a card. This is the
lever for "more screenshots": capture more, never stretch the windows.

**Hero still.** Pass the site's brand or H1 wording to `--sections` so one still lands at the top of the
page with logo and navbar in frame — that still is the hero card, and it removes any need to measure
bands. Content behind a tab or accordion (reviews, pricing, specs) is usually NOT in the single
full-page shot, which is exactly what the sections run is for.

**Section map.** From the full capture and, if useful, the page HTML (`curl` it and read the heading
order), record the sections top→bottom with approximate height fractions and a key/filler flag, e.g.
`{label:"hero", y:0.00-0.18, key:true} … {label:"footer", y:0.94-1.00, key:false}`. The map drives the
monologue order and the card order; filler never becomes a card.

## Failure = ask, then degrade (hard gate, on the FIRST try)

Any first-try failure — script error / bot wall / behind a login / unreachable / **fewer than 3 usable
cards** — ask the user immediately with ONE question ("Couldn't capture the site"), two options:

- **"I'll send screenshots"** — the user pastes the key screens (product, reviews, price, specs). They
  replace the capture: bring each one in with `media_upload_and_confirm` and use it as a section
  still **as-is**. They are usually DESKTOP frames — do
  not mobilise them, do not crop them to 3:4, skip the hero band work, and never cover-crop; the
  contain-fit box handles a wide frame (it just lands shorter).
- **"Make it without the site"** — go straight to the degrade path.

No self-started retries, no web-searching for images, never pull an image from anywhere but the page,
and never fabricate or AI-generate a UI. Screen content is the real capture OR the user's screenshots —
nothing else.

**If no screenshots arrive** (the user picks "make it without the site", ignores the question, or sends
nothing) → **degrade, do not dead-end**: generate the talking-head-only video (full creator + monologue
spine, no insets in the composite) and state in the report that the site could not be shown.

## Notes

- Do not upscale, restyle or edit the capture. Legible real UI is the whole point.
- If the mobile capture still shows a cookie banner (consent rendered in a cross-origin iframe), note it
  and do not turn a banner-covered frame into a card.
