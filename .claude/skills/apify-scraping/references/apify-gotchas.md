# Gotchas and cost guardrails

> Источник: apify/agent-skills (apify-ultimate-scraper), выдернут 2026-07-14.

## Pricing models

| Model | How it works | Action before running |
|-------|-------------|----------------------|
| FREE | No per-result cost, only platform compute | None needed |
| PAY_PER_EVENT (PPE) | Charged per result item | MUST estimate cost first |
| FLAT_PRICE_PER_MONTH | Monthly subscription | Verify user has active subscription |

To check an Actor's pricing:

    apify actors info "ACTOR_ID" --user-agent apify-agent-skills/apify-ultimate-scraper --json

Read `.currentPricingInfo.pricingModel` and `.currentPricingInfo.pricePerEvent`.

## Cost estimation protocol

Before running any PPE Actor:

1. Get the per-event price from Actor info (`.currentPricingInfo.pricePerEvent`)
2. Multiply by the requested result count
3. Present the estimate to the user with this disclaimer:

> **Estimated cost: ~$X for Y results.** This is a rough estimate only - actual costs can vary significantly depending on the Actor, data complexity, retries, and platform changes. Always check your Apify billing dashboard for actual charges.

4. If estimate > $5: warn explicitly
5. If estimate > $20: require explicit user confirmation before proceeding

**Important:** Cost estimates in the workflow guides are approximate and may be inaccurate. Always present them as rough guidance with the disclaimer above, never as exact amounts.

## Common pitfalls

**Cookie-dependent Actors**
Some social media scrapers require cookies or login sessions. If an Actor returns auth errors or empty results unexpectedly, check its README:

    apify actors info "ACTOR_ID" --user-agent apify-agent-skills/apify-ultimate-scraper --readme

Look for mentions of "cookies", "login", "session", or "proxy".

**Input mechanics**
Actor input is one JSON object, not an array. `--input` accepts inline JSON object input only; wrap inline JSON in quotes to avoid shell parsing issues. For JSON files or complex inputs, use `--input-file input.json`. If the CLI reports parse, path, or object-shape input errors, inspect the schema again with `apify actors info "ACTOR_ID" --user-agent apify-agent-skills/apify-ultimate-scraper --input --json`.

    apify actors call "ACTOR_ID" --input '{"maxItems":10}' --user-agent apify-agent-skills/apify-ultimate-scraper --json

Prefer this for larger inputs:

    apify actors call "ACTOR_ID" --input-file input.json --user-agent apify-agent-skills/apify-ultimate-scraper --json

