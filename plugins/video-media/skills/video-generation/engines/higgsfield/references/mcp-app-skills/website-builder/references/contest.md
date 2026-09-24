# App contest — how to enter, and how it shapes the build

Higgsfield runs an app contest with a **$100,000 total prize pool**. If the
user wants to enter (or asks what the contest is), this is the reference.
`participate_in_contest` is the tool that submits an app.

> Prizes, dates, and rules below are the **current** contest as of 2026-07-08.
> The contest is admin-curated and recurs — treat specifics (amounts, dates) as
> this round's, and the live details are on
> `https://higgsfield.ai/supercomputer/apps?tab=prizes`. The mechanics
> (auto-publish on entry, social-link submission, judging on real usage) are
> stable.

## What it is

- **$100,000 total.** 1st **$25,000**, 2nd **$15,000**, 3rd **$10,000**, plus
  **10 honorable mentions at $5,000 each**.
- **Timeline (this round):** submissions open **Jul 8, 2026**, close **Jul 22,
  2026 (8:00 AM PT)**; judging Jul 22–29; winners announced **Jul 29, 2026**.
  Rankings refresh every 24h during the contest.
- **No fixed theme** — build anything that gives people a reason to *create* on
  Higgsfield (productivity tools, games, image/video generators, novelty apps).

## How entering shapes what you build (bake this in from the start)

Even before the user mentions the contest, these are just good `type: "app"`
practice — and they're the eligibility bar and the scoring rubric:

- **Must use Higgsfield image and/or video generation.** An app that routes
  generation through a third-party API instead of Higgsfield is DISQUALIFIED.
  (This is already the app rule — generation runs on Higgsfield via the fnf
  SDK; never offer a bring-your-own-API path.)
- **Original work, no third-party IP.** No protected characters, films, music,
  celebrities, or brands — in the app's concept, assets, or generated output
  framing. (Also the platform content rule.)
- **Must be freshly published** on Higgsfield on/after the contest open date —
  a brand-new listing, not a pre-existing app.
- **Judging is mostly real usage.** Weights: **Usage generated 40%** (the
  primary metric — total Higgsfield generation by users inside the app),
  **Creativity & concept 30%**, **social engagement 15%**, **in-app gallery
  engagement 15%**. So design for repeat generation: a fast path to a first
  result, an obvious reason to generate again, shareable output. Artificially
  inflated usage is discounted at Higgsfield's discretion.

## Entering — `participate_in_contest` (it publishes for you)

An app not yet on the community feed is **published automatically by the
entry** — no separate `publish_website` call needed. The flow when the user
asks to enter:

1. **Make it listable.** The app needs a **live production deploy**
   (`deploy_website`) — an undeployed app is rejected ("deploy first"). And
   because the entry lists the app on the feed, the page metadata (`og_title`,
   cover, description in `app/src/app-meta.json`) must be filled with real
   values BEFORE entering — the auto-published listing renders from it, and an
   empty `og_title` makes it invisible on the feed (see
   `references/app-flow.md`). Deploy after changing metadata.
2. **Get the social link(s).** The contest requires the app posted to at least
   one **public** social platform (Instagram, TikTok, YouTube, or X) with a
   link back to the Higgsfield app and the **`#HiggsfieldApp`** hashtag.
   `participate_in_contest` requires one or more `urls`, each a link to that
   public post — any other host is rejected. The user posts it themselves; ask
   for the URL(s) if you don't have them, and remind them to include the app
   link + `#HiggsfieldApp` in the post.
3. **Submit.** Call `participate_in_contest` with the `website_id` and the
   `urls`. There's a single active contest, so no contest id. One entry per app
   — calling again OVERWRITES the urls (use it to fix or add links, it doesn't
   create a second entry).

```jsonc
// after deploy_website has shipped this website_id (metadata filled)
participate_in_contest({
  "website_id": "<the deployed app>",
  "urls": ["https://x.com/<user>/status/…"]  // ≥1 public post, #HiggsfieldApp
})
```

If the user asks to enter but hasn't posted anywhere yet, get the app deployed
with real metadata, then tell them the one thing only they can do — post it
publicly with the app link and `#HiggsfieldApp` — and enter as soon as they
give you the URL.

## Eligibility (relay if asked)

18+, a Higgsfield account, free to enter. No third-party IP. Prizes paid within
30 days of the announcement after eligibility verification; winners cover their
own taxes. Void where prohibited. Jury decisions are final. Full official rules
are on the prizes page.