**Rate limiting on large scrapes**
Platforms throttle or block large-volume scraping. Mitigations:
- Use proxy configuration when available: `"proxyConfiguration": {"useApifyProxy": true}`
- Set reasonable concurrency limits (check the Actor's `maxConcurrency` input)
- For 1,000+ results, suggest splitting into smaller batches

**Empty results**
Common causes:
- Too-narrow search query or geo-restriction (try broader terms)
- Platform blocking without proxy (enable Apify Proxy)
- Actor requires cookies/login but none provided
- Wrong input field name (always verify with `--input --json`)
- **Hashtag passed with or without the leading `#`** - Actors disagree; some strip it, some search for the literal string `#tag` and return nothing. Try both spellings before concluding the tag is dead.
- **Field name is `hashtags` in one Actor and `hashtagList` in another** - same data, different key. This is the single most common cause of a silent empty dataset on hashtag scrapes.
- **Profile passed as a full URL where the Actor expects a bare username** (or the reverse). `apify/instagram-reel-scraper` accepts both in `username[]`, most others do not.

**maxResults vs maxCrawledPages**
Different Actors use different limit field names. Common variants:
- `maxResults`, `resultsLimit`, `maxItems` - limit output items
- `maxCrawledPages`, `maxRequestsPerCrawl` - limit pages visited
Always fetch the input schema to find the correct field for the specific Actor.

**Deprecated Actors**
Check `.isDeprecated` in `apify actors info "ACTOR_ID" --user-agent apify-agent-skills/apify-ultimate-scraper --json`. If `true`:
1. Search for alternatives: `apify actors search "SIMILAR_KEYWORDS" --user-agent apify-agent-skills/apify-ultimate-scraper --json`
2. Prefer `apify` tier replacements over `community` alternatives

**LinkedIn pricing**
LinkedIn Actors are all PPE and vary significantly:
- `harvestapi/` Actors: generally cheaper ($0.001-0.01/result)
- `apimaestro/` Actors: generally more expensive ($0.005-0.02/result)
- `dev_fusion/` Actors: mid-range, useful for mass scraping with email enrichment
Always compare pricing before selecting a LinkedIn Actor.

**SEO tool pricing**
`radeance/` SEO scrapers (SimilarWeb, Ahrefs, SEMrush, Moz) have the highest per-result costs ($0.005-0.0275/result). For large-scale SEO analysis, estimate costs carefully and suggest batching.

## Social trendwatching: cost defaults and how trends are actually mined

Recurring job: "find what is going viral in niche X on Instagram / TikTok / YouTube".
Two things make or break it - the defaults you run with, and the fact that the feature
people expect does not exist.

**There is no "give me platform X trends" Actor.** No Apify Actor exposes a global
trending feed for a niche. Trends are mined in three ways, and you pick per task:

1. **Hashtag scrape** with top/recent sorting - fastest entry point for a topic.
2. **Profile scrape of niche opinion leaders** - the highest-signal source: you learn
   what works for *this* audience, not what is globally popular.
3. **Keyword search inside the niche** - fills gaps the first two miss.

This is a feature, not a limitation. A global trending feed is dominated by mass-market
content that a niche account cannot reproduce or convert. Filtering by hashtag and by a
curated profile list gives trends that are already validated on the target audience.

**Cost defaults for trendwatching runs.** [сервис]ing means running the same Actors
weekly over a growing account list, so defaults matter more than one-off savings:

| Setting | Default | Why |
|---------|---------|-----|
| results per Actor run | **20-30** | enough to compute a median and take the top 20%; more items rarely change which videos win |
| `downloadVideos` / `includeDownloadedVideo` | **false** | video bytes are the most expensive part of the run and are useless for shortlisting - watch the 5-10 winners by URL instead |
| `downloadCovers` | **false** unless the run feeds a visual board | cover images are cheap but add up across weekly runs on hundreds of accounts |
| `includeTranscript` | **false** | transcribe only the shortlisted videos, and cheaper elsewhere (e.g. Gemini) |
| `skipPinnedPosts` | **true** | pinned posts accumulate views for months and distort the median, making real outliers invisible |
| >100 results in one run | **confirm with the user first** | this is where a $2 job silently becomes a $30 one |

**Preferred Actors for this job** (IDs from `curated-actors.md`, verify before calling):

| Platform | Actor | Note |
|----------|-------|------|
| Instagram | `apify/instagram-reel-scraper` | reels with engagement fields; accepts both bare usernames and profile URLs in `username[]` |
| Instagram | `apify/instagram-hashtag-scraper` | hashtag route |
| Instagram | `apify/instagram-scraper` | general fallback |
| TikTok | `clockworks/free-tiktok-scraper` | free tier, limited volume - fine for weekly shortlists |
| TikTok | `clockworks/tiktok-scraper` | paid, more stable, covers trending feeds |
| YouTube | `streamers/youtube-scraper` | videos + metrics |

**Trending sounds** are not a separate Actor either. Scrape videos, then group by
`musicInfo` / `musicMeta` and take the 5 most repeated tracks. A track that shows up in
5 of 30 outlier videos is a live trend; anything appearing once is noise.

**Signal fields worth keeping** in the output for later analysis: `caption`, hashtags,
`musicInfo`, video duration, video URL, play/like/comment/share counts, and top comments
(comments often state outright what hooked people - the cheapest source of "why viral").

## Error recovery

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `status: FAILED` in run output | Actor crashed or input invalid | Read `.statusMessage` in JSON; check run log at `https://console.apify.com/actors/runs/RUN_ID/log` |
| `isDeprecated: true` in Actor info | Actor is end-of-life | Search for replacement: `apify actors search "KEYWORDS" --user-agent apify-agent-skills/apify-ultimate-scraper --json` |
| Empty dataset (0 items) | Query too narrow, geo-restriction, or anti-bot block | Broaden search terms; enable Apify Proxy; check Actor README with `apify actors info ACTOR_ID --user-agent apify-agent-skills/apify-ultimate-scraper --readme` |
| Run takes >10 minutes | Large scrape or slow target site | Switch to fire-and-forget: `apify actors start --user-agent apify-agent-skills/apify-ultimate-scraper --json`, poll with `apify runs info RUN_ID --user-agent apify-agent-skills/apify-ultimate-scraper --json` |

## Why Apify Actors vs raw HTTP scraping

Many n8n and automation workflows use raw HTTP Request nodes or self-hosted Puppeteer for web scraping. These hit common walls that Apify Actors handle transparently:

**Cloudflare and WAF bypass**
Raw HTTP requests fail on sites with Cloudflare Turnstile, DataDome, or other WAFs. Apify Actors use residential proxies and browser fingerprint rotation automatically. For the toughest sites, use `apify/camoufox-scraper`.

**JavaScript-rendered pages (SPAs)**
React, Vue, and Angular sites return empty HTML to plain HTTP requests. Apify's `apify/playwright-scraper` and `apify/camoufox-scraper` fully render JavaScript before extracting data.

**Anti-bot fingerprinting**
Even headless browsers get detected via TLS fingerprints (JA3 hashes). Apify's browser pool rotates fingerprints across requests automatically.

**Session and cookie management**
Social media platforms (LinkedIn, Instagram) require persistent sessions. Social media Actors handle cookie management and session rotation internally.

**Scaling without infrastructure**
Self-hosted Puppeteer at scale requires 4-8 GB RAM per browser instance. Apify Actors run on serverless infrastructure - no browser pool management, no RAM provisioning, no Docker orchestration.

## Platform-specific rate limits

**Instagram:** Aggressive rate limiting. Keep `maxResults` under 200 per run for profile/post scrapers. Use delays between runs. Instagram API scrapers (`apify/instagram-api-scraper`) have higher limits than browser-based ones.

**LinkedIn:** All LinkedIn Actors are community-maintained and PPE. LinkedIn actively blocks scraping at scale. Keep batch sizes under 100 profiles. Space runs at least 5 minutes apart. Expect occasional empty results.

**TikTok:** Anti-bot measures increasing. `clockworks/tiktok-scraper` handles most cases. For blocked regions, enable Apify Proxy with residential IPs.

**Google Maps:** Generally stable. Set `language: "en"` explicitly for consistent results. Large-area searches may return different results depending on zoom level - use specific location queries over broad city names.

**Amazon/E-commerce:** Heavy anti-bot. The `apify/e-commerce-scraping-tool` handles this via built-in proxy rotation. Raw HTTP requests will fail.
